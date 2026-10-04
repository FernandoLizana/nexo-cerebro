"""
Perfiles neuroanatómicos. Por defecto: red grande (~1.4k neuronas).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
import os


@dataclass(frozen=True)
class NeuroProfile:
    name: str = "neuro-biológico-grande"
    age_label: str = "~1.4k activas · ensambles en disco"

    n_sensory: int = 384
    n_limbic: int = 192
    n_associative: int = 304
    n_prefrontal: int = 112
    n_motor: int = 72

    n_dg: int = 96
    n_ca3: int = 96
    n_ca1: int = 72

    synapse_density: float = 0.082
    synaptic_gain: float = 17.0
    plasticity_mult: float = 1.35
    amygdala_gain: float = 1.15
    prefrontal_inhibition: float = 0.52
    social_bonding: float = 1.12
    motor_exploration: float = 0.9

    theta_hz: float = 5.5
    gamma_hz: float = 42.0
    e_i_ratio: float = 4.0
    interneurons: bool = True
    nmda_gating: bool = True
    homeostasis_every: int = 60
    refractory_ms: int = 2
    dg_sparsity: float = 0.025

    # Arquitectura avanzada (bloque A)
    enable_laminar_columns: bool = False
    interneuron_subtypes: bool = False
    enable_vascular_coupling: bool = False
    lobe_decompress_bytes: int = 65536

    # Corteza virtual indexada en disco (engramas)
    neurons_per_assembly: int = 20
    virtual_recall_k: int = 5
    virtual_inject_gain: float = 0.18
    virtual_disk_search_limit: int = 2500
    virtual_disk_budget_gb: float = 12.0
    virtual_disk_bytes_per_assembly: int = 320
    virtual_lsh_bits: int = 16
    virtual_hot_size: int = 48

    n_lobe_per_column: int = 24

    # Connectome scaffold (espacio lógico humano-escala)
    connectome_seed: int = 42
    logical_neuron_target: int = 86_000_000_000
    chunk_neurons: int = 16384
    chunk_cache_gb: float = 2.0
    scaffold_inject_gain: float = 0.08
    enable_scaffold_in_demo: bool = False


COMPACT_PROFILE = NeuroProfile(
    name="neuro-biológico",
    age_label="~500 neuronas",
    n_sensory=128,
    n_limbic=72,
    n_associative=112,
    n_prefrontal=40,
    n_motor=28,
    n_dg=40,
    n_ca3=40,
    n_ca1=32,
    synapse_density=0.11,
    dg_sparsity=0.08,
)

# ~10k neuronas activas — paper / GPU batch (corteza + hipocampo + lóbulos)
SCALE_10K_PROFILE = NeuroProfile(
    name="neuro-10k",
    age_label="~10k activas (GPU batch)",
    n_sensory=2560,
    n_limbic=1280,
    n_associative=2560,
    n_prefrontal=640,
    n_motor=320,
    n_dg=600,
    n_ca3=600,
    n_ca1=450,
    n_lobe_per_column=128,
    synapse_density=0.042,
    synaptic_gain=13.5,
    homeostasis_every=140,
    virtual_disk_budget_gb=0.25,
    virtual_hot_size=4,
    virtual_disk_search_limit=64,
)

# ~50k neuronas LIF activas — Fase 3 / GPU (RTX 3050+ recomendada)
# Ensambles virtuales siguen en disco; no confundir con LIF activas.
SCALE_50K_PROFILE = NeuroProfile(
    name="neuro-50k",
    age_label="~50k activas LIF (GPU) · virtuales en disco",
    n_sensory=12800,
    n_limbic=6400,
    n_associative=12800,
    n_prefrontal=3200,
    n_motor=1600,
    n_dg=3000,
    n_ca3=3000,
    n_ca1=2250,
    n_lobe_per_column=280,
    synapse_density=0.028,
    synaptic_gain=12.0,
    plasticity_mult=1.15,
    homeostasis_every=200,
    virtual_disk_budget_gb=0.5,
    virtual_hot_size=8,
    virtual_disk_search_limit=96,
    virtual_recall_k=6,
    virtual_inject_gain=0.14,
    scaffold_inject_gain=0.06,
)

# ~100k neuronas LIF activas — escala alta / GPU dedicada
SCALE_100K_PROFILE = NeuroProfile(
    name="neuro-100k",
    age_label="~100k activas LIF (GPU) · virtuales en disco",
    n_sensory=25600,
    n_limbic=12800,
    n_associative=25600,
    n_prefrontal=6400,
    n_motor=3200,
    n_dg=6000,
    n_ca3=6000,
    n_ca1=4500,
    n_lobe_per_column=400,
    synapse_density=0.022,
    synaptic_gain=11.5,
    plasticity_mult=1.08,
    homeostasis_every=240,
    dg_sparsity=0.025,
    virtual_disk_budget_gb=0.75,
    virtual_hot_size=12,
    virtual_disk_search_limit=128,
    virtual_recall_k=8,
    virtual_inject_gain=0.16,
    scaffold_inject_gain=0.07,
    enable_laminar_columns=True,
    interneuron_subtypes=True,
    enable_vascular_coupling=True,
    lobe_decompress_bytes=98304,
)

INFANT_APE_PROFILE = NeuroProfile(
    name="bebé-simio",
    age_label="12–18 meses (aprox.)",
    n_sensory=96,
    n_limbic=64,
    n_associative=96,
    n_prefrontal=32,
    n_motor=24,
    n_dg=28,
    n_ca3=28,
    n_ca1=24,
    plasticity_mult=2.2,
    amygdala_gain=1.45,
    prefrontal_inhibition=0.35,
    social_bonding=1.3,
    motor_exploration=1.2,
    homeostasis_every=80,
)

DEMO_LITE_PROFILE = NeuroProfile(
    name="demo-lite",
    age_label="~500 neuronas · demo liviana (bajo consumo)",
    n_sensory=128,
    n_limbic=72,
    n_associative=112,
    n_prefrontal=40,
    n_motor=28,
    n_dg=40,
    n_ca3=40,
    n_ca1=32,
    n_lobe_per_column=24,
    synapse_density=0.11,
    virtual_disk_budget_gb=0.15,
    virtual_hot_size=4,
    virtual_disk_search_limit=48,
    virtual_recall_k=3,
    enable_scaffold_in_demo=False,
)

VIRTUAL_LARGE_PROFILE = NeuroProfile(
    name="neuro-virtual-90M",
    age_label="~1.4k activas · ~800M indexadas (12 GB disco EGR1)",
    dg_sparsity=0.025,
    neurons_per_assembly=20,
    virtual_recall_k=5,
    virtual_inject_gain=0.18,
    virtual_disk_search_limit=2500,
    virtual_disk_budget_gb=12.0,
    virtual_disk_bytes_per_assembly=320,
    virtual_lsh_bits=16,
    virtual_hot_size=48,
    enable_scaffold_in_demo=True,
    scaffold_inject_gain=0.12,
    enable_vascular_coupling=True,
)

DEFAULT_PROFILE = VIRTUAL_LARGE_PROFILE

HUMAN_SCAFFOLD_PROFILE = replace(
    SCALE_10K_PROFILE,
    name="human-scaffold-10k",
    age_label="~10k activas · ~86B lógicas (seed 42)",
    connectome_seed=42,
    logical_neuron_target=86_000_000_000,
    chunk_neurons=16384,
    chunk_cache_gb=2.0,
    scaffold_inject_gain=0.08,
    virtual_disk_budget_gb=12.0,
    virtual_hot_size=48,
    virtual_disk_search_limit=2500,
)

InfantApeProfile = NeuroProfile


def resolve_default_profile() -> NeuroProfile:
    """Perfil por defecto; CEREBRO_DEMO_LITE=1 fuerza compacto liviano."""
    lite = os.environ.get("CEREBRO_DEMO_LITE", "").strip().lower()
    if lite in ("1", "true", "yes", "on", "lite"):
        return DEMO_LITE_PROFILE
    key = os.environ.get("CEREBRO_PROFILE", "").strip().lower()
    if key in ("lite", "demo-lite", "demo_lite", "compact"):
        return DEMO_LITE_PROFILE if key != "compact" else COMPACT_PROFILE
    gb = float(os.environ.get("CEREBRO_VIRTUAL_DISK_GB", "12"))
    p = VIRTUAL_LARGE_PROFILE
    if abs(gb - p.virtual_disk_budget_gb) < 0.01:
        return p
    max_asm = int(gb * (1024**3) / p.virtual_disk_bytes_per_assembly)
    virt_m = max_asm * p.neurons_per_assembly
    if virt_m >= 1_000_000:
        label = f"~1.4k activas · ~{virt_m // 1_000_000}M indexadas ({gb:.0f} GB disco)"
    else:
        label = f"~1.4k activas · ~{virt_m // 1000}k indexadas ({gb:.0f} GB disco)"
    return replace(p, virtual_disk_budget_gb=gb, age_label=label)


def profile_neuron_count(p: NeuroProfile) -> int:
    """Estimación de neuronas activas (corteza E/I + hipocampo + lóbulos)."""
    inh = 0
    if p.interneurons:
        inh += max(4, p.n_associative // 5) + max(4, p.n_limbic // 5)
    cortex = p.n_sensory + p.n_limbic + p.n_associative + p.n_prefrontal + p.n_motor + inh
    hippo = p.n_dg + p.n_ca3 + p.n_ca1
    lobes = 4 * p.n_lobe_per_column
    return cortex + hippo + lobes


def resolve_experiment_profile(name: str | None = None) -> NeuroProfile:
    key = (name or os.environ.get("CEREBRO_EXPERIMENT_PROFILE", "compact")).strip().lower()
    if key in ("50k", "scale50k", "scale_50k", "scale-50k"):
        return SCALE_50K_PROFILE
    if key in ("100k", "scale100k", "scale_100k", "scale-100k"):
        return SCALE_100K_PROFILE
    if key in ("10k", "scale10k", "scale_10k", "scale-10k"):
        return SCALE_10K_PROFILE
    if key in ("compact", "500", "fast"):
        return COMPACT_PROFILE
    if key in ("lite", "demo-lite", "demo_lite"):
        return DEMO_LITE_PROFILE
    if key in ("large", "1.4k", "default", "virtual"):
        return resolve_default_profile()
    raise ValueError(f"Perfil desconocido: {key!r}. Usa: compact, lite, 10k, 50k, 100k, large")
