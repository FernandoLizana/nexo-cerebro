"""
Neural Agent Loop — bucle embodied multi-fase; LLM solo en reflect (post hoc).

Fases: interocept → perceive → cognize → [imagine] → commit → verify → act → learn → reflect
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

import numpy as np

from .deliberation import MOTOR_AFFINITY
from .experiment_flags import get_flags
from .goal_stack import GoalStack
from .navigation import augment_motor, decode_cortex_motor, resolve_walk_goal
from .backend import get_backend
from .environment import circadian_profile
from .verbalize import format_episode_label
from .somatic_affordances import apply_somatic_contact
from .social_exchange import run_social_exchange

if TYPE_CHECKING:
    from .mind import InfantApeBrain


@dataclass
class AgentLoopState:
    pending_rechoice: bool = False
    failed_choice_key: str = ""
    phase_trace: list[str] = field(default_factory=list)
    chunks_loaded_last_tick: int = 0
    verified_this_tick: bool = False
    redeliberations: int = 0

    def to_dict(self) -> dict[str, Any]:
        return {
            "pending_rechoice": self.pending_rechoice,
            "failed_choice_key": self.failed_choice_key,
            "redeliberations": self.redeliberations,
            "chunks_loaded_last_tick": self.chunks_loaded_last_tick,
            "phase_trace": self.phase_trace[-8:],
        }


@dataclass
class NeuralAgentLoop:
    state: AgentLoopState = field(default_factory=AgentLoopState)
    goal_stack: GoalStack = field(default_factory=GoalStack)

    def run(self, brain: InfantApeBrain, *, steps: int = 1) -> dict:
        if brain.headless:
            return self._run_headless(brain, steps=steps)
        return self._run_full(brain, steps=steps)

    def _alive_guard(self, brain: InfantApeBrain) -> dict | None:
        if brain.lifecycle.alive:
            return None
        base = {
            "alive": False,
            "lifecycle": brain.lifecycle.to_dict(),
            "world": brain._world_dict(),
        }
        if brain.headless:
            base.update(
                {
                    "remembered": False,
                    "motor": [],
                    "deliberation": brain.deliberation.last.to_dict(),
                    "drives": brain._merged_drives(),
                    "cognition": brain.cognition.to_dict(),
                }
            )
        else:
            base.update(
                {
                    "character": brain.persona.to_dict(),
                    "message": brain.persona.message,
                }
            )
        return base

    def _apply_sleep_drive(self, drives: dict, hour: int) -> None:
        if hour >= 22 or hour < 5:
            drives["sleep_need"] = float(min(1.0, drives.get("sleep_need", 0) + 0.12))

    def _phase_interocept_headless(self, brain: InfantApeBrain, env: dict) -> None:
        brain.world.advance_clock(1)
        brain.lifecycle.age_ticks += 1
        brain.lifecycle._update_stage()
        circ = circadian_profile(env) if get_flags(brain).enable_circadian else None
        if circ is not None:
            env["circadian"] = circ
            self._apply_circadian_body_state(brain, circ)
        brain._last_env = env
        brain.affect.tick_decay()
        brain.body.tick(
            room_temp=brain.world.room_temperature(),
            activity=0.15,
            sleep_pressure=brain.brainstem.sleep_pressure,
            watching_tv=False,
            strain=1.0,
            ordeal_active=False,
            circadian=circ,
        )
        brain.nociceptor.tick(
            brain.body,
            room_temp=brain.world.room_temperature(),
            strain=1.0,
            ordeal_active=False,
        )
        brain.hedonics.tick(brain)
        self._apply_lifecycle_plasticity(brain)

    def _apply_circadian_body_state(self, brain: InfantApeBrain, circ: dict) -> None:
        """Ritmo sueño/alerta: modula cuerpo y tronco, no choice_key."""
        sleep_drive = float(circ.get("sleep_drive", 0.0) or 0.0)
        alertness = float(circ.get("alertness", 0.5) or 0.5)
        cortisol_target = float(circ.get("cortisol_target", brain.hypothalamus.cortisol))
        # Homeostatic sleep pressure rises at night and relaxes under daytime alertness.
        brain.brainstem.sleep_pressure = float(
            np.clip(
                brain.brainstem.sleep_pressure
                + 0.012 * sleep_drive
                - 0.005 * alertness,
                0,
                1,
            )
        )
        brain.brainstem.arousal_bias = float(
            np.clip(0.28 + 0.42 * alertness - 0.16 * sleep_drive, 0.12, 0.75)
        )
        brain.hypothalamus.cortisol = float(
            np.clip(0.88 * brain.hypothalamus.cortisol + 0.12 * cortisol_target, 0, 1)
        )

    def _phase_cognize(
        self,
        brain: InfantApeBrain,
        *,
        vision: dict,
        drives: dict,
        ambient: dict,
        redeliberate: bool = False,
    ) -> dict:
        flags = get_flags(brain)
        if redeliberate and self.state.failed_choice_key:
            brain.deliberation.set_penalty(self.state.failed_choice_key, flags.rechoice_penalty)
        else:
            brain.deliberation.clear_penalties()
        cog = brain.cognition.run(brain, vision=vision, drives=drives, ambient=ambient)
        if flags.enable_goal_stack:
            delib = brain.deliberation.last
            self.goal_stack.push_from_deliberation(delib.choice_key, delib.choice, brain)
            self.goal_stack.sync_working_memory(brain)
        winner = (brain.consciousness.last or {}).get("winner") or {}
        brain.decompress_governor.set_priorities(
            conscious_salience=float(winner.get("salience") or 0),
            surprise=float(cog.get("prediction", {}).get("surprise", 0)),
        )
        region = brain.connectome.region_for_choice(brain.deliberation.last.choice_key)
        self.state.phase_trace.append(f"cognize:{region}")
        self._inject_scaffold_attention(brain)
        return cog

    def _phase_prefetch(self, brain: InfantApeBrain) -> dict:
        stats = brain.decompression_prefetch.run_tick(brain)
        brain.decompress_governor.finalize_tick()
        self.state.phase_trace.append(
            f"prefetch:{stats.get('total_warmed', 0)}"
        )
        return stats

    def _inject_scaffold_attention(self, brain: InfantApeBrain) -> None:
        flags = get_flags(brain)
        if not flags.enable_connectome_scaffold or brain.chunk_store is None:
            return
        choice = brain.deliberation.last.choice_key or "explore"
        region = brain.connectome.region_for_choice(choice)
        governor = brain.decompress_governor
        chunks = brain.chunk_store.load_for_focus(
            region=region,
            choice_key=choice,
            dim=brain.n_sensory,
            k=1,
            governor=governor,
        )
        bias = brain.chunk_store.materialize_bias(chunks, brain.n_sensory)
        sem = brain.typed_memory.semantic_context_bias(brain, brain.world.current_room())
        combined = bias * 0.45 + sem * 0.35
        if float(np.abs(combined).max()) > 1e-5:
            brain.cortex.prime_working_memory(
                np.clip(combined, -0.5, 0.5).astype(np.float32), gain=0.28
            )
        self.state.chunks_loaded_last_tick = max(self.state.chunks_loaded_last_tick, len(chunks))

    def _prefetch_scaffold(self, brain: InfantApeBrain, choice_key: str) -> np.ndarray | None:
        flags = get_flags(brain)
        if not flags.enable_connectome_scaffold or brain.chunk_store is None:
            return None
        region = brain.connectome.region_for_choice(choice_key)
        governor = brain.decompress_governor
        chunks = brain.chunk_store.load_for_focus(
            region=region,
            choice_key=choice_key,
            dim=brain.n_sensory,
            k=2,
            governor=governor,
        )
        self.state.chunks_loaded_last_tick = len(chunks)
        return brain.chunk_store.materialize_bias(chunks, brain.n_sensory)

    def _phase_commit(
        self,
        brain: InfantApeBrain,
        *,
        delib,
        ep_steps: int,
        olfactory: np.ndarray | None,
    ) -> dict:
        flags = get_flags(brain)
        sensory, _ = brain._world_sensory()
        scaffold = self._prefetch_scaffold(brain, delib.choice_key)
        sem_bias = brain.typed_memory.semantic_context_bias(brain, brain.world.current_room())
        if sem_bias is not None and sem_bias.size:
            sensory = sensory + sem_bias * 0.25
        if scaffold is not None:
            sensory = sensory + scaffold
            np.clip(sensory, -1.0, 1.0, out=sensory)
        label = format_episode_label(delib.choice, brain.world.current_room())
        tags = ["world", "explore", brain.world.current_room(), delib.choice_key]
        winner = (brain.consciousness.last or {}).get("winner") or {}
        if get_flags(brain).enable_consciousness and float(winner.get("salience") or 0) > 0.42:
            tags.append("conscious")
        last_ep = brain._run_episode(
            sensory,
            modality="world",
            label=label,
            repeats=1,
            steps_per_repeat=ep_steps,
            tags=tags,
            motor_bias=brain.deliberation.motor_bias_array(brain),
            bind_deliberation=flags.bind_deliberation,
            olfactory=olfactory,
        )
        self.state.phase_trace.append("commit")
        return last_ep

    def _phase_verify(self, brain: InfantApeBrain, last_ep: dict) -> None:
        flags = get_flags(brain)
        self.state.verified_this_tick = False
        if not flags.enable_verify:
            return
        tick_intention = last_ep.get("intention_circuit") or {}
        aligned = bool(tick_intention.get("spike_aligned", True))
        conflict = float(brain.deliberation.last.conflict)
        if not aligned and conflict >= flags.verify_conflict_threshold:
            self.state.pending_rechoice = True
            self.state.failed_choice_key = brain.deliberation.last.choice_key
            self.state.redeliberations += 1
            brain._log_autonomy(
                f"repensó — spike no alineó con «{brain.deliberation.last.choice}»"
            )
        else:
            self.state.pending_rechoice = False
            self.state.failed_choice_key = ""
        self.state.verified_this_tick = True
        self.state.phase_trace.append("verify")

    def _affordance_goal_xy(
        self, brain: InfantApeBrain, *, candidate_key: str
    ) -> tuple[float, float] | None:
        """
        Prior de navegación desde affordances.

        Discriminación: si el object_id exitoso sigue en el mundo, va ahí
        (no al más cercano del tipo — podría ser la fuente seca).
        Transferencia: si el object_id ya no existe, nearest del mismo kind.
        No escribe choice_key.
        """
        if not get_flags(brain).enable_affordance_learning:
            return None
        if not hasattr(brain, "affordance_map"):
            return None
        best_present: tuple[float, tuple[float, float]] | None = None
        best_transfer_type = ""
        best_transfer_score = 0.12
        for record in brain.affordance_map.records.values():
            if record.candidate_key != candidate_key:
                continue
            if record.confidence < 0.12:
                continue
            if record.mean_homeostasis_gain < 0.01:
                continue
            # Ranking entre instancias presentes: confianza × ganancia.
            score = float(record.confidence) * float(
                max(0.01, record.mean_homeostasis_gain)
            )
            fu = brain.world.furniture_by_id(record.object_id)
            if fu is not None:
                center = (fu.x + fu.w / 2, fu.y + fu.h / 2)
                if best_present is None or score > best_present[0]:
                    best_present = (score, center)
            elif float(record.confidence) > best_transfer_score:
                # Transferencia por tipo cuando el object_id ya no existe.
                best_transfer_score = float(record.confidence)
                best_transfer_type = record.object_type
        if best_present is not None:
            return best_present[1]
        if best_transfer_type:
            return brain.world.nearest_furniture_center(best_transfer_type)
        return None

    def _affordance_water_goal(self, brain: InfantApeBrain) -> tuple[float, float] | None:
        return self._affordance_goal_xy(brain, candidate_key="drink")

    def _affordance_food_goal(self, brain: InfantApeBrain) -> tuple[float, float] | None:
        return self._affordance_goal_xy(brain, candidate_key="eat")

    def _affordance_hygiene_goal(self, brain: InfantApeBrain) -> tuple[float, float] | None:
        return self._affordance_goal_xy(brain, candidate_key="hygiene")

    def _apply_motor_events(
        self,
        brain: InfantApeBrain,
        *,
        motor_result: dict,
        drives: dict,
        delib,
        last_ep: dict | None,
        collect: list[dict] | None = None,
        log_bumps: bool = False,
    ) -> dict | None:
        """Aplica consecuencias reales de interacción (también en headless)."""
        updated = last_ep
        for ev in motor_result.get("events", []):
            if ev.get("type") == "bump":
                region = ev.get("region", "limbs")
                pain_amt = float(ev.get("pain", 0.03))
                brain.nociceptor.apply_collision(
                    region, pain_amt, label=str(ev.get("target", ""))
                )
                brain.nociceptor._project_to_body(brain.body)
                if log_bumps and ev.get("target"):
                    brain._log_autonomy(f"golpeó {ev.get('target')} — dolor {region}")
                    brain.cognition.stm.push(
                        f"golpe en {ev.get('target')}",
                        kind="pain",
                        salience=0.7,
                        tags=["nociception", region],
                    )
                continue
            if ev.get("type") == "move":
                continue
            if ev.get("type") == "interact" and get_flags(brain).enable_goal_stack:
                meta = ev.get("meta") or {}
                kind = meta.get("kind") or ev.get("target", "")
                if kind and self.goal_stack.on_interact_complete(str(kind)):
                    self.goal_stack.sync_working_memory(brain)
            if ev.get("type") == "drink" and get_flags(brain).enable_goal_stack:
                kind = str(ev.get("object_type") or "fountain")
                if self.goal_stack.on_interact_complete(kind) or self.goal_stack.on_interact_complete(
                    "fridge"
                ):
                    self.goal_stack.sync_working_memory(brain)
            updated = self._handle_world_event_with_affordance(
                brain,
                event=ev,
                last_ep=updated,
                drives=drives,
                decision_key=str(getattr(delib, "choice_key", "") or ""),
            )
            if collect is not None:
                collect.append({**ev, "remembered": (updated or {}).get("remembered")})
        return updated

    def _phase_act(
        self,
        brain: InfantApeBrain,
        *,
        last_ep: dict,
        delib,
        focused_drives: dict,
        ambient: dict,
    ) -> dict:
        flags = get_flags(brain)
        walk_goal = resolve_walk_goal(
            brain.world,
            focused_drives,
            companion_xy=(brain.companion.x, brain.companion.y),
            ambient=ambient,
            goal_stack=self.goal_stack if flags.enable_goal_stack else None,
            affordance_water_xy=self._affordance_water_goal(brain),
            affordance_food_xy=self._affordance_food_goal(brain),
            affordance_hygiene_xy=self._affordance_hygiene_goal(brain),
        )
        if walk_goal:
            brain.world.set_walk_goal(walk_goal[0], walk_goal[1])
        else:
            brain.world.clear_walk_goal()
        raw_motor = augment_motor(
            brain.world,
            last_ep["motor"],
            focused_drives,
            companion_xy=(brain.companion.x, brain.companion.y),
            ambient=ambient,
        )
        if not raw_motor and delib.choice_key:
            affinity = MOTOR_AFFINITY.get(delib.choice_key, [])
            if hasattr(brain, "schema_learner") and str(delib.choice_key).startswith("learned_"):
                affinity = brain.schema_learner.motor_affinity_for(delib.choice_key)
            for m in reversed(affinity):
                if m not in raw_motor:
                    raw_motor.insert(0, m)

        # Política continua: prior de heading; schemas no monopolizan
        if get_flags(brain).enable_continuous_motor and hasattr(brain, "motor_policy"):
            from .learned_schemas import all_action_schemas

            target = ""
            for s in all_action_schemas(brain):
                if s["key"] == delib.choice_key:
                    target = s.get("target", "")
                    break
            cmd = brain.motor_policy.decode(
                brain,
                list(raw_motor or []),
                choice_key=str(delib.choice_key or ""),
                choice_target=target,
                confidence=float(delib.confidence),
            )
            cont = brain.motor_policy.apply_to_world(brain, cmd)
            # Mezcla: continuo primero, spikes como refuerzo (no reemplaza PFC)
            raw_motor = list(dict.fromkeys(cont + list(raw_motor or [])))[:8]

        motor = decode_cortex_motor(raw_motor)
        result = brain.world.apply_motor(motor, drives=focused_drives, biomech=brain.biomech)
        if get_flags(brain).enable_learned_schemas and hasattr(brain, "schema_learner"):
            learned = brain.schema_learner.note_success(
                choice_key=str(delib.choice_key or ""),
                room=brain.world.current_room(),
                motor=list(raw_motor or []),
                dopamine=float(brain.modulators.dopamine),
                confidence=float(delib.confidence),
            )
            if learned:
                brain._log_autonomy(f"schema consolidado → {learned.label}")
        if get_flags(brain).enable_continuous_motor and hasattr(brain, "motor_policy"):
            # Recompensa inmediata suave para heading (no choice_key)
            r = float(brain.body.pleasure) - 0.3 * float(brain.body.total_pain())
            brain.motor_policy.learn(reward=r, dopamine=float(brain.modulators.dopamine))
        self.state.phase_trace.append("act")
        return result

    def _handle_world_event_with_affordance(
        self,
        brain: InfantApeBrain,
        *,
        event: dict,
        last_ep: dict | None,
        drives: dict,
        decision_key: str,
    ) -> dict:
        """Aplica primero el efecto real y luego aprende la transición observada."""
        flags = get_flags(brain)
        before = None
        if flags.enable_affordance_learning and hasattr(brain, "affordance_map"):
            from .affordance_map import body_snapshot

            before = body_snapshot(brain.body)
        updated_ep = brain._handle_world_event(event, last_ep)
        if before is not None:
            from .affordance_map import SUCCESS_GAIN_THRESHOLD, body_snapshot

            dominant_drive = (
                max(drives.items(), key=lambda item: item[1])[0] if drives else ""
            )
            after = body_snapshot(brain.body)
            record = brain.affordance_map.observe(
                event=event,
                before=before,
                after=after,
                dominant_drive=dominant_drive,
                room=brain.world.current_room(),
                decision_key=decision_key,
            )
            # Schemas desde éxito causal (no desde choice_key forzado).
            if (
                record is not None
                and flags.enable_learned_schemas
                and hasattr(brain, "schema_learner")
            ):
                gain = float((brain.affordance_map.last_observation or {}).get("homeostasis_gain", 0))
                if gain >= SUCCESS_GAIN_THRESHOLD:
                    learned = brain.schema_learner.note_affordance_success(
                        candidate_key=record.candidate_key,
                        object_type=record.object_type,
                        dominant_drive=record.dominant_drive,
                        room=brain.world.current_room(),
                        homeostasis_gain=gain,
                    )
                    if learned:
                        brain._log_autonomy(f"schema causal → {learned.label}")
        return updated_ep

    def _apply_lifecycle_plasticity(self, brain: InfantApeBrain) -> None:
        """Ajusta plasticidad/poda por etapa. No elige acciones."""
        if not get_flags(brain).enable_lifecycle_plasticity:
            return
        neuro = brain.lifecycle.neuro_modulation()
        brain.cortex.plasticity_mult = float(
            brain.profile.plasticity_mult * neuro.get("plasticity_scale", 1.0)
        )
        prune = float(neuro.get("prune_rate", 0.0))
        if prune > 0 and brain.lifecycle.age_ticks % 40 == 0:
            cx = brain.cortex
            for syn in (cx.s_to_l, cx.l_to_a, cx.a_to_a, cx.a_to_m):
                syn.soft_prune_weak(rate=prune)

    def _td_learn_after_act(
        self,
        brain: InfantApeBrain,
        *,
        last_ep: dict | None,
        focused_drives: dict,
        ambient: dict | None,
    ) -> None:
        """Actualiza V(s,a) tras el acto. No selecciona la siguiente acción."""
        flags = get_flags(brain)
        if not flags.enable_td_reward or not hasattr(brain, "td_reward"):
            return
        delib_now = brain.deliberation.last
        action = str(delib_now.choice_key or "")
        drives = focused_drives or {}
        top_drive = max(drives.items(), key=lambda x: x[1])[0] if drives else ""
        env = ambient or {}
        prev_room = str(env.get("room") or brain.world.current_room())
        hour = int(env.get("hour", 12))
        comfort0 = float(getattr(brain, "_td_comfort_prev", brain.body.comfort))
        comfort_delta = float(brain.body.comfort - comfort0)
        brain._td_comfort_prev = float(brain.body.comfort)
        surprise = 0.0
        if brain.cognition.last_summary:
            surprise = float(
                (brain.cognition.last_summary.get("prediction") or {}).get("surprise", 0)
            )
        r = brain.td_reward.instantaneous_reward(
            valence=float((last_ep or {}).get("valence", 0)),
            comfort_delta=comfort_delta,
            pleasure=float(brain.body.pleasure),
            pain=float(brain.body.total_pain()),
            hunger=float(brain.body.hunger),
            surprise=surprise,
        )
        next_drives = brain._merged_drives()
        next_top = max(next_drives.items(), key=lambda x: x[1])[0] if next_drives else top_drive
        brain.td_reward.observe(
            prev_room=prev_room,
            prev_drive=top_drive,
            action=action,
            reward=r,
            next_room=brain.world.current_room(),
            next_drive=next_top,
            hour=hour,
        )

    def _run_headless(self, brain: InfantApeBrain, *, steps: int) -> dict:
        dead = self._alive_guard(brain)
        if dead:
            return dead

        steps = max(1, min(steps, 4))
        last_ep: dict | None = None
        tick_intention: dict | None = None
        be = get_backend()
        ep_steps = 48 if be.gpu_available else 8

        for _ in range(steps):
            brain.decompress_governor.reset_tick()
            self.state.chunks_loaded_last_tick = 0
            env = brain.world.ambient()
            self._phase_interocept_headless(brain, env)
            vision = brain._scan_vision()
            drives = brain._merged_drives()
            hour = int(env.get("hour", 12))
            self._apply_sleep_drive(drives, hour)

            redelib = self.state.pending_rechoice
            self._phase_cognize(
                brain, vision=vision, drives=drives, ambient=env, redeliberate=redelib
            )
            if redelib:
                self.state.pending_rechoice = False

            delib = brain.deliberation.last
            _, olfactory = brain._world_sensory()
            last_ep = self._phase_commit(
                brain, delib=delib, ep_steps=ep_steps, olfactory=olfactory
            )
            tick_intention = last_ep.get("intention_circuit")
            self._phase_verify(brain, last_ep)

            focused_drives = brain.deliberation.focused_drives(drives)
            motor_result = self._phase_act(
                brain,
                last_ep=last_ep,
                delib=delib,
                focused_drives=focused_drives,
                ambient=env,
            )
            last_ep = self._apply_motor_events(
                brain,
                motor_result=motor_result,
                drives=drives,
                delib=delib,
                last_ep=last_ep,
            )
            self._td_learn_after_act(
                brain, last_ep=last_ep, focused_drives=focused_drives, ambient=env
            )
            if get_flags(brain).enable_grounding:
                from .grounding import tick_grounding

                tick_grounding(getattr(brain, "grounding", None))
            if get_flags(brain).enable_neural_telemetry and hasattr(brain, "neural_telemetry"):
                brain.neural_telemetry.record_from_tick(
                    {
                        "deliberation": delib.to_dict(),
                        "drives": drives,
                        "world": {"room": brain.world.current_room()},
                        "affordance_map": brain.affordance_map.to_dict(),
                        "events": list(motor_result.get("events") or []),
                    },
                    tick=int(brain.lifecycle.age_ticks),
                )
            self._phase_prefetch(brain)

        if last_ep is None:
            last_ep = {
                "hypothalamus": {"mood": brain.persona.mood, "energy": brain.hypothalamus.energy},
                "valence": 0.0,
                "arousal": 0.3,
                "remembered": False,
                "motor": [],
                "label": "pausa",
                "memory": {"key": "", "count": 0},
            }

        character = brain.persona.to_dict()
        character["message"] = ""
        out = brain._pack_result(last_ep, character, last_ep["label"].encode("utf-8"))
        out["world"] = brain.world.to_dict()
        out["drives"] = brain._merged_drives()
        out["deliberation"] = brain.deliberation.last.to_dict()
        out["cognition"] = brain.cognition.to_dict()
        out["consciousness"] = brain.consciousness.to_dict()
        out["environment"] = brain._last_env or brain.world.ambient()
        out["agent_loop"] = self.state.to_dict()
        out["goal_stack"] = self.goal_stack.to_dict()
        out["connectome"] = brain.connectome.to_dict()
        from .causal_hud import build_causal_hud

        out["causal_hud"] = build_causal_hud(brain)
        out["affordance_map"] = brain.affordance_map.to_dict()
        if tick_intention:
            out["intention_circuit"] = tick_intention
        return out

    def _run_full(self, brain: InfantApeBrain, *, steps: int) -> dict:
        brain._spawn_offspring_if_needed()
        dead = self._alive_guard(brain)
        if dead:
            return dead

        steps = max(1, min(steps, 4))
        all_events: list[dict] = []
        last_ep: dict | None = None
        tick_intention: dict | None = None
        brain._verbal_dialogue_turn = None
        strain = brain.journey.body_drain_multiplier()
        activity, phys_strain = brain.biomech.activity_strain()

        for step_i in range(steps):
            brain.decompress_governor.reset_tick()
            self.state.chunks_loaded_last_tick = 0
            echo_ev = brain._integrate_echo()
            if echo_ev:
                all_events.append(echo_ev)

            brain.world.advance_clock(1)
            env = brain.world.ambient()
            temporal = brain.temporal.observe(env, ticks=1)
            env["temporal"] = temporal
            circ = circadian_profile(env) if get_flags(brain).enable_circadian else None
            if circ is not None:
                env["circadian"] = circ
                self._apply_circadian_body_state(brain, circ)
            brain._last_env = env
            brain.chemistry.decay()
            brain.affect.tick_decay()
            brain.body.tick(
                room_temp=brain.world.room_temperature(),
                activity=activity,
                sleep_pressure=brain.brainstem.sleep_pressure,
                watching_tv=bool(brain.world.tv_state.get("active")),
                strain=strain * phys_strain,
                ordeal_active=brain.journey.in_ordeal(),
                circadian=circ,
            )
            brain.nociceptor.tick(
                brain.body,
                room_temp=brain.world.room_temperature(),
                strain=strain * phys_strain,
                ordeal_active=brain.journey.in_ordeal(),
            )
            brain.hedonics.tick(brain)
            brain.biomech.sync_pose(brain.world.agent_x, brain.world.agent_y)
            if brain.body.total_pain() > 0.25:
                brain.hypothalamus.cortisol = float(
                    np.clip(brain.hypothalamus.cortisol + 0.02, 0, 1)
                )
            vision = brain._scan_vision()
            lc_events = brain.lifecycle.tick(
                body=brain.body,
                companion_bond=brain.companion.bond_with_nexo,
                attachment=brain.persona.attachment,
                oxytocin=brain.hypothalamus.oxytocin,
                comfort=brain.body.comfort,
            )
            all_events.extend(lc_events)
            self._apply_lifecycle_plasticity(brain)

            journey_ev = brain.journey.tick(
                tick_n=brain.lifecycle.age_ticks,
                room=brain.world.current_room(),
                comfort=brain.body.comfort,
                bond=brain.companion.bond_with_nexo,
                alive=brain.lifecycle.alive,
                hero_zone=brain.world.hero_zone_key(),
                is_night=env.get("phase") == "night",
                light_level=float(env.get("light_level", 1.0)),
            )
            if journey_ev:
                all_events.append(journey_ev)
                if journey_ev.get("type") == "journey_reward":
                    brain.modulators.dopamine = min(1.0, brain.modulators.dopamine + 0.08)
                if journey_ev.get("type") in (
                    "journey_ordeal_start",
                    "journey_reward",
                    "journey_cycle_complete",
                    "journey_ordeal",
                ):
                    last_ep = brain._handle_world_event(journey_ev, last_ep)

            drives = brain._merged_drives()
            for dk, mult in brain.journey.drive_multipliers().items():
                drives[dk] = float(min(1.0, drives.get(dk, 0) * mult))
            if env.get("phase") == "night" and brain.world.current_room() == "jardín":
                drives["seek_warmth"] = float(min(1.0, drives.get("seek_warmth", 0) + 0.28))
                drives["seek_rest"] = float(min(1.0, drives.get("seek_rest", 0) + 0.15))
            hour = int(env.get("hour", 12))
            self._apply_sleep_drive(drives, hour)
            curiosity = drives.get("seek_curiosity", 0)
            if (
                step_i == 0
                and curiosity < 0.38
                and brain.world.tarot_stats().get("uninternalized", 0) > 0
                and brain.lifecycle.age_ticks % 45 == 0
            ):
                brain._log_autonomy("ignoró el tarot — poca curiosidad")
            if step_i == 0 and (hour >= 22 or hour < 6) and drives.get("sleep_need", 0) > 0.5:
                brain._log_autonomy(f"hora {env.get('clock', '?')} — busca descanso")
            if step_i == 0 and 7 <= hour < 10 and drives.get("seek_food", 0) > 0.35:
                brain._log_autonomy("mañana — hambre matutina")

            redelib = self.state.pending_rechoice
            cog = self._phase_cognize(
                brain, vision=vision, drives=drives, ambient=env, redeliberate=redelib
            )
            if redelib:
                self.state.pending_rechoice = False

            surprise = float(cog.get("prediction", {}).get("surprise", 0))
            brain.brain_facts.tick_focus()
            brain.anatomy.tick_focus()
            brain.circuit_hub.tick(brain, vision=vision, ambient=env, surprise=surprise)
            reflex = brain.reflexes.step(brain, surprise=surprise, vision=vision)
            if step_i == 0 and reflex.get("events"):
                for ev in reflex["events"][:2]:
                    brain._log_autonomy(ev)
            focused_drives = brain.deliberation.focused_drives(drives)
            delib = brain.deliberation.last
            if step_i == 0 and delib.inhibited:
                brain._log_autonomy(
                    f"libre albedrío — PFC elige {delib.choice} (impulso: {delib.limbic_winner})"
                )
            elif step_i == 0 and delib.agency > 0.45:
                brain._log_autonomy(f"libre albedrío → {delib.choice} ({delib.agency:.0%})")

            _, olfactory = brain._world_sensory()
            be = get_backend()
            mult = max(1.0, brain.learning_multiplier())
            ep_steps = 48 if be.gpu_available else 8
            if not brain.headless and be.gpu_available:
                ep_steps = int(min(48, max(32, round(12 + 4 * mult))))
            elif not brain.headless:
                ep_steps = int(min(18, round(6 + 2 * mult)))
            last_ep = self._phase_commit(
                brain, delib=delib, ep_steps=ep_steps, olfactory=olfactory
            )
            tick_intention = last_ep.get("intention_circuit")
            self._phase_verify(brain, last_ep)

            surprise = float(cog.get("prediction", {}).get("surprise", 0))
            dr = brain.daytime_replay.maybe_replay(
                brain, surprise=surprise, trigger_label=last_ep.get("label", "")
            )
            if dr:
                all_events.append({"type": "daytime_replay", **dr})
                if step_i == 0:
                    brain._log_autonomy(
                        f"replay diurno tras sorpresa ({dr.get('label', '?')[:32]})"
                    )

            motor_result = self._phase_act(
                brain,
                last_ep=last_ep,
                delib=delib,
                focused_drives=focused_drives,
                ambient=env,
            )
            all_events.extend(motor_result.get("events", []))

            contact = apply_somatic_contact(
                brain.world, brain.body, nociceptor=brain.nociceptor
            )
            if contact and step_i == 0:
                all_events.append({"type": "somatic_contact", **contact})
                comfort_delta = float((contact.get("effects") or {}).get("comfort", 0))
                if comfort_delta > 0:
                    brain.hedonics.reward(
                        "comfort",
                        min(0.35, comfort_delta * 9.0),
                        label=contact.get("label", ""),
                        affect=brain.affect,
                    )

            brain.biomech.apply_to_interoception(brain.body, brain.nociceptor)

            self._td_learn_after_act(
                brain,
                last_ep=last_ep,
                focused_drives=focused_drives,
                ambient=env,
            )

            if get_flags(brain).enable_grounding:
                from .grounding import tick_grounding

                tick_grounding(getattr(brain, "grounding", None))

            last_ep = self._apply_motor_events(
                brain,
                motor_result=motor_result,
                drives=drives,
                delib=delib,
                last_ep=last_ep,
                collect=all_events,
                log_bumps=True,
            ) or last_ep

            if get_flags(brain).enable_neural_telemetry and hasattr(brain, "neural_telemetry"):
                brain.neural_telemetry.record_from_tick(
                    {
                        "deliberation": delib.to_dict(),
                        "drives": drives,
                        "world": {"room": brain.world.current_room()},
                        "affordance_map": brain.affordance_map.to_dict(),
                        "events": list(motor_result.get("events") or []),
                        "agency_guard": {
                            "affordances_select_actions": False,
                            "deliberation_selects_actions": True,
                        },
                    },
                    tick=int(brain.lifecycle.age_ticks),
                )

            for lev in lc_events:
                if lev.get("type") == "lifecycle_death":
                    last_ep = brain._handle_world_event(lev, last_ep)

            comp_events = brain.companion.tick(
                brain.world,
                room_temp=brain.world.room_temperature(),
                sleep_pressure=brain.brainstem.sleep_pressure,
                nexo_x=brain.world.agent_x,
                nexo_y=brain.world.agent_y,
                chemistry=brain.chemistry,
            )
            for cev in comp_events:
                all_events.append(cev)
                if cev.get("type") == "companion_social" and not brain._caregiver_listening:
                    result = run_social_exchange(brain, trigger="proximity")
                    if result.get("event"):
                        all_events.append(result["event"])
                    nexo_ep = brain._nexo_episode_from_learn(result.get("learning", {}))
                    if nexo_ep:
                        last_ep = nexo_ep

            self._phase_prefetch(brain)

        thought = brain.think(vision=brain._last_vision)
        imagination = brain.imagination.advance_stream(
            brain, thought=thought, vision=brain._last_vision
        )
        if imagination and imagination.get("active"):
            last_ep = brain._last_ep or last_ep

        if last_ep is None:
            last_ep = {
                "hypothalamus": {"mood": brain.persona.mood, "energy": brain.hypothalamus.energy},
                "valence": 0.0,
                "arousal": 0.3,
                "remembered": False,
                "motor": [],
                "label": "pausa",
            }

        draft = brain._state_draft(
            last_ep,
            thought=thought.get("text"),
            event=all_events[-1] if all_events else None,
        )
        lctx = brain._language_context(
            ep=last_ep,
            draft=draft,
            mode="world",
            last_thought=thought.get("text"),
        )
        feel_text, feel_src = brain.language.describe_feelings(lctx)
        spoken, lang_src = brain._articulate(lctx)
        from .caregiver_dialogue import is_fragmentary_speech

        if brain._verbal_dialogue_turn:
            nx = brain._verbal_dialogue_turn.get("nexo", "")
            if nx and not is_fragmentary_speech(nx):
                spoken = nx
                lang_src = brain._verbal_dialogue_turn.get("sources", {}).get("nexo", lang_src)
        elif is_fragmentary_speech(spoken) and feel_text:
            spoken = feel_text
            lang_src = feel_src or lang_src
        character = brain.persona.react(
            hypothalamus=last_ep["hypothalamus"],
            valence=last_ep["valence"],
            arousal=last_ep["arousal"],
            modality="world",
            label=last_ep["label"],
            remembered=last_ep["remembered"],
            motor=last_ep["motor"],
            memory_hit=last_ep["memory"] if last_ep["remembered"] else None,
            reply=spoken,
        )

        out = brain._pack_result(last_ep, character, last_ep["label"].encode("utf-8"))
        out["world"] = brain._world_dict()
        out["body"] = brain._body_snapshot()
        out["companion"] = brain.companion.to_dict()
        out["feelings_text"] = feel_text
        out["world_events"] = all_events
        out["thought"] = thought
        out["thought_flow"] = thought.get("flow", brain.thoughts.stream_snapshot(12))
        out["vision"] = brain._last_vision
        out["language"] = {"source": lang_src, "feelings_source": feel_src, **brain.language.status()}
        out["lifecycle"] = brain.lifecycle.to_dict()
        out["journey"] = brain.journey.to_dict()
        out["environment"] = brain._last_env or brain.world.ambient()
        out["temporal"] = brain.temporal.to_dict()
        out["drives"] = brain._merged_drives()
        out["autonomy_log"] = brain._last_autonomy_log[-8:]
        out["tarot"] = brain.world.tarot_stats()
        out["cognition"] = brain.cognition.to_dict()
        out["deliberation"] = brain.deliberation.last.to_dict()
        out["agent_loop"] = self.state.to_dict()
        out["goal_stack"] = self.goal_stack.to_dict()
        out["connectome"] = brain.connectome.to_dict()
        from .causal_hud import build_causal_hud

        out["causal_hud"] = build_causal_hud(brain)
        out["affordance_map"] = brain.affordance_map.to_dict()
        out["counterfactual"] = brain.counterfactual.to_dict()
        if brain.chunk_store:
            out["connectome"]["chunks"] = brain.chunk_store.stats()
        if tick_intention:
            out["intention_circuit"] = tick_intention
            out["cognition"] = {**out["cognition"], "intention_circuit": tick_intention}
        out["lobes"] = brain.lobes.to_dict()
        out["lobe_cortex"] = brain.lobe_cortex.to_dict()
        out["daytime_replay"] = brain.daytime_replay.to_dict()
        out["reflexes"] = brain.reflexes.to_dict()
        out["learning_log"] = brain._learning_log[-8:]
        out["learning"] = brain.learning_hub.snapshot()
        out["dialogue"] = brain._dialogue_log[:6]
        if brain._dialogue_log:
            out["social_dialogue"] = brain._dialogue_log[0]
        out["affect"] = brain.affect.to_dict()
        out["hedonics"] = brain.hedonics.to_dict()
        out["consciousness"] = brain.consciousness.to_dict()
        if imagination:
            out["imagination"] = imagination
        surprise = 0.0
        if brain.cognition.last_summary:
            surprise = float(brain.cognition.last_summary.get("prediction", {}).get("surprise", 0))
        out["neuroanatomy"] = brain.atlas.update(brain, surprise=surprise)
        out["curriculum"] = brain.curriculum.to_dict()
        out["brain_facts"] = brain.brain_facts.to_dict()
        out["anatomy_book"] = brain.anatomy.to_dict()
        out["nociception"] = brain.nociceptor.to_dict()
        out["biomechanics"] = brain.biomech.to_dict()
        out["circuits"] = brain.circuit_hub.to_dict()
        out["typed_memory"] = brain.typed_memory.to_dict()
        out["sleep_architecture"] = brain.sleep_arch.to_dict()
        return out
