"""
Persistencia en disco: sinapsis, memorias episódicas, personaje y moduladores.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import TYPE_CHECKING, Any

import numpy as np

if TYPE_CHECKING:
    from .mind import InfantApeBrain
    from .synapse import SparseSynapses

from .companion import CompanionAgent
from .chemistry import PeerBond
from .journey import HeroJourney
from .lifecycle import LifecycleState


def _pack_synapse(syn: SparseSynapses, prefix: str) -> dict[str, np.ndarray]:
    return {
        f"{prefix}_w": syn.w,
        f"{prefix}_indices": syn.indices,
        f"{prefix}_indptr": syn.indptr,
    }


def _track_meta(state) -> dict[str, Any]:
    return {
        "completed": list(state.completed),
        "current_key": state.current_key,
        "last_key": state.last_key,
        "study_count": state.study_count,
        "focus_ticks": state.focus_ticks,
        "focus_tags": list(state.focus_tags),
    }


def _load_track(meta: dict | None, *, sections, track_name: str, default_factory):
    from .study_track import TrackState

    if not meta:
        return default_factory()
    return TrackState.from_dict(meta, sections=sections, track_name=track_name)

def _unpack_synapse(syn: SparseSynapses, data: dict[str, np.ndarray], prefix: str) -> None:
    syn.w = np.asarray(data[f"{prefix}_w"], dtype=np.float32)
    syn.indices = np.asarray(data[f"{prefix}_indices"], dtype=np.int32)
    syn.indptr = np.asarray(data[f"{prefix}_indptr"], dtype=np.int32)


def _memory_to_json(mem: dict) -> dict:
    return {
        "key": mem["key"],
        "label": mem["label"],
        "modality": mem["modality"],
        "pattern": np.asarray(mem["pattern"], dtype=np.float32).tolist(),
        "motor": mem.get("motor", []),
        "valence": float(mem.get("valence", 0)),
        "arousal": float(mem.get("arousal", 0)),
        "count": int(mem.get("count", 1)),
        "hits": int(mem.get("hits", 0)),
        "tags": list(mem.get("tags", [])),
    }


def _memory_from_json(d: dict) -> dict:
    return {
        **d,
        "pattern": np.asarray(d["pattern"], dtype=np.float32),
    }


class BrainPersistence:
    def __init__(self, base_dir: Path) -> None:
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        self.npz_path = self.base_dir / "weights.npz"
        self.meta_path = self.base_dir / "meta.json"

    def save(self, brain: InfantApeBrain) -> dict:
        if hasattr(brain, "typed_memory"):
            brain.typed_memory.save()
        if hasattr(brain, "affordance_map"):
            brain.affordance_map.save()
        cx = brain.cortex
        arrays: dict[str, np.ndarray] = {}
        syn_map = [
            ("s_to_l", cx.s_to_l),
            ("l_to_a", cx.l_to_a),
            ("a_to_a", cx.a_to_a),
            ("a_to_p", cx.a_to_p),
            ("p_to_a", cx.p_to_a),
            ("a_to_m", cx.a_to_m),
            ("s_to_m", cx.s_to_m),
            ("h_in_dg", brain.hippo.in_to_dg),
            ("h_dg_ca3", brain.hippo.dg_to_ca3),
            ("h_ca3_r", brain.hippo.ca3_recur),
            ("h_ca3_ca1", brain.hippo.ca3_to_ca1),
        ]
        for name, syn in syn_map:
            arrays.update(_pack_synapse(syn, name))

        arrays["bg_habit"] = brain.basal_ganglia.habit
        np.savez_compressed(self.npz_path, **arrays)

        meta = {
            "version": 3,
            "profile": brain.profile.name,
            "time_ms": brain.cortex.time_ms,
            "modulators": brain.modulators.to_dict(),
            "hypothalamus": {
                "dopamine": brain.hypothalamus.dopamine,
                "cortisol": brain.hypothalamus.cortisol,
                "oxytocin": brain.hypothalamus.oxytocin,
                "energy": brain.hypothalamus.energy,
                "familiarity": brain.hypothalamus.familiarity,
            },
            "brainstem_sleep": brain.brainstem.sleep_pressure,
            "nuclei_accumbens": brain.nuclei.accumbens_activation,
            "persona": brain.persona.to_dict(),
            "memory_count": brain.hippocampus.size,
            "body": brain.body.to_dict(),
            "biomechanics": brain.biomech.to_dict(),
            "hedonics": brain.hedonics.to_dict(),
            "consciousness": brain.consciousness.to_dict(),
            "world": brain.world.with_companion(
                brain.companion.to_dict() if getattr(brain, "companion", None) else None
            ),
            "thoughts_recent": brain.thoughts.recent(6),
            "companion": brain.companion.to_dict(),
            "lifecycle": brain.lifecycle.to_dict(),
            "journey": brain.journey.to_dict(),
            "chemistry": brain.chemistry.to_dict(),
            "offspring": brain.offspring_agent.to_dict() if brain.offspring_agent else None,
            "amygdala": {
                "valence": brain.amygdala.valence,
                "arousal": brain.amygdala.arousal,
            },
            "curriculum": {
                "completed": list(brain.curriculum.completed),
                "current_key": brain.curriculum.current_key,
                "last_key": brain.curriculum.last_key,
                "study_count": brain.curriculum.study_count,
                "focus_ticks": brain.curriculum.focus_ticks,
                "focus_anatomy": list(brain.curriculum.focus_anatomy),
            },
            "clinical_neurology": _track_meta(brain.clinical_neurology),
            "biopsych": _track_meta(brain.biopsych),
            "infant_brain": _track_meta(brain.infant_brain),
            "brain_facts": {
                "completed": list(brain.brain_facts.completed),
                "studied_order": list(brain.brain_facts.studied_order),
                "current_key": brain.brain_facts.current_key,
                "last_key": brain.brain_facts.last_key,
                "study_count": brain.brain_facts.study_count,
                "focus_ticks": brain.brain_facts.focus_ticks,
                "focus_modules": list(brain.brain_facts.focus_modules),
            },
            "sleep_architecture": brain.sleep_arch.to_dict(),
            "sleep_study_summary": {
                "total_actions": brain.sleep_study.log.total_actions,
                "total_sessions": brain.sleep_study.log.total_sessions,
                "background_ticks": brain.sleep_study.log.background_ticks,
            },
            "schema_learner": brain.schema_learner.to_dict(),
            "typed_memory_summary": {
                "semantic_count": len(brain.typed_memory.semantic),
                "procedural_count": len(brain.typed_memory.procedural),
            },
            "affordance_summary": {
                "record_count": len(brain.affordance_map.records),
                "save_error": brain.affordance_map.save_error or None,
            },
            "decompress_governor": brain.decompress_governor.cumulative_dict(),
        }
        self.meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        return {
            "saved": True,
            "path": str(self.base_dir),
            "memories": meta["memory_count"],
            "synapses_bytes": self.npz_path.stat().st_size if self.npz_path.exists() else 0,
        }

    def load(self, brain: InfantApeBrain) -> dict:
        if not self.meta_path.exists() or not self.npz_path.exists():
            return {"loaded": False, "reason": "no_state"}

        meta = json.loads(self.meta_path.read_text(encoding="utf-8"))
        if meta.get("profile") != brain.profile.name:
            return {
                "loaded": False,
                "reason": "profile_mismatch",
                "expected": brain.profile.name,
                "file": meta.get("profile"),
            }

        data = np.load(self.npz_path)
        cx = brain.cortex
        for name, syn in [
            ("s_to_l", cx.s_to_l),
            ("l_to_a", cx.l_to_a),
            ("a_to_a", cx.a_to_a),
            ("a_to_p", cx.a_to_p),
            ("p_to_a", cx.p_to_a),
            ("a_to_m", cx.a_to_m),
            ("s_to_m", cx.s_to_m),
            ("h_in_dg", brain.hippo.in_to_dg),
            ("h_dg_ca3", brain.hippo.dg_to_ca3),
            ("h_ca3_r", brain.hippo.ca3_recur),
            ("h_ca3_ca1", brain.hippo.ca3_to_ca1),
        ]:
            _unpack_synapse(syn, data, name)

        brain.basal_ganglia.habit = np.asarray(data["bg_habit"], dtype=np.float32)

        mods = meta.get("modulators", {})
        brain.modulators.dopamine = float(mods.get("dopamine", 0.5))
        brain.modulators.serotonin = float(mods.get("serotonin", 0.5))
        brain.modulators.norepinephrine = float(mods.get("norepinephrine", 0.45))
        brain.modulators.acetylcholine = float(mods.get("acetylcholine", 0.5))
        brain.modulators.gaba_tone = float(mods.get("gaba_tone", 0.4))
        brain.modulators.glutamate_drive = float(mods.get("glutamate_drive", 0.55))

        hypo = meta.get("hypothalamus", {})
        brain.hypothalamus.dopamine = float(hypo.get("dopamine", brain.hypothalamus.dopamine))
        brain.hypothalamus.cortisol = float(hypo.get("cortisol", 0.2))
        brain.hypothalamus.oxytocin = float(hypo.get("oxytocin", 0.4))
        brain.hypothalamus.energy = float(hypo.get("energy", 0.7))
        brain.hypothalamus.familiarity = float(hypo.get("familiarity", 0))

        brain.brainstem.sleep_pressure = float(meta.get("brainstem_sleep", 0))
        brain.nuclei.accumbens_activation = float(meta.get("nuclei_accumbens", 0.3))

        am = meta.get("amygdala", {})
        brain.amygdala.valence = float(am.get("valence", 0))
        brain.amygdala.arousal = float(am.get("arousal", 0.3))

        brain.cortex.time_ms = int(meta.get("time_ms", 0))

        p = meta.get("persona", {})
        brain.persona.name = p.get("name", brain.persona.name)
        brain.persona.mood = p.get("mood", "calm")
        brain.persona.message = p.get("message", brain.persona.message)
        brain.persona.energy = float(p.get("energy", 0.7))
        brain.persona.familiarity = float(p.get("familiarity", 0))
        brain.persona.attachment = float(p.get("attachment", 0.35))
        brain.persona.experiences = int(p.get("experiences", 0))
        brain.persona.learned = list(p.get("learned", []))
        brain.persona.dialogue = list(p.get("dialogue", []))

        legacy = meta.get("memories", [])
        if legacy and brain.hippocampus.size == 0:
            brain.memory_store.import_legacy([_memory_from_json(m) for m in legacy])

        world_data = meta.get("world")
        if world_data:
            from .archetype_cards import legacy_stats

            # Accept a legacy stats key; counts are rebuilt from objects.
            legacy_stats(world_data)
            brain.world.ensure_home()
            brain.world.agent_x = float(world_data.get("agent", {}).get("x", brain.world.agent_x))
            brain.world.agent_y = float(world_data.get("agent", {}).get("y", brain.world.agent_y))
            brain.world.agent_dir = int(world_data.get("agent", {}).get("dir", 1))
            if brain.world.agent_x < 178:
                brain.world.agent_x = 200.0
                brain.world.agent_y = 210.0
            if world_data.get("tv"):
                brain.world.tv_state = dict(world_data["tv"])
            if world_data.get("web"):
                brain.world.web_state = dict(world_data["web"])
            if world_data.get("pantry"):
                brain.world.pantry = list(world_data["pantry"])
            from .food_system import ensure_garden_crops, ensure_stove

            ensure_garden_crops(brain.world)
            ensure_stove(brain.world)
            env_data = world_data.get("environment")
            if env_data:
                from .environment import WorldClock

                brain.world.clock = WorldClock.from_dict(env_data)

        body_data = meta.get("body")
        if body_data:
            brain.body.load_dict(body_data)

        hed_data = meta.get("hedonics")
        if hed_data:
            brain.hedonics.load_dict(hed_data)
        con_data = meta.get("consciousness")
        if con_data:
            brain.consciousness.load_dict(con_data)

        bio_data = meta.get("biomechanics")
        if bio_data:
            brain.biomech.load_dict(bio_data)

        comp_data = meta.get("companion")
        if comp_data:
            brain.companion = CompanionAgent.from_dict(comp_data)
        else:
            brain.ensure_companion()

        brain.lifecycle = LifecycleState.from_dict(meta.get("lifecycle"))
        brain.journey = HeroJourney.from_dict(meta.get("journey"))
        brain.chemistry = PeerBond.from_dict(meta.get("chemistry"))
        cur_data = meta.get("curriculum")
        if cur_data:
            from .curriculum import CurriculumState

            brain.curriculum = CurriculumState.from_dict(cur_data)
        bf_data = meta.get("brain_facts")
        if bf_data:
            from .brain_facts import BrainFactsCorpus

            brain.brain_facts = BrainFactsCorpus.from_dict(bf_data)
        from .clinical_neurology import SECTIONS as CLIN_SECTIONS, default_state as clinical_default
        from .biopsych_curriculum import SECTIONS as BIO_SECTIONS, default_state as biopsych_default
        from .infant_brain_curriculum import SECTIONS as INF_SECTIONS, default_state as infant_default

        brain.clinical_neurology = _load_track(
            meta.get("clinical_neurology"),
            sections=CLIN_SECTIONS,
            track_name="clinical_neurology",
            default_factory=clinical_default,
        )
        brain.biopsych = _load_track(
            meta.get("biopsych"),
            sections=BIO_SECTIONS,
            track_name="biopsych",
            default_factory=biopsych_default,
        )
        brain.infant_brain = _load_track(
            meta.get("infant_brain"),
            sections=INF_SECTIONS,
            track_name="infant_brain",
            default_factory=infant_default,
        )
        sa_data = meta.get("sleep_architecture")
        if sa_data:
            from .sleep_architecture import SleepArchitecture

            brain.sleep_arch = SleepArchitecture(
                last_phase=str(sa_data.get("last_phase", "awake")),
                cycles_completed=int(sa_data.get("cycles_completed", 0)),
                total_replays=int(sa_data.get("total_replays", 0)),
                history=list(sa_data.get("recent_phases") or []),
            )
        sl_data = meta.get("schema_learner")
        if sl_data and hasattr(brain, "schema_learner"):
            from .learned_schemas import SchemaLearner

            brain.schema_learner = SchemaLearner.from_dict(sl_data)
        if hasattr(brain, "typed_memory"):
            brain.typed_memory.bind_state_dir(self.base_dir)
            brain.typed_memory.load()
        if hasattr(brain, "sleep_study"):
            brain.sleep_study.attach_brain(brain)
        gov_data = meta.get("decompress_governor")
        if gov_data and hasattr(brain, "decompress_governor"):
            brain.decompress_governor.load_cumulative(gov_data)
        off_data = meta.get("offspring") or meta.get("offspring_agent")
        if off_data:
            brain.offspring_agent = CompanionAgent.from_dict(off_data)
        elif brain.lifecycle.offspring:
            brain._spawn_offspring_if_needed()

        if world_data and world_data.get("objects"):
            from .archetype_cards import normalize_card_meta
            from .world import WorldObject

            brain.world.objects = [
                WorldObject(
                    id=o["id"],
                    kind=o.get("kind", "book"),
                    x=float(o["x"]),
                    y=float(o["y"]),
                    label=o.get("label", ""),
                    modality=o.get("modality", "document"),
                    zone=o.get("zone", "house"),
                    meta=normalize_card_meta(o.get("meta") or {}),
                )
                for o in world_data["objects"]
            ]
            brain.world._desk_slots = max(brain.world._desk_slots, len(brain.world.objects))

        return {
            "loaded": True,
            "memories": brain.hippocampus.size,
            "time_ms": brain.cortex.time_ms,
            "dialogue_turns": len(brain.persona.dialogue),
        }

    def exists(self) -> bool:
        return self.meta_path.exists() and self.npz_path.exists()
