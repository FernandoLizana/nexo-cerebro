"""
Corteza laminar con E/I, compuerta NMDA, modulación y ritmos θ/γ.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

import numpy as np

from .backend import get_backend
from .inhibition import InhibitoryMicrocircuit, SubtypeInhibitoryCircuit
from .neuron import LIFPopulation
from .profile import DEFAULT_PROFILE, NeuroProfile
from .synapse import SparseSynapses

if TYPE_CHECKING:
    from .cortical_layers import LaminarAssociativeStack
    from .neurotransmitters import NeuromodulatorState


@dataclass
class CorticalNetwork:
    profile: NeuroProfile = field(default_factory=lambda: DEFAULT_PROFILE)
    tick_ms: int = 1
    time_ms: int = field(default=0, init=False)
    _step_counter: int = field(default=0, init=False)
    _use_gpu_forward: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        p = self.profile
        self.n_sensory = p.n_sensory
        self.n_limbic = p.n_limbic
        self.n_associative = p.n_associative
        self.n_prefrontal = p.n_prefrontal
        self.n_motor = p.n_motor
        self.synapse_density = p.synapse_density
        self.synaptic_gain = p.synaptic_gain
        self.plasticity_mult = p.plasticity_mult
        ref = p.refractory_ms

        self.sensory = LIFPopulation(self.n_sensory, tau_ms=14.0, refrac_ms=ref)
        self.limbic = LIFPopulation(self.n_limbic, tau_ms=18.0, v_thresh=-53.0, refrac_ms=ref)
        self.associative = LIFPopulation(self.n_associative, tau_ms=22.0, v_thresh=-53.0, refrac_ms=ref)
        self.prefrontal = LIFPopulation(self.n_prefrontal, tau_ms=28.0, v_thresh=-51.5, refrac_ms=ref)
        self.motor = LIFPopulation(self.n_motor, tau_ms=15.0, v_thresh=-54.0, refrac_ms=ref)

        rng = np.random.default_rng(11)
        d = self.synapse_density
        eta = 0.0035 * self.plasticity_mult

        self.s_to_l = SparseSynapses(self.n_sensory, self.n_limbic, density=d * 1.1, rng=rng, eta=eta)
        self.l_to_a = SparseSynapses(self.n_limbic, self.n_associative, density=d, rng=rng, eta=eta)
        self.a_to_a = SparseSynapses(
            self.n_associative, self.n_associative, density=d * 0.72, rng=rng, eta=eta
        )
        self.a_to_p = SparseSynapses(self.n_associative, self.n_prefrontal, density=d * 0.55, rng=rng, eta=eta)
        self.p_to_a = SparseSynapses(self.n_prefrontal, self.n_associative, density=d * 0.48, rng=rng, eta=eta)
        self.a_to_m = SparseSynapses(self.n_associative, self.n_motor, density=d, rng=rng, eta=eta)
        self.s_to_m = SparseSynapses(
            self.n_sensory, self.n_motor, density=d * 0.22, rng=rng, eta=eta * 0.65
        )

        self.inh_a: InhibitoryMicrocircuit | SubtypeInhibitoryCircuit | None = None
        self.inh_l: InhibitoryMicrocircuit | SubtypeInhibitoryCircuit | None = None
        if p.interneurons:
            inh_cls = SubtypeInhibitoryCircuit if p.interneuron_subtypes else InhibitoryMicrocircuit
            self.inh_a = inh_cls(self.n_associative, density=d, rng=rng, refrac_ms=ref)
            self.inh_l = inh_cls(self.n_limbic, density=d, rng=rng, refrac_ms=ref)

        if p.enable_laminar_columns:
            from .cortical_layers import LaminarAssociativeStack

            self.laminar = LaminarAssociativeStack(
                n_per_layer=max(8, self.n_associative // 20),
                density=d * 0.95,
            )
        else:
            self.laminar = None

        self._external = np.zeros(self.n_sensory, dtype=np.float32)
        self._hippo_ctx = np.zeros(self.n_sensory, dtype=np.float32)
        self._syn_l = np.zeros(self.n_limbic, dtype=np.float32)
        self._syn_a = np.zeros(self.n_associative, dtype=np.float32)
        self._syn_p = np.zeros(self.n_prefrontal, dtype=np.float32)
        self._syn_m = np.zeros(self.n_motor, dtype=np.float32)
        self._wm = np.zeros(self.n_prefrontal, dtype=np.float32)
        self._limbic_olfactory = np.zeros(self.n_limbic, dtype=np.float32)
        self._lobe_boost_sensory = np.zeros(self.n_sensory, dtype=np.float32)
        self._lobe_boost_limbic = np.zeros(self.n_limbic, dtype=np.float32)
        self._lobe_boost_assoc = np.zeros(self.n_associative, dtype=np.float32)
        self._lobe_boost_pfc = np.zeros(self.n_prefrontal, dtype=np.float32)
        self._motor_laminar = np.zeros(self.n_motor, dtype=np.float32)
        self.syn_decay = 0.91
        self.history_motor: list[list[int]] = []
        self.last_raw_motor: list[int] = []
        if get_backend().gpu_available:
            for syn in self.iter_synapses():
                syn.enable_gpu_matrices()

    def iter_synapses(self) -> tuple[SparseSynapses, ...]:
        return (
            self.s_to_l,
            self.l_to_a,
            self.a_to_a,
            self.a_to_p,
            self.p_to_a,
            self.a_to_m,
            self.s_to_m,
        )

    def set_gpu_forward(self, enabled: bool) -> None:
        self._use_gpu_forward = enabled
        get_backend().set_active_gpu(enabled)

    @property
    def n_total(self) -> int:
        inh = 0
        if self.inh_a:
            inh += self.inh_a.n_inh
        if self.inh_l:
            inh += self.inh_l.n_inh
        laminar_n = self.laminar.n_neurons if self.laminar else 0
        return (
            self.n_sensory
            + self.n_limbic
            + self.n_associative
            + self.n_prefrontal
            + self.n_motor
            + inh
            + laminar_n
        )

    def reset(self) -> None:
        for pop in (self.sensory, self.limbic, self.associative, self.prefrontal, self.motor):
            pop.reset()
        if self.inh_a:
            self.inh_a.reset()
        if self.inh_l:
            self.inh_l.reset()
        self._external.fill(0.0)
        self._hippo_ctx.fill(0.0)
        self._syn_l.fill(0.0)
        self._syn_a.fill(0.0)
        self._syn_p.fill(0.0)
        self._syn_m.fill(0.0)
        self._wm.fill(0.0)
        self._limbic_olfactory.fill(0.0)
        self._lobe_boost_sensory.fill(0.0)
        self._lobe_boost_limbic.fill(0.0)
        self._lobe_boost_assoc.fill(0.0)
        self._lobe_boost_pfc.fill(0.0)
        self._motor_laminar.fill(0.0)
        if self.laminar:
            self.laminar.reset()
        self.time_ms = 0
        self._step_counter = 0
        self.history_motor.clear()
        self.last_raw_motor.clear()

    def set_stimulus(self, pattern: list[float] | list[int], hippo_ctx: np.ndarray | None = None) -> None:
        p = np.asarray(pattern, dtype=np.float32)
        if p.size != self.n_sensory:
            raise ValueError(f"Se esperan {self.n_sensory} valores, recibidos {p.size}")
        self._external = np.clip(p * 28.0, 0.0, 40.0)
        if hippo_ctx is not None:
            h = np.asarray(hippo_ctx, dtype=np.float32).ravel()
            if h.size >= self.n_sensory:
                self._hippo_ctx = np.clip(h[: self.n_sensory] * 12.0, 0, 18)
            else:
                self._hippo_ctx.fill(0)
                self._hippo_ctx[: h.size] = np.clip(h * 12.0, 0, 18)
        else:
            self._hippo_ctx.fill(0)
        n = min(self.n_prefrontal, p.size)
        self._wm = np.clip(self._wm * 0.4 + p[:n] * 0.6, 0, 1)

    def inject_olfactory(self, pattern: np.ndarray) -> None:
        """Olfato directo al límbico (sin pasar por tálamo)."""
        n = min(self.n_limbic, int(np.asarray(pattern).size))
        if n <= 0:
            return
        p = np.asarray(pattern, dtype=np.float32).ravel()[:n]
        self._limbic_olfactory[:n] = np.clip(p * 18.0, 0, 22)

    def prime_working_memory(self, pattern: np.ndarray, *, gain: float = 0.55) -> None:
        """Meta conductual prefrontal antes del episodio (intención voluntaria)."""
        n = min(self.n_prefrontal, int(np.asarray(pattern).size))
        if n <= 0:
            return
        p = np.asarray(pattern, dtype=np.float32).ravel()[:n]
        g = float(np.clip(gain, 0.1, 0.95))
        self._wm[:n] = np.clip(self._wm[:n] * (1.0 - g) + p * g, 0.0, 1.0)

    def tick(
        self,
        steps: int = 1,
        *,
        use_stdp: bool = True,
        modulators: NeuromodulatorState | None = None,
        theta_amp: float = 1.0,
        gamma_amp: float = 1.0,
        delta_amp: float = 0.0,
        hippo_mode: str = "encode",
    ) -> dict:
        from .neurotransmitters import NeuromodulatorState as NM

        mods = modulators or NM()

        g_base = self.synaptic_gain * mods.gain_scale()
        inh_scale = mods.inhibition_scale()
        pfc_inhib = self.profile.prefrontal_inhibition * inh_scale
        d = self.syn_decay
        z_s = np.zeros(self.n_sensory, dtype=np.float32)
        z_l = np.zeros(self.n_limbic, dtype=np.float32)
        z_a = np.zeros(self.n_associative, dtype=np.float32)
        z_p = np.zeros(self.n_prefrontal, dtype=np.float32)
        z_m = np.zeros(self.n_motor, dtype=np.float32)

        from .oscillations import BrainOscillators

        for _ in range(steps):
            eta_s = (
                BrainOscillators.plasticity_gate(theta_amp, gamma_amp, delta_amp=delta_amp)
                * self.plasticity_mult
                * mods.plasticity_scale()
            )

            i_s = self._external + self._hippo_ctx + self._lobe_boost_sensory
            self.sensory.integrate(z_s, i_s)
            self._lobe_boost_sensory *= 0.9

            if self.laminar is not None:
                assoc_b, motor_b = self.laminar.step(
                    self.sensory.v,
                    gain=g_base,
                    gamma_amp=gamma_amp,
                    n_assoc=self.n_associative,
                    n_motor=self.n_motor,
                )
                self._lobe_boost_assoc[: assoc_b.size] += assoc_b * 6.0
                self._motor_laminar[: motor_b.size] = motor_b

            impulse_l = self.s_to_l.forward(self.sensory.spikes) * g_base * gamma_amp
            self._syn_l = self._syn_l * d + impulse_l + self._lobe_boost_limbic
            self._lobe_boost_limbic *= 0.9
            if self._limbic_olfactory.any():
                self._syn_l = np.clip(
                    self._syn_l + self._limbic_olfactory.astype(np.float32) * 0.35,
                    0,
                    40,
                )
                self._limbic_olfactory *= 0.88
            if self.inh_l:
                self._syn_l = self.inh_l.shunt(self.limbic.spikes, self._syn_l)
            self.limbic.integrate(self._syn_l, z_l)

            impulse_a = self.l_to_a.forward(self.limbic.spikes) * g_base * gamma_amp
            impulse_a += self.a_to_a.forward(self.associative.spikes) * g_base
            impulse_a += self.p_to_a.forward(self.prefrontal.spikes) * g_base * 0.82
            impulse_a += self._lobe_boost_assoc
            self._lobe_boost_assoc *= 0.9

            if self.profile.nmda_gating:
                nmda = mods.nmda_open_probability(self.associative.v_mean)
                impulse_a *= 0.55 + 0.45 * nmda

            self._syn_a = self._syn_a * d + impulse_a
            if self.inh_a:
                self._syn_a = self.inh_a.shunt(self.associative.spikes, self._syn_a)
            if self.n_prefrontal and self.n_associative:
                reps = int(np.ceil(self.n_associative / self.n_prefrontal))
                projected = np.tile(self._wm, reps)[: self.n_associative]
                self._syn_a = np.maximum(self._syn_a - pfc_inhib * projected.astype(np.float32) * 0.75, 0)
            self.associative.integrate(self._syn_a, z_a)

            i_p = self.a_to_p.forward(self.associative.spikes) * g_base * 0.68
            i_p += self._wm * 5.5 * theta_amp
            i_p += self._lobe_boost_pfc
            self._lobe_boost_pfc *= 0.9
            self._syn_p = self._syn_p * d + i_p
            self.prefrontal.integrate(self._syn_p, z_p)
            self._wm = np.clip(self._wm * 0.91 + self.prefrontal.v[: self.n_prefrontal] * 0.012, 0, 1)

            impulse_m = self.a_to_m.forward(self.associative.spikes) * g_base
            impulse_m += self.s_to_m.forward(self.sensory.spikes) * g_base * 0.32
            if self._motor_laminar.any():
                impulse_m = impulse_m + self._motor_laminar[: self.n_motor] * g_base * 4.5
                self._motor_laminar *= 0.88
            self._syn_m = self._syn_m * d + impulse_m
            self.motor.integrate(self._syn_m, z_m)

            if use_stdp:
                pairs = [
                    (self.s_to_l, self.sensory.spikes, self.limbic.spikes),
                    (self.l_to_a, self.limbic.spikes, self.associative.spikes),
                    (self.a_to_a, self.associative.spikes, self.associative.spikes),
                    (self.a_to_p, self.associative.spikes, self.prefrontal.spikes),
                    (self.p_to_a, self.prefrontal.spikes, self.associative.spikes),
                    (self.a_to_m, self.associative.spikes, self.motor.spikes),
                    (self.s_to_m, self.sensory.spikes, self.motor.spikes),
                ]
                for syn, pre, post in pairs:
                    syn.plasticity_step(pre, post, eta_scale=eta_s, use_stdp=True)

            self._step_counter += 1
            if self.profile.homeostasis_every > 0 and self._step_counter % self.profile.homeostasis_every == 0:
                for syn in (self.s_to_l, self.l_to_a, self.a_to_a, self.a_to_m):
                    syn.homeostatic_scale()

            self.time_ms += self.tick_ms
            if self.motor.spikes.any():
                self.last_raw_motor = np.flatnonzero(self.motor.spikes).tolist()
            if self._use_gpu_forward:
                get_backend().record_gpu_steps(1)

        snap = self.snapshot()
        snap["hippo_mode"] = hippo_mode
        snap["oscillators"] = {
            "theta": round(theta_amp, 3),
            "gamma": round(gamma_amp, 3),
            "delta": round(delta_amp, 3),
        }
        return snap

    def snapshot(self) -> dict:
        return {
            "time_ms": self.time_ms,
            "rates": {
                "limbic": float(self.limbic.spikes.mean()),
                "associative": float(self.associative.spikes.mean()),
                "prefrontal": float(self.prefrontal.spikes.mean()),
                "motor": float(self.motor.spikes.mean()),
            },
            "spikes": {
                "limbic": np.flatnonzero(self.limbic.spikes).tolist()[:16],
                "associative": np.flatnonzero(self.associative.spikes).tolist()[:16],
                "prefrontal": np.flatnonzero(self.prefrontal.spikes).tolist(),
                "motor_raw": self.last_raw_motor,
            },
            "motor_history_len": len(self.history_motor),
            "last_motor_pattern": self.history_motor[-1] if self.history_motor else [],
            "working_memory_norm": round(float(np.linalg.norm(self._wm)), 3),
            "interneurons": (self.inh_a.n_inh if self.inh_a else 0)
            + (self.inh_l.n_inh if self.inh_l else 0),
            "mem_mb_approx": round(self._memory_bytes() / (1024 * 1024), 3),
        }

    def _memory_bytes(self) -> int:
        total = 0
        for pop in (self.sensory, self.limbic, self.associative, self.prefrontal, self.motor):
            total += pop.v.nbytes + pop.spikes.nbytes
        for syn in (self.s_to_l, self.l_to_a, self.a_to_a, self.a_to_p, self.p_to_a, self.a_to_m, self.s_to_m):
            total += syn.w.nbytes + syn.indices.nbytes + syn.indptr.nbytes
        return total

    def encode_label(self, label: str) -> list[float]:
        vec = np.zeros(self.n_sensory, dtype=np.float32)
        raw = label.encode("utf-8") or b"\x00"
        for i, ch in enumerate(raw):
            base = (ch + i * 17) % self.n_sensory
            for k in range(3):
                vec[(base + k * 5) % self.n_sensory] = 1.0
        return vec.tolist()

    def activity_map(self, width: int = 48) -> dict:
        """Mapa 2D: filas = regiones, columnas = actividad normalizada."""

        def row(pop: LIFPopulation) -> list[float]:
            denom = max(pop.v_thresh - pop.v_rest, 1.0)
            act = np.clip((pop.v - pop.v_rest) / denom, 0.0, 1.25)
            act = act.astype(np.float32)
            act[pop.spikes] = 1.0
            if act.size == 0:
                return [0.0] * width
            x_old = np.linspace(0.0, 1.0, act.size)
            x_new = np.linspace(0.0, 1.0, width)
            return np.interp(x_new, x_old, act).round(3).tolist()

        regions = [
            {"id": "sensory", "label": "Sensorial", "values": row(self.sensory)},
            {"id": "limbic", "label": "Límbico", "values": row(self.limbic)},
            {"id": "associative", "label": "Asociativa", "values": row(self.associative)},
            {"id": "prefrontal", "label": "Prefrontal", "values": row(self.prefrontal)},
            {"id": "motor", "label": "Motor", "values": row(self.motor)},
        ]
        return {
            "width": width,
            "time_ms": self.time_ms,
            "regions": regions,
            "spike_counts": {r["id"]: int(sum(v >= 0.99 for v in r["values"])) for r in regions},
        }

    def export_weights_summary(self) -> str:
        layers = [
            ("s→l", self.s_to_l),
            ("l→a", self.l_to_a),
            ("a→m", self.a_to_m),
        ]
        lines = [f"{n}: {s.w.size} syn" for n, s in layers]
        return json.dumps({"layers": lines, "neurons": self.n_total, "profile": self.profile.name})
