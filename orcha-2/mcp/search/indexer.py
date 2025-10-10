import os
import pickle
import hashlib
from pathlib import Path
from rank_bm25 import BM25Okapi

class MenuIndexer:
    def __init__(self, categories, cache_dir="data/indexes"):
        # Flatten all menu items
        self.items = [item for cat in categories for item in cat.items]
        self.docs = [item.item.lower() for item in self.items]
        self.tokens = [doc.split() for doc in self.docs]
        
        # Setup caching
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate cache key from menu content
        content_hash = self._generate_hash()
        self.cache_file = self.cache_dir / f"bm25_index_{content_hash}.pkl"
        
        # Try to load from cache or build fresh
        self.bm25 = self._load_or_build_index()
        self.lookup = {item.item.lower(): item for item in self.items}
    
    def _generate_hash(self):
        """Generate deterministic hash from menu items for caching"""
        content = "\n".join(sorted(self.docs))
        return hashlib.md5(content.encode()).hexdigest()[:8]
    
    def _load_or_build_index(self):
        """Load BM25 index from cache or build and save"""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'rb') as f:
                    return pickle.load(f)
            except Exception as e:
                print(f"Cache load failed: {e}, rebuilding index")
        
        # Build new index
        bm25 = BM25Okapi(self.tokens)
        
        # Save to cache
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(bm25, f)
        except Exception as e:
            print(f"Cache save failed: {e}")
        
        return bm25

    def search(self, query, k=5):
        query_tokens = query.lower().split()
        scores = self.bm25.get_scores(query_tokens)
        ranked = sorted(zip(self.items, scores), key=lambda x: x[1], reverse=True)[:k]
        return [item for item, _ in ranked]

# Backwards-compatible alias expected by some tests/docs
BM25Indexer = MenuIndexer
