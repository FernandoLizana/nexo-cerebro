"""
Deliberación prefrontal — competencia Go/No-Go entre impulsos subcorticales y corteza.

No es un agente LLM: las acciones compiten como canales neuronales.
Límbico (drives, amígdala, dolor) vs PFC (WM + actividad prefrontal) → ganglios basales.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np

from .encode import encode_text
from .experiment_flags import get_flags

if TYPE_CHECKING:
    from .mind import InfantApeBrain

# Acciones conductuales = esquemas motores aprendibles (no intents de chatbot)
ACTION_SCHEMAS: tuple[dict[str, str], ...] = (
    {"key": "eat", "drive": "seek_food", "label": "comer", "target": "fridge"},
    {"key": "harvest", "drive": "seek_food", "label": "cosechar", "target": "garden"},
    {"key": "cook", "drive": "seek_cook", "label": "cocinar", "target": "stove"},
    {"key": "drink", "drive": "seek_water", "label": "beber", "target": "fridge"},
    {"key": "rest", "drive": "seek_rest", "label": "descansar", "target": ""},
    {"key": "sleep", "drive": "sleep_need", "label": "dormir", "target": ""},
    {"key": "tv", "drive": "seek_stimulus", "label": "estimularse (TV)", "target": ""},
    {"key": "research", "drive": "seek_curiosity", "label": "buscar en la web", "target": "desk"},
    {"key": "study", "drive": "seek_curiosity", "label": "estudiar neurociencia", "target": "desk"},
    {"key": "clinical", "drive": "seek_curiosity", "label": "neurología clínica (UDD)", "target": "desk"},
    {"key": "biopsych", "drive": "seek_curiosity", "label": "biological psychology", "target": "desk"},
    {"key": "infant", "drive": "seek_curiosity", "label": "libro infantil del cerebro", "target": "desk"},
    {"key": "companion", "drive": "seek_companion", "label": "acercarse a Nira", "target": "companion"},
    {"key": "hygiene", "drive": "seek_hygiene", "label": "higiene", "target": "bath"},
    {"key": "bathroom", "drive": "seek_bathroom", "label": "baño", "target": "toilet"},
    {"key": "relief", "drive": "seek_relief", "label": "atender dolor", "target": ""},
    {"key": "warmth", "drive": "seek_warmth", "label": "buscar calor", "target": ""},
    {"key": "wander", "drive": "", "label": "deambular", "target": ""},
)

# Sesgo hacia índices motores corticales (0–3 loc, 4 interact)
MOTOR_AFFINITY: dict[str, list[int]] = {
    "eat": [4, 1],
    "harvest": [4, 1, 3],
    "cook": [4, 1],
    "drink": [4, 1],
    "rest": [4, 2],
    "sleep": [4, 2],
    "tv": [4, 0],
    "explore": [4, 1, 3],
    "research": [4, 1],
    "study": [4, 1],
    "clinical": [4, 1],
    "biopsych": [4, 1],
    "infant": [4, 1],
    "companion": [1, 3],
    "hygiene": [4],
    "bathroom": [4],
    "relief": [2, 4],
    "warmth": [1, 0],
    "wander": [0, 1, 2, 3],
}


@dataclass
class ActionContestant:
    key: str
    label: str
    drive: str
    limbic: float = 0.0
    pfc: float = 0.0
    habit: float = 0.0
    go: float = 0.0
    no_go: float = 0.0
    net: float = 0.0
    selected: bool = False


@dataclass
class DeliberationResult:
    choice: str = "deambular"
    choice_key: str = "wander"
    drive_key: str = ""
    confidence: float = 0.25
    agency: float = 0.0
    conflict: float = 0.0
    limbic_winner: str = ""
    pfc_winner: str = ""
    limbic_winner_key: str = ""
    pfc_winner_key: str = ""
    inhibited: bool = False
    contestants: list[ActionContestant] = field(default_factory=list)
    motor_bias: list[float] = field(default_factory=list)
    trace: list[str] = field(default_factory=list)
    agency_metrics: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "choice": self.choice,
            "choice_key": self.choice_key,
            "drive_key": self.drive_key,
            "confidence": round(self.confidence, 3),
            "agency": round(self.agency, 3),
            "conflict": round(self.conflict, 3),
            "limbic_winner": self.limbic_winner,
            "pfc_winner": self.pfc_winner,
            "limbic_winner_key": self.limbic_winner_key,
            "pfc_winner_key": self.pfc_winner_key,
            "inhibited": self.inhibited,
            "contestants": [
                {
                    "key": c.key,
                    "label": c.label,
                    "limbic": round(c.limbic, 3),
                    "pfc": round(c.pfc, 3),
                    "habit": round(c.habit, 3),
                    "go": round(c.go, 3),
                    "no_go": round(c.no_go, 3),
                    "net": round(c.net, 3),
                    "selected": c.selected,
                }
                for c in self.contestants[:8]
            ],
            "trace": self.trace[:5],
            "agency_metrics": self.agency_metrics,
            "legacy_agency_score": round(self.agency, 3),
        }


@dataclass
class PrefrontalDeliberation:
    """Circuito PFC–striatum: inhibición de impulsos y selección voluntaria."""

    _encodings: dict[str, np.ndarray] = field(default_factory=dict, init=False)
    last: DeliberationResult = field(default_factory=DeliberationResult, init=False)
    _last_decision_record: Any = field(default=None, init=False)
    _habit_channels: dict[str, float] = field(default_factory=dict, init=False)
    _penalties: dict[str, float] = field(default_factory=dict, init=False)

    def set_penalty(self, choice_key: str, amount: float) -> None:
        self._penalties[choice_key] = float(amount)

    def clear_penalties(self) -> None:
        self._penalties.clear()

    def _ensure_encodings(self, n_pfc: int, schemas: list[dict] | None = None) -> None:
        schemas = schemas or list(ACTION_SCHEMAS)
        need = any(s["key"] not in self._encodings for s in schemas)
        if self._encodings and not need and next(iter(self._encodings.values())).size == n_pfc:
            return
        # Reconstruye solo claves faltantes / tamaño incorrecto
        if self._encodings and next(iter(self._encodings.values())).size != n_pfc:
            self._encodings.clear()
        for schema in schemas:
            key = schema["key"]
            if key in self._encodings and self._encodings[key].size == n_pfc:
                continue
            raw = encode_text(f"motor_schema:{key}:{schema['label']}", n_pfc)
            self._encodings[key] = raw.astype(np.float32)

    def _pfc_support(self, brain: InfantApeBrain, key: str) -> float:
        n_pfc = brain.cortex.n_prefrontal
        if n_pfc <= 0:
            return 0.0
        enc = self._encodings.get(key)
        if enc is None:
            return 0.0
        wm = brain.cortex._wm[:n_pfc]
        pfc_v = brain.cortex.prefrontal.v[:n_pfc]
        denom = max(float(np.linalg.norm(pfc_v)), 1e-6)
        pfc_norm = pfc_v / denom
        wm_match = float(np.dot(wm, enc))
        act_match = float(np.dot(pfc_norm, enc))
        ach = brain.modulators.acetylcholine
        support = float(np.clip(0.55 * wm_match + 0.45 * act_match * (0.7 + 0.3 * ach), 0, 1.25))
        # WM sobrecargada debilita match prefrontal (no fuerza limbic).
        if hasattr(brain, "working_memory") and brain.working_memory.limited:
            support *= float(brain.working_memory.pfc_gain_scale())
        return float(np.clip(support, 0, 1.25))

    def _limbic_urgency(
        self,
        brain: InfantApeBrain,
        schema: dict,
        drives: dict,
        *,
        pain: float,
        attended: list[dict],
    ) -> float:
        drive = schema["drive"]
        if not drive:
            return 0.12 + 0.08 * brain.modulators.dopamine
        base = float(drives.get(drive, 0.0))
        arousal = float(brain.amygdala.arousal)
        valence = float(brain.amygdala.valence)
        boost = 0.12 * arousal
        if valence < -0.2:
            boost += 0.08 * (-valence)
        if schema["key"] == "relief" and pain > 0.12:
            base = max(base, pain * 1.1)
        if attended and attended[0].get("kind") == "pain" and schema["key"] == "relief":
            base = max(base, 0.55)
        if schema["key"] == "companion":
            base = max(base, brain.chemistry.seek_companion_drive() * 0.85)
        if hasattr(brain, "affect"):
            sv = brain.affect.subjective_valence()
            sa = brain.affect.subjective_arousal()
            if schema["key"] in ("study", "research", "clinical", "biopsych", "infant"):
                base += max(0.0, sv) * 0.1 + sa * 0.08
            if schema["key"] == "relief" and (sv < -0.15 or pain > 0.2):
                base += 0.12
        from .behavior_integration import deliberation_track_boost

        base += deliberation_track_boost(brain, schema["key"])
        return float(np.clip(base + boost, 0, 1.2))

    def _habit_bias(self, brain: InfantApeBrain, key: str, room: str, hour: int) -> float:
        from .learned_schemas import all_action_schemas

        schema = next((s for s in all_action_schemas(brain) if s["key"] == key), None)
        if not schema or not schema["drive"]:
            return self._habit_channels.get(key, 0.0)
        cue = f"{room}|{hour // 3}|{schema['drive']}"
        h = brain.cognition.habits.routines.get(cue, 0.0)
        ch = self._habit_channels.get(key, 0.0)
        # Schemas aprendidos: hábito contextual extra (aún compiten)
        if key.startswith("learned_"):
            ch = max(ch, 0.22)
        return float(np.clip(0.6 * h + 0.4 * ch, 0, 1))

    def run(
        self,
        brain: InfantApeBrain,
        *,
        drives: dict,
        ambient: dict,
        attended: list[dict],
        habit: dict | None,
        surprise: float,
    ) -> DeliberationResult:
        from .learned_schemas import all_action_schemas

        n_pfc = brain.cortex.n_prefrontal
        n_motor = brain.cortex.n_motor
        schemas = all_action_schemas(brain)
        self._ensure_encodings(n_pfc, schemas)

        room = brain.world.current_room()
        hour = int(ambient.get("hour", 12))
        pain = brain.body.total_pain()
        da = brain.modulators.dopamine
        gaba = brain.modulators.gaba_tone
        serotonin = brain.modulators.serotonin
        pfc_inhib = float(brain.profile.prefrontal_inhibition)
        if get_flags(brain).enable_lifecycle_plasticity:
            pfc_inhib *= float(brain.lifecycle.neuro_modulation().get("pfc_inhibition_scale", 1.0))

        contestants: list[ActionContestant] = []
        for schema in schemas:
            key = schema["key"]
            limbic = self._limbic_urgency(brain, schema, drives, pain=pain, attended=attended)
            if key != "wander" and limbic < 0.08 and schema["drive"] not in drives:
                continue
            pfc = self._pfc_support(brain, key)
            hab = self._habit_bias(brain, key, room, hour)
            if habit and habit.get("routine", "").startswith(schema["label"][:4]):
                hab = max(hab, float(habit.get("strength", 0)))

            go = (
                limbic * (0.5 + 0.35 * da)
                + pfc * (0.42 + 0.28 * brain.modulators.acetylcholine)
                + hab * (0.35 + 0.25 * da)
            )
            contestants.append(
                ActionContestant(
                    key=key,
                    label=schema["label"],
                    drive=schema["drive"],
                    limbic=limbic,
                    pfc=pfc,
                    habit=hab,
                    go=go,
                )
            )

        if hasattr(brain, "consciousness") and get_flags(brain).enable_consciousness:
            brain.consciousness.apply_deliberation_bias(contestants)

        # TD: sesgo Go acotado — nunca elige ganador (libre albedrío / agency PFC).
        flags_early = get_flags(brain)
        if (
            flags_early.enable_td_reward
            and hasattr(brain, "td_reward")
            and contestants
        ):
            top_d = ""
            if drives:
                top_d = max(drives.items(), key=lambda x: x[1])[0]
            # Conflicto estimado previo (limbic vs pfc tops en go aún sin no-go)
            lim_k = max(contestants, key=lambda c: c.limbic).key
            pfc_k = max(contestants, key=lambda c: c.pfc).key
            pre_conflict = 0.35 if lim_k != pfc_k else 0.0
            biases = brain.td_reward.go_biases(
                room=room,
                top_drive=top_d,
                hour=hour,
                action_keys=[c.key for c in contestants],
                conflict=pre_conflict,
            )
            for c in contestants:
                b = biases.get(c.key, 0.0)
                if b:
                    c.go = float(c.go + b)
                    # PFC fuerte: puede ignorar sesgo hedónico/TD (protege voluntad)
                    if c.pfc > 0.35 and b > 0 and lim_k == c.key and pfc_k != c.key:
                        c.go = float(c.go - 0.55 * b)

        # Affordances: evidencia causal acotada. Solo modifica canales Go/No-Go
        # de concursantes existentes; el ganador sigue naciendo exclusivamente
        # en el max() de este método.
        if (
            flags_early.enable_affordance_learning
            and hasattr(brain, "affordance_map")
            and contestants
        ):
            top_drive = max(drives.items(), key=lambda x: x[1])[0] if drives else ""
            biases = brain.affordance_map.biases_for(
                candidate_keys=[c.key for c in contestants],
                dominant_drive=top_drive,
                room=room,
            )
            for contestant in contestants:
                contestant.go = float(
                    contestant.go + biases.get(contestant.key, 0.0)
                )

        if (
            flags_early.enable_counterfactual
            and hasattr(brain, "counterfactual")
            and contestants
        ):
            top_drive = max(drives.items(), key=lambda x: x[1])[0] if drives else ""
            cf_biases = brain.counterfactual.biases_for(
                candidate_keys=[c.key for c in contestants],
                dominant_drive=top_drive,
                room=room,
                affordance_map=getattr(brain, "affordance_map", None),
            )
            for contestant in contestants:
                contestant.go = float(
                    contestant.go + cf_biases.get(contestant.key, 0.0)
                )

        if (
            flags_early.enable_reward_learning
            and hasattr(brain, "reward_learning")
            and contestants
        ):
            brain.reward_learning.model_based_pfc_boost(brain, contestants)

        if (
            flags_early.enable_motor_dynamics
            and hasattr(brain, "motor_dynamics")
            and contestants
        ):
            brain.motor_dynamics.basal_habituation(brain, contestants)

        if (
            flags_early.enable_lifecycle_dynamics
            and flags_early.enable_cognitive_aging
            and hasattr(brain, "lifecycle_dynamics")
            and contestants
        ):
            brain.lifecycle_dynamics.deliberation_aging_boost(brain, contestants)

        if not contestants:
            contestants.append(ActionContestant(key="wander", label="deambular", drive=""))

        limbic_top = max(contestants, key=lambda c: c.limbic)
        pfc_top = max(contestants, key=lambda c: c.pfc)
        conflict = 0.0
        if limbic_top.key != pfc_top.key and limbic_top.limbic > 0.28 and pfc_top.pfc > 0.22:
            conflict = float(
                np.clip((limbic_top.limbic + pfc_top.pfc) * 0.35 * (1.0 - serotonin * 0.4), 0, 0.85)
            )

        trace: list[str] = []
        for c in contestants:
            ng = gaba * pfc_inhib * (0.25 + conflict)
            if c.key == limbic_top.key and pfc_top.key != c.key and pfc_top.pfc > c.pfc + 0.08:
                ng += pfc_top.pfc * pfc_inhib * 0.65
                trace.insert(0, f"PFC inhibe impulso «{c.label}»")
            if surprise > 0.5:
                ng += 0.06 * surprise
            c.no_go = float(ng)
            c.net = float(c.go - c.no_go)
            pen = self._penalties.get(c.key, 0.0)
            if pen > 0:
                c.net -= pen
                trace.append(f"penaliza reelección «{c.label}»")

        if flags_early.enable_executive_cognition and hasattr(brain, "executive"):
            brain.executive.stroop_in_deliberation(
                brain, contestants, limbic_top=limbic_top, pfc_top=pfc_top
            )
            for c in contestants:
                c.net = float(c.go - c.no_go)

        noise_scale = 0.055 * (1.0 - da * 0.45)
        rng = brain.random_streams.decision if brain.random_streams is not None else np.random.default_rng(int(brain.seed))
        for c in contestants:
            c.net += float(rng.normal(0, noise_scale))

        winner = max(contestants, key=lambda c: c.net)
        flags = get_flags(brain)
        if flags.force_limbic_winner and limbic_top.limbic > 0.05:
            for c in contestants:
                c.selected = False
            winner = limbic_top
        winner.selected = True

        inhibited = limbic_top.key != winner.key and limbic_top.limbic > winner.limbic * 0.85
        if inhibited:
            trace.insert(0, f"voluntad → «{winner.label}» frena «{limbic_top.label}»")

        agency = float(np.clip(winner.pfc / (winner.limbic + winner.pfc + 0.15), 0, 1))
        if inhibited:
            agency = float(np.clip(agency + 0.2, 0, 1))

        ordered = sorted(contestants, key=lambda c: c.net, reverse=True)
        margin = ordered[0].net - ordered[1].net if len(ordered) >= 2 else float(ordered[0].net if ordered else 0.0)
        from nexo.agency_metrics import compute_agency_metrics, confidence_from_margin

        confidence = confidence_from_margin(margin, temperature=0.10)
        confidence = float(np.clip(confidence * 0.65 + winner.go * 0.25 - conflict * 0.15, 0.12, 0.96))

        agency_metrics = compute_agency_metrics(
            legacy_agency=agency,
            contestants=contestants,
            winner_key=winner.key,
            limbic_winner_key=limbic_top.key,
            inhibited=inhibited,
            conflict=conflict,
            pfc_veto=inhibited and winner.key == pfc_top.key,
        )
        from nexo.decision_port import DecisionPort, config_hash_from_brain

        _decision_record = DecisionPort.commit(
            choice_key=winner.key,
            tick=int(getattr(brain.sim_clock, "tick", brain.lifecycle.age_ticks)),
            seed=int(brain.seed),
            config_hash=config_hash_from_brain(brain),
            contestants=contestants,
            limbic_winner_key=limbic_top.key,
            pfc_winner_key=pfc_top.key,
            inhibited=inhibited,
            margin=margin,
            legacy_agency_score=agency,
        )
        self._last_decision_record = _decision_record

        motor_bias = np.zeros(n_motor, dtype=np.float32)
        affinity = MOTOR_AFFINITY.get(winner.key, [0])
        if hasattr(brain, "schema_learner") and winner.key.startswith("learned_"):
            affinity = brain.schema_learner.motor_affinity_for(winner.key)
        for idx in affinity:
            if idx < n_motor:
                motor_bias[idx] += 0.35 + 0.25 * confidence
        if winner.pfc > winner.limbic:
            for i in range(min(3, n_motor)):
                motor_bias[i] += 0.06 * winner.pfc

        self._habit_channels[winner.key] = float(
            np.clip(self._habit_channels.get(winner.key, 0) + 0.05 * (0.4 + da), 0, 1)
        )

        if winner.drive:
            brain.cognition.habits.reinforce(room, hour, winner.drive, da)

        result = DeliberationResult(
            choice=winner.label,
            choice_key=winner.key,
            drive_key=winner.drive,
            confidence=confidence,
            agency=agency,
            conflict=conflict,
            limbic_winner=limbic_top.label,
            pfc_winner=pfc_top.label,
            limbic_winner_key=limbic_top.key,
            pfc_winner_key=pfc_top.key,
            inhibited=inhibited,
            contestants=sorted(contestants, key=lambda c: -c.net),
            motor_bias=motor_bias.tolist(),
            trace=trace,
            agency_metrics=agency_metrics.to_dict(),
        )
        self.last = result
        if flags.enable_executive_cognition and hasattr(brain, "executive"):
            brain.executive.post_deliberation(
                brain,
                contestants=contestants,
                limbic_top=limbic_top,
                pfc_top=pfc_top,
            )
        return result

    def motor_bias_array(self, brain: InfantApeBrain) -> np.ndarray:
        n = brain.cortex.n_motor
        bias = np.zeros(n, dtype=np.float32)
        for i, v in enumerate(self.last.motor_bias[:n]):
            bias[i] = float(v)
        proc = brain.typed_memory.procedural_motor_bias(
            brain, self.last.choice_key, brain.world.current_room()
        )
        m = min(n, proc.size)
        if m:
            bias[:m] += proc[:m]
        return bias

    def focused_drives(self, drives: dict) -> dict:
        """Impulsos filtrados por la acción ganadora (meta cortical, no max global)."""
        if not self.last.drive_key:
            return drives
        dk = self.last.drive_key
        out = {k: float(v) * 0.35 for k, v in drives.items()}
        out[dk] = float(max(drives.get(dk, 0.0), 0.42 + self.last.confidence * 0.25))
        return out
