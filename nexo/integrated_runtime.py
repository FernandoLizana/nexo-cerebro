"""Runtime cognitivo integrado v1 — scheduler + conectoma + cuerpo."""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

from nexo.body.body_state import VirtualBody
from nexo.body.metabolism import MetabolismEngine
from nexo.core.clock import SimulationClock
from nexo.core.process import (
    AttentionProcess,
    BasalGangliaSelectorProcess,
    LegacyBrainAdapterProcess,
    MotorExecutionProcess,
    SensoryRelayProcess,
    WorkingMemoryProcess,
)
from nexo.core.process_body import (
    AllostasisProcess,
    BodyInteroceptionProcess,
    MetabolismProcess,
)
from nexo.core.process_perception import (
    PredictiveAttentionProcess,
    PredictiveHierarchyProcess,
    RawSensoryCaptureProcess,
    ThalamicRelayProcess,
)
from nexo.core.process_memory import (
    EnhancedWorkingMemoryProcess,
    HippocampalEncoderProcess,
    HippocampalRetrievalProcess,
)
from nexo.core.process_executive import (
    CerebellarCorrectionProcess,
    EnhancedBasalGangliaProcess,
    GoalStackProcess,
    PrefrontalDeliberationProcess,
)
from nexo.core.process_learning import (
    ConnectomePlasticityProcess,
    NeuromodulatorUpdateProcess,
    TDBiasProcess,
    TDLearningProcess,
)
from nexo.core.process_consciousness import (
    GlobalWorkspaceProcess,
    MetacognitionProcess,
)
from nexo.core.process_social import (
    LanguageProductionProcess,
    SocialExchangeProcess,
    SocialModelProcess,
    TheoryOfMindProcess,
)
from nexo.core.process_sleep import (
    ConsolidationProcess,
    DevelopmentProcess,
    MemoryReplayProcess,
    SleepArchitectureProcess,
)
from nexo.core.process_evaluation import BehavioralSnapshotProcess
from nexo.core.process_intervention import ConnectomeLesionAuditProcess
from nexo.core.process_connectome import ConnectomeDeliveryProcess
from nexo.core.process_analysis import BehavioralFingerprintProcess
from nexo.core.process_routing import ConnectomeRoutingAuditProcess
from nexo.core.process_telemetry import IntegratedTraceProcess
from nexo.memory.hippocampus.store import HippocampalStore
from nexo.working_memory.buffer import WorkingMemoryBuffer
from nexo.basal_ganglia.gate import ActionGate
from nexo.cerebellum.coordinator import CerebellarCoordinator
from nexo.planning.goal_stack import GoalStack
from nexo.prefrontal.deliberation import PrefrontalDeliberator
from nexo.neuromodulation.state import NeuromodulatorState
from nexo.reinforcement.td_learning import TDRewardSystem
from nexo.workspace.global_workspace import GlobalWorkspace
from nexo.metacognition.monitor import MetacognitiveMonitor
from nexo.social.agent_model import CaregiverModel
from nexo.social.theory_of_mind import TheoryOfMindEngine
from nexo.language.composer import UtteranceComposer
from nexo.sleep.architecture import SleepArchitecture
from nexo.development.tracker import DevelopmentTracker
from nexo.memory.consolidation import MemoryConsolidator
from nexo.core.scheduler import CognitiveScheduler
from nexo.core.state_store import StateStore
from nexo.connectome.graph import ConnectomeGraph
from nexo.connectome.routing import ConnectomeRouter
from nexo.demo.room_scenario import RoomWorld
from nexo.homeostasis.controller import HomeostaticController
from nexo.random_streams import RandomStreams
from nexo.interventions.profiles import LESION_NONE, apply_lesion_profile
from nexo.telemetry.recorder import TelemetryLevel, TelemetryRecorder
from nexo.telemetry.integrated_trace import IntegratedTraceCollector
from nexo.thalamus.reticular import ReticularNucleus


def _repo_root() -> Path:
    return Path(__file__).resolve().parent.parent


@dataclass
class IntegratedRuntimeConfig:
    seed: int = 42
    ticks: int = 80
    connectome_path: Path = field(default_factory=lambda: _repo_root() / "configs/connectome/connectome_v1.yaml")
    telemetry_level: TelemetryLevel = TelemetryLevel.SUMMARY
    use_legacy_adapter: bool = False
    disable_processes: tuple[str, ...] = ()
    profile: str = "integrated_v1"
    body_enabled: bool = True
    perception_mode: str = "legacy"  # legacy | predictive
    memory_mode: str = "legacy"  # legacy | integrated
    executive_mode: str = "legacy"  # legacy | integrated
    learning_mode: str = "legacy"  # legacy | integrated
    consciousness_mode: str = "legacy"  # legacy | integrated
    social_mode: str = "legacy"  # legacy | integrated
    sleep_mode: str = "legacy"  # legacy | integrated
    evaluation_mode: str = "legacy"  # legacy | integrated
    intervention_mode: str = "legacy"  # legacy | integrated
    lesion_profile: str = "lesion_none"
    latency_mode: str = "legacy"  # legacy | integrated
    analysis_mode: str = "legacy"  # legacy | integrated
    routing_mode: str = "legacy"  # legacy | integrated
    statistics_mode: str = "legacy"  # legacy | integrated (metadata para batería)
    tracing_mode: str = "legacy"  # legacy | integrated
    replication_mode: str = "legacy"  # legacy | integrated
    permutation_mode: str = "legacy"  # legacy | integrated (estadística batería)
    correction_mode: str = "legacy"  # legacy | integrated (FDR sobre p-values)
    eventlog_mode: str = "legacy"  # legacy | integrated
    meta_analysis_mode: str = "legacy"  # legacy | integrated (agrega réplicas)
    replication_batch_mode: str = "legacy"  # legacy | integrated (multi-seed)
    cross_battery_mode: str = "legacy"  # legacy | integrated (compara baterías)
    phenomenology_mode: str = "legacy"  # legacy | integrated (timeline event_log)
    legacy_bridge_mode: str = "legacy"  # legacy | integrated (compara con InfantApeBrain)
    world_mode: str = "room"  # room | extended
    inference_mode: str = "legacy"  # legacy | integrated (CI bootstrap en efectos)
    orchestration_mode: str = "legacy"  # legacy | integrated (pipeline batería+meta)
    legacy_adapter_mode: str = "legacy"  # legacy | integrated (InfantApeBrain en scheduler)
    scale_mode: str = "legacy"  # legacy | integrated (perfil escala computacional)
    hierarchical_inference_mode: str = "legacy"  # legacy | integrated (efectos por capa)
    deliberation_bridge_mode: str = "legacy"  # legacy | integrated (auditoría PFC vs legacy)
    deliberation_fusion_mode: str = "legacy"  # legacy | integrated (fusión advisory)
    deliberation_unified_mode: str = "legacy"  # legacy | integrated (motor unificado)
    world2d_legacy_actions_mode: str = "legacy"  # legacy | integrated (mapeo choice_key)
    world2d_full_actions_mode: str = "legacy"  # legacy | integrated (catálogo completo)
    world2d_legacy_env_mode: str = "legacy"  # legacy | integrated (entorno hogar enriquecido)
    lif_scale_mode: str = "legacy"  # legacy | integrated (sonda bench LIF/GPU)
    gpu_bench_mode: str = "legacy"  # legacy | integrated (bench CI-safe)
    publication_mode: str = "legacy"  # legacy | integrated (bundle publicación)
    paper_pack_mode: str = "legacy"  # legacy | integrated (CSV + LaTeX paper)
    battery_paper_mode: str = "legacy"  # legacy | integrated (tablas desde batería)
    full_publication_mode: str = "legacy"  # legacy | integrated (bundle paper completo)
    deliberation_weight_mode: str = "legacy"  # legacy | integrated (peso legacy configurable)
    legacy_advisory_weight: float = 0.0  # 0=integrado, 1=legacy, 0.5=empate→integrado
    paper_figures_mode: str = "legacy"  # legacy | integrated (SVG desde batería)
    pipeline_paper_mode: str = "legacy"  # legacy | integrated (pipeline E2E paper)
    latex_master_mode: str = "legacy"  # legacy | integrated (LaTeX maestro)
    battery_full_mode: str = "legacy"  # legacy | integrated (batería + FDR export)
    release_bundle_mode: str = "legacy"  # legacy | integrated (checksums release)
    legacy_adapter_early_mode: str = "legacy"  # legacy | integrated (adapter priority 61)
    world2d_headless_mode: str = "legacy"  # legacy | integrated (step_toward headless)
    roadmap100_bridge_mode: str = "legacy"  # legacy | integrated (flags roadmap100 legacy)
    flask_demo_bridge_mode: str = "legacy"  # legacy | integrated (puente Flask demo)
    world3d_sync_mode: str = "legacy"  # legacy | integrated (estado game3d.js)
    autonomy_guard_mode: str = "legacy"  # legacy | integrated (contrato autonomía)
    hypothalamus_multimodal_mode: str = "legacy"  # legacy | integrated (hipotálamo advisory)
    companion_integrated_mode: str = "legacy"  # legacy | integrated (Nira dyad)
    flask_unified_mode: str = "legacy"  # legacy | integrated (Flask demo unificado)
    unified_motor_mode: str = "legacy"  # legacy | integrated (motor integrado primario)
    agent_loop_sync_mode: str = "legacy"  # legacy | integrated (post-tick cognitivo lite)
    memory_bridge_mode: str = "legacy"  # legacy | integrated (hippo ↔ SQLite advisory)
    flask_study_proxy_mode: str = "legacy"  # legacy | integrated (overlay rutas estudio)
    roadmap100_e_block_mode: str = "legacy"  # legacy | integrated (auditoría E1–E8)
    memory_unification_mode: str = "legacy"  # legacy | integrated (hippo→SQLite post-sueño)
    causal_certificate_mode: str = "legacy"  # legacy | integrated (certificado agency/tick)
    day_in_the_life_mode: str = "legacy"  # legacy | integrated (timeline 24h acelerada)
    agency_audit_mode: str = "legacy"  # legacy | integrated (auditoría agency H2)
    science_bundle_mode: str = "legacy"  # legacy | integrated (envelope ciencia personal)


@dataclass
class IntegratedRuntime:
    config: IntegratedRuntimeConfig
    streams: RandomStreams = field(init=False)
    clock: SimulationClock = field(default_factory=SimulationClock)
    state_store: StateStore = field(default_factory=StateStore)
    scheduler: CognitiveScheduler = field(init=False)
    world: RoomWorld = field(init=False)
    body: VirtualBody = field(default_factory=VirtualBody)
    homeostatic_controller: HomeostaticController = field(init=False)
    telemetry: TelemetryRecorder = field(init=False)
    legacy_brain: Any | None = None

    def __post_init__(self) -> None:
        from nexo.demo.world_factory import create_world

        if self.config.legacy_adapter_mode == "integrated" and self.legacy_brain is None:
            from brain.mind import InfantApeBrain
            from brain.profile import COMPACT_PROFILE

            experiment_flags = None
            if self.config.roadmap100_bridge_mode == "integrated":
                from nexo.experiment_conditions import roadmap100_full_v1_flags

                experiment_flags = roadmap100_full_v1_flags()
            brain_kwargs: dict[str, Any] = {
                "profile": COMPACT_PROFILE,
                "headless": True,
                "auto_save": False,
                "seed": self.config.seed,
            }
            if experiment_flags is not None:
                brain_kwargs["experiment_flags"] = experiment_flags
            self.legacy_brain = InfantApeBrain(**brain_kwargs)
            self.config.use_legacy_adapter = True

        self.world = create_world(self.config.world_mode, seed=self.config.seed)
        if hasattr(self.world, "legacy_actions_enabled"):
            self.world.legacy_actions_enabled = self.config.world2d_legacy_actions_mode == "integrated"
        if hasattr(self.world, "full_actions_enabled"):
            self.world.full_actions_enabled = self.config.world2d_full_actions_mode == "integrated"
        if hasattr(self.world, "legacy_env_enabled"):
            self.world.legacy_env_enabled = self.config.world2d_legacy_env_mode == "integrated"
        if hasattr(self.world, "headless_enabled"):
            self.world.headless_enabled = self.config.world2d_headless_mode == "integrated"
        if hasattr(self.world, "sync3d_enabled"):
            self.world.sync3d_enabled = self.config.world3d_sync_mode == "integrated"
        if hasattr(self.world, "attach_brain") and self.legacy_brain is not None:
            self.world.attach_brain(self.legacy_brain)
            if hasattr(self.world, "legacy_actions_enabled"):
                self.world.legacy_actions_enabled = self.config.world2d_legacy_actions_mode == "integrated"
            if hasattr(self.world, "full_actions_enabled"):
                self.world.full_actions_enabled = self.config.world2d_full_actions_mode == "integrated"
        self.streams = RandomStreams.from_root_seed(self.config.seed)
        self.homeostatic_controller = HomeostaticController(
            body=self.body,
            metabolism=MetabolismEngine(),
        )
        graph = ConnectomeGraph.from_yaml(self.config.connectome_path)
        errs = graph.validate()
        if errs:
            raise ValueError(f"Connectome inválido: {errs[:5]}")
        router = ConnectomeRouter(graph=graph, rng=self.streams.neural)
        router.latency_enabled = self.config.latency_mode == "integrated"
        if self.config.intervention_mode == "integrated":
            apply_lesion_profile(self.config.lesion_profile, router.lesions)
        self.telemetry = TelemetryRecorder(level=self.config.telemetry_level)
        self.scheduler = CognitiveScheduler(
            clock=self.clock,
            state_store=self.state_store,
            router=router,
            rng=self.streams.decision,
            config={
                "world_state": self.world,
                "homeostatic_controller": self.homeostatic_controller,
                "drives": None,
                "memory_rng": self.streams.memory,
                "wm_buffer": WorkingMemoryBuffer(capacity=4),
                "hippocampal_store": HippocampalStore(capacity=64),
                "goal_stack": GoalStack(),
                "action_gate": ActionGate(),
                "cerebellum": CerebellarCoordinator(),
                "prefrontal_deliberator": PrefrontalDeliberator(),
                "modulators": NeuromodulatorState(),
                "td_system": TDRewardSystem(),
                "learning_rng": self.streams.learning,
                "global_workspace": GlobalWorkspace(),
                "metacognitive_monitor": MetacognitiveMonitor(),
                "caregiver_model": CaregiverModel(),
                "tom_engine": TheoryOfMindEngine(),
                "utterance_composer": UtteranceComposer(),
                "sleep_architecture": SleepArchitecture(),
                "development_tracker": DevelopmentTracker(),
                "memory_consolidator": MemoryConsolidator(),
            },
            telemetry=self.telemetry,
            legacy_brain=self.legacy_brain,
        )
        self.world.sync_from_body(self.body)
        self.scheduler.config["_runtime_ref"] = self
        self.scheduler.config["routing_mode"] = self.config.routing_mode
        self.scheduler.config["deliberation_bridge_mode"] = self.config.deliberation_bridge_mode
        self.scheduler.config["deliberation_fusion_mode"] = self.config.deliberation_fusion_mode
        self.scheduler.config["deliberation_unified_mode"] = self.config.deliberation_unified_mode
        self.scheduler.config["deliberation_weight_mode"] = self.config.deliberation_weight_mode
        self.scheduler.config["legacy_adapter_early_mode"] = self.config.legacy_adapter_early_mode
        self.scheduler.config["roadmap100_bridge_mode"] = self.config.roadmap100_bridge_mode
        self.scheduler.config["flask_demo_bridge_mode"] = self.config.flask_demo_bridge_mode
        self.scheduler.config["world3d_sync_mode"] = self.config.world3d_sync_mode
        self.scheduler.config["autonomy_guard_mode"] = self.config.autonomy_guard_mode
        self.scheduler.config["hypothalamus_multimodal_mode"] = self.config.hypothalamus_multimodal_mode
        self.scheduler.config["companion_integrated_mode"] = self.config.companion_integrated_mode
        self.scheduler.config["flask_unified_mode"] = self.config.flask_unified_mode
        self.scheduler.config["unified_motor_mode"] = self.config.unified_motor_mode
        self.scheduler.config["agent_loop_sync_mode"] = self.config.agent_loop_sync_mode
        self.scheduler.config["memory_bridge_mode"] = self.config.memory_bridge_mode
        self.scheduler.config["flask_study_proxy_mode"] = self.config.flask_study_proxy_mode
        self.scheduler.config["roadmap100_e_block_mode"] = self.config.roadmap100_e_block_mode
        self.scheduler.config["memory_unification_mode"] = self.config.memory_unification_mode
        self.scheduler.config["causal_certificate_mode"] = self.config.causal_certificate_mode
        self.scheduler.config["day_in_the_life_mode"] = self.config.day_in_the_life_mode
        self.scheduler.config["agency_audit_mode"] = self.config.agency_audit_mode
        self.scheduler.config["science_bundle_mode"] = self.config.science_bundle_mode
        if self.config.flask_unified_mode == "integrated" or self.config.unified_motor_mode == "integrated":
            self.scheduler.config["suppress_legacy_world_tick"] = True
        if self.config.tracing_mode == "integrated":
            self.scheduler.config["trace_collector"] = IntegratedTraceCollector()
        self._register_default_processes()

    def _register_default_processes(self) -> None:
        procs = [
            MetabolismProcess(),
            BodyInteroceptionProcess(),
            AllostasisProcess(),
        ]
        procs.extend(self._intervention_processes())
        procs.extend(self._deliberation_bridge_processes())
        procs.extend(self._deliberation_fusion_processes())
        procs.extend(self._deliberation_unified_processes())
        procs.extend(self._deliberation_weight_processes())
        procs.extend(self._roadmap100_bridge_processes())
        procs.extend(self._flask_demo_bridge_processes())
        procs.extend(self._world3d_sync_processes())
        procs.extend(self._autonomy_guard_processes())
        procs.extend(self._hypothalamus_multimodal_processes())
        procs.extend(self._companion_integrated_processes())
        procs.extend(self._unified_motor_processes())
        procs.extend(self._agent_loop_sync_processes())
        procs.extend(self._memory_bridge_processes())
        procs.extend(self._roadmap100_e_block_processes())
        procs.extend(self._memory_unification_processes())
        procs.extend(self._causal_certificate_processes())
        procs.extend(self._agency_audit_processes())
        procs.extend(self._tracing_processes())
        procs.extend(self._sleep_processes())
        if self.config.perception_mode == "predictive":
            reticular = ReticularNucleus()
            procs.extend([
                RawSensoryCaptureProcess(),
                ThalamicRelayProcess(reticular=reticular),
                PredictiveHierarchyProcess(reticular=reticular),
                PredictiveAttentionProcess(),
            ])
        else:
            procs.extend([
                SensoryRelayProcess(),
                AttentionProcess(),
            ])
        procs.extend(self._social_processes())
        procs.extend(self._consciousness_processes())
        procs.extend(self._memory_processes())
        procs.extend(self._learning_processes())
        procs.extend(self._executive_processes())
        procs.append(MotorExecutionProcess())
        procs.extend(self._post_motor_learning_processes())
        procs.extend(self._post_motor_social_processes())
        procs.extend(self._post_motor_sleep_processes())
        procs.extend(self._evaluation_processes())
        if self.config.use_legacy_adapter and self.legacy_brain is not None:
            if self.config.legacy_adapter_early_mode == "integrated":
                from nexo.core.process_legacy_early import LegacyEarlyBrainAdapterProcess

                procs.append(LegacyEarlyBrainAdapterProcess())
            else:
                procs.append(LegacyBrainAdapterProcess())
        for p in procs:
            enabled = p.process_id not in self.config.disable_processes
            self.scheduler.register(p, enabled=enabled)

    def _memory_processes(self) -> list:
        if self.config.memory_mode == "integrated":
            return [
                EnhancedWorkingMemoryProcess(),
                HippocampalRetrievalProcess(),
                HippocampalEncoderProcess(),
            ]
        return [WorkingMemoryProcess()]

    def _consciousness_processes(self) -> list:
        if self.config.consciousness_mode == "integrated":
            return [
                GlobalWorkspaceProcess(),
                MetacognitionProcess(),
            ]
        return []

    def _social_processes(self) -> list:
        if self.config.social_mode == "integrated":
            return [
                SocialModelProcess(),
                TheoryOfMindProcess(),
            ]
        return []

    def _post_motor_social_processes(self) -> list:
        if self.config.social_mode == "integrated":
            return [
                SocialExchangeProcess(),
                LanguageProductionProcess(),
            ]
        return []

    def _sleep_processes(self) -> list:
        if self.config.sleep_mode == "integrated":
            return [SleepArchitectureProcess()]
        return []

    def _post_motor_sleep_processes(self) -> list:
        if self.config.sleep_mode == "integrated":
            return [
                MemoryReplayProcess(),
                ConsolidationProcess(),
                DevelopmentProcess(),
            ]
        return []

    def _executive_processes(self) -> list:
        if self.config.executive_mode == "integrated":
            return [
                GoalStackProcess(),
                PrefrontalDeliberationProcess(),
                EnhancedBasalGangliaProcess(),
                CerebellarCorrectionProcess(),
            ]
        return [BasalGangliaSelectorProcess()]

    def _learning_processes(self) -> list:
        if self.config.learning_mode == "integrated":
            return [TDBiasProcess()]
        return []

    def _post_motor_learning_processes(self) -> list:
        if self.config.learning_mode == "integrated":
            return [
                NeuromodulatorUpdateProcess(),
                TDLearningProcess(),
                ConnectomePlasticityProcess(),
            ]
        return []

    def _evaluation_processes(self) -> list:
        procs: list = []
        if self.config.evaluation_mode == "integrated":
            procs.append(BehavioralSnapshotProcess())
        if self.config.analysis_mode == "integrated":
            procs.append(BehavioralFingerprintProcess())
        return procs

    def _intervention_processes(self) -> list:
        procs: list = []
        if self.config.intervention_mode == "integrated":
            procs.append(ConnectomeLesionAuditProcess())
        if self.config.latency_mode == "integrated":
            procs.append(ConnectomeDeliveryProcess())
        if self.config.routing_mode == "integrated":
            procs.append(ConnectomeRoutingAuditProcess())
        return procs

    def _deliberation_bridge_processes(self) -> list:
        if self.config.deliberation_bridge_mode == "integrated":
            from nexo.core.process_deliberation_bridge import DeliberationBridgeAuditProcess

            return [DeliberationBridgeAuditProcess()]
        return []

    def _deliberation_fusion_processes(self) -> list:
        if self.config.deliberation_fusion_mode == "integrated":
            from nexo.core.process_deliberation_fusion import DeliberationFusionProcess

            return [DeliberationFusionProcess()]
        return []

    def _deliberation_unified_processes(self) -> list:
        if self.config.deliberation_unified_mode == "integrated":
            if self.config.deliberation_weight_mode == "integrated":
                return []
            from nexo.core.process_deliberation_unified import DeliberationUnifiedProcess

            return [DeliberationUnifiedProcess()]
        return []

    def _deliberation_weight_processes(self) -> list:
        if self.config.deliberation_weight_mode == "integrated":
            from nexo.core.process_deliberation_weight import DeliberationWeightProcess

            return [DeliberationWeightProcess()]
        return []

    def _roadmap100_bridge_processes(self) -> list:
        if self.config.roadmap100_bridge_mode == "integrated":
            from nexo.core.process_roadmap100_bridge import Roadmap100BridgeProcess

            return [Roadmap100BridgeProcess()]
        return []

    def _flask_demo_bridge_processes(self) -> list:
        if self.config.flask_demo_bridge_mode == "integrated":
            from nexo.core.process_flask_demo_bridge import FlaskDemoBridgeProcess

            return [FlaskDemoBridgeProcess()]
        return []

    def _world3d_sync_processes(self) -> list:
        if self.config.world3d_sync_mode == "integrated":
            from nexo.core.process_world3d_sync import World3DSyncProcess

            return [World3DSyncProcess()]
        return []

    def _autonomy_guard_processes(self) -> list:
        if self.config.autonomy_guard_mode == "integrated":
            from nexo.core.process_autonomy_guard import AutonomyGuardProcess

            return [AutonomyGuardProcess()]
        return []

    def _hypothalamus_multimodal_processes(self) -> list:
        if self.config.hypothalamus_multimodal_mode == "integrated":
            from nexo.core.process_hypothalamus_multimodal import HypothalamusMultimodalProcess

            return [HypothalamusMultimodalProcess()]
        return []

    def _companion_integrated_processes(self) -> list:
        if self.config.companion_integrated_mode == "integrated":
            from nexo.core.process_companion_integrated import CompanionIntegratedProcess

            return [CompanionIntegratedProcess()]
        return []

    def _unified_motor_processes(self) -> list:
        if self.config.unified_motor_mode == "integrated":
            from nexo.core.process_unified_motor import UnifiedMotorProcess

            return [UnifiedMotorProcess()]
        return []

    def _agent_loop_sync_processes(self) -> list:
        if self.config.agent_loop_sync_mode == "integrated":
            from nexo.core.process_agent_loop_sync import AgentLoopSyncProcess

            return [AgentLoopSyncProcess()]
        return []

    def _memory_bridge_processes(self) -> list:
        if self.config.memory_bridge_mode == "integrated":
            from nexo.core.process_memory_bridge import MemoryBridgeProcess

            return [MemoryBridgeProcess()]
        return []

    def _roadmap100_e_block_processes(self) -> list:
        if self.config.roadmap100_e_block_mode == "integrated":
            from nexo.core.process_roadmap100_e_block import Roadmap100EBlockProcess

            return [Roadmap100EBlockProcess()]
        return []

    def _memory_unification_processes(self) -> list:
        if self.config.memory_unification_mode == "integrated":
            from nexo.core.process_memory_unification import MemoryUnificationProcess

            return [MemoryUnificationProcess()]
        return []

    def _causal_certificate_processes(self) -> list:
        if self.config.causal_certificate_mode == "integrated":
            from nexo.core.process_causal_certificate import CausalCertificateProcess

            return [CausalCertificateProcess()]
        return []

    def _agency_audit_processes(self) -> list:
        if self.config.agency_audit_mode == "integrated":
            from nexo.core.process_agency_audit import AgencyAuditProcess

            return [AgencyAuditProcess()]
        return []

    def _tracing_processes(self) -> list:
        if self.config.tracing_mode == "integrated":
            return [IntegratedTraceProcess()]
        return []

    def run(self, ticks: int | None = None) -> dict[str, Any]:
        n = ticks if ticks is not None else self.config.ticks
        events = self.scheduler.run(n)
        return self.build_result(events)

    def run_sidecar(self, ticks: int) -> dict[str, Any]:
        """Auditoría integrada sin re-ejecutar `world_tick` legacy (Flask unificado)."""
        prev = bool(self.scheduler.config.get("suppress_legacy_world_tick"))
        self.scheduler.config["suppress_legacy_world_tick"] = True
        try:
            return self.run(ticks)
        finally:
            self.scheduler.config["suppress_legacy_world_tick"] = prev

    def build_result(self, events: list[Any] | None = None) -> dict[str, Any]:
        state = self.state_store.state
        traj = [
            {
                "tick": ev.tick,
                "type": ev.event_type,
                "action": ev.payload.get("action"),
            }
            for ev in self.state_store.event_log
            if ev.event_type == "action.selected"
        ]
        raw = json.dumps(traj, sort_keys=True).encode()
        th = hashlib.sha256(raw).hexdigest()
        drives = self.scheduler.config.get("drives")
        surprises = self.scheduler.config.get("surprises") or {}
        store: HippocampalStore | None = self.scheduler.config.get("hippocampal_store")
        gate: ActionGate | None = self.scheduler.config.get("action_gate")
        stack: GoalStack | None = self.scheduler.config.get("goal_stack")
        mods: NeuromodulatorState | None = self.scheduler.config.get("modulators")
        td: TDRewardSystem | None = self.scheduler.config.get("td_system")
        meta: MetacognitiveMonitor | None = self.scheduler.config.get("metacognitive_monitor")
        sleep_arch: SleepArchitecture | None = self.scheduler.config.get("sleep_architecture")
        dev: DevelopmentTracker | None = self.scheduler.config.get("development_tracker")
        plasticity = self.scheduler.router.plasticity
        log = self.state_store.event_log
        result: dict[str, Any] = {
            "profile": self.config.profile,
            "seed": self.config.seed,
            "ticks": self.clock.tick,
            "trajectory_hash": th,
            "perception_mode": self.config.perception_mode,
            "memory_mode": self.config.memory_mode,
            "executive_mode": self.config.executive_mode,
            "learning_mode": self.config.learning_mode,
            "consciousness_mode": self.config.consciousness_mode,
            "social_mode": self.config.social_mode,
            "sleep_mode": self.config.sleep_mode,
            "evaluation_mode": self.config.evaluation_mode,
            "intervention_mode": self.config.intervention_mode,
            "lesion_profile": self.config.lesion_profile,
            "latency_mode": self.config.latency_mode,
            "connectome_signals_delivered": self.scheduler.router.latency_buffer.total_delivered,
            "connectome_delivery_events": sum(1 for e in log if e.event_type == "connectome.signal_delivered"),
            "connectome_lesions_active": len(self.scheduler.router.lesions.active_lesions()),
            "connectome_lesion_events": sum(1 for e in log if e.event_type == "connectome.lesion_applied"),
            "mean_surprise": (
                sum(surprises.values()) / len(surprises) if surprises else 0.0
            ),
            "final_energy": self.body.energy if self.config.body_enabled else state.homeostatic.energy,
            "final_fatigue": self.body.fatigue,
            "dominant_drives": list(drives.dominant()) if drives else [],
            "actions_taken": list(self.world.action_history),
            "episodes_encoded": len(self.world.episodes),
            "hippocampal_episodes": len(store.episodes) if store else 0,
            "memory_encodings": sum(1 for e in log if e.event_type == "memory.encoded"),
            "memory_retrievals": sum(1 for e in log if e.event_type == "memory.retrieved"),
            "deliberation_events": sum(1 for e in log if e.event_type == "deliberation.completed"),
            "pfc_vetoes": sum(1 for e in log if e.event_type == "action.vetoed"),
            "plan_depth_max": stack.depth() if stack else 0,
            "max_habit_strength": gate.max_habit() if gate else 0.0,
            "mean_dopamine": mods.dopamine if mods else 0.0,
            "td_updates": td.updates if td else 0,
            "last_td_delta": td.last_delta if td else 0.0,
            "plastic_edges": len(plasticity.weights),
            "neuromodulation_events": sum(1 for e in log if e.event_type == "neuromodulation.updated"),
            "plasticity_events": sum(1 for e in log if e.event_type == "plasticity.updated"),
            "workspace_broadcasts": sum(1 for e in log if e.event_type == "workspace.broadcast"),
            "metacognition_events": sum(1 for e in log if e.event_type == "metacognition.updated"),
            "metacognitive_clarity": meta.last.clarity if meta else 0.0,
            "metacognitive_doubt": meta.last.doubt if meta else 0.0,
            "metacognitive_felt": meta.last.felt if meta else "",
            "social_exchanges": sum(1 for e in log if e.event_type == "social.exchange"),
            "language_utterances": sum(1 for e in log if e.event_type == "language.produced"),
            "tom_inferences": sum(1 for e in log if e.event_type == "social.tom_inferred"),
            "last_utterance": self.scheduler.config.get("last_utterance", ""),
            "sleep_phase": sleep_arch.phase if sleep_arch else "awake",
            "sleep_cycles": sleep_arch.cycles_completed if sleep_arch else 0,
            "memory_replays": sum(1 for e in log if e.event_type == "memory.replayed"),
            "memory_consolidations": sum(1 for e in log if e.event_type == "memory.consolidated"),
            "development_stage": dev.stage.value if dev else "infant",
            "development_maturation": dev.maturation if dev else 0.0,
            "behavior_snapshots": sum(1 for e in log if e.event_type == "behavior.snapshot"),
            "behavior_fingerprints": sum(1 for e in log if e.event_type == "behavior.fingerprint"),
            "analysis_mode": self.config.analysis_mode,
            "routing_mode": self.config.routing_mode,
            "statistics_mode": self.config.statistics_mode,
            "connectome_routing_events": sum(1 for e in log if e.event_type == "connectome.routing_active"),
            "tracing_mode": self.config.tracing_mode,
            "trace_events": sum(1 for e in log if e.event_type == "telemetry.trace"),
            "replication_mode": self.config.replication_mode,
            "replication_id": self._replication_id(),
            "permutation_mode": self.config.permutation_mode,
            "correction_mode": self.config.correction_mode,
            "eventlog_mode": self.config.eventlog_mode,
            "meta_analysis_mode": self.config.meta_analysis_mode,
            "replication_batch_mode": self.config.replication_batch_mode,
            "cross_battery_mode": self.config.cross_battery_mode,
            "phenomenology_mode": self.config.phenomenology_mode,
            "legacy_bridge_mode": self.config.legacy_bridge_mode,
            "world_mode": self.config.world_mode,
            "inference_mode": self.config.inference_mode,
            "orchestration_mode": self.config.orchestration_mode,
            "legacy_adapter_mode": self.config.legacy_adapter_mode,
            "scale_mode": self.config.scale_mode,
            "hierarchical_inference_mode": self.config.hierarchical_inference_mode,
            "deliberation_bridge_mode": self.config.deliberation_bridge_mode,
            "deliberation_fusion_mode": self.config.deliberation_fusion_mode,
            "deliberation_unified_mode": self.config.deliberation_unified_mode,
            "world2d_legacy_actions_mode": self.config.world2d_legacy_actions_mode,
            "world2d_full_actions_mode": self.config.world2d_full_actions_mode,
            "world2d_legacy_env_mode": self.config.world2d_legacy_env_mode,
            "lif_scale_mode": self.config.lif_scale_mode,
            "gpu_bench_mode": self.config.gpu_bench_mode,
            "publication_mode": self.config.publication_mode,
            "paper_pack_mode": self.config.paper_pack_mode,
            "battery_paper_mode": self.config.battery_paper_mode,
            "full_publication_mode": self.config.full_publication_mode,
            "deliberation_weight_mode": self.config.deliberation_weight_mode,
            "legacy_advisory_weight": self.config.legacy_advisory_weight,
            "paper_figures_mode": self.config.paper_figures_mode,
            "pipeline_paper_mode": self.config.pipeline_paper_mode,
            "latex_master_mode": self.config.latex_master_mode,
            "battery_full_mode": self.config.battery_full_mode,
            "release_bundle_mode": self.config.release_bundle_mode,
            "legacy_adapter_early_mode": self.config.legacy_adapter_early_mode,
            "world2d_headless_mode": self.config.world2d_headless_mode,
            "roadmap100_bridge_mode": self.config.roadmap100_bridge_mode,
            "flask_demo_bridge_mode": self.config.flask_demo_bridge_mode,
            "world3d_sync_mode": self.config.world3d_sync_mode,
            "autonomy_guard_mode": self.config.autonomy_guard_mode,
            "hypothalamus_multimodal_mode": self.config.hypothalamus_multimodal_mode,
            "companion_integrated_mode": self.config.companion_integrated_mode,
            "flask_unified_mode": self.config.flask_unified_mode,
            "unified_motor_mode": self.config.unified_motor_mode,
            "agent_loop_sync_mode": self.config.agent_loop_sync_mode,
            "memory_bridge_mode": self.config.memory_bridge_mode,
            "flask_study_proxy_mode": self.config.flask_study_proxy_mode,
            "roadmap100_e_block_mode": self.config.roadmap100_e_block_mode,
            "memory_unification_mode": self.config.memory_unification_mode,
            "causal_certificate_mode": self.config.causal_certificate_mode,
            "day_in_the_life_mode": self.config.day_in_the_life_mode,
            "agency_audit_mode": self.config.agency_audit_mode,
            "science_bundle_mode": self.config.science_bundle_mode,
            "event_count": len(log),
            "telemetry": self.telemetry.summary(),
        }
        if self.config.analysis_mode == "integrated":
            from nexo.behavioral.fingerprint import metric_fingerprint_hash
            from nexo.behavioral.metrics import compute_metrics

            result["metric_fingerprint"] = metric_fingerprint_hash(compute_metrics(self, result))
            result["metric_fingerprint"] = (
                self.scheduler.config.get("last_metric_fingerprint") or result["metric_fingerprint"]
            )
        else:
            result["metric_fingerprint"] = ""
        collector: IntegratedTraceCollector | None = self.scheduler.config.get("trace_collector")
        if collector is not None:
            result["trace_summary"] = collector.summary()
        else:
            result["trace_summary"] = {}
        return result

    def export_trace(self, path: Path) -> dict[str, Any]:
        collector: IntegratedTraceCollector | None = self.scheduler.config.get("trace_collector")
        if collector is None:
            return {"exported": False, "reason": "tracing_mode not integrated"}
        collector.export_json(path)
        return {"exported": True, "path": str(path), "summary": collector.summary()}

    def _replication_id(self) -> str:
        from nexo.behavioral.replication import config_fingerprint

        return config_fingerprint(self.config)

    def export_replication(self, output_dir: Path, result: dict[str, Any] | None = None) -> dict[str, Any]:
        if self.config.replication_mode != "integrated":
            return {"exported": False, "reason": "replication_mode not integrated"}
        from nexo.behavioral.replication import build_replication_bundle

        payload = result if result is not None else self.build_result()
        return build_replication_bundle(self, payload, output_dir)

    def export_meta_analysis(self, replication_root: Path, output_path: Path) -> dict[str, Any]:
        if self.config.meta_analysis_mode != "integrated":
            return {"exported": False, "reason": "meta_analysis_mode not integrated"}
        from nexo.behavioral.meta_analysis import export_meta_analysis

        return export_meta_analysis(replication_root, output_path)

    def export_replication_batch(
        self,
        seeds: tuple[int, ...],
        base_dir: Path,
        *,
        ticks: int | None = None,
    ) -> dict[str, Any]:
        if self.config.replication_batch_mode != "integrated":
            return {"exported": False, "reason": "replication_batch_mode not integrated"}
        from nexo.behavioral.replication_batch import run_replication_batch_from_config

        return run_replication_batch_from_config(self.config, seeds, base_dir, ticks=ticks)

    def export_cross_battery(
        self,
        report_paths: dict[str, Path],
        output_path: Path,
    ) -> dict[str, Any]:
        if self.config.cross_battery_mode != "integrated":
            return {"exported": False, "reason": "cross_battery_mode not integrated"}
        from nexo.behavioral.cross_battery import export_cross_battery

        return export_cross_battery(report_paths, output_path)

    def export_legacy_bridge(self, result: dict[str, Any], output_path: Path) -> dict[str, Any]:
        if self.config.legacy_bridge_mode != "integrated":
            return {"exported": False, "reason": "legacy_bridge_mode not integrated"}
        from nexo.behavioral.legacy_bridge import export_legacy_bridge

        return export_legacy_bridge(
            result,
            seed=self.config.seed,
            ticks=int(result.get("ticks", self.config.ticks)),
            output_path=output_path,
        )

    def export_legacy_adapter_report(self, result: dict[str, Any], output_path: Path) -> dict[str, Any]:
        if self.config.legacy_adapter_mode != "integrated":
            return {"exported": False, "reason": "legacy_adapter_mode not integrated"}
        from nexo.behavioral.legacy_adapter import export_legacy_adapter_report

        return export_legacy_adapter_report(self, result, output_path)

    def export_scale_profile(
        self,
        result: dict[str, Any],
        output_path: Path,
        *,
        elapsed_seconds: float | None = None,
    ) -> dict[str, Any]:
        if self.config.scale_mode != "integrated":
            return {"exported": False, "reason": "scale_mode not integrated"}
        from nexo.behavioral.scale_profile import export_scale_profile

        return export_scale_profile(self, result, output_path, elapsed_seconds=elapsed_seconds)

    def export_deliberation_bridge(self, result: dict[str, Any], output_path: Path) -> dict[str, Any]:
        if self.config.deliberation_bridge_mode != "integrated":
            return {"exported": False, "reason": "deliberation_bridge_mode not integrated"}
        from nexo.behavioral.deliberation_bridge import export_deliberation_bridge

        return export_deliberation_bridge(self, result, output_path)

    def export_deliberation_fusion(self, result: dict[str, Any], output_path: Path) -> dict[str, Any]:
        if self.config.deliberation_fusion_mode != "integrated":
            return {"exported": False, "reason": "deliberation_fusion_mode not integrated"}
        from nexo.behavioral.deliberation_fusion import export_deliberation_fusion

        return export_deliberation_fusion(self, result, output_path)

    def export_deliberation_unified(self, result: dict[str, Any], output_path: Path) -> dict[str, Any]:
        if self.config.deliberation_unified_mode != "integrated":
            return {"exported": False, "reason": "deliberation_unified_mode not integrated"}
        from nexo.behavioral.deliberation_unified import export_deliberation_unified

        return export_deliberation_unified(self, result, output_path)

    def export_lif_scale_probe(
        self,
        output_path: Path,
        *,
        profile_key: str = "compact",
        ticks: int = 2,
        run_bench: bool = False,
    ) -> dict[str, Any]:
        if self.config.lif_scale_mode != "integrated":
            return {"exported": False, "reason": "lif_scale_mode not integrated"}
        from nexo.behavioral.lif_scale import export_lif_scale_probe

        return export_lif_scale_probe(
            output_path,
            profile_key=profile_key,
            ticks=ticks,
            run_bench=run_bench,
        )

    def export_gpu_bench(
        self,
        output_path: Path,
        *,
        profile_key: str = "compact",
        ticks: int = 1,
        ci_safe: bool = True,
    ) -> dict[str, Any]:
        if self.config.gpu_bench_mode != "integrated":
            return {"exported": False, "reason": "gpu_bench_mode not integrated"}
        from nexo.behavioral.gpu_bench import export_gpu_bench

        return export_gpu_bench(
            output_path,
            profile_key=profile_key,
            ticks=ticks,
            ci_safe=ci_safe,
        )

    def export_publication_bundle(
        self,
        result: dict[str, Any],
        output_dir: Path,
        *,
        artifact_paths: dict[str, Path] | None = None,
    ) -> dict[str, Any]:
        if self.config.publication_mode != "integrated":
            return {"exported": False, "reason": "publication_mode not integrated"}
        from nexo.behavioral.publication import export_publication_bundle

        return export_publication_bundle(self, result, output_dir, artifact_paths=artifact_paths)

    def export_paper_pack(self, result: dict[str, Any], output_dir: Path) -> dict[str, Any]:
        if self.config.paper_pack_mode != "integrated":
            return {"exported": False, "reason": "paper_pack_mode not integrated"}
        from nexo.behavioral.paper_pack import export_paper_pack

        return export_paper_pack(self, result, output_dir)

    def export_battery_paper(
        self,
        report_paths: dict[str, Path],
        output_dir: Path,
    ) -> dict[str, Any]:
        if self.config.battery_paper_mode != "integrated":
            return {"exported": False, "reason": "battery_paper_mode not integrated"}
        from nexo.behavioral.battery_paper import export_battery_paper

        return export_battery_paper(report_paths, output_dir)

    def export_full_publication_bundle(
        self,
        result: dict[str, Any],
        output_dir: Path,
        *,
        artifact_paths: dict[str, Path] | None = None,
        paper_pack_dir: Path | None = None,
        battery_paper_dir: Path | None = None,
        figures_dir: Path | None = None,
    ) -> dict[str, Any]:
        if self.config.full_publication_mode != "integrated":
            return {"exported": False, "reason": "full_publication_mode not integrated"}
        from nexo.behavioral.publication import export_full_publication_bundle

        return export_full_publication_bundle(
            self,
            result,
            output_dir,
            artifact_paths=artifact_paths,
            paper_pack_dir=paper_pack_dir,
            battery_paper_dir=battery_paper_dir,
            figures_dir=figures_dir,
        )

    def export_deliberation_weight(self, result: dict[str, Any], output_path: Path) -> dict[str, Any]:
        if self.config.deliberation_weight_mode != "integrated":
            return {"exported": False, "reason": "deliberation_weight_mode not integrated"}
        from nexo.behavioral.deliberation_weight import export_deliberation_weight

        return export_deliberation_weight(self, result, output_path)

    def export_paper_figures(self, report_path: Path, output_dir: Path) -> dict[str, Any]:
        if self.config.paper_figures_mode != "integrated":
            return {"exported": False, "reason": "paper_figures_mode not integrated"}
        from nexo.behavioral.paper_figures import export_paper_figures

        return export_paper_figures(report_path, output_dir)

    def run_pipeline_paper(
        self,
        manifest_path: Path,
        output_dir: Path,
        *,
        pipeline_output: Path | None = None,
        meta_root: Path | None = None,
        meta_output: Path | None = None,
        cross_reports: dict[str, Path] | None = None,
        cross_output: Path | None = None,
    ) -> dict[str, Any]:
        if self.config.pipeline_paper_mode != "integrated":
            return {"exported": False, "reason": "pipeline_paper_mode not integrated"}
        from nexo.behavioral.pipeline_paper import run_pipeline_paper

        return run_pipeline_paper(
            manifest_path,
            output_dir=output_dir,
            meta_root=meta_root,
            meta_output=meta_output,
            cross_reports=cross_reports,
            cross_output=cross_output,
            pipeline_output=pipeline_output,
        )

    def run_pipeline_paper_auto(
        self,
        manifest_path: Path,
        output_dir: Path,
        result: dict[str, Any],
        *,
        pipeline_output: Path | None = None,
        meta_root: Path | None = None,
        meta_output: Path | None = None,
        cross_reports: dict[str, Path] | None = None,
        cross_output: Path | None = None,
    ) -> dict[str, Any]:
        if self.config.pipeline_paper_mode != "integrated":
            return {"exported": False, "reason": "pipeline_paper_mode not integrated"}
        from nexo.behavioral.pipeline_paper import run_pipeline_paper_auto

        return run_pipeline_paper_auto(
            manifest_path=manifest_path,
            output_dir=output_dir,
            result=result,
            pipeline_output=pipeline_output,
            meta_root=meta_root,
            meta_output=meta_output,
            cross_reports=cross_reports,
            cross_output=cross_output,
            build_latex=self.config.latex_master_mode == "integrated",
        )

    def export_latex_master(
        self,
        result: dict[str, Any],
        output_dir: Path,
        *,
        paper_pack_dir: Path | None = None,
        battery_paper_dir: Path | None = None,
        figures_dir: Path | None = None,
    ) -> dict[str, Any]:
        if self.config.latex_master_mode != "integrated":
            return {"exported": False, "reason": "latex_master_mode not integrated"}
        from nexo.behavioral.latex_master import export_latex_master

        return export_latex_master(
            result,
            output_dir,
            paper_pack_dir=paper_pack_dir,
            battery_paper_dir=battery_paper_dir,
            figures_dir=figures_dir,
        )

    def run_battery_full(self, manifest_path: Path, output_dir: Path) -> dict[str, Any]:
        if self.config.battery_full_mode != "integrated":
            return {"exported": False, "reason": "battery_full_mode not integrated"}
        from nexo.behavioral.battery_full import run_battery_full

        return run_battery_full(manifest_path, output_dir)

    def export_release_bundle(
        self,
        result: dict[str, Any],
        output_dir: Path,
        *,
        artifact_roots: dict[str, Path] | None = None,
        config_path: str = "configs/nexo/integrated_v50.yaml",
    ) -> dict[str, Any]:
        if self.config.release_bundle_mode != "integrated":
            return {"exported": False, "reason": "release_bundle_mode not integrated"}
        from nexo.behavioral.release_bundle import export_release_bundle

        return export_release_bundle(
            result,
            output_dir,
            artifact_roots=artifact_roots,
            config_path=config_path,
        )

    def export_legacy_adapter_early(self, result: dict[str, Any], output_path: Path) -> dict[str, Any]:
        if self.config.legacy_adapter_early_mode != "integrated":
            return {"exported": False, "reason": "legacy_adapter_early_mode not integrated"}
        from nexo.behavioral.legacy_adapter_early import export_legacy_adapter_early

        return export_legacy_adapter_early(self, result, output_path)

    def export_roadmap100_bridge(self, result: dict[str, Any], output_path: Path) -> dict[str, Any]:
        if self.config.roadmap100_bridge_mode != "integrated":
            return {"exported": False, "reason": "roadmap100_bridge_mode not integrated"}
        from nexo.behavioral.roadmap100_bridge import export_roadmap100_bridge

        return export_roadmap100_bridge(self, result, output_path)

    def export_flask_demo_bridge(self, result: dict[str, Any], output_path: Path) -> dict[str, Any]:
        if self.config.flask_demo_bridge_mode != "integrated":
            return {"exported": False, "reason": "flask_demo_bridge_mode not integrated"}
        from nexo.behavioral.flask_demo_bridge import export_flask_demo_bridge

        return export_flask_demo_bridge(self, result, output_path)

    def export_world3d_sync(self, result: dict[str, Any], output_path: Path) -> dict[str, Any]:
        if self.config.world3d_sync_mode != "integrated":
            return {"exported": False, "reason": "world3d_sync_mode not integrated"}
        from nexo.behavioral.world3d_sync_report import export_world3d_sync

        return export_world3d_sync(self, result, output_path)

    def export_autonomy_guard(self, result: dict[str, Any], output_path: Path) -> dict[str, Any]:
        if self.config.autonomy_guard_mode != "integrated":
            return {"exported": False, "reason": "autonomy_guard_mode not integrated"}
        from nexo.behavioral.autonomy_guard import export_autonomy_guard

        return export_autonomy_guard(self, result, output_path)

    def export_hypothalamus_multimodal(self, result: dict[str, Any], output_path: Path) -> dict[str, Any]:
        if self.config.hypothalamus_multimodal_mode != "integrated":
            return {"exported": False, "reason": "hypothalamus_multimodal_mode not integrated"}
        from nexo.behavioral.hypothalamus_multimodal import export_hypothalamus_multimodal

        return export_hypothalamus_multimodal(self, result, output_path)

    def export_companion_integrated(self, result: dict[str, Any], output_path: Path) -> dict[str, Any]:
        if self.config.companion_integrated_mode != "integrated":
            return {"exported": False, "reason": "companion_integrated_mode not integrated"}
        from nexo.behavioral.companion_integrated import export_companion_integrated

        return export_companion_integrated(self, result, output_path)

    def export_unified_motor(self, result: dict[str, Any], output_path: Path) -> dict[str, Any]:
        if self.config.unified_motor_mode != "integrated":
            return {"exported": False, "reason": "unified_motor_mode not integrated"}
        from nexo.behavioral.unified_motor import export_unified_motor

        return export_unified_motor(self, result, output_path)

    def export_agent_loop_sync(self, result: dict[str, Any], output_path: Path) -> dict[str, Any]:
        if self.config.agent_loop_sync_mode != "integrated":
            return {"exported": False, "reason": "agent_loop_sync_mode not integrated"}
        from nexo.behavioral.agent_loop_sync import export_agent_loop_sync

        return export_agent_loop_sync(self, result, output_path)

    def export_memory_bridge(self, result: dict[str, Any], output_path: Path) -> dict[str, Any]:
        if self.config.memory_bridge_mode != "integrated":
            return {"exported": False, "reason": "memory_bridge_mode not integrated"}
        from nexo.behavioral.memory_bridge import export_memory_bridge

        return export_memory_bridge(self, result, output_path)

    def export_roadmap100_e_block(self, result: dict[str, Any], output_path: Path) -> dict[str, Any]:
        if self.config.roadmap100_e_block_mode != "integrated":
            return {"exported": False, "reason": "roadmap100_e_block_mode not integrated"}
        from nexo.behavioral.roadmap100_e_block import export_roadmap100_e_block

        return export_roadmap100_e_block(self, result, output_path)

    def export_memory_unification(self, result: dict[str, Any], output_path: Path) -> dict[str, Any]:
        if self.config.memory_unification_mode != "integrated":
            return {"exported": False, "reason": "memory_unification_mode not integrated"}
        from nexo.behavioral.memory_unification import export_memory_unification

        return export_memory_unification(self, result, output_path)

    def export_causal_certificate(self, result: dict[str, Any], output_path: Path) -> dict[str, Any]:
        if self.config.causal_certificate_mode != "integrated":
            return {"exported": False, "reason": "causal_certificate_mode not integrated"}
        from nexo.behavioral.causal_certificate import export_causal_certificate

        return export_causal_certificate(self, result, output_path)

    def export_day_in_the_life(self, result: dict[str, Any], output_path: Path) -> dict[str, Any]:
        if self.config.day_in_the_life_mode != "integrated":
            return {"exported": False, "reason": "day_in_the_life_mode not integrated"}
        from nexo.demo.day_in_the_life import export_day_timeline

        return export_day_timeline(self, result, output_path)

    def export_agency_audit(self, result: dict[str, Any], output_path: Path) -> dict[str, Any]:
        if self.config.agency_audit_mode != "integrated":
            return {"exported": False, "reason": "agency_audit_mode not integrated"}
        from nexo.behavioral.agency_audit import export_agency_audit

        return export_agency_audit(self, result, output_path)

    def export_science_bundle(self, result: dict[str, Any], output_path: Path) -> dict[str, Any]:
        if self.config.science_bundle_mode != "integrated":
            return {"exported": False, "reason": "science_bundle_mode not integrated"}
        from nexo.behavioral.science_bundle import export_science_bundle

        return export_science_bundle(self, result, output_path, repo_root=_repo_root())


def load_yaml_config(path: Path) -> dict[str, Any]:
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def runtime_from_config(path: Path, *, legacy_brain: Any | None = None, ablation_id: str | None = None) -> IntegratedRuntime:
    data = load_yaml_config(path)
    cfg = IntegratedRuntimeConfig(
        seed=int(data.get("seed", 42)),
        ticks=int(data.get("ticks", 80)),
        connectome_path=_repo_root() / str(data.get("connectome", "configs/connectome/connectome_v1.yaml")),
        telemetry_level=TelemetryLevel[data.get("telemetry_level", "SUMMARY").upper()],
        use_legacy_adapter=bool(data.get("use_legacy_adapter", False)),
        disable_processes=tuple(data.get("disable_processes", ())),
        profile=str(data.get("profile", path.stem)),
        body_enabled=bool(data.get("body_enabled", True)),
        perception_mode=str(data.get("perception_mode", "legacy")),
        memory_mode=str(data.get("memory_mode", "legacy")),
        executive_mode=str(data.get("executive_mode", "legacy")),
        learning_mode=str(data.get("learning_mode", "legacy")),
        consciousness_mode=str(data.get("consciousness_mode", "legacy")),
        social_mode=str(data.get("social_mode", "legacy")),
        sleep_mode=str(data.get("sleep_mode", "legacy")),
        evaluation_mode=str(data.get("evaluation_mode", "legacy")),
        intervention_mode=str(data.get("intervention_mode", "legacy")),
        lesion_profile=str(data.get("lesion_profile", LESION_NONE.lesion_id)),
        latency_mode=str(data.get("latency_mode", "legacy")),
        analysis_mode=str(data.get("analysis_mode", "legacy")),
        routing_mode=str(data.get("routing_mode", "legacy")),
        statistics_mode=str(data.get("statistics_mode", "legacy")),
        tracing_mode=str(data.get("tracing_mode", "legacy")),
        replication_mode=str(data.get("replication_mode", "legacy")),
        permutation_mode=str(data.get("permutation_mode", "legacy")),
        correction_mode=str(data.get("correction_mode", "legacy")),
        eventlog_mode=str(data.get("eventlog_mode", "legacy")),
        meta_analysis_mode=str(data.get("meta_analysis_mode", "legacy")),
        replication_batch_mode=str(data.get("replication_batch_mode", "legacy")),
        cross_battery_mode=str(data.get("cross_battery_mode", "legacy")),
        phenomenology_mode=str(data.get("phenomenology_mode", "legacy")),
        legacy_bridge_mode=str(data.get("legacy_bridge_mode", "legacy")),
        world_mode=str(data.get("world_mode", "room")),
        inference_mode=str(data.get("inference_mode", "legacy")),
        orchestration_mode=str(data.get("orchestration_mode", "legacy")),
        legacy_adapter_mode=str(data.get("legacy_adapter_mode", "legacy")),
        scale_mode=str(data.get("scale_mode", "legacy")),
        hierarchical_inference_mode=str(data.get("hierarchical_inference_mode", "legacy")),
        deliberation_bridge_mode=str(data.get("deliberation_bridge_mode", "legacy")),
        deliberation_fusion_mode=str(data.get("deliberation_fusion_mode", "legacy")),
        deliberation_unified_mode=str(data.get("deliberation_unified_mode", "legacy")),
        world2d_legacy_actions_mode=str(data.get("world2d_legacy_actions_mode", "legacy")),
        world2d_full_actions_mode=str(data.get("world2d_full_actions_mode", "legacy")),
        world2d_legacy_env_mode=str(data.get("world2d_legacy_env_mode", "legacy")),
        lif_scale_mode=str(data.get("lif_scale_mode", "legacy")),
        gpu_bench_mode=str(data.get("gpu_bench_mode", "legacy")),
        publication_mode=str(data.get("publication_mode", "legacy")),
        paper_pack_mode=str(data.get("paper_pack_mode", "legacy")),
        battery_paper_mode=str(data.get("battery_paper_mode", "legacy")),
        full_publication_mode=str(data.get("full_publication_mode", "legacy")),
        deliberation_weight_mode=str(data.get("deliberation_weight_mode", "legacy")),
        legacy_advisory_weight=float(data.get("legacy_advisory_weight", 0.0)),
        paper_figures_mode=str(data.get("paper_figures_mode", "legacy")),
        pipeline_paper_mode=str(data.get("pipeline_paper_mode", "legacy")),
        latex_master_mode=str(data.get("latex_master_mode", "legacy")),
        battery_full_mode=str(data.get("battery_full_mode", "legacy")),
        release_bundle_mode=str(data.get("release_bundle_mode", "legacy")),
        legacy_adapter_early_mode=str(data.get("legacy_adapter_early_mode", "legacy")),
        world2d_headless_mode=str(data.get("world2d_headless_mode", "legacy")),
        roadmap100_bridge_mode=str(data.get("roadmap100_bridge_mode", "legacy")),
        flask_demo_bridge_mode=str(data.get("flask_demo_bridge_mode", "legacy")),
        world3d_sync_mode=str(data.get("world3d_sync_mode", "legacy")),
        autonomy_guard_mode=str(data.get("autonomy_guard_mode", "legacy")),
        hypothalamus_multimodal_mode=str(data.get("hypothalamus_multimodal_mode", "legacy")),
        companion_integrated_mode=str(data.get("companion_integrated_mode", "legacy")),
        flask_unified_mode=str(data.get("flask_unified_mode", "legacy")),
        unified_motor_mode=str(data.get("unified_motor_mode", "legacy")),
        agent_loop_sync_mode=str(data.get("agent_loop_sync_mode", "legacy")),
        memory_bridge_mode=str(data.get("memory_bridge_mode", "legacy")),
        flask_study_proxy_mode=str(data.get("flask_study_proxy_mode", "legacy")),
        roadmap100_e_block_mode=str(data.get("roadmap100_e_block_mode", "legacy")),
        memory_unification_mode=str(data.get("memory_unification_mode", "legacy")),
        causal_certificate_mode=str(data.get("causal_certificate_mode", "legacy")),
        day_in_the_life_mode=str(data.get("day_in_the_life_mode", "legacy")),
        agency_audit_mode=str(data.get("agency_audit_mode", "legacy")),
        science_bundle_mode=str(data.get("science_bundle_mode", "legacy")),
    )
    if ablation_id:
        from nexo.ablation.profiles import ABLATION_REGISTRY

        ablation = ABLATION_REGISTRY.get(ablation_id)
        if ablation is not None:
            cfg = ablation.apply(cfg)
    rt = IntegratedRuntime(config=cfg, legacy_brain=legacy_brain)
    dil = data.get("day_in_the_life") or {}
    if cfg.day_in_the_life_mode == "integrated" and dil:
        rt.clock.seconds_per_tick = float(dil.get("seconds_per_tick", 300.0))
        if dil.get("ticks"):
            rt.config.ticks = int(dil["ticks"])
    return rt
