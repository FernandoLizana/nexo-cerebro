"""
Cerebro biológico abreviado: corteza E/I, hipocampo DG-CA3-CA1, moduladores, núcleos, personaje.
"""

from __future__ import annotations

import os
import time
from dataclasses import dataclass, field
from pathlib import Path

import numpy as np

from .companion import CompanionAgent
from .character import Persona, classify_intent
from .chemistry import PeerBond
from .cognition import CognitiveCycle
from .affect import AffectChemistry
from .imagination import ImaginationEngine
from .temporal import TemporalPerception
from .deliberation import PrefrontalDeliberation
from .intention import (
    deliberation_gate_context,
    enforce_pfc_motor_veto,
    hippocampus_stress_factor,
    merge_intention_into_sensory,
    prime_prefrontal_wm,
    record_spike_alignment,
    sync_basal_habits,
)
from .lobes import LobeRouter
from .lobe_cortex import LobeCorticalColumns
from .daytime_replay import DaytimeReplay
from .reflexes import BrainstemReflexes
from .curiosity import curiosity_drives
from .environment import apply_circadian_drives, circadian_profile
from .cortex import CorticalNetwork
from .encode import encode_file, encode_text, stimulus_id
from .embeddings import SemanticEmbedder
from .episodic_context import fuse_episodic_pattern
from .hippocampus_core import HippocampalFormation
from .neurotransmitters import NeuromodulatorState
from .nuclei import SubcorticalNuclei
from .oscillations import BrainOscillators
from .experiment_flags import AblationFlags, get_flags
from nexo.random_streams import RandomStreams
from nexo.simulation_clock import SimulationClock
from .td_reward import TDRewardSystem
from .grounding import (
    GroundingState,
    apply_utterance_grounding,
    merge_grounding_drives,
    merge_grounding_sensory,
    tick_grounding,
)
from .affordance_map import AffordanceMap
from .neural_telemetry import NeuralTelemetry
from .counterfactual_simulator import CounterfactualSimulator
from .causal_hud import build_causal_hud
from .observatory_hud import build_observatory_hud
from .learned_schemas import SchemaLearner
from .motor_policy import ContinuousMotorPolicy
from .profile import DEFAULT_PROFILE, INFANT_APE_PROFILE, NeuroProfile, resolve_default_profile
from .regions import Amygdala, Hippocampus, Hypothalamus, Thalamus
from .backend import get_backend
from .memory_store import EpisodicMemoryStore
from .virtual_assembly import VirtualAssemblyStore
from .verbalize import humanize_memory_label
from .working_memory import WorkingMemory
from .thoughts import ThoughtGenerator
from .body import BodyState
from .nociception import NociceptiveTerminal
from .biomechanics import BiomechanicalBody
from .hedonics import HedonicState
from .consciousness import ConsciousnessIntegrator
from .somatic_affordances import apply_somatic_contact
from .internal_signal import state_packet
from .journey import HeroJourney
from .lifecycle import LifecycleState
from .learning_hub import LearningEvent, LearningHub
from .library import import_file, list_books, read_book
from .neuroanatomy import BrainAtlas
from .archetype_cards import (
    LEGACY_SYMBOL_FIELD,
    card_from_object,
    card_key_from_meta,
    draw_card,
    get_card,
    is_archetype_card_meta,
    is_touch_event,
    reading_with_memories,
    recall_query,
)
from .language_cortex import LanguageContext, LanguageCortex
from .language_network import LanguageNetwork, tutor_from_env
from .caregiver_dialogue import is_fragmentary_speech, reply_engages_caregiver
from .vision import encode_visual, scan_world
from .world import World2D
from .persist import BrainPersistence
from .curriculum import CurriculumState, get_section, study_section
from .brain_facts import BrainFactsCorpus, get_chapter, study_chapter
from .anatomy_curriculum import AnatomyCorpus, get_section, study_anatomy_section
from .circuit_hub import CircuitHub
from .insula_module import InsulaCortex
from .cingulate_module import CingulateMonitor
from .brain_states import BrainStateController
from .sensory_hub import SensoryPathwayHub
from .sleep_architecture import SleepArchitecture
from .clinical_neurology import default_state as clinical_default, get_clinical_section, study_clinical_section
from .biopsych_curriculum import default_state as biopsych_default, get_biopsych_section, study_biopsych_section
from .infant_brain_curriculum import default_state as infant_default, get_infant_section, study_infant_section
from .sleep_study import SleepStudyEngine
from .memory_systems import TypedMemorySystems
from .regional_latency import RegionalSignalBus
from .scn_clock import SCNClock
from .sensory_perception import SensoryPerceptionStack
from .vision import SaccadeController, enrich_depth_2_5d
from .executive_cognition import ExecutiveCognitionStack
from .memory_dynamics import MemoryDynamicsStack
from .reward_learning import RewardLearningStack
from .affect_dynamics import AffectDynamicsStack
from .language_dynamics import LanguageDynamicsStack, study_tracks_snapshot
from .motor_dynamics import EmbodiedMotorStack
from .lifecycle_dynamics import LifecycleDynamicsStack
from .validation_dynamics import ValidationDynamicsStack
from .temporal_prediction import TemporalPredictor
from .agent_loop import NeuralAgentLoop
from .connectome_blueprint import ConnectomeBlueprint
from .decompression_governor import DecompressionGovernor
from .decompression_prefetch import DecompressionPrefetcher
from .cortical_chunks import CorticalChunkStore
from .subcortex import BasalGanglia, Brainstem, BrocaArea, Cerebellum

# Live user state when CEREBRO_STATE_DIR is unset. Tests must set the env var
# (see tests/conftest.py) so they never write here.
DEFAULT_STATE_DIR = Path(__file__).resolve().parent.parent / "data" / "brain_state"


def get_default_state_dir() -> Path:
    """Resolve the default brain state directory.

    Honours ``CEREBRO_STATE_DIR`` when set so callers (especially the test
    suite) can redirect persistence without patching module attributes.
    """
    override = os.environ.get("CEREBRO_STATE_DIR", "").strip()
    if override:
        return Path(override).expanduser()
    return DEFAULT_STATE_DIR


@dataclass
class InfantApeBrain:
    profile: NeuroProfile = field(default_factory=lambda: DEFAULT_PROFILE)
    seed: int = 0
    condition_id: str = "baseline"
    random_streams: RandomStreams | None = None
    sim_clock: SimulationClock = field(default_factory=SimulationClock)
    cortex: CorticalNetwork = field(init=False)
    hippo: HippocampalFormation = field(init=False)
    thalamus: Thalamus = field(init=False)
    hippocampus: Hippocampus = field(init=False)
    amygdala: Amygdala = field(init=False)
    hypothalamus: Hypothalamus = field(init=False)
    basal_ganglia: BasalGanglia = field(init=False)
    brainstem: Brainstem = field(init=False)
    cerebellum: Cerebellum = field(init=False)
    modulators: NeuromodulatorState = field(default_factory=NeuromodulatorState)
    oscillators: BrainOscillators = field(init=False)
    nuclei: SubcorticalNuclei = field(default_factory=SubcorticalNuclei)
    td_reward: TDRewardSystem = field(default_factory=TDRewardSystem)
    grounding: GroundingState = field(default_factory=GroundingState)
    affordance_map: AffordanceMap = field(default_factory=AffordanceMap)
    neural_telemetry: NeuralTelemetry = field(default_factory=NeuralTelemetry)
    counterfactual: CounterfactualSimulator = field(default_factory=CounterfactualSimulator)
    schema_learner: SchemaLearner = field(default_factory=SchemaLearner)
    motor_policy: ContinuousMotorPolicy = field(default_factory=ContinuousMotorPolicy)
    broca: BrocaArea = field(default_factory=BrocaArea)
    persona: Persona = field(default_factory=Persona)
    persistence: BrainPersistence = field(init=False)
    memory_store: EpisodicMemoryStore = field(init=False)
    virtual_store: VirtualAssemblyStore = field(init=False)
    world: World2D = field(init=False)
    thoughts: ThoughtGenerator = field(init=False)
    language: LanguageCortex = field(init=False)
    language_network: LanguageNetwork = field(init=False)
    embedder: SemanticEmbedder = field(init=False)
    working_memory: WorkingMemory = field(init=False)
    lifecycle: LifecycleState = field(default_factory=LifecycleState)
    journey: HeroJourney = field(default_factory=HeroJourney)
    chemistry: PeerBond = field(default_factory=PeerBond)
    offspring_agent: CompanionAgent | None = field(default=None, init=False)
    _last_ep: dict | None = field(default=None, init=False)
    _last_vision: dict | None = field(default=None, init=False)
    _pending_echoes: list[dict] = field(default_factory=list, init=False)
    _pending_echo_glimmer: str | None = field(default=None, init=False)
    _last_autonomy_log: list[str] = field(default_factory=list, init=False)
    _learning_log: list[str] = field(default_factory=list, init=False)
    _dialogue_log: list[dict] = field(default_factory=list, init=False)
    _verbal_dialogue_turn: dict | None = field(default=None, init=False)
    learning_hub: LearningHub = field(init=False)
    affect: AffectChemistry = field(init=False)
    imagination: ImaginationEngine = field(init=False)
    deliberation: PrefrontalDeliberation = field(init=False)
    temporal: TemporalPerception = field(init=False)
    atlas: BrainAtlas = field(default_factory=BrainAtlas)
    lobes: LobeRouter = field(default_factory=LobeRouter)
    lobe_cortex: LobeCorticalColumns = field(default_factory=LobeCorticalColumns)
    daytime_replay: DaytimeReplay = field(default_factory=DaytimeReplay)
    reflexes: BrainstemReflexes = field(default_factory=BrainstemReflexes)
    curriculum: CurriculumState = field(default_factory=CurriculumState)
    brain_facts: BrainFactsCorpus = field(default_factory=BrainFactsCorpus)
    anatomy: AnatomyCorpus = field(default_factory=AnatomyCorpus)
    clinical_neurology: TrackState = field(default_factory=clinical_default)
    biopsych: TrackState = field(default_factory=biopsych_default)
    infant_brain: TrackState = field(default_factory=infant_default)
    nociceptor: NociceptiveTerminal = field(default_factory=NociceptiveTerminal)
    biomech: BiomechanicalBody = field(default_factory=BiomechanicalBody)
    hedonics: HedonicState = field(default_factory=HedonicState)
    consciousness: ConsciousnessIntegrator = field(default_factory=ConsciousnessIntegrator)
    circuit_hub: CircuitHub = field(default_factory=CircuitHub)
    insula: InsulaCortex = field(default_factory=InsulaCortex)
    cingulate: CingulateMonitor = field(default_factory=CingulateMonitor)
    brain_states: BrainStateController = field(default_factory=BrainStateController)
    sensory_hub: SensoryPathwayHub = field(default_factory=SensoryPathwayHub)
    typed_memory: TypedMemorySystems = field(default_factory=TypedMemorySystems)
    sleep_arch: SleepArchitecture = field(default_factory=SleepArchitecture)
    sleep_study: SleepStudyEngine = field(default_factory=SleepStudyEngine)
    signal_bus: RegionalSignalBus = field(default_factory=RegionalSignalBus)
    scn_clock: SCNClock = field(default_factory=SCNClock)
    temporal_predictor: TemporalPredictor = field(default_factory=TemporalPredictor)
    sensory_stack: SensoryPerceptionStack = field(default_factory=SensoryPerceptionStack)
    saccades: SaccadeController = field(default_factory=SaccadeController)
    executive: ExecutiveCognitionStack = field(default_factory=ExecutiveCognitionStack)
    memory_dynamics: MemoryDynamicsStack = field(default_factory=MemoryDynamicsStack)
    reward_learning: RewardLearningStack = field(default_factory=RewardLearningStack)
    affect_dynamics: AffectDynamicsStack = field(default_factory=AffectDynamicsStack)
    language_dynamics: LanguageDynamicsStack = field(default_factory=LanguageDynamicsStack)
    motor_dynamics: EmbodiedMotorStack = field(default_factory=EmbodiedMotorStack)
    lifecycle_dynamics: LifecycleDynamicsStack = field(default_factory=LifecycleDynamicsStack)
    validation_dynamics: ValidationDynamicsStack = field(default_factory=ValidationDynamicsStack)
    _last_env: dict | None = field(default=None, init=False)
    body: BodyState = field(init=False)
    companion: CompanionAgent = field(init=False)
    auto_save: bool = True
    headless: bool = False
    state_dir: Path | None = None
    experiment_flags: AblationFlags = field(default_factory=AblationFlags)
    connectome: ConnectomeBlueprint = field(init=False)
    chunk_store: CorticalChunkStore | None = field(default=None, init=False)
    decompress_governor: DecompressionGovernor = field(default_factory=DecompressionGovernor)
    decompression_prefetch: DecompressionPrefetcher = field(default_factory=DecompressionPrefetcher)
    agent_loop: NeuralAgentLoop = field(init=False)
    _caregiver_vision: dict = field(default_factory=dict, init=False)
    _caregiver_listening: bool = field(default=False, init=False)
    relationship_model: object | None = field(default=None, init=False)

    def __post_init__(self) -> None:
        if self.random_streams is None:
            self.random_streams = RandomStreams.from_root_seed(self.seed)
        try:
            from .relationship_model import RelationshipModel

            self.relationship_model = RelationshipModel()
        except Exception:
            self.relationship_model = None
        sd = Path(self.state_dir) if self.state_dir is not None else get_default_state_dir()
        self.state_dir = sd
        self.persistence = BrainPersistence(sd)
        p = self.profile
        self.memory_store = EpisodicMemoryStore(
            sd,
            pattern_dim=p.n_sensory,
        )
        self.virtual_store = VirtualAssemblyStore(
            sd,
            pattern_dim=p.n_sensory,
            neurons_per_assembly=p.neurons_per_assembly,
            hot_size=p.virtual_hot_size,
            disk_search_limit=p.virtual_disk_search_limit,
            recall_k=p.virtual_recall_k,
            inject_gain=p.virtual_inject_gain,
            disk_budget_gb=p.virtual_disk_budget_gb,
            bytes_per_assembly=p.virtual_disk_bytes_per_assembly,
            lsh_bits=p.virtual_lsh_bits,
        )
        self.world = World2D()
        self.world.bind_rng(self.random_streams.world)
        self.thoughts = ThoughtGenerator()
        self.language = LanguageCortex()
        net = LanguageNetwork()
        net.tutor = tutor_from_env()
        self.language_network = net
        self.embedder = SemanticEmbedder()
        self.working_memory = WorkingMemory()
        self.working_memory.limited = bool(self.experiment_flags.enable_limited_wm)
        self.cognition = CognitiveCycle()
        self.learning_hub = LearningHub()
        self.affect = AffectChemistry()
        self.imagination = ImaginationEngine()
        self.deliberation = PrefrontalDeliberation()
        self.connectome = ConnectomeBlueprint(
            seed=p.connectome_seed,
            logical_neurons=p.logical_neuron_target,
        )
        chunk_root = sd / "connectome"
        self.chunk_store = CorticalChunkStore(
            blueprint=self.connectome,
            cache_dir=chunk_root,
            chunk_neurons=p.chunk_neurons,
            inject_gain=p.scaffold_inject_gain,
        )
        self.agent_loop = NeuralAgentLoop()
        self.temporal = TemporalPerception()
        self.typed_memory.bind_state_dir(sd)
        self.affordance_map.bind_state_dir(sd)
        self.sleep_study.attach_brain(self)
        if p.enable_scaffold_in_demo:
            from dataclasses import replace as _replace

            self.experiment_flags = _replace(
                self.experiment_flags, enable_connectome_scaffold=True
            )
        from dataclasses import replace

        flags = self.experiment_flags
        p = replace(
            p,
            enable_laminar_columns=p.enable_laminar_columns or flags.enable_laminar_columns,
            interneuron_subtypes=p.interneuron_subtypes or flags.enable_interneuron_subtypes,
            enable_vascular_coupling=p.enable_vascular_coupling or flags.enable_vascular_coupling,
        )
        self.profile = p
        self.decompress_governor.configure_lobe_budgets(p.lobe_decompress_bytes)
        from .vascular import CerebralVascularBed

        self.vascular = CerebralVascularBed() if p.enable_vascular_coupling else None
        self.body = BodyState()
        self.memory_store.attach_embedder(self.embedder)
        self.companion = self._spawn_companion()
        self.n_sensory = p.n_sensory
        self.cortex = CorticalNetwork(profile=p)
        self.lobe_cortex = LobeCorticalColumns(n_per_lobe=p.n_lobe_per_column)
        self.lobe_cortex.bind_cortex(self.cortex)
        self.hippo = HippocampalFormation(
            n_in=p.n_sensory,
            n_dg=p.n_dg,
            n_ca3=p.n_ca3,
            n_ca1=p.n_ca1,
            dg_sparsity=p.dg_sparsity,
        )
        self.oscillators = BrainOscillators(theta_hz=p.theta_hz, gamma_hz=p.gamma_hz)
        self.thalamus = Thalamus(
            n_out=self.n_sensory,
            gains={
                "text": 1.0,
                "image": 1.12,
                "document": 0.92,
                "audio": 1.08,
                "social": 1.22,
                "world": 1.05,
                "video": 1.12,
                "occipital": 1.15,
                "temporal": 1.08,
                "parietal": 1.05,
                "frontal": 1.12,
                "time": 0.92,
            },
        )
        self.hippocampus = Hippocampus(capacity=512)
        self.hippocampus.attach_store(self.memory_store)
        self.amygdala = Amygdala()
        self.hypothalamus = Hypothalamus(oxytocin=0.42)
        self.basal_ganglia = BasalGanglia(n_motor=p.n_motor)
        self.brainstem = Brainstem(arousal_bias=0.46)
        self.cerebellum = Cerebellum()
        self.persona.species_label = f"{p.name} · {p.age_label}"
        if get_backend().gpu_available:
            for syn in self.cortex.iter_synapses():
                syn.enable_gpu_matrices()
            for syn in (
                self.hippo.in_to_dg,
                self.hippo.dg_to_ca3,
                self.hippo.ca3_recur,
                self.hippo.ca3_to_ca1,
            ):
                syn.enable_gpu_matrices()
        self.language_dynamics.bind_brain(self)
        self.motor_dynamics.bind_continuous_motor(self)

    @property
    def n_total(self) -> int:
        return self.cortex.n_total + self.hippo.n_neurons + self.lobe_cortex.n_neurons

    @property
    def n_active(self) -> int:
        return self.n_total

    @property
    def n_virtual(self) -> int:
        return self.virtual_store.virtual_neuron_count()

    @property
    def n_virtual_max(self) -> int:
        return self.virtual_store.max_virtual_neurons

    def bootstrap_virtual_cortex(self) -> dict:
        """Indexa recuerdos episódicos existentes como ensambles en disco."""
        mem_n = self.memory_store.total_count()
        asm_n = self.virtual_store.total_count()
        if mem_n == 0:
            return {
                "ingested": 0,
                "reason": "sin memorias episódicas",
                "virtual_neurons": self.n_virtual,
            }
        if asm_n >= mem_n and asm_n > 0:
            return {
                "ingested": 0,
                "reason": "ya indexado",
                "assemblies": asm_n,
                "virtual_neurons": self.n_virtual,
                "max_virtual_neurons": self.n_virtual_max,
            }
        stats = self.virtual_store.bootstrap_from_memories(self.memory_store)
        stats["max_virtual_neurons"] = self.n_virtual_max
        stats["disk_budget_gb"] = self.profile.virtual_disk_budget_gb
        return stats

    def bootstrap_semantic_index(self, *, limit: int = 120) -> dict:
        """Indexa embeddings semánticos para recuerdos sin vector."""
        n = self.memory_store.backfill_embeddings(limit=limit)
        return {"backfilled": n, **self.embedder.status()}

    def _current_goal(self) -> str | None:
        if self.deliberation.last.drive_key:
            return self.deliberation.last.drive_key
        drives = self._merged_drives()
        if not drives:
            return None
        best = max(drives.items(), key=lambda x: x[1])
        return best[0] if best[1] > 0.25 else None

    def _merged_drives(self) -> dict[str, float]:
        stats = self.world.archetype_card_stats()
        from .node_offerings import unread_offerings

        drives = curiosity_drives(
            self.body,
            self.modulators,
            unseen_cards=stats.get("uninternalized", 0),
            internalized_cards=stats.get("internalized", 0),
            sleep_pressure=self.brainstem.sleep_pressure,
            valence=self.amygdala.valence,
            unread_shelf=len(unread_offerings()),
        )
        drives["sleep_need"] = float(max(0.0, self.brainstem.sleep_pressure - 0.45))
        drives["seek_companion"] = self.chemistry.seek_companion_drive()
        apply_circadian_drives(drives, self.world.ambient())
        for k, v in self.hedonics.drives().items():
            drives[k] = float(max(drives.get(k, 0.0), v))
        if self.hedonics.craving > 0.28:
            drives["seek_food"] = float(max(drives.get("seek_food", 0.0), self.hedonics.craving * 0.72))
        if get_flags(self).enable_grounding:
            drives = merge_grounding_drives(drives, self.grounding)
        return drives

    def _body_snapshot(self) -> dict:
        d = {**self.body.to_dict(), "nociception": self.nociceptor.to_dict()}
        feelings = list(d.get("feelings", []))
        seen = {f["signal"] for f in feelings}
        for hf in self.hedonics.feelings():
            if hf["signal"] not in seen:
                feelings.append(hf)
        feelings.sort(key=lambda x: -x["intensity"])
        d["feelings"] = feelings[:12]
        return d

    def _log_autonomy(self, msg: str) -> None:
        self._last_autonomy_log.append(msg[:120])
        if len(self._last_autonomy_log) > 12:
            self._last_autonomy_log.pop(0)

    def inject_echo(self, text: str) -> dict:
        """Eco auditivo → monólogo interior (no estímulo social)."""
        text = (text or "").strip()
        if not text:
            raise ValueError("Eco vacío")
        self._pending_echoes.append({"text": text[:200]})
        self._pending_echo_glimmer = text[:80]
        frag = self.thoughts.inject_fragment("echo", text[:80], 0.52)
        if get_flags(self).enable_grounding:
            apply_utterance_grounding(self, text, duration_ticks=6)
        self.working_memory.push(
            label=text[:60],
            modality="audio",
            room=self.world.current_room(),
            remembered=False,
            valence=0.0,
            goal="introspect",
            tags=["inner_echo", "phonological"],
        )
        return {
            "echo": True,
            "queued": len(self._pending_echoes),
            "fragment": frag,
            "thought_flow": self.thoughts.stream_snapshot(12),
            "autonomy_log": self._last_autonomy_log[-6:],
        }

    def ingest_caregiver_frame(self, image_bytes: bytes) -> dict:
        """Frame de webcam del cuidador → percepción visual de presencia."""
        if not image_bytes:
            raise ValueError("Imagen vacía")
        pattern, _mod = encode_file(image_bytes, "caregiver.jpg", self.n_sensory)
        mean = float(np.mean(pattern))
        prev = float(self._caregiver_vision.get("mean", mean))
        motion = abs(mean - prev) > 0.07
        gist = (
            "cuidador en cámara — se mueve"
            if motion
            else "cuidador en cámara — rostro presente"
        )
        self._caregiver_vision = {
            "ts": time.time(),
            "gist": gist,
            "mean": mean,
            "motion": motion,
        }
        self.working_memory.push(
            label=gist[:60],
            modality="vision",
            room=self.world.current_room(),
            remembered=False,
            valence=0.15,
            goal="perceive",
            tags=["caregiver", "camera", "social"],
        )
        self._log_autonomy("te ve en la cámara")
        return {
            "ok": True,
            "gist": gist,
            "caregiver_visible": True,
            "motion": motion,
        }

    def set_caregiver_listening(self, active: bool) -> dict:
        self._caregiver_listening = bool(active)
        if active:
            self._log_autonomy("escucha al cuidador (micrófono)")
        return {"listening": self._caregiver_listening}

    def caregiver_status(self) -> dict:
        cv = self._caregiver_vision or {}
        age = time.time() - float(cv.get("ts", 0)) if cv.get("ts") else None
        return {
            "listening": self._caregiver_listening,
            "visible": age is not None and age < 12.0,
            "vision_age_sec": round(age, 1) if age is not None else None,
            "gist": cv.get("gist", ""),
        }

    def caregiver_speak(self, text: str, *, voice_from_sky: bool = False) -> dict:
        """Voz/texto del cuidador → red Wernicke/Broca, sin órdenes motoras."""
        text = (text or "").strip()
        if not text:
            raise ValueError("Mensaje vacío")
        if self.language.enabled and not self.language.available:
            self.language.ping()
        if voice_from_sky:
            self._log_autonomy("una voz desde el cielo le habla…")
            self.hypothalamus.oxytocin = float(min(1.0, self.hypothalamus.oxytocin + 0.04))
        else:
            self._log_autonomy(f"te escuchó: {text[:48]}")

        intent = classify_intent(text)
        ground_meta = None
        if get_flags(self).enable_grounding or get_flags(self).enable_grounding_chat:
            ground_meta = apply_utterance_grounding(self, text, duration_ticks=10).to_dict()

        lctx_pre = self._language_context(
            user_message=text, intent=intent, mode="chat", caregiver_from_sky=voice_from_sky
        )

        pattern = encode_text(text, self.n_sensory)
        if get_flags(self).enable_grounding or get_flags(self).enable_grounding_chat:
            pattern = merge_grounding_sensory(pattern, self.grounding, gain=0.4)
        sensory = self.thalamus.relay({"social": pattern})
        ep = self._run_episode(
            sensory,
            modality="social",
            label=f"chat:{text[:36]}",
            repeats=1,
            steps_per_repeat=18,
            social=True,
            tags=["social", "caregiver", intent],
        )

        lctx = self._language_context(
            ep=ep,
            user_message=text,
            intent=intent,
            draft=self._state_draft(ep),
            mode="chat",
            last_thought=(self.thoughts.recent(1)[0]["text"] if self.thoughts.recent(1) else None),
            caregiver_from_sky=voice_from_sky,
        )

        exchange = self.language_network.caregiver_exchange(self, text, lctx, self.language)
        reply = exchange.reply
        if get_flags(self).enable_language_dynamics:
            reply = self.language_dynamics.post_articulate(self, reply, lctx, channel="outer")
        wernicke = {
            "intent_hint": exchange.comprehension.intent,
            "topics": exchange.comprehension.topics,
            "source": exchange.comprehension.source,
        }

        character = self.persona.converse(
            text, broca_reply=reply, hypothalamus=ep["hypothalamus"]
        )
        out = self._pack_result(ep, character, text.encode("utf-8"))
        out["caregiver"] = True
        out["voice_from_sky"] = voice_from_sky
        out["intent"] = exchange.comprehension.intent
        out["reply"] = reply
        out["character"]["message"] = reply
        out["language"] = {
            **self.language.status(),
            "source": exchange.source,
            "comprehension": wernicke,
            "network": {
                "wernicke": exchange.comprehension.source,
                "broca_plan": exchange.plan.intent,
                "tutor_learned": exchange.tutor_learned,
                "tutor_recalled": exchange.tutor_recalled,
                "learned_exemplars_used": len(exchange.plan.learned_exemplars),
                **self.language_network.status(self),
            },
        }
        out["body"] = self._body_snapshot()
        out["hedonics"] = self.hedonics.to_dict()
        out["biomechanics"] = self.biomech.to_dict()
        out["consciousness"] = self.consciousness.to_dict()
        out["drives"] = self._merged_drives()
        if ground_meta is not None:
            out["grounding"] = ground_meta
        return out

    def _integrate_echo(self) -> dict | None:
        if not self._pending_echoes:
            return None
        echo = self._pending_echoes.pop(0)
        raw_text = echo["text"]
        pattern = encode_text(raw_text, self.n_sensory).astype(np.float32) * 0.38
        sensory = self.thalamus.relay(
            {
                "audio": pattern,
                "world": self._world_sensory_vector() * 0.25,
            }
        )
        ep = self._run_episode(
            sensory,
            modality="audio",
            label=f"eco:{raw_text[:28]}",
            repeats=1,
            steps_per_repeat=20,
            social=False,
            tags=["inner_echo", "introspect", "phonological"],
        )
        self.thoughts.inject_fragment("echo", raw_text[:70], 0.58)
        self._log_autonomy(f"integró eco introspectivo: {raw_text[:40]}")
        return {"type": "echo_integrated", "text": raw_text[:60], "episode": ep.get("label")}

    def _semantic_text(
        self,
        label: str,
        modality: str,
        tags: list[str] | None = None,
    ) -> str:
        return self.embedder.memory_semantic_text(
            label=label,
            modality=modality,
            room=self.world.current_room(),
            body=self.body.to_dict(),
            tags=tags,
        )

    def _companion_near(self, *, radius: float = 90.0) -> bool:
        comp = getattr(self, "companion", None)
        if not comp:
            return False
        return float(
            np.hypot(comp.x - self.world.agent_x, comp.y - self.world.agent_y)
        ) < radius

    def _study_tracks_snapshot(self) -> dict:
        if get_flags(self).enable_curriculum_verbalization or get_flags(self).enable_language_dynamics:
            return study_tracks_snapshot(self)
        return {
            "clinical": self.clinical_neurology.to_dict(),
            "biopsych": self.biopsych.to_dict(),
            "infant": self.infant_brain.to_dict(),
        }

    def _cortical_snapshot(self) -> dict:
        def layer_mean(pop) -> float:
            denom = max(pop.v_thresh - pop.v_rest, 1.0)
            act = np.clip((pop.v - pop.v_rest) / denom, 0, 1.25)
            return round(float(act.mean()), 3)

        return {
            "sensory": layer_mean(self.cortex.sensory),
            "associative": layer_mean(self.cortex.associative),
            "prefrontal": layer_mean(self.cortex.prefrontal),
            "motor": layer_mean(self.cortex.motor),
            "working_memory_norm": round(float(np.linalg.norm(self.cortex._wm)), 3),
        }

    def _apply_social_chemistry(self, ep: dict, *, social: bool) -> None:
        if not social:
            label = (ep.get("label") or "").lower()
            if "nira" not in label and "companion" not in label and "con nira" not in label:
                return
        dist = float(np.hypot(self.companion.x - self.world.agent_x, self.companion.y - self.world.agent_y))
        self.chemistry.on_social_episode(
            valence=float(ep.get("valence", 0)),
            arousal=float(ep.get("arousal", 0)),
            dopamine=self.modulators.dopamine,
            proximity=float(np.clip(1.0 - dist / 90.0, 0, 1)),
        )
        self.chemistry.sync_to_hypothalamus(self.hypothalamus)
        self.chemistry.sync_persona_attachment(self.persona, self.companion.persona)
        self.companion.bond_with_nexo = self.chemistry.attraction

    def _state_draft(self, ep: dict, **kwargs) -> str:
        thought_packet = kwargs.pop("thought_packet", None)
        return state_packet(
            ep=ep,
            body=self._body_snapshot(),
            room=kwargs.pop("room", self.world.current_room()),
            world=kwargs.pop("world", self._world_dict()),
            motor=kwargs.pop("motor", ep.get("motor", [])),
            working_memory=self.working_memory.snapshot(),
            current_goal=self.working_memory.dominant_goal() or self._current_goal(),
            companion_present=self._companion_near(),
            modulators=self.modulators.to_dict(),
            chemistry=self.chemistry.to_dict(),
            cortical=self._cortical_snapshot(),
            consciousness=self.consciousness.to_dict(),
            thought_packet=thought_packet,
            **kwargs,
        )

    def add_library_book_to_desk(self, rel_path: str) -> dict:
        data, filename = read_book(rel_path)
        out = self.experience(data=data, filename=filename, label=filename, repeats=3)
        out["world"] = self._world_dict()
        return out

    def import_to_library(self, data: bytes, filename: str) -> dict:
        return import_file(data, filename)

    def draw_archetype_card(self) -> dict:
        card = draw_card()
        recalled = self.memory_store.recall_for_symbol(card.tags, recall_query(card), k=3)
        text = reading_with_memories(card, recalled)
        out = self.experience(text=text, label=f"◈ {card.name_es}", repeats=2, social=False)
        mem_key = out.get("memory", {}).get("key", "")
        self.world.add_archetype_card(
            card_key=card.key,
            name_es=card.name_es,
            memory_key=mem_key,
        )
        if card.key == "rebirth":
            self.lifecycle.apply_deep_transformation()
        out["symbol"] = card.to_dict()
        out["symbol_memories"] = [
            {"label": m.get("label"), "room": m.get("room"), "similarity": m.get("similarity")}
            for m in recalled
        ]
        out["world"] = self._world_dict()
        return out

    def bootstrap_archetype_deck(self) -> dict:
        from .archetype_cards import all_cards, legacy_object_ids, object_id_for

        added = 0
        existing = {o.id for o in self.world.objects}
        for card in all_cards():
            if object_id_for(card.key) in existing or existing & legacy_object_ids(card.key):
                continue
            self.world.add_archetype_card(card_key=card.key, name_es=card.name_es)
            added += 1
        return {"added": added, "total": len(all_cards())}

    def reproduce(self) -> dict:
        result = self.lifecycle.reproduce(
            nexo_name=self.persona.name,
            companion_name=self.companion.name,
            nexo_x=self.world.agent_x,
            nexo_y=self.world.agent_y,
        )
        if not result.get("ok"):
            return result
        o = self.lifecycle.offspring
        assert o
        self.offspring_agent = CompanionAgent(
            name=o["name"],
            species_label="infante",
            x=float(o["x"]),
            y=float(o["y"]),
        )
        self.offspring_agent.persona.species_label = f"hijo gen {o['generation']}"
        self.hypothalamus.oxytocin = min(1.0, self.hypothalamus.oxytocin + 0.15)
        sensory = self.thalamus.relay(
            {"social": encode_text(f"Nació {o['name']}, nuestro hijo", self.n_sensory)}
        )
        ep = self._run_episode(
            sensory,
            modality="social",
            label=f"nacimiento:{o['name']}",
            repeats=2,
            steps_per_repeat=40,
            social=True,
            tags=["lifecycle", "birth", "family"],
        )
        return {
            **result,
            "episode": ep,
            "world": self._world_dict(),
            "lifecycle": self.lifecycle.to_dict(),
        }

    def reborn(self) -> dict:
        """Nuevo ciclo tras la muerte (Juicio / renacimiento)."""
        gen = self.lifecycle.generation + 1
        self.lifecycle = LifecycleState(
            generation=gen,
            vitality=1.0,
            alive=True,
            parent_name=self.persona.name,
        )
        self.persona.mood = "curious"
        self.persona.message = "…algo despierta de nuevo…"
        self.body = BodyState()
        return {"reborn": True, "lifecycle": self.lifecycle.to_dict(), "world": self._world_dict()}

    def _spawn_offspring_if_needed(self) -> None:
        if self.lifecycle.offspring and not self.offspring_agent:
            o = self.lifecycle.offspring
            self.offspring_agent = CompanionAgent(
                name=o["name"],
                species_label="infante",
                x=float(o.get("x", 260)),
                y=float(o.get("y", 220)),
            )

    def _spawn_companion(self) -> CompanionAgent:
        c = CompanionAgent(
            name="Nira",
            species_label=self.profile.age_label,
            x=280.0,
            y=230.0,
        )
        c.persona.species_label = self.profile.age_label
        return c

    def ensure_companion(self) -> CompanionAgent:
        if not getattr(self, "companion", None):
            self.companion = self._spawn_companion()
        return self.companion

    def provide_care(
        self,
        *,
        bath: bool = True,
        feed: bool = True,
        bathroom: bool = True,
        drink: bool = True,
        companion: bool = True,
        move_to_bathroom: bool = True,
    ) -> dict:
        """Cuidado del cuidador: baño, comida, necesidades."""
        self.world.ensure_home()
        if move_to_bathroom:
            bc = self.world.furniture_center("bath")
            if bc:
                self.world.step_toward(bc[0], bc[1], max_steps=12)
                self.companion.x = bc[0] + 55
                self.companion.y = bc[1] + 10

        nexo_applied: list[str] = []
        if bath:
            self.body.bathe(0.65)
            self.nociceptor.gate_inhibition(0.22)
            self.nociceptor._project_to_body(self.body)
            nexo_applied.append("baño")
        if bathroom:
            self.body.relieve(0.7)
            nexo_applied.append("necesidades")
        if feed:
            self.body.eat(0.55)
            nexo_applied.append("comida")
        if drink:
            self.body.drink(0.45)
            nexo_applied.append("agua")

        comp_result = None
        if companion:
            comp_result = self.companion.apply_care(
                bath=bath, feed=feed, bathroom=bathroom, drink=drink
            )
            self.companion.persona.message = "Gracias… me siento mejor."
            self.persona.message = "Me bañaron, comí y me siento limpio."

        self.hypothalamus.oxytocin = float(
            np.clip(self.hypothalamus.oxytocin + 0.08, 0, 1)
        )
        self.persona.mood = "content"
        self.try_autosave()
        return {
            "care": True,
            "nexo": {"applied": nexo_applied, "body": self.body.to_dict()},
            "companion": comp_result,
            "world": self.world.with_companion(self.companion.to_dict()),
        }

    def _world_dict(self) -> dict:
        d = self.world.with_companion(self.companion.to_dict())
        d["lifecycle"] = self.lifecycle.to_dict()
        d["journey"] = self.journey.to_dict()
        d["chemistry"] = self.chemistry.to_dict()
        if self._last_vision:
            d["vision"] = self._last_vision
        d["biomechanics"] = self.biomech.to_dict()
        from .food_system import pantry_dict

        d["pantry"] = pantry_dict(self.world)
        if self.offspring_agent:
            d["offspring"] = self.offspring_agent.to_dict()
        return d

    def _rich_episodic_context(self) -> dict:
        """Olfato, afecto y postura para codificación episódica rica."""
        if not get_flags(self).enable_rich_episodic_context:
            return {}
        olf = (self.lobes.last or {}).get("olfaction") or {}
        _, prop_meta = self.sensory_stack.proprioception.integrate(self)
        return {
            "olfaction": olf,
            "affect": {
                "valence": float(getattr(self.amygdala, "valence", 0)),
                "arousal": float(getattr(self.amygdala, "arousal", 0)),
            },
            "posture": prop_meta,
        }

    def _episode_context(self, motor: list[int] | None = None) -> dict:
        return {
            "body": self.body.to_dict(),
            "room": self.world.current_room(),
            "motor": list(motor or []),
        }

    def _inject_virtual(
        self,
        sensory: np.ndarray,
        *,
        body: dict | None = None,
        room: str = "",
        motor: list[int] | None = None,
    ) -> tuple[np.ndarray, dict]:
        fused, _ = fuse_episodic_pattern(
            sensory,
            n=self.n_sensory,
            body=body or self.body.to_dict(),
            room=room or self.world.current_room(),
            motor=motor or [],
            n_motor=self.profile.n_motor,
        )
        injected, meta = self.virtual_store.inject(
            fused,
            k=self.profile.virtual_recall_k,
            governor=self.decompress_governor,
        )
        meta["multimodal"] = True
        meta["governor"] = self.decompress_governor.to_dict()
        # Fase 3: ensambles virtuales → columnas lobulares (no solo sensory)
        if get_flags(self).enable_lobe_virtual_inject:
            lobe_vecs, lobe_meta = self.virtual_store.inject_to_lobes(
                fused,
                n_per_lobe=self.profile.n_lobe_per_column,
                k=self.profile.virtual_recall_k,
                governor=self.decompress_governor,
            )
            self._virtual_lobe_vecs = lobe_vecs
            meta["lobe_inject"] = lobe_meta
        return injected, meta

    def _language_context(
        self,
        *,
        ep: dict | None = None,
        user_message: str = "",
        intent: str = "neutral",
        draft: str = "",
        mode: str = "chat",
        last_thought: str | None = None,
        thought_packet: dict | None = None,
        companion_speaker: bool = False,
        partner_line: str = "",
        thought_flow: list | None = None,
        caregiver_from_sky: bool = False,
    ) -> LanguageContext:
        ep = ep or {}
        hypo = ep.get("hypothalamus", {})
        prior = ep.get("prior")
        mems = [
            humanize_memory_label(m.get("label", ""))
            for m in self.hippocampus.list_recent(5)
            if m.get("label")
        ]
        visible = [
            o.get("label") or o.get("kind", "")
            for o in self.world.visible_objects()
            if o.get("label") or o.get("kind")
        ]
        comp = getattr(self, "companion", None)
        if companion_speaker and comp:
            bdict = comp.body.to_dict()
            mood = comp.persona.mood
            attachment = float(comp.persona.attachment)
            energy = float(comp.body.comfort)
        else:
            bdict = self._body_snapshot()
            mood = hypo.get("mood", self.persona.mood)
            attachment = float(self.persona.attachment)
            energy = float(hypo.get("energy", self.persona.energy))
        return LanguageContext(
            user_message=user_message,
            intent=intent,
            mood=mood,
            draft=draft,
            remembered=bool(ep.get("remembered")),
            memory_label=humanize_memory_label(prior.get("label", "")) if prior else None,
            recent_memories=mems,
            last_thought=last_thought,
            visible_world=visible,
            energy=energy,
            attachment=attachment,
            valence=float(ep.get("valence", 0)),
            arousal=float(ep.get("arousal", 0)),
            motor=list(ep.get("motor") or []),
            mode=mode,
            room=self.world.current_room(),
            body=bdict,
            drives=self._merged_drives() if not companion_speaker else {},
            feelings=bdict.get("feelings", []),
            tv=dict(self.world.tv_state),
            web=dict(self.world.web_state),
            working_memory=self.working_memory.snapshot(),
            current_goal=self.working_memory.dominant_goal() or self._current_goal(),
            companion_name=comp.name if comp else None,
            companion_present=self._companion_near(),
            modulators=self.modulators.to_dict(),
            chemistry=self.chemistry.to_dict(),
            thought_packet=thought_packet or {},
            vision=self._last_vision or {},
            thought_flow=thought_flow if thought_flow is not None else self.thoughts.stream_snapshot(10),
            cortical=self._cortical_snapshot(),
            consciousness=self.consciousness.to_dict(),
            dyad_speaker="nira" if companion_speaker else "nexo",
            partner_line=partner_line,
            caregiver_from_sky=caregiver_from_sky,
            study_tracks=self._study_tracks_snapshot() if not companion_speaker else {},
        )

    def _articulate(
        self,
        ctx: LanguageContext,
        *,
        kind: str = "express",
    ) -> tuple[str, str]:
        if kind == "thought":
            text, src = self.language.articulate_thought(ctx)
            if get_flags(self).enable_language_dynamics:
                text = self.language_dynamics.post_articulate(self, text, ctx, channel="inner")
            return text, src
        return self.language.express(ctx)

    def reset(self) -> None:
        name = self.persona.name
        self.cortex.reset()
        self.hippo.reset()
        self.hippocampus.clear()
        self.world = World2D()
        self.world.bind_rng(self.random_streams.world)
        self.thoughts = ThoughtGenerator()
        self.language = LanguageCortex()
        net = LanguageNetwork()
        net.tutor = tutor_from_env()
        self.language_network = net
        self.body = BodyState()
        self.companion = self._spawn_companion()
        self.amygdala = Amygdala()
        self.hypothalamus = Hypothalamus(oxytocin=0.42)
        self.modulators = NeuromodulatorState()
        self.oscillators = BrainOscillators(
            theta_hz=self.profile.theta_hz, gamma_hz=self.profile.gamma_hz
        )
        self.nuclei = SubcorticalNuclei()
        self.basal_ganglia.reset()
        self.brainstem = Brainstem(arousal_bias=0.46)
        self.cerebellum.reset()
        self.curriculum = CurriculumState()
        self.brain_facts = BrainFactsCorpus()
        self.clinical_neurology = clinical_default()
        self.biopsych = biopsych_default()
        self.infant_brain = infant_default()
        self.circuit_hub = CircuitHub()
        self.typed_memory = TypedMemorySystems()
        self.sleep_arch = SleepArchitecture()
        self.persona = Persona(name=name)
        self.persona.species_label = f"{self.profile.name} · {self.profile.age_label}"

    def encode_label(self, label: str) -> list[float]:
        return encode_text(label, self.n_sensory).tolist()

    def save_state(self) -> dict:
        return self.persistence.save(self)

    def load_state(self) -> dict:
        return self.persistence.load(self)

    def try_autosave(self) -> dict | None:
        if not self.auto_save:
            return None
        try:
            return self.save_state()
        except OSError:
            return None

    def activity_map(self, width: int = 48) -> dict:
        def hippo_row(pop) -> list[float]:
            denom = max(pop.v_thresh - pop.v_rest, 1.0)
            act = np.clip((pop.v - pop.v_rest) / denom, 0.0, 1.25).astype(np.float32)
            act[pop.spikes] = 1.0
            x_old = np.linspace(0.0, 1.0, act.size)
            x_new = np.linspace(0.0, 1.0, width)
            return np.interp(x_new, x_old, act).round(3).tolist()

        data = self.cortex.activity_map(width)
        data["regions"].extend(
            [
                {"id": "dg", "label": "Hipocampo DG", "values": hippo_row(self.hippo.dg)},
                {"id": "ca3", "label": "CA3", "values": hippo_row(self.hippo.ca3)},
                {"id": "ca1", "label": "CA1", "values": hippo_row(self.hippo.ca1)},
            ]
        )
        data["neuromodulators"] = self.modulators.to_dict()
        data["regions"].extend(self.lobe_cortex.activity_rows(width))
        return data

    def _oscillator_step(
        self,
        *,
        motor_pending: bool = False,
    ) -> tuple[float, float, str, float]:
        flags = get_flags(self)
        sleep_state = getattr(self.brain_states, "state", "awake") or "awake"
        if flags.enable_rhythm_pac or flags.enable_sleep_spindles:
            depth_map = {
                "awake": self.oscillators.sleep_depth,
                "nrem_light": 0.5,
                "nrem_deep": 0.85,
                "rem": 0.2,
                "sleep": 0.6,
            }
            self.oscillators.set_sleep_depth(depth_map.get(sleep_state, 0.0))
            snap = self.oscillators.step_full(
                sleep_state=sleep_state,
                motor_pending=motor_pending and flags.enable_rhythm_pac,
            )
            return snap.theta_amp, snap.gamma_amp, snap.mode, snap.delta_amp
        theta_amp, gamma_amp, mode = self.oscillators.step()
        return theta_amp, gamma_amp, mode, 0.0

    def _simulate(
        self,
        sensory: np.ndarray,
        *,
        total_steps: int,
        cortisol: float | None = None,
        motor_pending: bool = False,
    ) -> dict:
        snap: dict = {}
        stress = cortisol if cortisol is not None else self.hypothalamus.cortisol
        be = get_backend()
        be.begin_episode()
        use_gpu = be.want_gpu_for_episode(self.n_total, total_steps)
        self.cortex.set_gpu_forward(use_gpu)
        g = self.cortex.synaptic_gain * self.modulators.gain_scale()
        hippo_gain = g * 0.08 * hippocampus_stress_factor(stress)
        lobe_vecs = (self.lobes.last or {}).get("vectors") if hasattr(self, "lobes") else None
        virt_lobes = getattr(self, "_virtual_lobe_vecs", None)
        if virt_lobes and get_flags(self).enable_lobe_virtual_inject:
            if lobe_vecs:
                merged = {}
                for k in ("occipital", "temporal", "parietal", "frontal"):
                    a = np.asarray(lobe_vecs.get(k, np.zeros(1)), dtype=np.float32).ravel()
                    b = np.asarray(virt_lobes.get(k, np.zeros(1)), dtype=np.float32).ravel()
                    n = max(a.size, b.size)
                    if a.size < n:
                        a = np.pad(a, (0, n - a.size))
                    if b.size < n:
                        b = np.pad(b, (0, n - b.size))
                    merged[k] = np.clip(0.65 * a + 0.35 * b, 0, 1)
                lobe_vecs = merged
            else:
                lobe_vecs = virt_lobes
        try:
            for _ in range(total_steps):
                theta_amp, gamma_amp, mode, delta_amp = self._oscillator_step(
                    motor_pending=motor_pending,
                )
                # Columnas lobulares: demo siempre; headless si inyección virtual ON
                if lobe_vecs and (not self.headless or get_flags(self).enable_lobe_virtual_inject):
                    self.lobe_cortex.step(
                        self.cortex,
                        vectors=lobe_vecs,
                        gain=g * (0.07 if not self.headless else 0.045),
                    )
                hippo_ctx = self.hippo.step(
                    sensory,
                    gain=hippo_gain,
                    theta_amp=theta_amp,
                    mode=mode,
                    stress=stress,
                )
                self.cortex.set_stimulus(sensory.tolist(), hippo_ctx)
                snap = self.cortex.tick(
                    1,
                    use_stdp=not self.headless,
                    modulators=self.modulators,
                    theta_amp=theta_amp,
                    gamma_amp=gamma_amp,
                    delta_amp=delta_amp,
                    hippo_mode=mode,
                )
                if use_gpu and be._gpu_steps_this_episode >= be.max_gpu_steps:
                    self.cortex.set_gpu_forward(False)
                    use_gpu = False
        finally:
            self.cortex.set_gpu_forward(False)
            if use_gpu or be._gpu_steps_this_episode > 0:
                be.release_gpu()
        snap["compute"] = {
            "backend": be.label,
            "gpu_steps_used": be._gpu_steps_this_episode,
        }
        return snap

    def _run_episode(
        self,
        sensory: np.ndarray,
        *,
        modality: str,
        label: str,
        repeats: int,
        steps_per_repeat: int,
        social: bool = False,
        tags: list[str] | None = None,
        motor_bias: np.ndarray | None = None,
        bind_deliberation: bool = False,
        olfactory: np.ndarray | None = None,
        motor_pending: bool = False,
    ) -> dict:
        ep_ctx = self._episode_context(motor=[])
        raw_sensory = np.asarray(sensory, dtype=np.float32).copy()
        intention_meta = None
        gate_ctx = None
        if bind_deliberation and self.deliberation.last.choice_key:
            sensory, intention_meta = merge_intention_into_sensory(
                raw_sensory, self, self.deliberation
            )
            prime_prefrontal_wm(self, self.deliberation)
            gate_ctx = deliberation_gate_context(self.deliberation.last)
            if tags is not None:
                tags = list(tags) + [
                    "intention",
                    self.deliberation.last.choice_key,
                ]
        else:
            sensory = raw_sensory

        flags = get_flags(self)
        semantic_text = self._semantic_text(label, modality, tags)
        if flags.disable_hippocampus:
            prior = None
        else:
            prior = self.hippocampus.recall(
                raw_sensory,
                body=ep_ctx["body"],
                room=ep_ctx["room"],
                motor=ep_ctx["motor"],
                semantic_text=semantic_text,
                brain=self,
            )
        remembered = prior is not None
        sensory, virtual_meta = self._inject_virtual(
            sensory,
            body=ep_ctx["body"],
            room=ep_ctx["room"],
            motor=ep_ctx["motor"],
        )
        total = repeats * steps_per_repeat
        if not self.headless:
            self.atlas.prepare_episode(self)
        if olfactory is not None and olfactory.size:
            self.cortex.inject_olfactory(olfactory)
        snap = self._simulate(
            sensory,
            total_steps=total,
            cortisol=self.hypothalamus.cortisol,
            motor_pending=motor_pending,
        )

        raw = snap.get("spikes", {}).get("motor_raw", [])
        motor = self.basal_ganglia.gate(
            self.cortex.motor.v,
            self.cortex.motor.spikes,
            dopamine=self.modulators.dopamine,
            drive=float(self.amygdala.arousal),
            exploration=self.profile.motor_exploration,
            action_bias=motor_bias,
            deliberation=gate_ctx,
            pfc_inhibition=self.profile.prefrontal_inhibition,
            rng_seed=self.lifecycle.age_ticks,
        )
        pfc_veto = False
        if gate_ctx:
            motor, pfc_veto = enforce_pfc_motor_veto(
                motor, gate_ctx, n_motor=self.cortex.n_motor
            )
        if gate_ctx:
            sync_basal_habits(self, self.deliberation)
            if intention_meta is not None:
                intention_meta.pfc_veto = pfc_veto
                record_spike_alignment(
                    intention_meta,
                    motor_spikes=self.cortex.motor.spikes,
                    motor=motor,
                )
        if not motor and raw and not (gate_ctx and gate_ctx.get("inhibited")):
            motor = raw[: min(5, len(raw))]
        motor = self.cerebellum.integrate(motor)
        if motor:
            self.cortex.history_motor.append(motor)
            snap["last_motor_pattern"] = motor

        valence, arousal = self.amygdala.evaluate(
            sensory, modality, gain=self.profile.amygdala_gain, social=social
        )
        stem_arousal = self.brainstem.modulate(self.cortex.time_ms, self.hypothalamus.cortisol)
        arousal = float(np.clip(0.45 * arousal + 0.55 * stem_arousal, 0, 1))

        novelty = 0.1 if remembered else 0.9
        motor_reward = len(motor) / max(self.cortex.n_motor, 1)
        if flags.enable_td_reward:
            # Pulso fáxico desde δ previo (aprendizaje ocurre tras el acto en agent_loop).
            motor_reward = float(
                np.clip(0.55 * motor_reward + 0.45 * self.td_reward.dopamine_pulse(), 0, 1)
            )
        self.nuclei.step(
            self.modulators,
            valence=valence,
            arousal=arousal,
            novelty=novelty,
            motor_reward=motor_reward,
        )
        self.modulators.update(
            reward=self.nuclei.accumbens_activation,
            stress=float(np.clip(arousal * max(-valence, 0), 0, 1)),
            novelty=novelty,
            attention=float(self.modulators.acetylcholine),
            sleep_pressure=self.brainstem.sleep_pressure,
            social_bond=self.chemistry.attraction if social else 0.0,
        )

        surprise = 0.0
        if self.cognition.last_summary:
            surprise = float(self.cognition.last_summary.get("prediction", {}).get("surprise", 0))
        if not flags.disable_affect:
            self.affect.process_stimulus(
                valence=valence,
                arousal=arousal,
                novelty=novelty,
                pain=self.body.total_pain(),
                social_bond=self.chemistry.attraction if social else self.chemistry.proximity * 0.4,
                attention=float(self.modulators.acetylcholine),
                surprise=surprise,
            )
            self.affect.step()
            self.affect.sync_modulators(self.modulators)
            if flags.enable_affect_dynamics:
                stress = float(np.clip(arousal * max(-valence, 0), 0, 1))
                self.affect_dynamics.post_stimulus(self, stress=stress)

        if flags.disable_hippocampus:
            memory = {"key": "", "count": 0}
        else:
            rich = self._rich_episodic_context()
            memory = self.hippocampus.consolidate(
                raw_sensory,
                label=label,
                modality=modality,
                motor=motor,
                valence=valence,
                arousal=arousal,
                tags=tags,
                body=self.body.to_dict(),
                room=self.world.current_room(),
                olfaction=rich.get("olfaction"),
                affect=rich.get("affect"),
                posture=rich.get("posture"),
            )
            if flags.enable_memory_dynamics:
                self.memory_dynamics.on_encode(
                    self,
                    memory,
                    label=label,
                    valence=valence,
                    arousal=arousal,
                    tags=tags,
                )

        hypo = self.hypothalamus.update(
            valence=valence,
            arousal=arousal,
            novelty=novelty,
            motor_activity=len(motor) / max(self.cortex.n_motor, 1),
            remembered=remembered,
            hour=float(self.world.ambient().get("hour", 12)),
            circadian=flags.enable_circadian,
        )
        if not flags.disable_affect:
            self.affect.sync_hypothalamus(self.hypothalamus, valence=valence, arousal=arousal)
            valence = float(np.clip(0.55 * valence + 0.45 * self.affect.subjective_valence(), -1, 1))
            arousal = float(np.clip(0.5 * arousal + 0.5 * self.affect.subjective_arousal(), 0, 1))
        hypo["mood"] = self.hypothalamus._mood_label(valence, arousal)
        if self.brainstem.sleep_pressure > 0.82:
            hypo["mood"] = "sleepy"

        goal = self._current_goal()
        self.working_memory.set_goal(goal)
        self.working_memory.push(
            label=label,
            modality=modality,
            room=self.world.current_room(),
            remembered=remembered,
            valence=valence,
            goal=goal,
            tags=tags,
        )

        ep_result = {
            "snap": snap,
            "sensory": sensory,
            "modality": modality,
            "label": label,
            "remembered": remembered,
            "prior": prior,
            "memory": memory,
            "valence": valence,
            "arousal": arousal,
            "hypothalamus": hypo,
            "motor": motor,
            "virtual": virtual_meta,
            "tags": tags,
            "context": {
                "room": self.world.current_room(),
                "body": self.body.to_dict(),
            },
        }
        if intention_meta is not None:
            ep_result["intention_circuit"] = intention_meta.to_dict()
            ep_result["deliberation"] = self.deliberation.last.to_dict()
        if self.lobes.last:
            ep_result["lobes"] = self.lobes.to_dict()
        self._apply_social_chemistry(ep_result, social=social)
        mem_sys = self.typed_memory.after_episode(
            self,
            label=label,
            tags=list(tags or []),
            modality=modality,
            motor=motor,
            room=self.world.current_room(),
            valence=valence,
            remembered=remembered,
        )
        ep_result["memory_system"] = mem_sys
        self._last_ep = ep_result
        return ep_result

    def sleep(
        self,
        cycles: int = 3,
        steps_per_cycle: int = 120,
        *,
        replay_mode: str | None = None,
    ) -> dict:
        """Sueño NREM/REM con replay SWR y consolidación por fases."""
        arch_out = self.sleep_arch.run(
            self,
            cycles=cycles,
            steps_per_cycle=steps_per_cycle,
            replay_mode=replay_mode,
        )
        replays = arch_out["replays"]
        consolidated = arch_out["consolidation"]
        virtual_ingested = arch_out["virtual_ingested"]
        labels_replayed = arch_out["labels_replayed"]
        replay_weights = arch_out["replay_weights"]
        virtual_stats = self.virtual_store.sleep_consolidate()
        tutor_sleep = self.language_network.consolidate_tutor_on_sleep(self)
        sleep_study_out = self.sleep_study.run_sleep_session(self, max_actions=1)
        dream_sequence = self._build_dream_sequence(labels_replayed, consolidated)
        nira_associations: list[dict] = []
        dyad_learning: dict = {"nira_receptive": False, "promoted": False}
        try:
            from .dyad_learning import nira_receptive_step

            prior_pool = [
                str(lab) for lab in labels_replayed if lab
            ] + [
                str(c.get("label", ""))
                for c in consolidated
                if isinstance(c, dict) and c.get("label")
            ]
            if not prior_pool:
                prior_pool = ["silencio", "casa"]
            for i, dream in enumerate(dream_sequence[:6]):
                experience = str(dream.get("text") or dream)[:120]
                prior = prior_pool[i % len(prior_pool)][:120]
                if not experience:
                    continue
                rec = nira_receptive_step(
                    experience=experience,
                    prior_memory=prior,
                    authorized=True,
                )
                # Symbolic associations stay unverified; never auto-promote.
                nira_associations.append(rec.to_dict())
            dyad_learning = {
                "nira_receptive": True,
                "associations": len(nira_associations),
                "promoted": False,
                "kinds": [a.get("kind") for a in nira_associations],
            }
        except ImportError:
            pass
        except Exception:
            dyad_learning = {"nira_receptive": False, "promoted": False, "error": True}
        # Persist for observatory /api/dyad/learning (real sleep output only).
        self._nira_associations = list(nira_associations)[-24:]
        self._dyad_learning = dict(dyad_learning)
        self.modulators.update(
            reward=0.25,
            stress=0.04,
            novelty=0.08,
            attention=0.12,
            sleep_pressure=self.brainstem.sleep_pressure,
        )
        self.brainstem.rest(0.4)
        self.typed_memory.save()
        self.persona.mood = "sleepy"
        lctx = self._language_context(
            draft=self._state_draft(
                {"hypothalamus": {"mood": "sleepy"}, "valence": 0.2, "arousal": 0.2, "remembered": True},
            ),
            mode="sleep",
        )
        msg, _ = self.language.express(lctx)
        self.persona.message = msg
        saved = self.try_autosave()

        return {
            "slept": True,
            "cycles": cycles,
            "replays": replays,
            "consolidation": consolidated,
            "labels_replayed": labels_replayed,
            "replay_weights": replay_weights,
            "dreams": dream_sequence,
            "nira_associations": nira_associations,
            "dyad_learning": dyad_learning,
            "sleep_mode": arch_out.get("sleep_mode", "nrem_rem_architecture"),
            "replay_mode": arch_out.get("replay_mode", "default"),
            "active_forgetting": arch_out.get("active_forgetting", 0),
            "sleep_phases": arch_out.get("phase_log", []),
            "swr_bursts": arch_out.get("swr_bursts", 0),
            "virtual_assemblies": {
                "ingested": virtual_ingested,
                "consolidation": virtual_stats,
                "total": self.virtual_store.total_count(),
                "virtual_neurons": self.n_virtual,
            },
            "language_tutor_sleep": tutor_sleep,
            "sleep_study": sleep_study_out,
            "sleep_study_log": self.sleep_study.to_dict(),
            "sleep_pressure": round(self.brainstem.sleep_pressure, 3),
            "character": self.persona.to_dict(),
            "neuromodulators": self.modulators.to_dict(),
            "persistence": saved,
            "world": {
                **self._world_dict(),
                "dream_mode": True,
                "dreams": dream_sequence,
            },
        }

    def _build_dream_sequence(
        self,
        labels: list[str],
        consolidated: list[dict],
    ) -> list[dict]:
        """Fragmentos oníricos mezclados para la UI."""
        pool: list[str] = []
        pool.extend(labels)
        pool.extend(c.get("label", "") for c in consolidated if c.get("label"))
        if not pool:
            pool = ["casa", "Nira", "jardín", "silencio"]
        rng = np.random.default_rng(int(self.cortex.time_ms) % 100000)
        chosen = list(pool)
        rng.shuffle(chosen)
        dreams: list[dict] = []
        for i, label in enumerate(chosen[:8]):
            dreams.append(
                {
                    "text": str(label)[:48],
                    "x": float(rng.uniform(40, self.world.width - 40)),
                    "y": float(rng.uniform(50, self.world.height - 60)),
                    "drift": float(rng.uniform(-0.4, 0.4)),
                    "alpha": float(rng.uniform(0.35, 0.85)),
                    "hue": int(rng.integers(240, 300)),
                }
            )
        return dreams

    def _scan_vision(self) -> dict:
        if self.headless:
            vision = {"scene_gist": "", "objects": [], "headless": True}
            self._last_vision = vision
            return vision
        off = self.offspring_agent.to_dict() if self.offspring_agent else None
        env = self.world.ambient()
        vision = scan_world(
            self.world,
            companion=self.companion.to_dict(),
            offspring=off,
            light_level=float(env.get("light_level", 1.0)),
        )
        felt = (env.get("temporal") or {}).get("felt") or env.get("clock", "")
        if felt and vision.get("scene_gist"):
            vision["scene_gist"] = f"{vision['scene_gist']} · {felt}"
        if get_flags(self).enable_advanced_sensory:
            vision = enrich_depth_2_5d(vision)
        if get_flags(self).enable_saccadic_vision:
            vision = self.saccades.apply(vision, tick=self.lifecycle.age_ticks)
        cv = self._caregiver_vision or {}
        if cv.get("ts") and time.time() - float(cv["ts"]) < 12.0:
            cgist = str(cv.get("gist", "cuidador presente"))
            vision["caregiver"] = {"visible": True, "gist": cgist}
            vision["foveal"] = list(vision.get("foveal") or [])
            vision["foveal"].insert(
                0,
                {
                    "id": "caregiver_cam",
                    "kind": "caregiver",
                    "label": "Cuidador",
                    "interpretation": cgist,
                    "salience": 0.85,
                    "zone": "fovea",
                    "modality": "social",
                    "distance": 30.0,
                    "angle_deg": 0.0,
                },
            )
            base = vision.get("scene_gist") or ""
            if "cuidador" not in base.lower():
                vision["scene_gist"] = f"{base} · {cgist}".strip(" ·")
        self._last_vision = vision
        gist = vision.get("scene_gist", "")
        if gist:
            self.working_memory.push(
                label=gist[:60],
                modality="world",
                room=self.world.current_room(),
                remembered=False,
                valence=0.0,
                goal="perceive",
                tags=["vision", "percept"],
            )
        return vision

    def learning_multiplier(self) -> float:
        return float(max(1.0, self.world.clock.learning_multiplier))

    def configure_time(self, data: dict) -> dict:
        c = self.world.clock
        if data.get("realtime") is True:
            c.use_realtime()
        elif data.get("realtime") is False:
            c.realtime = False
        if "paused" in data:
            c.paused = bool(data["paused"])
        if "time_scale" in data:
            c.time_scale = float(np.clip(float(data["time_scale"]), 0.25, 120.0))
        if "turbo" in data:
            c.turbo = bool(data["turbo"])
            if c.turbo:
                c.realtime = False
                c.paused = False
                c.time_scale = max(c.time_scale, 30.0)
                c.learning_multiplier = max(c.learning_multiplier, 4.0)
                c.minutes_per_tick = max(c.minutes_per_tick, 12.0)
            else:
                c.learning_multiplier = float(
                    np.clip(float(data.get("learning_multiplier", 1.0)), 1.0, 12.0)
                )
        elif "learning_multiplier" in data:
            c.learning_multiplier = float(
                np.clip(float(data["learning_multiplier"]), 1.0, 12.0)
            )
        if "minutes_per_tick" in data:
            c.minutes_per_tick = float(np.clip(float(data["minutes_per_tick"]), 0.5, 60.0))
        if "hour" in data:
            c.set_sim_time(int(data["hour"]), int(data.get("minute", 0)))
        if "minute" in data and "hour" not in data:
            h = c.current_dt().hour if hasattr(c, "current_dt") else 12
            c.set_sim_time(h, int(data["minute"]))
        if "seek_minutes" in data:
            c.seek_minutes(int(data["seek_minutes"]))
        if "sim_day_offset" in data:
            c.sim_day_offset = max(0, int(data["sim_day_offset"]))
        self._last_env = self.world.ambient()
        self.temporal.observe(self._last_env)
        return self.time_state()

    def time_state(self) -> dict:
        env = self.world.ambient()
        temporal = self.temporal.last_observe or self.temporal.observe(env)
        circ = (self._last_env or {}).get("circadian")
        if circ is None and get_flags(self).enable_circadian:
            circ = circadian_profile(env)
        return {
            "clock": self.world.clock.to_dict(),
            "environment": env,
            "temporal": temporal,
            "circadian": circ,
        }

    def _world_sensory(self) -> tuple[np.ndarray, np.ndarray]:
        intero = self.body.encode(self.n_sensory)
        noc = self.nociceptor.encode(max(8, self.n_sensory // 12))
        prop = self.biomech.encode(max(8, self.n_sensory // 14))
        if noc.size and intero.size:
            n = min(len(intero), len(noc))
            intero[:n] = np.clip(intero[:n] + noc[:n] * 0.42, 0, 1)
        if prop.size and intero.size:
            n = min(len(intero), len(prop))
            intero[:n] = np.clip(intero[:n] + prop[:n] * 0.35, 0, 1)
        raw = self.world.encode_perception(self.n_sensory, interoception=intero)
        vision = self._last_vision or self._scan_vision()
        env = self._last_env or self.world.ambient()
        temporal = self.temporal.encode(max(8, self.n_sensory // 32), env)
        sensory, olfactory, _ = self.lobes.route(
            self,
            world_raw=raw,
            vision=vision,
            temporal=temporal,
            intero=intero,
            ambient=env,
        )
        stack_out: dict = {}
        if get_flags(self).enable_advanced_sensory:
            stack_out = self.sensory_stack.tick(self, vision=vision)
            sensory = self.sensory_stack.blend_sensory(self, sensory, stack=stack_out)
            if stack_out.get("meta"):
                self.sensory_hub.last_modalities = list(
                    set(self.sensory_hub.last_modalities + list(stack_out["meta"].keys()))
                )[:10]
        if get_flags(self).enable_multimodal_delays:
            self.sensory_hub.use_delays = True
            audio_pat = stack_out.get("audio_pat")
            if audio_pat is None:
                from .encode import encode_text

                audio_pat = encode_text(
                    self._pending_echo_glimmer or env.get("phase", "day"),
                    self.n_sensory,
                )
            prop_pat = stack_out.get("prop_pat")
            if prop_pat is None:
                prop_pat = prop if prop.size else intero
            fused, fuse_meta = self.sensory_hub.fuse_patterns(
                vision_pat=sensory,
                audio_pat=audio_pat,
                proprio_pat=prop_pat,
                n=self.n_sensory,
            )
            sensory = np.clip(0.55 * sensory + 0.45 * fused, 0, 1)
            self.sensory_hub.last_fusion = fuse_meta
        if get_flags(self).enable_grounding:
            sensory = merge_grounding_sensory(sensory, self.grounding)
        return sensory, olfactory

    def _world_sensory_vector(self) -> np.ndarray:
        sensory, _ = self._world_sensory()
        return sensory

    def _learning_agents(self, radius: float = 68.0) -> list[str]:
        agents = ["nexo"]
        if self._companion_near(radius=radius):
            agents.append("nira")
        return agents

    def _nexo_episode_from_learn(self, learn_result: dict) -> dict | None:
        for item in learn_result.get("episode_list", []):
            if item.get("agent") == "nexo":
                return item.get("episode")
        return None

    def _handle_world_event(self, ev: dict, last_ep: dict | None) -> dict:
        from .youtube_tool import search as yt_search

        et = ev.get("type")
        if et == "harvest":
            from .food_system import harvest_crop

            result = harvest_crop(self.world, str(ev.get("object_id", "")))
            if result:
                self.hedonics.reward(
                    "harvest",
                    0.38,
                    label=result.get("label", "cosecha"),
                    affect=self.affect,
                )
                self.body.comfort = float(np.clip(self.body.comfort + 0.06, 0, 1))
                self._log_autonomy(f"cosechó {result.get('label', 'cultivo')}")
                label = f"cosechar {result.get('label', 'cultivo')}"
            else:
                label = "cosecha fallida"
            sensory = self._world_sensory_vector()
            return self._run_episode(
                sensory,
                modality="world",
                label=label,
                repeats=1,
                steps_per_repeat=20,
                tags=["world", "harvest", "garden"],
            )
        if et == "cook":
            from .food_system import cook_meal

            meal = cook_meal(self.world)
            if meal:
                self.hedonics.reward(
                    "cook",
                    0.42,
                    label=meal.get("label", "comida"),
                    affect=self.affect,
                )
                self._log_autonomy(f"cocinó {meal.get('label', 'comida')}")
                label = f"cocinar {meal.get('label', 'comida')}"
            else:
                label = "cocina vacía"
            sensory = self._world_sensory_vector()
            return self._run_episode(
                sensory,
                modality="world",
                label=label,
                repeats=1,
                steps_per_repeat=24,
                tags=["world", "cook", "kitchen"],
            )
        if et == "eat_cooked":
            from .food_system import eat_cooked

            meal = eat_cooked(self.world)
            if meal:
                amt = float(meal.get("amount", 0.35))
                self.body.eat(amt)
                self.body.drink(0.1)
                self.hedonics.reward(
                    "eat_cooked",
                    float(meal.get("pleasure_bonus", 0.42)),
                    label=meal.get("label", "comida"),
                    affect=self.affect,
                )
                self._log_autonomy(f"comió {meal.get('label', 'comida cocida')}")
                label = f"comer {meal.get('label', 'comida cocida')}"
            else:
                self.body.eat(0.4)
                self.body.drink(0.15)
                self.hedonics.reward("eat_cooked", 0.25, label="nevera", affect=self.affect)
                label = "comer en casa"
            sensory = self._world_sensory_vector()
            return self._run_episode(
                sensory,
                modality="world",
                label=label,
                repeats=1,
                steps_per_repeat=22,
                tags=["world", "eat", "meal"],
            )
        if et == "eat":
            label_src = str(ev.get("target", "nevera"))
            self.body.eat(0.45)
            if str(ev.get("object_type", "")) != "food_bowl":
                self.body.drink(0.2)
            self.hedonics.reward(
                "eat_raw",
                0.22,
                label=label_src,
                affect=self.affect,
            )
            sensory = self._world_sensory_vector()
            return self._run_episode(
                sensory,
                modality="world",
                label=f"comer de {label_src}",
                repeats=1,
                steps_per_repeat=22,
                tags=["world", "eat", str(ev.get("object_type", "fridge"))],
            )
        if et == "drink":
            oid = str(ev.get("object_id") or "")
            dry = bool(ev.get("dry")) or self.world.is_object_dry(oid)
            if dry:
                # Fallo causal: intentó beber y no hubo alivio.
                self.body.comfort = float(max(0.0, self.body.comfort - 0.02))
                sensory = self._world_sensory_vector()
                return self._run_episode(
                    sensory,
                    modality="world",
                    label=f"beber seco de {ev.get('target', 'fuente')}",
                    repeats=1,
                    steps_per_repeat=12,
                    tags=["world", "drink", "dry", str(ev.get("object_type", "fountain"))],
                )
            self.body.drink(0.42)
            self.hedonics.reward("drink", 0.2, label=str(ev.get("target", "agua")), affect=self.affect)
            sensory = self._world_sensory_vector()
            return self._run_episode(
                sensory,
                modality="world",
                label=f"beber de {ev.get('target', 'fuente')}",
                repeats=1,
                steps_per_repeat=18,
                tags=["world", "drink", str(ev.get("object_type", "water_source"))],
            )
        if et == "bathe":
            self.body.bathe(0.5)
            self.nociceptor.gate_inhibition(0.18)
            self.nociceptor._project_to_body(self.body)
            sensory = self._world_sensory_vector()
            return self._run_episode(
                sensory,
                modality="world",
                label="baño en casa",
                repeats=1,
                steps_per_repeat=24,
                tags=["world", "bath", "hygiene"],
            )
        if et == "bathroom":
            self.body.relieve(0.55)
            sensory = self._world_sensory_vector()
            return self._run_episode(
                sensory,
                modality="world",
                label="baño (necesidades)",
                repeats=1,
                steps_per_repeat=18,
                tags=["world", "bathroom"],
            )
        if et == "rest":
            amb = self.world.ambient()
            hour = int(amb.get("hour", 12))
            at_night = amb.get("phase") == "night" or hour >= 22 or hour < 6
            self.body.rest(0.45 if at_night else 0.3)
            rest_amt = 0.26 if at_night and self.brainstem.sleep_pressure > 0.65 else 0.08
            self.brainstem.rest(rest_amt)
            if at_night and self.brainstem.sleep_pressure > 0.78:
                self._log_autonomy(f"durmió en la cama ({amb.get('clock', '')})")
                sleep_out = self.sleep(cycles=2, steps_per_cycle=90)
                return {
                    "hypothalamus": {
                        "mood": "sleepy",
                        "energy": round(self.hypothalamus.energy, 3),
                    },
                    "valence": 0.12,
                    "arousal": 0.16,
                    "remembered": sleep_out.get("replays", 0) > 0,
                    "motor": [],
                    "label": "sueño NREM/REM",
                    "sleep": sleep_out,
                }
            if at_night and self.brainstem.sleep_pressure > 0.72:
                self._log_autonomy(f"descansó en la cama ({amb.get('clock', '')})")
            sensory = self._world_sensory_vector()
            return self._run_episode(
                sensory,
                modality="world",
                label="descansar",
                repeats=1,
                steps_per_repeat=20,
                tags=["world", "rest"],
            )
        if et == "tv_use":
            lctx = self._language_context(ep=last_ep or {}, mode="world")
            query, _ = self.language.suggest_youtube_query(lctx)
            results = yt_search(query, limit=3)
            if results:
                pick = results[0]
                self.world.set_tv_playing(
                    query=query,
                    title=pick["title"],
                    video_id=pick["video_id"],
                    url=pick["url"],
                )
                agents = self.learning_hub.agents_near_tv(self)
                content = f"Búsqueda YouTube: {query}. Título: {pick['title']}."
                lr = self.learning_hub.learn(
                    self,
                    LearningEvent(
                        source="youtube",
                        label=pick["title"][:70],
                        content=content,
                        modality="video",
                        tags=["world", "tv", "youtube", f"q:{query[:18]}"],
                        agents=agents,
                        steps_per_repeat=36,
                    ),
                )
                ep = self._nexo_episode_from_learn(lr) or last_ep or {
                    "hypothalamus": {"mood": self.persona.mood},
                    "valence": 0.1,
                    "arousal": 0.4,
                    "remembered": lr.get("learned", {}).get("remembered", False),
                    "motor": [],
                    "label": pick["title"][:50],
                }
                ep["youtube"] = {"query": query, **pick}
                return ep
            return self._run_episode(
                self._world_sensory_vector(),
                modality="world",
                label="tv sin señal",
                repeats=1,
                steps_per_repeat=18,
                tags=["world", "tv"],
            )
        if et == "web_search":
            from .web_fetch import fetch_page_text
            from .web_search import format_for_learning, search as web_search_fn

            lctx = self._language_context(ep=last_ep or {}, mode="world")
            query, _ = self.language.suggest_web_query(lctx)
            payload = web_search_fn(query, limit=8)
            results = payload.get("results") or []
            if results:
                self.world.set_web_session(
                    query=query,
                    provider=str(payload.get("provider", "web")),
                    results=results,
                )
                content = format_for_learning(payload)
                top = results[0]
                page = fetch_page_text(str(top.get("url", "")))
                if page:
                    content = content + "\n\nExtracto:\n" + page[:1600]
                learn_steps = int(32 * self.learning_multiplier())
                lr = self.learning_hub.learn(
                    self,
                    LearningEvent(
                        source="google",
                        label=f"Web: {top.get('title', query)[:60]}",
                        content=content,
                        modality="text",
                        tags=["world", "web", "internet", "google", f"q:{query[:18]}"],
                        agents=self._learning_agents(55),
                        steps_per_repeat=learn_steps,
                    ),
                )
                ep = self._nexo_episode_from_learn(lr) or last_ep or {
                    "hypothalamus": {"mood": self.persona.mood},
                    "valence": 0.12,
                    "arousal": 0.42,
                    "remembered": lr.get("learned", {}).get("remembered", False),
                    "motor": [],
                    "label": top.get("title", query)[:50],
                }
                ep["web"] = {"query": query, "provider": payload.get("provider"), "results": results[:3]}
                self._log_autonomy(f"buscó en la web: {query[:40]}")
                return ep
            return self._run_episode(
                self._world_sensory_vector(),
                modality="world",
                label="web sin resultados",
                repeats=1,
                steps_per_repeat=18,
                tags=["world", "web"],
            )
        if et == "curriculum_study":
            key = ev.get("section_key")
            section = get_section(key) if key else self.curriculum.suggest_next()
            if not section:
                return last_ep or self._run_episode(
                    self._world_sensory_vector(),
                    modality="world",
                    label="currículo vacío",
                    repeats=1,
                    steps_per_repeat=16,
                    tags=["curriculum"],
                )
            result = study_section(self, section)
            lr = result.get("learning", {})
            ep = self._nexo_episode_from_learn(lr) or last_ep or {
                "hypothalamus": {"mood": self.persona.mood},
                "valence": 0.15,
                "arousal": 0.45,
                "remembered": lr.get("learned", {}).get("remembered", False),
                "motor": [],
                "label": section.title[:50],
            }
            ep["curriculum"] = result.get("section")
            self._log_autonomy(f"estudió lección {section.n}: {section.title[:36]}")
            self._learning_log.append(f"📚 {section.title}")
            if len(self._learning_log) > 12:
                self._learning_log.pop(0)
            return ep
        if et == "brain_facts_study":
            key = ev.get("chapter_key")
            chapter = get_chapter(key) if key else self.brain_facts.suggest_next()
            if not chapter:
                return last_ep or self._run_episode(
                    self._world_sensory_vector(),
                    modality="world",
                    label="Brain Facts vacío",
                    repeats=1,
                    steps_per_repeat=16,
                    tags=["brain_facts"],
                )
            result = study_chapter(self, chapter)
            lr = result.get("learning", {})
            ep = self._nexo_episode_from_learn(lr) or last_ep or {
                "hypothalamus": {"mood": self.persona.mood},
                "valence": 0.18,
                "arousal": 0.48,
                "remembered": lr.get("learned", {}).get("remembered", False),
                "motor": [],
                "label": chapter.title[:50],
            }
            ep["brain_facts"] = result.get("chapter")
            ep["circuits"] = result.get("circuits")
            self._log_autonomy(f"leyó Brain Facts: {chapter.title[:40]}")
            self._learning_log.append(f"📖 {chapter.title}")
            if len(self._learning_log) > 12:
                self._learning_log.pop(0)
            return ep
        if et == "anatomy_study":
            key = ev.get("section_key")
            section = get_section(key) if key else self.anatomy.suggest_next()
            if not section:
                return last_ep or self._run_episode(
                    self._world_sensory_vector(),
                    modality="world",
                    label="Anatomía vacía",
                    repeats=1,
                    steps_per_repeat=16,
                    tags=["anatomy"],
                )
            result = study_anatomy_section(self, section)
            lr = result.get("learning", {})
            ep = self._nexo_episode_from_learn(lr) or last_ep or {
                "hypothalamus": {"mood": self.persona.mood},
                "valence": 0.16,
                "arousal": 0.46,
                "remembered": lr.get("learned", {}).get("remembered", False),
                "motor": [],
                "label": section.title[:50],
            }
            ep["anatomy_book"] = result.get("section")
            self._log_autonomy(f"leyó Anatomía: {section.title[:40]}")
            self._learning_log.append(f"🦴 {section.title}")
            if len(self._learning_log) > 12:
                self._learning_log.pop(0)
            return ep
        if et == "clinical_study":
            key = ev.get("section_key")
            section = get_clinical_section(key) if key else self.clinical_neurology.suggest_next()
            if not section:
                return last_ep or self._run_episode(
                    self._world_sensory_vector(),
                    modality="world",
                    label="Manual UDD vacío",
                    repeats=1,
                    steps_per_repeat=16,
                    tags=["clinical"],
                )
            result = study_clinical_section(self, section)
            lr = result.get("learning", {})
            ep = self._nexo_episode_from_learn(lr) or last_ep or {
                "hypothalamus": {"mood": self.persona.mood},
                "valence": 0.08,
                "arousal": 0.52,
                "remembered": lr.get("learned", {}).get("remembered", False),
                "motor": [],
                "label": section.title[:50],
            }
            ep["clinical_neurology"] = result.get("section")
            self._log_autonomy(f"estudió clínica: {section.title[:36]}")
            self._learning_log.append(f"🏥 {section.title}")
            if len(self._learning_log) > 12:
                self._learning_log.pop(0)
            return ep
        if et == "biopsych_study":
            key = ev.get("section_key")
            section = get_biopsych_section(key) if key else self.biopsych.suggest_next()
            if not section:
                return last_ep or self._run_episode(
                    self._world_sensory_vector(),
                    modality="world",
                    label="Biopsych vacío",
                    repeats=1,
                    steps_per_repeat=16,
                    tags=["biopsych"],
                )
            result = study_biopsych_section(self, section)
            lr = result.get("learning", {})
            ep = self._nexo_episode_from_learn(lr) or last_ep or {
                "hypothalamus": {"mood": self.persona.mood},
                "valence": 0.14,
                "arousal": 0.44,
                "remembered": lr.get("learned", {}).get("remembered", False),
                "motor": [],
                "label": section.title[:50],
            }
            ep["biopsych"] = result.get("section")
            self._log_autonomy(f"estudió biopsych: {section.title[:36]}")
            self._learning_log.append(f"🧬 {section.title}")
            if len(self._learning_log) > 12:
                self._learning_log.pop(0)
            return ep
        if et == "infant_study":
            key = ev.get("section_key")
            section = get_infant_section(key) if key else self.infant_brain.suggest_next()
            if not section:
                return last_ep or self._run_episode(
                    self._world_sensory_vector(),
                    modality="world",
                    label="Libro infantil vacío",
                    repeats=1,
                    steps_per_repeat=16,
                    tags=["infant_brain"],
                )
            result = study_infant_section(self, section)
            lr = result.get("learning", {})
            ep = self._nexo_episode_from_learn(lr) or last_ep or {
                "hypothalamus": {"mood": self.persona.mood},
                "valence": 0.22,
                "arousal": 0.36,
                "remembered": lr.get("learned", {}).get("remembered", False),
                "motor": [],
                "label": section.title[:50],
            }
            ep["infant_brain"] = result.get("section")
            self._log_autonomy(f"leyó infantil: {section.title[:36]}")
            self._learning_log.append(f"🧒 {section.title}")
            if len(self._learning_log) > 12:
                self._learning_log.pop(0)
            return ep
        if et == "node_study":
            from .node_offerings import take_offering

            item = take_offering((ev.get("meta") or {}).get("offering_id"))
            if not item:
                return last_ep or self._run_episode(
                    self._world_sensory_vector(),
                    modality="world",
                    label="el estante de nodos está vacío",
                    repeats=1,
                    steps_per_repeat=12,
                    tags=["node"],
                )
            from .collective_capacity import learn_offering

            learned = learn_offering(self, item, via="curiosidad")
            lr = learned["learned"]
            name = str(item.get("name") or "material")
            who = str(item.get("source") or "nodo")
            text = str(item.get("text") or "")
            ep = self._nexo_episode_from_learn(lr) or last_ep or {
                "hypothalamus": {"mood": self.persona.mood},
                "valence": 0.18,
                "arousal": 0.4,
                "remembered": lr.get("learned", {}).get("remembered", False),
                "motor": [],
                "label": name[:50],
            }
            self._log_autonomy(f"quiso aprender de {who}: {name[:36]}")
            self._learning_log.append(f"nodo · {name[:40]}")
            if len(self._learning_log) > 12:
                self._learning_log.pop(0)
            return ep
        if et == "library_study":
            from .text_extract import extract_plain_text

            books = list_books()
            if not books:
                return last_ep or self._run_episode(
                    self._world_sensory_vector(),
                    modality="world",
                    label="biblioteca vacía",
                    repeats=1,
                    steps_per_repeat=14,
                    tags=["library"],
                )
            rel = ev.get("book_path") or books[0]["path"]
            name = str(rel)
            text = ""
            try:
                data, fn = read_book(str(rel))
                name = fn
                text = extract_plain_text(data, fn)
            except OSError:
                pass
            if not text.strip():
                text = f"Libro: {name}. (PDF escaneado — contenido ilustrado pendiente de OCR.)"
            lr = self.learning_hub.learn(
                self,
                LearningEvent(
                    source="library",
                    label=f"📂 {name[:48]}",
                    content=text[:8000],
                    modality="text",
                    tags=["library", "escritorio", f"book:{rel[:24]}"],
                    agents=self._learning_agents(50),
                    steps_per_repeat=28,
                ),
            )
            ep = self._nexo_episode_from_learn(lr) or last_ep or {
                "hypothalamus": {"mood": self.persona.mood},
                "valence": 0.16,
                "arousal": 0.42,
                "remembered": lr.get("learned", {}).get("remembered", False),
                "motor": [],
                "label": name[:50],
            }
            ep["library"] = {"path": rel, "name": name}
            self._log_autonomy(f"leyó biblioteca: {name[:36]}")
            self._learning_log.append(f"📂 {name[:40]}")
            if len(self._learning_log) > 12:
                self._learning_log.pop(0)
            return ep
        if is_touch_event(et):
            meta = ev.get("meta") or {}
            card = get_card(
                ev.get("symbol_key") or ev.get(LEGACY_SYMBOL_FIELD) or card_key_from_meta(meta)
            )
            if not card:
                card = card_from_object(ev.get("object_id", ""), ev.get("label", ""))
            if not card:
                return last_ep or self._run_episode(
                    self._world_sensory_vector(), modality="world", label="toque vacío", repeats=1, steps_per_repeat=18
                )
            recalled = self.memory_store.recall_for_symbol(card.tags, recall_query(card), k=3)
            text = reading_with_memories(card, recalled)
            lr = self.learning_hub.learn(
                self,
                LearningEvent(
                    source="archetype_card",
                    label=f"◈ {card.name_es}",
                    content=text,
                    modality="text",
                    tags=[*card.tags, "archetype_card", "internalized", "curiosity"],
                    agents=self._learning_agents(55),
                    steps_per_repeat=38,
                ),
            )
            ep = self._nexo_episode_from_learn(lr) or last_ep or {
                "hypothalamus": {"mood": self.persona.mood},
                "valence": 0.1,
                "arousal": 0.45,
                "remembered": lr.get("learned", {}).get("remembered", False),
                "motor": [],
                "label": card.name_es,
            }
            ep["valence"] = float(np.clip(ep.get("valence", 0) + card.valence * 0.35, -1, 1))
            ep["arousal"] = float(np.clip(ep.get("arousal", 0) + card.arousal * 0.25, 0, 1))
            ep["symbol"] = card.to_dict()
            ep["symbol_memories"] = [
                {"label": m.get("label"), "room": m.get("room"), "similarity": m.get("similarity")}
                for m in recalled
            ]
            personal = text[:180]
            self.world.mark_archetype_internalized(ev.get("object_id", ""), personal=personal)
            self.thoughts.inject_fragment("archetype_card", f"{card.name_es} — {card.concept}", 0.68)
            self._log_autonomy(f"tocó e interiorizó {card.name_es} (curiosidad)")
            if card.key == "rebirth":
                self.lifecycle.apply_deep_transformation()
            return ep
        if et in ("read", "touch"):
            meta = ev.get("meta") or {}
            if is_archetype_card_meta(meta):
                return last_ep
            card = card_from_object(ev.get("object_id", ""), ev.get("label", ""))
            if card:
                recalled = self.memory_store.recall_for_symbol(card.tags, recall_query(card), k=3)
                content = reading_with_memories(card, recalled)
                label = f"◈ {card.name_es}"
                source = "archetype_card"
                tags = ["world", et, *card.tags]
            else:
                content, label = self.learning_hub.resolve_book_content(self, ev)
                source = "book"
                tags = ["world", et, "read"]
                recalled = []
                if "brain facts" in label.lower() or "brain_facts" in str(ev.get("memory_key", "")).lower():
                    chapter = self.brain_facts.suggest_next()
                    if chapter:
                        result = study_chapter(self, chapter)
                        lr = result.get("learning", {})
                        ep = self._nexo_episode_from_learn(lr) or last_ep or {}
                        ep["brain_facts"] = result.get("chapter")
                        ep["circuits"] = result.get("circuits")
                        self._log_autonomy(f"leyó Brain Facts: {chapter.title[:40]}")
                        return ep
            lr = self.learning_hub.learn(
                self,
                LearningEvent(
                    source=source,
                    label=label[:80],
                    content=content,
                    modality=ev.get("modality", "text"),
                    tags=tags,
                    agents=self._learning_agents(),
                    steps_per_repeat=34,
                ),
            )
            ep = self._nexo_episode_from_learn(lr) or last_ep or {
                "hypothalamus": {"mood": self.persona.mood},
                "valence": 0.05,
                "arousal": 0.35,
                "remembered": lr.get("learned", {}).get("remembered", False),
                "motor": [],
                "label": label[:50],
            }
            if card:
                ep["valence"] = float(np.clip(ep.get("valence", 0) + card.valence * 0.35, -1, 1))
                ep["arousal"] = float(np.clip(ep.get("arousal", 0) + card.arousal * 0.25, 0, 1))
                ep["symbol"] = card.to_dict()
                ep["symbol_memories"] = [
                    {"label": m.get("label"), "room": m.get("room"), "similarity": m.get("similarity")}
                    for m in recalled
                ]
            return ep
        if et == "journey_ordeal":
            sensory = self._world_sensory_vector()
            ordeal = ev.get("ordeal") or {}
            return self._run_episode(
                sensory,
                modality="world",
                label=ordeal.get("label", "prueba del héroe"),
                repeats=1,
                steps_per_repeat=42,
                tags=list(ordeal.get("tags", ["journey", "ordeal"])),
            )
        if et in ("journey_ordeal_start", "journey_reward", "journey_cycle_complete"):
            sensory = self.thalamus.relay(
                {"social": encode_text(f"Etapa del camino: {ev.get('type', '')}", self.n_sensory)}
            )
            return self._run_episode(
                sensory,
                modality="social",
                label=f"journey:{ev.get('type', 'stage')}",
                repeats=1,
                steps_per_repeat=34,
                tags=["journey", ev.get("type", "stage")],
            )
        if et == "lifecycle_death":
            self.persona.mood = "sleepy"
            self.persona.message = f"…{self.lifecycle.death_cause}…"
            sensory = self._world_sensory_vector()
            return self._run_episode(
                sensory,
                modality="world",
                label=f"fin del ciclo: {self.lifecycle.death_cause}",
                repeats=1,
                steps_per_repeat=30,
                tags=["lifecycle", "death", self.lifecycle.death_cause or "unknown"],
            )
        if last_ep:
            return last_ep
        sensory = self._world_sensory_vector()
        return self._run_episode(
            sensory,
            modality="world",
            label=f"entorno@{self.world.current_room()}",
            repeats=1,
            steps_per_repeat=20,
            tags=["world"],
        )

    def _world_tick_headless(self, *, steps: int = 1) -> dict:
        """Deprecated — usar agent_loop.run."""
        return self.agent_loop.run(self, steps=steps)

    def world_tick(self, *, steps: int = 1) -> dict:
        """Paso autónomo en el hogar: cuerpo + percepción + acción + sentir."""
        try:
            from .collective_capacity import notice

            self._collective = notice(self)
        except Exception:
            self._collective = {"error": "notice skipped"}
        return self.agent_loop.run(self, steps=steps)

    def think(self, ep: dict | None = None, *, vision: dict | None = None) -> dict:
        ep = ep or self._last_ep or {
            "hypothalamus": {
                "mood": self.persona.mood,
                "energy": self.hypothalamus.energy,
                "oxytocin": self.hypothalamus.oxytocin,
            },
            "valence": self.amygdala.valence,
            "arousal": self.amygdala.arousal,
            "remembered": False,
            "motor": [],
        }
        raw = self.thoughts.generate(self, ep=ep, vision=vision or self._last_vision)
        draft = self._state_draft(ep, thought_packet=raw.get("packet"))
        lctx = self._language_context(
            ep=ep,
            draft=draft,
            mode="thought",
            last_thought=raw.get("draft"),
            thought_packet=raw.get("packet"),
        )
        text, src = self._articulate(lctx, kind="thought")
        raw["text"] = text
        raw["language_source"] = src
        return raw

    def experience(
        self,
        *,
        data: bytes | None = None,
        filename: str = "",
        text: str | None = None,
        label: str = "",
        tags: list[str] | None = None,
        repeats: int = 4,
        steps_per_repeat: int = 75,
        social: bool = False,
    ) -> dict:
        repeats = max(1, min(repeats, 12))
        steps_per_repeat = max(20, min(steps_per_repeat, 220))

        if text is not None:
            pattern = encode_text(text, self.n_sensory)
            modality = "social" if social else "text"
            data = (text or "").encode("utf-8")
            label = label or (text[:40] + ("…" if len(text) > 40 else ""))
        elif data is not None:
            pattern, modality = encode_file(data, filename, self.n_sensory)
            label = label or filename or stimulus_id(data, modality)
        else:
            raise ValueError("Se requiere 'text' o datos de archivo")

        label = str(label)[:120]
        sensory = self.thalamus.relay({modality: pattern})
        ep = self._run_episode(
            sensory,
            modality=modality,
            label=label,
            repeats=repeats,
            steps_per_repeat=steps_per_repeat,
            social=social,
            tags=tags,
        )
        draft_reply = None
        draft = self._state_draft(ep)
        if self.headless:
            draft_reply, feel_text = "", ""
        else:
            lctx = self._language_context(ep=ep, draft=draft, mode="experience", user_message=label)
            draft_reply, _ = self._articulate(lctx)
            feel_text, _ = self.language.describe_feelings(lctx)

        character = self.persona.react(
            hypothalamus=ep["hypothalamus"],
            valence=ep["valence"],
            arousal=ep["arousal"],
            modality=ep["modality"],
            label=label,
            remembered=ep["remembered"],
            motor=ep["motor"],
            memory_hit=ep["memory"] if ep["remembered"] else None,
            reply=draft_reply,
        )
        if modality != "world":
            self.world.add_stimulus_object(
                label=label,
                modality=modality,
                memory_key=ep["memory"]["key"],
            )
        out = self._pack_result(ep, character, data or b"")
        out["body"] = self.body.to_dict()
        out["feelings_text"] = feel_text
        out["language"] = self.language.status()
        out["world"] = self._world_dict()
        return out

    def interact(self, message: str, *, caregiver_from_sky: bool = False) -> dict:
        message = (message or "").strip()
        if not message:
            raise ValueError("Mensaje vacío")

        intent = classify_intent(message)
        if get_flags(self).enable_grounding:
            apply_utterance_grounding(self, message, duration_ticks=8)
        lctx_pre = self._language_context(user_message=message, intent=intent, mode="chat")
        wernicke = self.language.comprehend(message, lctx_pre)
        intent = wernicke.get("intent_hint", intent)
        extra_tags = ["social", intent] + [f"topic:{t}" for t in wernicke.get("topics", [])]

        for hit in self.memory_store.semantic_search(message, k=3, threshold=0.58):
            self.working_memory.push(
                label=hit.get("label", "?"),
                modality=hit.get("modality", "social"),
                room=hit.get("room", ""),
                remembered=True,
                valence=float(hit.get("valence", 0)),
                goal=self._current_goal(),
                tags=hit.get("tags"),
            )

        pattern = encode_text(message, self.n_sensory)
        if get_flags(self).enable_grounding and self.grounding.sensory_trace is not None:
            pattern = merge_grounding_sensory(pattern, self.grounding, gain=0.35)
        sensory = self.thalamus.relay({"social": pattern})
        label = f"chat:{message[:36]}"

        ep = self._run_episode(
            sensory,
            modality="social",
            label=label,
            repeats=2,
            steps_per_repeat=55,
            social=True,
            tags=extra_tags,
        )

        draft = self._state_draft(
            ep,
            thought=(self.thoughts.recent(1)[0]["text"] if self.thoughts.recent(1) else None),
        )
        lctx = self._language_context(
            ep=ep,
            user_message=message,
            intent=intent,
            draft=draft,
            mode="chat",
            last_thought=(self.thoughts.recent(1)[0]["text"] if self.thoughts.recent(1) else None),
            caregiver_from_sky=caregiver_from_sky,
        )
        reply, lang_src = self._articulate(lctx)
        if message and (
            lang_src in ("internal", "broca")
            or is_fragmentary_speech(reply)
            or not reply_engages_caregiver(message, reply)
        ):
            reply = self.language.caregiver_reply_fallback(lctx)
            lang_src = "caregiver_fallback"

        character = self.persona.converse(
            message, broca_reply=reply, hypothalamus=ep["hypothalamus"]
        )
        out = self._pack_result(ep, character, message.encode("utf-8"))
        out["intent"] = intent
        out["reply"] = reply
        out["language"] = {
            **self.language.status(),
            "source": lang_src,
            "comprehension": wernicke,
        }
        return out

    def user_interact(
        self,
        *,
        action: str = "call",
        target: str = "",
        message: str = "",
        x: float | None = None,
        y: float | None = None,
    ) -> dict:
        """Modo observador: el cuidador no mueve ni ordena a Nexo."""
        raise ValueError(
            "Modo autónomo: Nexo no recibe órdenes motoras. "
            "Usa /api/echo para sembrar un eco introspectivo."
        )

    def _pack_result(self, ep: dict, character: dict, data: bytes) -> dict:
        mem = ep["memory"]
        prior = ep["prior"]
        out = {
            "label": ep["label"],
            "modality": ep["modality"],
            "stimulus_id": stimulus_id(data, ep["label"]),
            "remembered": ep["remembered"],
            "valence": round(ep["valence"], 3),
            "arousal": round(ep["arousal"], 3),
            "hypothalamus": ep["hypothalamus"],
            "neuromodulators": self.modulators.to_dict(),
            "character": character,
            "reply": character.get("message"),
            "cortex": ep["snap"],
            "brain": {
                "profile": self.profile.name,
                "neurons_active": self.n_active,
                "neurons_virtual": self.n_virtual,
                "neurons": self.n_active,
                "hippocampus_neurons": self.hippo.n_neurons,
                "interneurons": ep["snap"].get("interneurons", 0),
                "basal_ganglia_habit_norm": round(float(np.linalg.norm(self.basal_ganglia.habit)), 3),
                "sleep_pressure": round(self.brainstem.sleep_pressure, 3),
                "accumbens": round(self.nuclei.accumbens_activation, 3),
                "td_reward": self.td_reward.to_dict() if get_flags(self).enable_td_reward else None,
            },
            "memory": {
                "key": mem["key"],
                "count": mem.get("count", 1),
                "similarity": prior.get("similarity") if prior else None,
            },
            "hippocampus_size": self.hippocampus.size,
            "memories_recent": self.hippocampus.list_recent(),
            "memory_disk": {
                "total": self.hippocampus.size,
                "hot_cache": len(self.memory_store.hot_entries),
                "path": str(self.persistence.base_dir / "memories"),
            },
            "virtual_cortex": {
                "assemblies": self.virtual_store.total_count(),
                "virtual_neurons": self.n_virtual,
                "max_virtual_neurons": self.n_virtual_max,
                "neurons_per_assembly": self.profile.neurons_per_assembly,
                "recalled_last": ep.get("virtual", {}),
                "disk": self.virtual_store.disk_usage_bytes(),
                "recent": self.virtual_store.list_recent(4),
                "decompress_governor": self.decompress_governor.to_dict(),
                "decompression_prefetch": self.decompression_prefetch.to_dict(),
                "path": str(self.persistence.base_dir / "assemblies"),
            },
            "language_cortex": self.language.status(),
        }
        if self.auto_save:
            saved = self.try_autosave()
            if saved:
                out["persistence"] = saved
        return out

    def snapshot(self) -> dict:
        if not self.consciousness.winners:
            try:
                self.cognition.run(
                    self,
                    vision=self._last_vision,
                    drives=self._merged_drives(),
                    ambient=self.world.ambient(),
                )
            except Exception:
                pass
        return {
            "time_ms": self.cortex.time_ms,
            "neurons_active": self.n_active,
            "neurons_virtual": self.n_virtual,
            "neurons": self.n_active,
            "profile": {"name": self.profile.name, "age_label": self.profile.age_label},
            "neuromodulators": self.modulators.to_dict(),
            "cortex": self.cortex.snapshot(),
            "hypothalamus": {
                "mood": Hypothalamus._mood_label(self.amygdala.valence, self.amygdala.arousal),
                "dopamine": round(self.hypothalamus.dopamine, 3),
                "cortisol": round(self.hypothalamus.cortisol, 3),
                "oxytocin": round(self.hypothalamus.oxytocin, 3),
                "energy": round(self.hypothalamus.energy, 3),
                "sleep_pressure": round(self.brainstem.sleep_pressure, 3),
                "circadian": (self._last_env or {}).get("circadian"),
            },
            "character": self.persona.to_dict(),
            "memories": self.hippocampus.list_recent(),
            "world": self._world_dict(),
            "body": self._body_snapshot(),
            "nociception": self.nociceptor.to_dict(),
            "biomechanics": self.biomech.to_dict(),
            "hedonics": self.hedonics.to_dict(),
            "consciousness": self.consciousness.to_dict(),
            "companion": self.companion.to_dict(),
            "thoughts_recent": self.thoughts.recent(4),
            "memory_disk": {
                "total": self.hippocampus.size,
                "hot_cache": len(self.memory_store.hot_entries),
            },
            "virtual_cortex": {
                "assemblies": self.virtual_store.total_count(),
                "virtual_neurons": self.n_virtual,
                "max_virtual_neurons": self.n_virtual_max,
                "disk_budget_gb": self.profile.virtual_disk_budget_gb,
                "disk": self.virtual_store.disk_usage_bytes(),
                "decompress_governor": self.decompress_governor.to_dict(),
                "decompression_prefetch": self.decompression_prefetch.to_dict(),
            },
            "connectome_scaffold": {
                **self.connectome.to_dict(),
                "active_neurons": self.n_active,
                "chunks": self.chunk_store.stats() if self.chunk_store else {},
            },
            "agent_loop": self.agent_loop.state.to_dict(),
            "goal_stack": self.agent_loop.goal_stack.to_dict(),
            "language_cortex": self.language.status(),
            "persistence": {"exists": self.persistence.exists()},
            "compute": get_backend().label,
            "neuroanatomy": self.atlas.update(self),
            "brain_facts": self.brain_facts.to_dict(),
            "anatomy_book": self.anatomy.to_dict(),
            "clinical_neurology": self.clinical_neurology.to_dict(),
            "biopsych": self.biopsych.to_dict(),
            "infant_brain": self.infant_brain.to_dict(),
            "circuits": self.circuit_hub.to_dict(),
            "typed_memory": self.typed_memory.to_dict(),
            "sleep_architecture": self.sleep_arch.to_dict(),
            "signal_bus": self.signal_bus.to_dict(),
            "oscillators": self.oscillators.to_dict(),
            "scn_clock": self.scn_clock.to_dict(),
            "temporal_prediction": self.temporal_predictor.to_dict(),
            "sensory_perception": self.sensory_stack.to_dict(),
            "saccades": {
                "count": self.saccades.saccade_count,
                "last_target": self.saccades.last_target,
                "shift_deg": round(self.saccades.gaze_shift_deg, 1),
            },
            "executive_cognition": self.executive.to_dict(),
            "memory_dynamics": self.memory_dynamics.to_dict(),
            "reward_learning": self.reward_learning.to_dict(),
            "affect_dynamics": self.affect_dynamics.to_dict(),
            "language_dynamics": self.language_dynamics.to_dict(),
            "motor_dynamics": self.motor_dynamics.to_dict(),
            "lifecycle_dynamics": self.lifecycle_dynamics.to_dict(),
            "validation_dynamics": self.validation_dynamics.to_dict(),
            "insula_unified": (self.insula.integrate(self).get("unified_feelings") or []),
            "td_reward": self.td_reward.to_dict(),
            "working_memory": self.working_memory.to_dict(),
            "attention": self.cognition.attention_budget.to_dict(),
            "grounding": self.grounding.to_dict(),
            "affordance_map": self.affordance_map.to_dict(),
            "neural_telemetry": self.neural_telemetry.to_dict(),
            "counterfactual": self.counterfactual.to_dict(),
            "causal_hud": build_causal_hud(self),
            "observatory_hud": build_observatory_hud(self) if get_flags(self).enable_observatory_hud else {},
            "schema_learner": self.schema_learner.to_dict(),
            "lifecycle": self.lifecycle.to_dict(),
            "experiment_flags": {
                "enable_td_reward": get_flags(self).enable_td_reward,
                "enable_circadian": get_flags(self).enable_circadian,
                "enable_limited_wm": get_flags(self).enable_limited_wm,
                "enable_attention_budget": get_flags(self).enable_attention_budget,
                "enable_selective_sleep": get_flags(self).enable_selective_sleep,
                "enable_grounding": get_flags(self).enable_grounding,
                "enable_learned_schemas": get_flags(self).enable_learned_schemas,
                "enable_lifecycle_plasticity": get_flags(self).enable_lifecycle_plasticity,
                "enable_lobe_virtual_inject": get_flags(self).enable_lobe_virtual_inject,
                "enable_continuous_motor": get_flags(self).enable_continuous_motor,
                "enable_multimodal_delays": get_flags(self).enable_multimodal_delays,
                "enable_affordance_learning": get_flags(self).enable_affordance_learning,
                "enable_neural_telemetry": get_flags(self).enable_neural_telemetry,
                "enable_counterfactual": get_flags(self).enable_counterfactual,
                "enable_sleep_study": get_flags(self).enable_sleep_study,
                "enable_sleep_web": get_flags(self).enable_sleep_web,
                "enable_consciousness": get_flags(self).enable_consciousness,
            },
            "motor_policy": self.motor_policy.to_dict(),
            "sensory_hub": self.sensory_hub.to_dict(),
        }


HumanBrain = InfantApeBrain
