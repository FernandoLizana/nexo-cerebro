"""Bloque A — escala y arquitectura neuronal."""

from __future__ import annotations

import numpy as np
import pytest

from brain.cortical_layers import LaminarAssociativeStack
from brain.decompression_governor import DecompressionGovernor
from brain.hippocampus_core import HippocampalFormation
from brain.inhibition import InhibitoryMicrocircuit, SubtypeInhibitoryCircuit
from brain.lifecycle import LifecycleState
from brain.profile import (
    SCALE_100K_PROFILE,
    profile_neuron_count,
    resolve_experiment_profile,
)
from brain.vascular import CerebralVascularBed


def test_scale_100k_profile_count():
    p = SCALE_100K_PROFILE
    n = profile_neuron_count(p)
    assert n >= 95_000
    assert p.dg_sparsity == 0.025
    assert p.enable_laminar_columns is True


def test_resolve_100k_profile():
    assert resolve_experiment_profile("100k").name == "neuro-100k"


def test_dg_sparsity_biological():
    h = HippocampalFormation(n_in=128, n_dg=96, n_ca3=96, n_ca1=72, dg_sparsity=0.025)
    sensory = np.random.rand(128).astype(np.float32)
    h.step(sensory, gain=1.0, theta_amp=1.0, mode="encode")
    active = int(h.dg.spikes.sum())
    k = max(1, int(96 * 0.025))
    assert active <= k + 1


def test_laminar_stack_produces_boosts():
    stack = LaminarAssociativeStack(n_per_layer=12)
    sensory = np.random.rand(64).astype(np.float32)
    assoc, motor = stack.step(sensory, gain=1.0, n_assoc=48, n_motor=24)
    assert assoc.size == 48
    assert motor.size == 24
    assert float(assoc.max()) >= 0.0


def test_subtype_inhibitory_circuit():
    rng = np.random.default_rng(0)
    inh = SubtypeInhibitoryCircuit(80, density=0.1, rng=rng)
    spikes = np.random.rand(80) > 0.7
    cur = np.ones(80, dtype=np.float32) * 2.0
    out = inh.shunt(spikes, cur)
    assert out.shape == cur.shape
    assert inh.n_inh > inh.n_pv


def test_governor_lobe_budgets():
    gov = DecompressionGovernor()
    gov.configure_lobe_budgets(4096)
    assert gov.can_spend_lobe("occipital", 2000)
    assert gov.record_lobe("occipital", 2000, kind="assembly")
    assert gov.lobe_bytes_used["occipital"] == 2000


def test_vascular_modulates_gain():
    from brain import InfantApeBrain
    from brain.profile import COMPACT_PROFILE

    brain = InfantApeBrain(profile=COMPACT_PROFILE)
    brain.vascular = CerebralVascularBed()
    base = brain.cortex.synaptic_gain
    brain.vascular.step(brain)
    assert brain.cortex.synaptic_gain != base or brain.vascular.glucose != 0.88


def test_epigenetic_profile_reduces_plasticity_in_adult():
    lc = LifecycleState()
    lc.stage = "adulto"
    epi = lc.epigenetic_profile()
    young = LifecycleState()
    young.stage = "joven"
    assert epi["expression_plasticity"] < young.epigenetic_profile()["expression_plasticity"]
