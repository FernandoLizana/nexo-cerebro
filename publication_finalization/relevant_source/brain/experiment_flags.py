"""
Flags centralizados para ablaciones reproducibles (paper / experiments/).

Se adjuntan a ``InfantApeBrain.experiment_flags``; el runner headless los configura
sin esparcir ``if`` por ``mind.py``.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .mind import InfantApeBrain


@dataclass(frozen=True)
class AblationFlags:
    bind_deliberation: bool = True
    force_limbic_winner: bool = False
    disable_hippocampus: bool = False
    disable_affect: bool = False
    enable_verify: bool = True
    enable_goal_stack: bool = True
    enable_connectome_scaffold: bool = False
    enable_consciousness: bool = True
    # TD dopamina predictiva: OFF en batch paper (E1–E3); ON en demo vía app.py / env.
    enable_td_reward: bool = False
    # Ritmo circadiano de cortisol (sesgo suave; no fuerza acciones).
    enable_circadian: bool = False
    # WM con capacidad/interferencia (Miller ~7); OFF en paper.
    enable_limited_wm: bool = False
    # Atención competitiva top-down/bottom-up con presupuesto; OFF en paper.
    enable_attention_budget: bool = False
    # Sueño selectivo (prioriza |valence|); OFF en paper E3; E4 lo activa explícito.
    enable_selective_sleep: bool = False
    # Lenguaje grounded (palabras→drives/sensory); OFF en paper; ON en demo.
    enable_grounding: bool = False
    # Schemas motores aprendidos por consolidación; OFF en paper.
    enable_learned_schemas: bool = False
    # Plasticidad / inhibición PFC según etapa vital; OFF en paper.
    enable_lifecycle_plasticity: bool = False
    # Inyección virtual → columnas lobulares (50k / escala); OFF en paper.
    enable_lobe_virtual_inject: bool = False
    # Política motora continua (priors); OFF en paper.
    enable_continuous_motor: bool = False
    # Latencias multimodales vision/audition/proprio; OFF en paper.
    enable_multimodal_delays: bool = False
    # Level 2: objeto+interacción→consecuencia; evidencia acotada para PFC.
    enable_affordance_learning: bool = False
    # Level 2.2: telemetría cognitiva compacta por tick (API/Arena).
    enable_neural_telemetry: bool = False
    # Level 2.3: predicciones contrafactuales acotadas (no eligen acción).
    enable_counterfactual: bool = False
    verify_conflict_threshold: float = 0.35
    rechoice_penalty: float = 0.15


def get_flags(brain: InfantApeBrain) -> AblationFlags:
    return getattr(brain, "experiment_flags", AblationFlags())


def apply_condition(name: str) -> AblationFlags:
    key = name.strip().lower().replace("-", "").replace("_", "")
    table: dict[str, AblationFlags] = {
        "full": AblationFlags(),
        "nobind": replace(AblationFlags(), bind_deliberation=False),
        "nopfc": replace(AblationFlags(), force_limbic_winner=True),
        "nohippo": replace(AblationFlags(), disable_hippocampus=True),
        "noaffect": replace(AblationFlags(), disable_affect=True),
        "noverify": replace(AblationFlags(), enable_verify=False),
        "nogoalstack": replace(AblationFlags(), enable_goal_stack=False),
        "noscaffold": replace(AblationFlags(), enable_connectome_scaffold=False),
        "scaffold": replace(AblationFlags(), enable_connectome_scaffold=True),
        "noconscious": replace(AblationFlags(), enable_consciousness=False),
        "notd": replace(AblationFlags(), enable_td_reward=False),
        "td": replace(AblationFlags(), enable_td_reward=True),
        "nowm": replace(AblationFlags(), enable_limited_wm=False),
        "noattention": replace(AblationFlags(), enable_attention_budget=False),
    }
    if key not in table:
        raise ValueError(f"Condición desconocida: {name!r}. Usa: {', '.join(table)}")
    return table[key]


CONDITION_NAMES: tuple[str, ...] = ("full", "nobind", "nopfc", "nohippo", "noaffect", "noconscious")


def resolve_demo_flags() -> AblationFlags:
    """Flags para Flask demo: TD + circadiano + WM + atención ON; paper batch sigue OFF."""
    import os

    def _on(name: str, default: str = "1") -> bool:
        return os.environ.get(name, default).strip().lower() not in ("0", "false", "off", "no")

    return replace(
        AblationFlags(),
        enable_td_reward=_on("CEREBRO_TD"),
        enable_circadian=_on("CEREBRO_CIRCADIAN"),
        enable_limited_wm=_on("CEREBRO_LIMITED_WM"),
        enable_attention_budget=_on("CEREBRO_ATTENTION_BUDGET"),
        enable_grounding=_on("CEREBRO_GROUNDING"),
        enable_learned_schemas=_on("CEREBRO_LEARNED_SCHEMAS"),
        enable_lifecycle_plasticity=_on("CEREBRO_LIFECYCLE_PLASTICITY"),
        enable_lobe_virtual_inject=_on("CEREBRO_LOBE_VIRTUAL"),
        enable_continuous_motor=_on("CEREBRO_CONTINUOUS_MOTOR"),
        enable_multimodal_delays=_on("CEREBRO_MULTIMODAL"),
        enable_affordance_learning=_on("CEREBRO_AFFORDANCES"),
        enable_neural_telemetry=_on("CEREBRO_TELEMETRY"),
        enable_counterfactual=_on("CEREBRO_COUNTERFACTUAL"),
        # Demo: schemas desde hábitos + éxitos causales (Level 2.4).
        # Paper batch sigue con AblationFlags() → OFF.
    )
