from typing import List, Optional, Dict
from core.services.menu.menu_service import MenuService
from rank_bm25 import BM25Okapi
import pickle
import logging
import re
from pathlib import Path
from collections import defaultdict

from models.base.menu_models import OrderType

try:
    from nltk.stem import SnowballStemmer

    _STEMMER = SnowballStemmer("english")
    _HAS_STEMMER = True
except ImportError:
    _STEMMER = None
    _HAS_STEMMER = False
    logging.warning(
        "NLTK SnowballStemmer not available. Install with: pip install nltk"
    )


logger = logging.getLogger(__name__)


class MenuSearchService:
    def __init__(self, menu_service: MenuService) -> None:
        self._menu_service: MenuService = menu_service
        self._bm25_index_base_path = Path("data") / self._menu_service.get_vendor()

    async def sync_indexes(self) -> None:
        """Public method to synchronize all indexes.

        This wraps the internal index syncs and logs failures.
        """
        try:
            await self._sync_b25_indexes()
            logger.info("MenuSearchService: All indexes synced successfully")
        except Exception as exc:
            logger.exception("MenuSearchService: Failed to sync indexes: %s", exc)
            # Re-raise so callers can decide how to handle
            raise

    async def _sync_b25_indexes(self) -> None:
        """Internal coordinator for BM25 index synchronization."""
        try:
            await self._sync_b25_categories_index()
        except Exception as exc:
            logger.exception("MenuSearchService: Error syncing BM25 indexes: %s", exc)
            raise

    async def _sync_b25_categories_index(self) -> None:
        """Create a BM25 index for categories for each order type and persist it to disk.

        This method is defensive: it logs and continues on per-order-type failures so
        a single bad order type does not abort the whole sync.
        """
        try:
            order_types: List[OrderType] = await self._menu_service.get_order_types()
        except Exception as exc:
            logger.exception("MenuSearchService: Unable to fetch order types: %s", exc)
            raise

        try:
            self._bm25_index_base_path.mkdir(parents=True, exist_ok=True)
        except Exception as exc:
            logger.exception(
                "MenuSearchService: Failed to create directory %s: %s",
                self._bm25_index_base_path,
                exc,
            )
            raise

        for ot in order_types:
            try:
                order_type_name = getattr(ot, "orderType", str(ot))

                snake = ot.get_snake_case()

                logger.info(
                    "MenuSearchService: Syncing categories BM25 index for order type '%s' (snake: %s)",
                    order_type_name,
                    snake,
                )

                categories = await self._menu_service.get_categories(order_type_name)

                # Tokenize categories defensively (lowercase for case-insensitive search)
                tokenized_cats = [str(cat).lower().split() for cat in categories]

                bm25_index = BM25Okapi(tokenized_cats)

                index_path = (
                    self._bm25_index_base_path / f"{snake}_categories_b25_index.pkl"
                )

                with open(index_path, "wb") as f:
                    pickle.dump(bm25_index, f, protocol=pickle.HIGHEST_PROTOCOL)

                categories_path = self._bm25_index_base_path / f"{snake}_categories.pkl"

                with open(categories_path, "wb") as f:
                    pickle.dump(categories, f, protocol=pickle.HIGHEST_PROTOCOL)

            except Exception as exc:
                # Catch-all per-order-type to avoid aborting the whole loop
                logger.exception(
                    "MenuSearchService: Unexpected error while processing order type %s: %s",
                    ot,
                    exc,
                )
                continue

    async def simple_search_categories(
        self, query: str, orderType: str, top_n: int = 5
    ) -> List[str]:
        """Perform a simple BM25 search over categories for a given order type.

        Args:
            query (str): The search query string.
            orderType (str): The order type context (e.g., "Delivery", "Pickup").
            top_n (int): Number of top results to return.
        Returns:
            List[str]: List of top matching category names.
        """
        # Determine snake-case filename for the order type

        o_type = OrderType(orderType=orderType, requiresAddress=False)
        snake = o_type.get_snake_case()
        index_path = self._bm25_index_base_path / f"{snake}_categories_b25_index.pkl"
        docs_path = self._bm25_index_base_path / f"{snake}_categories.pkl"

        bm25_index: Optional[BM25Okapi] = None
        docs: List[str] = []

        if not index_path.exists() or not docs_path.exists():
            await self.sync_indexes()

        # Try to load prebuilt index from disk (may exist now after sync)
        if index_path.exists():
            try:
                with open(index_path, "rb") as f:
                    bm25_index = pickle.load(f)
                with open(docs_path, "rb") as f:
                    docs = pickle.load(f)
            except Exception as exc:
                logger.exception(
                    "MenuSearchService: Failed to load BM25 index from %s: %s",
                    index_path,
                    exc,
                )
                bm25_index = None

        if bm25_index is None:
            logger.warning(
                "MenuSearchService: BM25 index not available for orderType '%s'; returning empty results",
                orderType,
            )
            raise RuntimeError(f"BM25 index not available for orderType '{orderType}'")

        return self._simple_bm25_search(query, bm25_index, docs, top_n)

    def _stem_tokens(self, tokens: List[str]) -> List[str]:
        """Apply stemming to a list of tokens.

        Args:
            tokens: List of word tokens to stem

        Returns:
            List of stemmed tokens, or original tokens if stemmer not available
        """
        if not _HAS_STEMMER or _STEMMER is None:
            return tokens

        try:
            return [_STEMMER.stem(token) for token in tokens]
        except Exception as exc:
            logger.warning(
                "MenuSearchService: Stemming failed, using original tokens: %s", exc
            )
            return tokens

    def _reciprocal_rank_fusion(
        self, ranked_lists: List[List[str]], k: int = 60
    ) -> List[str]:
        """Combine multiple ranked lists using Reciprocal Rank Fusion (RRF).

        RRF formula: score(doc) = sum(1 / (k + rank_i)) for all lists containing doc
        where k is a constant (typically 60) and rank_i is the rank in list i (1-indexed)

        Args:
            ranked_lists: List of ranked document lists (each is ordered by relevance)
            k: RRF constant parameter (default 60, recommended in literature)

        Returns:
            Fused list of documents ranked by combined RRF scores
        """
        if not ranked_lists:
            return []

        if len(ranked_lists) == 1:
            return ranked_lists[0]

        # Calculate RRF scores for each document
        rrf_scores: Dict[str, float] = defaultdict(float)

        for ranked_list in ranked_lists:
            for rank, doc in enumerate(ranked_list, start=1):
                # RRF score contribution from this list
                rrf_scores[doc] += 1.0 / (k + rank)

        # Sort documents by RRF score (descending)
        sorted_docs = sorted(rrf_scores.items(), key=lambda x: x[1], reverse=True)

        # Return only the document names, sorted by score
        return [doc for doc, score in sorted_docs]

    def _simple_bm25_search(
        self, query: str, bm25_index: BM25Okapi, docs: List[str], top_n: int
    ) -> List[str]:
        """Perform BM25 search with both original and stemmed queries, then fuse results.

        This method:
        1. Searches with the original (lowercased) query
        2. Searches with stemmed query tokens
        3. Combines results using Reciprocal Rank Fusion (RRF)
        4. Returns top_n results from the fused ranking

        Args:
            query: User's search query string
            bm25_index: Pre-built BM25 index
            docs: Original document strings (category names)
            top_n: Number of top results to return

        Returns:
            List of top matching category names
        """
        if not query or not query.strip():
            logger.warning(
                "MenuSearchService: empty query passed to _simple_bm25_search"
            )
            return []

        try:
            # Tokenize and lowercase the query
            tokenized_query = query.lower().split()
            if not tokenized_query:
                return []

            # Get results with original query (multiply top_n to have more candidates for fusion)
            search_top_n = max(top_n * 2, 10)  # Get more results for better fusion

            original_results = []
            try:
                # Get scores to filter out zero-score results
                scores = bm25_index.get_scores(tokenized_query)
                # Get indices sorted by score
                scored_indices = [(i, scores[i]) for i in range(len(scores))]
                # Filter out zero scores and sort by score descending
                non_zero_scored = [
                    (i, score) for i, score in scored_indices if score > 0
                ]
                non_zero_scored.sort(key=lambda x: x[1], reverse=True)

                # Get top documents with non-zero scores
                original_results = [
                    docs[i] for i, score in non_zero_scored[:search_top_n]
                ]

                logger.debug(
                    "MenuSearchService: Original query '%s' returned %d results (max score: %.3f)",
                    query,
                    len(original_results),
                    max(scores) if len(scores) > 0 else 0,
                )
            except Exception as exc:
                logger.warning(
                    "MenuSearchService: Original query search failed: %s", exc
                )

            # If stemmer is available, also search with stemmed query
            stemmed_results = []
            if _HAS_STEMMER and _STEMMER is not None:
                try:
                    stemmed_tokens = self._stem_tokens(tokenized_query)

                    # Only do stemmed search if tokens actually changed
                    if stemmed_tokens != tokenized_query:
                        # Get scores to filter out zero-score results
                        stemmed_scores = bm25_index.get_scores(stemmed_tokens)
                        # Get indices sorted by score
                        stemmed_scored_indices = [
                            (i, stemmed_scores[i]) for i in range(len(stemmed_scores))
                        ]
                        # Filter out zero scores and sort by score descending
                        stemmed_non_zero = [
                            (i, score)
                            for i, score in stemmed_scored_indices
                            if score > 0
                        ]
                        stemmed_non_zero.sort(key=lambda x: x[1], reverse=True)

                        # Get top documents with non-zero scores
                        stemmed_results = [
                            docs[i] for i, score in stemmed_non_zero[:search_top_n]
                        ]

                        logger.debug(
                            "MenuSearchService: Stemmed query '%s' -> '%s' returned %d results (max score: %.3f)",
                            " ".join(tokenized_query),
                            " ".join(stemmed_tokens),
                            len(stemmed_results),
                            max(stemmed_scores) if len(stemmed_scores) > 0 else 0,
                        )
                except Exception as exc:
                    logger.warning(
                        "MenuSearchService: Stemmed query search failed: %s", exc
                    )

            # Combine results using Reciprocal Rank Fusion
            ranked_lists = [list(original_results)]
            if stemmed_results:
                ranked_lists.append(list(stemmed_results))

            fused_results = self._reciprocal_rank_fusion(ranked_lists, k=60)

            # Return top_n results
            final_results = fused_results[:top_n]

            logger.info(
                "MenuSearchService: Query '%s' returned %d results (from %d original, %d stemmed)",
                query,
                len(final_results),
                len(original_results),
                len(stemmed_results),
            )

            return final_results

        except Exception as exc:
            logger.exception(
                "MenuSearchService: Error during _simple_bm25_search: %s", exc
            )
            return []
