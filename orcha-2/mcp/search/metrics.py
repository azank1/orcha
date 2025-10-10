"""
Search metrics utilities for evaluating ranked retrieval.
Includes precision@k, recall@k, average precision (AP), mean average precision (MAP), and nDCG.
"""
from __future__ import annotations

from typing import Iterable, List, Sequence, Set
import math


def precision_at_k(pred: Sequence[str], rel: Set[str], k: int) -> float:
    if k <= 0:
        return 0.0
    top_k = pred[:k]
    if not top_k:
        return 0.0
    hits = sum(1 for x in top_k if x in rel)
    return hits / float(len(top_k))


def recall_at_k(pred: Sequence[str], rel: Set[str], k: int) -> float:
    if not rel:
        return 0.0
    top_k = pred[:k]
    hits = sum(1 for x in top_k if x in rel)
    return hits / float(len(rel))


def average_precision(pred: Sequence[str], rel: Set[str]) -> float:
    if not rel:
        return 0.0
    ap_sum = 0.0
    hits = 0
    for i, x in enumerate(pred, start=1):
        if x in rel:
            hits += 1
            ap_sum += hits / float(i)
    return ap_sum / float(len(rel))


def mean_average_precision(all_pred: List[Sequence[str]], all_rel: List[Set[str]]) -> float:
    if not all_pred or not all_rel or len(all_pred) != len(all_rel):
        return 0.0
    return sum(average_precision(p, r) for p, r in zip(all_pred, all_rel)) / float(len(all_pred))


def dcg_at_k(gains: Sequence[float], k: int) -> float:
    k = min(k, len(gains))
    if k == 0:
        return 0.0
    return gains[0] + sum(gains[i] / math.log2(i + 1) for i in range(1, k))


def ndcg_at_k(pred: Sequence[str], rel_gain: dict[str, float], k: int) -> float:
    # Gains for prediction
    gains = [rel_gain.get(x, 0.0) for x in pred]
    ideal_gains = sorted(rel_gain.values(), reverse=True)
    dcg = dcg_at_k(gains, k)
    idcg = dcg_at_k(ideal_gains, k)
    if idcg == 0:
        return 0.0
    return dcg / idcg

__all__ = [
    "precision_at_k",
    "recall_at_k",
    "average_precision",
    "mean_average_precision",
    "ndcg_at_k",
]
