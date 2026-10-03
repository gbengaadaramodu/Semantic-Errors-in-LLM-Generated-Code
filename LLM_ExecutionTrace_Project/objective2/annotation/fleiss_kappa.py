"""
Fleiss' Kappa Inter-Annotator Agreement Module.

Computes Fleiss' Kappa statistic for multi-annotator categorical ground-truth ratings.
"""

from typing import List


def compute_fleiss_kappa(ratings: List[List[int]]) -> float:
    """
    Computes Fleiss' Kappa for a matrix of ratings where ratings[i][j] is the
    number of annotators who assigned subject i to category j.
    """
    if not ratings or not ratings[0]:
        return 0.0

    N = len(ratings) # Number of subjects
    k = len(ratings[0]) # Number of categories
    n = sum(ratings[0]) # Number of annotators per subject

    if n <= 1 or N == 0:
        return 0.0

    # P_i: extent of agreement for subject i
    P_i = []
    for row in ratings:
        sum_sq = sum(r * r for r in row)
        P_i.append((sum_sq - n) / (n * (n - 1)))

    P_bar = sum(P_i) / N

    # P_e: chance agreement
    P_j = []
    for j in range(k):
        col_sum = sum(ratings[i][j] for i in range(N))
        P_j.append(col_sum / (N * n))

    P_e = sum(pj * pj for pj in P_j)

    if P_e == 1.0:
        return 1.0

    kappa = (P_bar - P_e) / (1.0 - P_e)
    return round(kappa, 4)
