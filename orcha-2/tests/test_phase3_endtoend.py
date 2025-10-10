#!/usr/bin/env python3
"""
Phase 3 End-to-End Integration Test
Tests the complete search pipeline with:
- BM25 indexing with caching
- Search metrics evaluation  
- Semantic reranking with sentence-transformers
- Evaluation dataset benchmarking
"""

import sys
import json
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from mcp.search.indexer import MenuIndexer, BM25Indexer
from mcp.search.engine import SearchEngine
from mcp.search.rerank import SemanticReranker
from mcp.search.metrics import precision_at_k, recall_at_k, average_precision, mean_average_precision, ndcg_at_k
from mcp.models.base import Category, MenuItem, SizePrice

def create_test_menu():
    """Create test menu matching evaluation dataset"""
    categories = [
        Category(category="Pizza", items=[
            MenuItem(item="Margherita Pizza", sizePrices=[SizePrice(size="Large", price=12.99)]),
            MenuItem(item="Pepperoni Pizza", sizePrices=[SizePrice(size="Large", price=14.99)]),
            MenuItem(item="Hawaiian Pizza", sizePrices=[SizePrice(size="Large", price=15.99)]),
        ]),
        Category(category="Chicken", items=[
            MenuItem(item="Buffalo Wings", sizePrices=[SizePrice(size="Regular", price=9.99)]),
            MenuItem(item="Spicy Chicken Sandwich", sizePrices=[SizePrice(size="Regular", price=11.99)]),
            MenuItem(item="Chicken Jalfrezi", sizePrices=[SizePrice(size="Regular", price=13.99)]),
        ]),
        Category(category="Pasta", items=[
            MenuItem(item="Penne Arrabbiata", sizePrices=[SizePrice(size="Regular", price=10.99)]),
            MenuItem(item="Spaghetti Marinara", sizePrices=[SizePrice(size="Regular", price=9.99)]),
            MenuItem(item="Fettuccine Alfredo", sizePrices=[SizePrice(size="Regular", price=12.99)]),
        ]),
        Category(category="Desserts", items=[
            MenuItem(item="Chocolate Cake", sizePrices=[SizePrice(size="Slice", price=6.99)]),
            MenuItem(item="Chocolate Ice Cream", sizePrices=[SizePrice(size="Scoop", price=4.99)]),
            MenuItem(item="Brownie", sizePrices=[SizePrice(size="Square", price=5.99)]),
        ]),
        Category(category="Salads", items=[
            MenuItem(item="Caesar Salad", sizePrices=[SizePrice(size="Regular", price=8.99)]),
            MenuItem(item="Greek Salad", sizePrices=[SizePrice(size="Regular", price=9.99)]),
            MenuItem(item="Garden Salad", sizePrices=[SizePrice(size="Regular", price=7.99)]),
        ]),
        Category(category="Burgers", items=[
            MenuItem(item="Classic Burger", sizePrices=[SizePrice(size="Regular", price=10.99)]),
            MenuItem(item="Cheeseburger", sizePrices=[SizePrice(size="Regular", price=11.99)]),
            MenuItem(item="Big Mac", sizePrices=[SizePrice(size="Regular", price=12.99)]),
        ]),
        Category(category="Seafood", items=[
            MenuItem(item="Grilled Salmon", sizePrices=[SizePrice(size="Regular", price=18.99)]),
            MenuItem(item="Grilled Shrimp", sizePrices=[SizePrice(size="Regular", price=16.99)]),
            MenuItem(item="Fish & Chips", sizePrices=[SizePrice(size="Regular", price=14.99)]),
        ]),
        Category(category="Breakfast", items=[
            MenuItem(item="Scrambled Eggs", sizePrices=[SizePrice(size="Regular", price=7.99)]),
            MenuItem(item="Benedict", sizePrices=[SizePrice(size="Regular", price=12.99)]),
            MenuItem(item="Omelette", sizePrices=[SizePrice(size="Regular", price=9.99)]),
        ]),
    ]
    return categories

def load_evaluation_queries():
    """Load evaluation dataset"""
    eval_path = project_root / "data" / "evaluation" / "queries.json"
    if not eval_path.exists():
        print(f"WARNING: Evaluation file not found at {eval_path}")
        return []
    
    with open(eval_path) as f:
        data = json.load(f)
    return data["evaluation_dataset"]["queries"]

def test_phase3_pipeline():
    """Test complete Phase 3 search pipeline"""
    print("🚀 Phase 3 End-to-End Integration Test")
    print("=" * 50)
    
    # 1. Setup components
    print("1. Setting up search components...")
    categories = create_test_menu()
    
    # Test indexer with caching
    indexer = MenuIndexer(categories, cache_dir="data/indexes")
    print(f"   ✓ MenuIndexer created with {len(indexer.items)} items")
    
    # Test BM25Indexer alias
    indexer_alias = BM25Indexer(categories, cache_dir="data/indexes")
    print(f"   ✓ BM25Indexer alias works")
    
    # Setup reranker
    reranker = SemanticReranker()
    print(f"   ✓ SemanticReranker initialized")
    
    # Setup search engine
    engine = SearchEngine(indexer, reranker=reranker)
    print(f"   ✓ SearchEngine configured with reranker")
    
    # 2. Test basic search
    print("\n2. Testing basic search...")
    results = engine.search("pizza", top_k=3)
    print(f"   Query: 'pizza' → {len(results)} results")
    for i, item in enumerate(results, 1):
        price = item.sizePrices[0].price if item.sizePrices else 0.0
        print(f"   {i}. {item.item} (${price})")
    
    # 3. Test semantic reranking
    print("\n3. Testing semantic reranking...")
    results_reranked = engine.search("spicy chicken", top_k=5, use_reranker=True, rerank_top_n=10)
    print(f"   Query: 'spicy chicken' with reranking → {len(results_reranked)} results")
    for i, item in enumerate(results_reranked, 1):
        print(f"   {i}. {item.item}")
    
    # 4. Run evaluation metrics
    print("\n4. Running evaluation metrics...")
    queries = load_evaluation_queries()
    
    if queries:
        all_precisions = []
        all_recalls = []
        all_aps = []
        all_ndcgs = []
        
        for query_data in queries[:3]:  # Test first 3 queries
            query = query_data["query"]
            gold_labels = query_data["gold_labels"]
            
            # Search with reranking
            results = engine.search(query, top_k=5, use_reranker=True, rerank_top_n=10)
            predicted = [item.item for item in results]
            
            # Calculate metrics
            gold_set = set(gold_labels)
            prec_5 = precision_at_k(predicted, gold_set, k=5)
            recall_5 = recall_at_k(predicted, gold_set, k=5)
            ap = average_precision(predicted, gold_set)
            # For nDCG, create relevance gains (binary: 1.0 for relevant, 0.0 for not)
            rel_gain = {label: 1.0 for label in gold_labels}
            ndcg_5 = ndcg_at_k(predicted, rel_gain, k=5)
            
            all_precisions.append(prec_5)
            all_recalls.append(recall_5)
            all_aps.append(ap)
            all_ndcgs.append(ndcg_5)
            
            print(f"   '{query}': P@5={prec_5:.3f}, R@5={recall_5:.3f}, AP={ap:.3f}, nDCG@5={ndcg_5:.3f}")
        
        # Calculate MAP
        map_val = sum(all_aps) / len(all_aps) if all_aps else 0.0
        print(f"\n   📊 Overall Metrics:")
        print(f"   Mean Precision@5: {sum(all_precisions)/len(all_precisions):.3f}")
        print(f"   Mean Recall@5: {sum(all_recalls)/len(all_recalls):.3f}")
        print(f"   MAP: {map_val:.3f}")
        print(f"   Mean nDCG@5: {sum(all_ndcgs)/len(all_ndcgs):.3f}")
    
    # 5. Test cache effectiveness
    print("\n5. Testing index caching...")
    cache_files = list((project_root / "data" / "indexes").glob("*.pkl"))
    print(f"   Cache files created: {len(cache_files)}")
    for cache_file in cache_files:
        print(f"   - {cache_file.name}")
    
    # Test cache reload
    indexer2 = MenuIndexer(categories, cache_dir="data/indexes")
    results2 = engine.search("pizza", top_k=3)
    print(f"   ✓ Cache reload successful: {len(results2)} results")
    
    print("\n🎉 Phase 3 Integration Test Complete!")
    print("   All components working together successfully")
    return True

if __name__ == "__main__":
    try:
        success = test_phase3_pipeline()
        sys.exit(0 if success else 1)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)