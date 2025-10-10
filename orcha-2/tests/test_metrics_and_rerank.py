#!/usr/bin/env python3
"""
Lightweight tests for metrics and optional semantic reranking.
Run with: python -m or just python this file.
"""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

repo_root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(repo_root))

from mcp.search.metrics import precision_at_k, recall_at_k, average_precision, mean_average_precision, ndcg_at_k
from mcp.search.engine import SearchEngine
from mcp.search.rerank import SemanticReranker


class _Item:
    def __init__(self, item: str):
        self.item = item

class _Category:
    def __init__(self, name: str, items):
        self.category = name
        self.items = [ _Item(x) for x in items ]


def run_metrics_demo():
    pred = ["pepperoni pizza", "margherita pizza", "bbq wings", "caesar salad"]
    rel = {"margherita pizza", "pepperoni pizza"}
    print("precision@1 =", precision_at_k(pred, rel, 1))
    print("recall@2 =", recall_at_k(pred, rel, 2))
    print("AP =", average_precision(pred, rel))
    print("MAP =", mean_average_precision([pred], [rel]))
    print("nDCG@3 =", ndcg_at_k(pred, {"pepperoni pizza": 3.0, "margherita pizza": 2.0}, 3))


def run_rerank_demo():
    cats = [
        _Category("Pizzas", ["Margherita Pizza", "Pepperoni Pizza", "Hawaiian Pizza"]),
        _Category("Wings", ["BBQ Wings"]) ,
    ]
    engine = SearchEngine(cats)
    base = engine.search("pizza", top_k=3)
    print("Base top-3:", [x.item for x in base])

    rr = SemanticReranker()
    if rr.enabled:
        reranked = rr.rerank("pepperoni pizza", base)
        print("Reranked top-3:", [x.item for x in reranked])
    else:
        print("Semantic reranker not enabled (sentence-transformers not installed)")


if __name__ == "__main__":
    print("-- Metrics Demo --")
    run_metrics_demo()
    print("\n-- Rerank Demo --")
    run_rerank_demo()
