"""Tests estadística."""

from __future__ import annotations

import math

from nexo.statistics import summarize_values


def test_empty_sample():
    s = summarize_values([])
    assert "empty_sample" in s.warnings
    assert math.isnan(s.mean)


def test_single_observation():
    s = summarize_values([1.0])
    assert "single_seed" in s.warnings


def test_zero_variance():
    s = summarize_values([0.5, 0.5, 0.5])
    assert "constant_across_seeds" in s.warnings


def test_nan_filtered():
    s = summarize_values([1.0, float("nan"), 2.0])
    assert s.n_nan == 1
    assert "nan_values_filtered" in s.warnings


def test_mean_difference_not_cohens_d():
    s = summarize_values([2.0, 4.0], baseline=1.0)
    assert s.mean_difference == 2.0
    assert s.cohens_d is not None
