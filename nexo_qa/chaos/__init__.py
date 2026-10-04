"""P8 Cognitive Chaos Testing."""

from nexo_qa.chaos.aggregation import aggregate_population_chaos, cohort_sensitivity_matrix
from nexo_qa.chaos.models import ChaosSpec, PairedChaosDelta, PerturbationSpec
from nexo_qa.chaos.offline import analyze_pairs, analyze_chaos_directory
from nexo_qa.chaos.pairs import compute_paired_delta, status_degradation_rate, validate_pair_invariants
from nexo_qa.chaos.planner import ChaosPlanner
from nexo_qa.chaos.runner import ChaosRunner, ChaosRunnerConfig, ChaosState

__all__ = [
    "ChaosPlanner",
    "ChaosRunner",
    "ChaosRunnerConfig",
    "ChaosSpec",
    "ChaosState",
    "PairedChaosDelta",
    "PerturbationSpec",
    "aggregate_population_chaos",
    "analyze_chaos_directory",
    "analyze_pairs",
    "cohort_sensitivity_matrix",
    "compute_paired_delta",
    "status_degradation_rate",
    "validate_pair_invariants",
]
