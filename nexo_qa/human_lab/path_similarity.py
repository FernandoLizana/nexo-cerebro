"""Path similarity — normalized Levenshtein on semantic action sequences."""

from __future__ import annotations


def levenshtein(a: list[str], b: list[str]) -> int:
    if not a:
        return len(b)
    if not b:
        return len(a)
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        curr = [i]
        for j, cb in enumerate(b, 1):
            cost = 0 if ca == cb else 1
            curr.append(min(prev[j] + 1, curr[j - 1] + 1, prev[j - 1] + cost))
        prev = curr
    return prev[-1]


def normalized_levenshtein_similarity(a: list[str], b: list[str]) -> float:
    if not a and not b:
        return 1.0
    dist = levenshtein(a, b)
    return 1.0 - dist / max(len(a), len(b), 1)


def sequence_overlap(a: list[str], b: list[str]) -> float:
    if not a or not b:
        return 0.0
    sa, sb = set(a), set(b)
    return len(sa & sb) / max(1, len(sa | sb))


def ngram_overlap(a: list[str], b: list[str], n: int = 2) -> float:
    def ngrams(seq: list[str]) -> set[tuple[str, ...]]:
        return {tuple(seq[i : i + n]) for i in range(max(0, len(seq) - n + 1))}

    na, nb = ngrams(a), ngrams(b)
    if not na and not nb:
        return 1.0
    if not na or not nb:
        return 0.0
    return len(na & nb) / len(na | nb)
