"""Tests Sprint 11 — lesiones connectome integradas."""

from __future__ import annotations

import numpy as np

from nexo.connectome.graph import ConnectomeGraph
from nexo.connectome.routing import ConnectomeRouter
from nexo.integrated_runtime import IntegratedRuntime, IntegratedRuntimeConfig, _repo_root, runtime_from_config
from nexo.interventions.lesion import LesionState
from nexo.interventions.profiles import LESION_REGISTRY, apply_lesion_profile
from nexo.interventions.routing_helpers import route_gain


def _repo_connectome():
    return _repo_root() / "configs/connectome/connectome_v1.yaml"


def test_severed_edge_zeros_route():
    graph = ConnectomeGraph.from_yaml(_repo_connectome())
    router = ConnectomeRouter(graph=graph)
    apply_lesion_profile("lesion_sever_thal_visual", router.lesions)
    signal = np.array([1.0, 0.5, 0.2])
    routed = router.route("thalamus_relay", "visual_cortex", signal, 1.0)
    assert np.allclose(routed, 0.0)


def test_intact_edge_routes_nonzero():
    graph = ConnectomeGraph.from_yaml(_repo_connectome())
    router = ConnectomeRouter(graph=graph)
    signal = np.array([1.0, 0.5, 0.2])
    routed = router.route("thalamus_relay", "visual_cortex", signal, 1.0)
    assert float(np.linalg.norm(routed)) > 0.0


def test_weaken_profile_scales_weight():
    graph = ConnectomeGraph.from_yaml(_repo_connectome())
    full = ConnectomeRouter(graph=graph)
    weak = ConnectomeRouter(graph=graph)
    apply_lesion_profile("lesion_weaken_pfc_bg", weak.lesions)
    signal = np.array([1.0, 0.3, 0.1])
    full_out = full.route("prefrontal", "basal_ganglia", signal, 1.0)
    weak_out = weak.route("prefrontal", "basal_ganglia", signal, 1.0)
    assert float(np.linalg.norm(weak_out)) < float(np.linalg.norm(full_out))


def test_lesion_audit_emits_events():
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=10,
            perception_mode="predictive",
            executive_mode="integrated",
            intervention_mode="integrated",
            lesion_profile="lesion_sever_pfc_bg",
        )
    )
    result = rt.run()
    assert result["connectome_lesion_events"] >= 1
    assert result["connectome_lesions_active"] >= 1


def test_lesion_changes_trajectory():
    base = IntegratedRuntimeConfig(
        seed=42,
        ticks=50,
        perception_mode="predictive",
        memory_mode="integrated",
        executive_mode="integrated",
        intervention_mode="integrated",
        lesion_profile="lesion_none",
    )
    lesioned = IntegratedRuntimeConfig(
        seed=42,
        ticks=50,
        perception_mode="predictive",
        memory_mode="integrated",
        executive_mode="integrated",
        intervention_mode="integrated",
        lesion_profile="lesion_sever_pfc_bg",
    )
    full = IntegratedRuntime(base).run()
    cut = IntegratedRuntime(lesioned).run()
    assert full["trajectory_hash"] != cut["trajectory_hash"]


def test_intervention_legacy_skips_audit():
    rt = IntegratedRuntime(
        IntegratedRuntimeConfig(
            seed=42,
            ticks=10,
            intervention_mode="legacy",
            lesion_profile="lesion_sever_pfc_bg",
        )
    )
    result = rt.run()
    assert result["intervention_mode"] == "legacy"
    assert result["connectome_lesion_events"] == 0


def test_integrated_v11_yaml_runs():
    rt = runtime_from_config(_repo_root() / "configs/nexo/integrated_v11.yaml")
    result = rt.run(40)
    assert result["profile"] == "integrated_v11"
    assert result["intervention_mode"] == "integrated"
    assert result["lesion_profile"] == "lesion_none"


def test_lesion_registry_covers_profiles():
    assert "lesion_sever_hippo_pfc" in LESION_REGISTRY
    state = LesionState()
    apply_lesion_profile("lesion_sever_hippo_pfc", state)
    assert route_gain(ConnectomeRouter(ConnectomeGraph.from_yaml(_repo_connectome()), lesions=state),
                      "hippocampus", "prefrontal", (0.5, 0.2)) == 0.0
