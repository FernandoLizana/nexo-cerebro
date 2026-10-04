"""
Servidor Flask: cerebro neuro-biológico + personaje + persistencia + mapa cortical.
"""

from __future__ import annotations

import os
import threading
from pathlib import Path


def _configure_gpu_env() -> None:
    """Activa CUDA en NVIDIA dedicada (laptops híbridas)."""
    from brain.gpu_env import configure_cuda_env

    configure_cuda_env()


def _configure_language_env() -> None:
    """Por defecto: corteza neural (cero LLM). Ollama solo si se pide explícitamente."""
    os.environ.setdefault("CEREBRO_LANGUAGE", "neural")
    os.environ.setdefault("CEREBRO_OLLAMA", "0")
    os.environ.setdefault("CEREBRO_EMBED_OLLAMA", "0")
    os.environ.setdefault("CEREBRO_OLLAMA_MODEL", "llama3.2:1b")
    os.environ.setdefault("CEREBRO_OLLAMA_MAX_TOKENS", "80")
    os.environ.setdefault("OLLAMA_KEEP_ALIVE", "0")


_configure_gpu_env()
_configure_language_env()


def _configure_architecture_env() -> None:
    """Bloque A — escala/arquitectura: lóbulos virtuales, laminar, vascular, prefetch."""
    os.environ.setdefault("CEREBRO_LOBE_VIRTUAL", "1")
    os.environ.setdefault("CEREBRO_LAMINAR", "1")
    os.environ.setdefault("CEREBRO_VASCULAR", "1")
    os.environ.setdefault("CEREBRO_DECOMPRESS_PREFETCH", "1")
    os.environ.setdefault("CEREBRO_LIFECYCLE_PLASTICITY", "1")
    os.environ.setdefault("CEREBRO_CIRCADIAN", "1")
    os.environ.setdefault("CEREBRO_RHYTHM_PAC", "1")
    os.environ.setdefault("CEREBRO_SLEEP_SPINDLES", "1")
    os.environ.setdefault("CEREBRO_SCN", "1")
    os.environ.setdefault("CEREBRO_LOBE_BUS", "1")
    os.environ.setdefault("CEREBRO_TEMPORAL_PRED", "1")
    os.environ.setdefault("CEREBRO_ADVANCED_SENSORY", "1")
    os.environ.setdefault("CEREBRO_SACCADIC", "1")
    os.environ.setdefault("CEREBRO_SUPERIOR_COLLICULUS", "1")
    os.environ.setdefault("CEREBRO_REFERRED_PAIN", "1")
    os.environ.setdefault("CEREBRO_CARDIAC", "1")
    os.environ.setdefault("CEREBRO_MULTIMODAL", "1")
    os.environ.setdefault("CEREBRO_EXECUTIVE", "1")
    os.environ.setdefault("CEREBRO_DUAL_TASK", "1")
    os.environ.setdefault("CEREBRO_STROOP", "1")
    os.environ.setdefault("CEREBRO_SET_SHIFT", "1")
    os.environ.setdefault("CEREBRO_DMN", "1")
    os.environ.setdefault("CEREBRO_METACOG", "1")
    os.environ.setdefault("CEREBRO_TOWER_GOALS", "1")
    os.environ.setdefault("CEREBRO_IMAG_MOTOR", "1")
    os.environ.setdefault("CEREBRO_ATTENTION_BUDGET", "1")
    os.environ.setdefault("CEREBRO_LIMITED_WM", "1")
    os.environ.setdefault("CEREBRO_COUNTERFACTUAL", "1")
    os.environ.setdefault("CEREBRO_MEMORY_DYNAMICS", "1")
    os.environ.setdefault("CEREBRO_RICH_EPISODIC", "1")
    os.environ.setdefault("CEREBRO_FORGETTING", "1")
    os.environ.setdefault("CEREBRO_INTERFERENCE", "1")
    os.environ.setdefault("CEREBRO_SOURCE_CONFUSION", "1")
    os.environ.setdefault("CEREBRO_FLASHBULB", "1")
    os.environ.setdefault("CEREBRO_AUTOBIOGRAPHY", "1")
    os.environ.setdefault("CEREBRO_SELECTIVE_SLEEP", "1")
    os.environ.setdefault("CEREBRO_TD", "1")
    os.environ.setdefault("CEREBRO_AFFORDANCES", "1")
    os.environ.setdefault("CEREBRO_LEARNED_SCHEMAS", "1")
    os.environ.setdefault("CEREBRO_REWARD_LEARNING", "1")
    os.environ.setdefault("CEREBRO_RPE_SURPRISE", "1")
    os.environ.setdefault("CEREBRO_CAUSAL_TRANSFER", "1")
    os.environ.setdefault("CEREBRO_LATENT_LEARNING", "1")
    os.environ.setdefault("CEREBRO_SCHEMA_EXTINCTION", "1")
    os.environ.setdefault("CEREBRO_MODEL_BASED", "1")
    os.environ.setdefault("CEREBRO_METAPLASTICITY", "1")
    os.environ.setdefault("CEREBRO_AFFECT_DYNAMICS", "1")
    os.environ.setdefault("CEREBRO_RECEPTOR_PANEL", "1")
    os.environ.setdefault("CEREBRO_HPA_AXIS", "1")
    os.environ.setdefault("CEREBRO_EMOTION_REG", "1")
    os.environ.setdefault("CEREBRO_EMPATHY", "1")
    os.environ.setdefault("CEREBRO_ATTACHMENT", "1")
    os.environ.setdefault("CEREBRO_SOCIAL_SHAME", "1")
    os.environ.setdefault("CEREBRO_WANTING", "1")
    os.environ.setdefault("CEREBRO_FRUSTRATION", "1")
    os.environ.setdefault("CEREBRO_PERSISTENT_MOOD", "1")
    os.environ.setdefault("CEREBRO_SOCIAL_TURNS", "1")
    os.environ.setdefault("CEREBRO_LANGUAGE_DYNAMICS", "1")
    os.environ.setdefault("CEREBRO_NEURAL_LANG", "1")
    os.environ.setdefault("CEREBRO_CURRICULUM_VOICE", "1")
    os.environ.setdefault("CEREBRO_GROUNDING", "1")
    os.environ.setdefault("CEREBRO_PROSODY", "1")
    os.environ.setdefault("CEREBRO_INNER_SPEECH", "1")
    os.environ.setdefault("CEREBRO_BILINGUAL", "1")
    os.environ.setdefault("CEREBRO_LANGUAGE_TUTOR", "1")
    os.environ.setdefault("CEREBRO_MOTOR_DYNAMICS", "1")
    os.environ.setdefault("CEREBRO_CONTINUOUS_MOTOR", "1")
    os.environ.setdefault("CEREBRO_CEREBELLUM", "1")
    os.environ.setdefault("CEREBRO_BASAL_HABIT", "1")
    os.environ.setdefault("CEREBRO_MUSCULAR_FATIGUE", "1")
    os.environ.setdefault("CEREBRO_WORLD_DEPTH", "1")
    os.environ.setdefault("CEREBRO_SOMATIC", "1")
    os.environ.setdefault("CEREBRO_FOOD_CYCLE", "1")
    os.environ.setdefault("CEREBRO_DESK_STUDY", "1")
    os.environ.setdefault("CEREBRO_LIFECYCLE_DYNAMICS", "1")
    os.environ.setdefault("CEREBRO_FULL_SLEEP", "1")
    os.environ.setdefault("CEREBRO_NOCTURNAL_STUDY", "1")
    os.environ.setdefault("CEREBRO_LIFECYCLE_STAGES", "1")
    os.environ.setdefault("CEREBRO_PUBERTY", "1")
    os.environ.setdefault("CEREBRO_COGNITIVE_AGING", "1")
    os.environ.setdefault("CEREBRO_SLEEP_STUDY", "1")
    os.environ.setdefault("CEREBRO_VALIDATION", "1")
    os.environ.setdefault("CEREBRO_OBSERVATORY", "1")
    os.environ.setdefault("CEREBRO_TELEMETRY", "1")


_configure_architecture_env()

from flask import Flask, jsonify, render_template, request, send_file
import numpy as np
from werkzeug.utils import secure_filename

from brain import InfantApeBrain
from brain.backend import get_backend
from brain.experience_journal import build_journal
from brain.experiment_flags import resolve_demo_flags
from brain.library import ensure_library, list_books
from brain.profile import resolve_default_profile, profile_neuron_count
from brain.sleep_background import maybe_start_sleep_background
from brain.archetype_cards import all_cards

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

_brain_lock = threading.Lock()


def _json_safe(value):
    """Convierte episodios/aprendizaje a tipos serializables (sin ndarray)."""
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (np.integer, np.floating)):
        return value.item()
    if isinstance(value, dict):
        return {str(k): _json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [_json_safe(v) for v in value]
    return str(value)


def _study_response(*, studied: dict, track: dict, learning: dict | None = None) -> dict:
    remembered = False
    label = studied.get("title")
    if learning:
        learned = learning.get("learned") or {}
        remembered = bool(learned.get("remembered", False))
        label = learned.get("label") or label
    return {
        "studied": studied,
        "remembered": remembered,
        "label": label,
        **track,
    }


def _study_unified_overlay(response: dict, *, track: str) -> dict:
    if _unified_session is None:
        return response
    from nexo.demo.flask_study_proxy import wrap_study_response

    return wrap_study_response(_unified_session, response, track=track)


_compute = get_backend()
brain = InfantApeBrain(profile=resolve_default_profile(), experiment_flags=resolve_demo_flags())
_boot = brain.load_state()
_virtual_boot = brain.bootstrap_virtual_cortex()
_semantic_boot = brain.bootstrap_semantic_index(limit=40)
_card_boot = brain.bootstrap_archetype_deck()
ensure_library()
brain.world.ensure_home()
if brain.world.agent_x < 178:
    brain.world.agent_x = 200.0
    brain.world.agent_y = 210.0
brain.world.ensure_agent_free()
brain.ensure_companion()
_care_boot = brain.provide_care(bath=True, feed=True, bathroom=True, drink=True, companion=True)
_sleep_bg = maybe_start_sleep_background(brain, brain.sleep_study, _brain_lock)

_unified_session = None


def _flask_unified_enabled() -> bool:
    from nexo.demo.flask_unified import flask_unified_enabled_by_default

    return flask_unified_enabled_by_default()


if _flask_unified_enabled():
    from nexo.demo.flask_unified import create_unified_session

    _unified_session = create_unified_session(brain)



from nexo.observatory_api import register_observatory_routes, patch_collective_quarantine
register_observatory_routes(app, brain)

@app.get("/")
def game():
    return render_template(
        "game.html",
        n_total=brain.n_total,
        n_virtual=brain.n_virtual,
        n_virtual_max=brain.n_virtual_max,
        compute_backend=_compute.label,
        state_loaded=_boot.get("loaded", False),
        language_available=brain.language.available,
        language_backend=brain.language.backend,
    )


@app.get("/lab")
def index():
    p = brain.profile
    return render_template(
        "index.html",
        n_sensory=brain.n_sensory,
        n_total=brain.n_total,
        persona_name=brain.persona.name,
        profile_name=p.name,
        profile_age=p.age_label,
        state_loaded=_boot.get("loaded", False),
        state_memories=_boot.get("memories", 0),
        compute_backend=_compute.label,
    )


@app.get("/api/health")
def health():
    from brain.engram_codec import codec_stats

    disk = brain.virtual_store.disk_usage_bytes()
    return jsonify(
        {
            "ok": True,
            "neurons_active": brain.n_active,
            "neurons_virtual": brain.n_virtual,
            "neurons_virtual_max": brain.n_virtual_max,
            "neurons": brain.n_active,
            "assemblies_on_disk": brain.virtual_store.total_count(),
            "virtual_cortex": {
                "neurons_per_assembly": brain.profile.neurons_per_assembly,
                "disk_budget_gb": brain.profile.virtual_disk_budget_gb,
                "disk_bytes": disk["total_bytes"],
                "disk_mb": round(disk["total_bytes"] / (1024 * 1024), 2),
                "disk_used_pct": disk["used_pct"],
                "max_assemblies": disk["max_assemblies"],
                "capacity_remaining": disk["capacity_remaining"],
                "codec": codec_stats(),
                "decompress_governor": brain.decompress_governor.to_dict(),
                "lsh_bits": brain.profile.virtual_lsh_bits,
                "bootstrap": _virtual_boot,
            },
            "profile": brain.profile.name,
            "profile_label": brain.profile.age_label,
            "persistence": brain.persistence.exists(),
            "compute": _compute.label,
            "gpu_available": _compute.gpu_available,
            "compute_diagnostics": _compute.gpu_diagnostics(
                n_neurons=brain.n_active,
                episode_steps=32,
            ),
            "language_cortex": brain.language.status(),
            "language_network": brain.language_network.status(brain),
            "semantic_embedder": brain.embedder.status(),
            "semantic_bootstrap": _semantic_boot,
            "working_memory_slots": len(brain.working_memory.slots),
            "td_reward": brain.td_reward.to_dict()
            if brain.experiment_flags.enable_td_reward
            else {"enabled": False},
            "working_memory": brain.working_memory.to_dict(),
            "attention": brain.cognition.attention_budget.to_dict(),
            "circadian": brain.time_state().get("circadian"),
            "grounding": brain.grounding.to_dict(),
            "affordance_map": brain.affordance_map.to_dict(),
            "neural_telemetry": brain.neural_telemetry.to_dict(),
            "counterfactual": brain.counterfactual.to_dict(),
            "schema_learner": brain.schema_learner.to_dict(),
            "lifecycle": brain.lifecycle.to_dict(),
            "motor_policy": brain.motor_policy.to_dict(),
            "sensory_hub": brain.sensory_hub.to_dict(),
            "profile_neurons_active_lif": profile_neuron_count(brain.profile),
            "agency_guard": {
                "td_selects_actions": False,
                "attention_selects_actions": False,
                "wm_selects_actions": False,
                "grounding_selects_actions": False,
                "affordances_select_actions": False,
                "counterfactual_selects_actions": False,
                "learned_schemas_select_actions": False,
                "lifecycle_selects_actions": False,
                "continuous_motor_selects_actions": False,
                "multimodal_selects_actions": False,
                "llm_selects_actions": False,
                "deliberation_selects_actions": True,
            },
            "flask_unified": _unified_session is not None,
            "integrated_profile": (
                _unified_session.runtime.config.profile if _unified_session is not None else None
            ),
        }
    )


@app.post("/api/virtual/bootstrap")
def virtual_bootstrap():
    return jsonify(brain.bootstrap_virtual_cortex())


@app.get("/api/state")
def state():
    if _unified_session is not None:
        return jsonify(_unified_session.snapshot())
    return jsonify(brain.snapshot())


@app.get("/api/neural/telemetry/latest")
def neural_telemetry_latest():
    return jsonify(
        {
            "enabled": bool(brain.experiment_flags.enable_neural_telemetry),
            "latest": brain.neural_telemetry.latest(),
            "summary": brain.neural_telemetry.to_dict(),
            "affordance_map": brain.affordance_map.to_dict(),
            "agency_guard": {
                "affordances_select_actions": False,
                "telemetry_selects_actions": False,
                "deliberation_selects_actions": True,
            },
        }
    )


@app.get("/api/neural/causal/hud")
def neural_causal_hud():
    from brain.causal_hud import build_causal_hud

    hud = build_causal_hud(brain)
    if _unified_session is not None:
        hud["integrated"] = _unified_session.causal_hud_overlay()
    return jsonify(hud)


@app.get("/api/neural/observatory")
def neural_observatory():
    from brain.observatory_hud import build_observatory_hud

    return jsonify(
        {
            "enabled": bool(brain.experiment_flags.enable_observatory_hud),
            "observatory": build_observatory_hud(brain),
        }
    )


@app.get("/api/experiments/battery")
def experiments_battery():
    manifest = brain.validation_dynamics.battery_manifest(profile="10k", seeds=20)
    return jsonify(
        {
            "enabled": bool(brain.experiment_flags.enable_validation_dynamics),
            "manifest": manifest,
            "last_smoke": brain.validation_dynamics.last_smoke,
        }
    )


@app.get("/api/experiments/battery/status")
def experiments_battery_status():
    """Lee reportes JSON y CSV parciales de baterías en disco."""
    from pathlib import Path
    import json

    root = Path("experiments/results")
    reports: list[dict] = []
    for pattern in ("battery_full_report.json", "battery_smoke_report.json", "**/battery_*_report.json"):
        for path in sorted(root.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)[:4]:
            try:
                reports.append({"path": str(path), "data": json.loads(path.read_text(encoding="utf-8"))})
            except Exception:
                pass
    partial: dict[str, int] = {}
    for out in (root / "battery_10k_full", root / "_battery_smoke_e12", root):
        if not out.is_dir():
            continue
        partial[str(out)] = len(list(out.glob("e*.csv")))
    return jsonify(
        {
            "reports": reports[:2],
            "csv_files_by_dir": partial,
            "hint": "Full battery runs headless; refresh while experiments/run_battery_10k is active",
        }
    )


@app.get("/api/cortex/map")
def cortex_map():
    return jsonify(brain.activity_map())


@app.get("/api/persona")
def persona():
    return jsonify(brain.persona.to_dict())


@app.get("/api/chat/history")
def chat_history():
    return jsonify({"dialogue": brain.persona.dialogue})


@app.post("/api/save")
def save_state():
    return jsonify(brain.save_state())


@app.post("/api/load")
def load_state():
    result = brain.load_state()
    if result.get("loaded"):
        result["snapshot"] = brain.snapshot()
    return jsonify(result)


@app.post("/api/chat")
def chat():
    """Compat: redirige al eco introspectivo."""
    data = request.get_json(force=True, silent=True) or {}
    message = str(data.get("message", "")).strip()
    if not message:
        return jsonify({"error": "Falta 'message'"}), 400
    try:
        return jsonify(brain.inject_echo(message))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.post("/api/echo")
def echo_stimulus():
    data = request.get_json(force=True, silent=True) or {}
    text = str(data.get("text", data.get("message", ""))).strip()
    if not text:
        return jsonify({"error": "Falta 'text'"}), 400
    try:
        return jsonify(brain.inject_echo(text))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.post("/api/reset")
def reset():
    brain.reset()
    return jsonify({"reset": True, **brain.snapshot()})


@app.post("/api/experience/text")
def experience_text():
    data = request.get_json(force=True, silent=True) or {}
    text = str(data.get("text", "")).strip()
    if not text:
        return jsonify({"error": "Falta 'text'"}), 400
    label = str(data.get("label", "")).strip()
    repeats = int(data.get("repeats", 4))
    return jsonify(brain.experience(text=text, label=label or text[:40], repeats=repeats))


@app.post("/api/experience")
def experience_file():
    if "file" not in request.files:
        return jsonify({"error": "Campo 'file' requerido"}), 400
    f = request.files["file"]
    if not f or not f.filename:
        return jsonify({"error": "Archivo vacío"}), 400
    raw = f.read()
    if not raw:
        return jsonify({"error": "Archivo sin contenido"}), 400
    label = request.form.get("label", "").strip()
    repeats = int(request.form.get("repeats", 4))
    filename = secure_filename(f.filename)
    try:
        return jsonify(
            brain.experience(
                data=raw,
                filename=filename,
                label=label or filename,
                repeats=repeats,
            )
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.get("/api/library")
def library_list():
    return jsonify({"books": list_books(), "dir": str(ensure_library())})


@app.post("/api/library/import")
def library_import():
    if "file" not in request.files:
        return jsonify({"error": "Campo 'file' requerido"}), 400
    f = request.files["file"]
    if not f or not f.filename:
        return jsonify({"error": "Archivo vacío"}), 400
    raw = f.read()
    try:
        return jsonify(brain.import_to_library(raw, secure_filename(f.filename)))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.post("/api/library/desk")
def library_to_desk():
    return jsonify({"error": "Modo autónomo: libros en biblioteca; Nexo los lleva al escritorio si le interesa."}), 403


@app.get("/api/archetype-cards")
def archetype_card_list():
    return jsonify({"cards": [a.to_dict() for a in all_cards()], "deck_boot": _card_boot})


@app.post("/api/archetype-cards/draw")
def archetype_card_draw():
    return jsonify({"error": "Símbolos autónomos: Nexo los toca por curiosidad, no por comando."}), 403


@app.get("/api/lifecycle")
def lifecycle_status():
    return jsonify(brain.lifecycle.to_dict())


@app.post("/api/lifecycle/reproduce")
def lifecycle_reproduce():
    return jsonify({"error": "Ciclo autónomo: la reproducción surge del vínculo interno."}), 403


@app.post("/api/lifecycle/reborn")
def lifecycle_reborn():
    data = request.get_json(force=True, silent=True) or {}
    if not brain.lifecycle.alive:
        return jsonify(brain.reborn())
    return jsonify({"error": "Renacer solo tras la muerte."}), 403


@app.get("/api/journey")
def journey_status():
    return jsonify(brain.journey.to_dict())


@app.post("/api/learn")
def learn():
    data = request.get_json(force=True, silent=True) or {}
    label = str(data.get("label", "hola"))
    repeats = int(data.get("repeats", 5))
    return jsonify(brain.experience(text=label, label=label, repeats=repeats))


@app.post("/api/recall")
def recall():
    data = request.get_json(force=True, silent=True) or {}
    label = str(data.get("label", "")).strip()
    if not label:
        return jsonify({"error": "Falta 'label'"}), 400
    prior = brain.hippocampus.recall(
        np.asarray(brain.encode_label(label), dtype=np.float32),
        body=brain.body.to_dict(),
        room=brain.world.current_room(),
    )
    result = brain.experience(text=label, label=label, repeats=2, steps_per_repeat=80)
    result["prior_memory"] = prior
    return jsonify(result)


@app.post("/api/tick")
def tick():
    data = request.get_json(force=True, silent=True) or {}
    steps = max(1, min(int(data.get("steps", 10)), 500))
    t, g, m = brain.oscillators.step()
    snap = brain.cortex.tick(
        steps, modulators=brain.modulators, theta_amp=t, gamma_amp=g, hippo_mode=m
    )
    snap["activity_map"] = brain.activity_map()
    return jsonify(snap)


@app.get("/api/fly/status")
def fly_status():
    from nexo.demo.fly_bridge import status

    return jsonify(status())


@app.post("/api/fly/pulse")
def fly_pulse():
    from nexo.demo.fly_bridge import pulse

    body = request.get_json(silent=True) or {}
    result = pulse(body.get("neurons") or [], duration_ms=body.get("duration_ms") or 100)
    return jsonify(result), (200 if result.get("ok") else 409)


@app.get("/api/world3d/blender")
def world3d_blender():
    contract_path = Path("static/models/blender_contract.json")
    contract = {}
    if contract_path.is_file():
        import json

        contract = json.loads(contract_path.read_text(encoding="utf-8"))
    drop = Path("data/world3d")
    present = (drop / "house.glb").is_file() or (drop / "house.gltf").is_file()
    return jsonify({**contract, "present": present, "drop_dir": str(drop.resolve())})


@app.get("/api/world3d/model")
def world3d_model():
    drop = Path("data/world3d")
    for name, mime in (("house.glb", "model/gltf-binary"), ("house.gltf", "model/gltf+json")):
        path = drop / name
        if path.is_file():
            return send_file(path, mimetype=mime)
    return jsonify({"error": "no blender model"}), 404


@app.get("/api/collective")
def collective_status():
    from brain.collective_capacity import apply_capacity, probe_retention

    notice = getattr(brain, "_collective", None) or {}
    last = getattr(brain, "_collective_last", None) or {}
    grown = apply_capacity(brain)
    retention = probe_retention(brain)
    return jsonify(
        {
            "notice": notice,
            "last": last or None,
            "wm": brain.working_memory.effective_capacity(),
            "hippocampus": brain.hippocampus.capacity,
            "links": getattr(brain, "collective_links", 0),
            "capacity": grown,
            "retention": retention,
            "metric": "working_memory_and_hippocampus",
            "not_connectome": True,
            "quarantine": patch_collective_quarantine({}, last)["quarantine"],
        }
    )


@app.get("/api/world")
def world_state():
    if _unified_session is not None:
        return jsonify(_unified_session.world_dict())
    return jsonify(brain._world_dict())


@app.get("/api/integrated/status")
def integrated_status():
    if _unified_session is None:
        return jsonify({"unified": False, "hint": "Set NEXO_FLASK_UNIFIED=1 to enable"}), 404
    return jsonify(_unified_session.status())


@app.get("/api/search")
def web_search_api():
    q = (request.args.get("q") or "").strip()
    if not q:
        return jsonify({"error": "missing q"}), 400
    from brain.web_search import search

    return jsonify(search(q, limit=int(request.args.get("limit", 5))))


@app.get("/api/curriculum")
def curriculum_state():
    from nexo.demo.flask_study_proxy import curriculum_overlay

    return jsonify(curriculum_overlay(_unified_session, brain.curriculum.to_dict()))


@app.post("/api/curriculum/study")
def curriculum_study():
    data = request.get_json(force=True, silent=True) or {}
    key = (data.get("key") or request.args.get("key") or "").strip() or None
    from brain.curriculum import get_section, study_section

    section = get_section(key) if key else brain.curriculum.suggest_next()
    if not section:
        return jsonify({"error": "no sections"}), 404
    result = study_section(brain, section)
    return jsonify(
        _study_unified_overlay(
            _study_response(
                studied=section.to_dict(done=True),
                track={"curriculum": brain.curriculum.to_dict()},
                learning=result.get("learning"),
            ),
            track="curriculum",
        )
    )


@app.get("/api/clinical-neurology")
def clinical_neurology_state():
    return jsonify(brain.clinical_neurology.to_dict())


@app.post("/api/clinical-neurology/study")
def clinical_neurology_study():
    data = request.get_json(force=True, silent=True) or {}
    key = (data.get("key") or request.args.get("key") or "").strip() or None
    from brain.clinical_neurology import get_clinical_section, study_clinical_section

    section = get_clinical_section(key) if key else brain.clinical_neurology.suggest_next()
    if not section:
        return jsonify({"error": "no sections"}), 404
    with _brain_lock:
        try:
            result = study_clinical_section(brain, section)
            brain.try_autosave()
        except Exception as exc:
            return jsonify({"error": str(exc), "clinical_neurology": brain.clinical_neurology.to_dict()}), 500
    return jsonify(
        _study_unified_overlay(
            _study_response(
                studied=section.to_dict(done=True),
                track={"clinical_neurology": brain.clinical_neurology.to_dict()},
                learning=result.get("learning"),
            ),
            track="clinical_neurology",
        )
    )


@app.get("/api/biopsych")
def biopsych_state():
    return jsonify(brain.biopsych.to_dict())


@app.post("/api/biopsych/study")
def biopsych_study():
    data = request.get_json(force=True, silent=True) or {}
    key = (data.get("key") or request.args.get("key") or "").strip() or None
    from brain.biopsych_curriculum import get_biopsych_section, study_biopsych_section

    section = get_biopsych_section(key) if key else brain.biopsych.suggest_next()
    if not section:
        return jsonify({"error": "no sections"}), 404
    with _brain_lock:
        try:
            result = study_biopsych_section(brain, section)
            brain.try_autosave()
        except Exception as exc:
            return jsonify({"error": str(exc), "biopsych": brain.biopsych.to_dict()}), 500
    return jsonify(
        _study_unified_overlay(
            _study_response(
                studied=section.to_dict(done=True),
                track={"biopsych": brain.biopsych.to_dict()},
                learning=result.get("learning"),
            ),
            track="biopsych",
        )
    )


@app.get("/api/infant-brain")
def infant_brain_state():
    return jsonify(brain.infant_brain.to_dict())


@app.post("/api/infant-brain/study")
def infant_brain_study():
    data = request.get_json(force=True, silent=True) or {}
    key = (data.get("key") or request.args.get("key") or "").strip() or None
    from brain.infant_brain_curriculum import get_infant_section, study_infant_section

    section = get_infant_section(key) if key else brain.infant_brain.suggest_next()
    if not section:
        return jsonify({"error": "no sections"}), 404
    with _brain_lock:
        try:
            result = study_infant_section(brain, section)
            brain.try_autosave()
        except Exception as exc:
            return jsonify({"error": str(exc), "infant_brain": brain.infant_brain.to_dict()}), 500
    return jsonify(
        _study_unified_overlay(
            _study_response(
                studied=section.to_dict(done=True),
                track={"infant_brain": brain.infant_brain.to_dict()},
                learning=result.get("learning"),
            ),
            track="infant_brain",
        )
    )


@app.get("/api/brain-facts")
def brain_facts_state():
    return jsonify(brain.brain_facts.to_dict())


@app.post("/api/brain-facts/study")
def brain_facts_study():
    data = request.get_json(force=True, silent=True) or {}
    key = (data.get("key") or request.args.get("key") or "").strip() or None
    from brain.brain_facts import get_chapter, study_chapter

    chapter = get_chapter(key) if key else brain.brain_facts.suggest_next()
    if not chapter:
        return jsonify({"error": "no chapters"}), 404
    result = study_chapter(brain, chapter)
    payload = _study_unified_overlay(
        _study_response(
            studied=chapter.to_dict(done=True),
            track={"brain_facts": brain.brain_facts.to_dict()},
            learning=result.get("learning"),
        ),
        track="brain_facts",
    )
    payload["circuits"] = _json_safe(result.get("circuits"))
    return jsonify(payload)


@app.get("/api/anatomy")
def anatomy():
    return jsonify(brain.atlas.update(brain))


@app.get("/api/time")
def get_time():
    if _unified_session is not None:
        return jsonify(_unified_session.time_state())
    return jsonify(brain.time_state())


@app.post("/api/time")
def set_time():
    data = request.get_json(force=True, silent=True) or {}
    try:
        return jsonify(brain.configure_time(data))
    except (TypeError, ValueError) as e:
        return jsonify({"error": str(e)}), 400


@app.post("/api/world/tick")
def world_tick():
    data = request.get_json(force=True, silent=True) or {}
    steps = int(data.get("steps", 1))
    try:
        with _brain_lock:
            try:
                from brain.collective_capacity import notice

                brain._collective = notice(brain)
            except Exception:
                brain._collective = {"error": "notice skipped"}
            if _unified_session is not None:
                out = _unified_session.world_tick(steps=steps)
            else:
                out = brain.world_tick(steps=steps)
        if _sleep_bg:
            out["sleep_study_background"] = _sleep_bg.status()
        return jsonify(out)
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.get("/api/sleep-study/history")
def sleep_study_history():
    with _brain_lock:
        return jsonify(
            {
                "sleep_study": brain.sleep_study.to_dict(),
                "background": _sleep_bg.status() if _sleep_bg else {"active": False},
                "sleep_pressure": round(brain.brainstem.sleep_pressure, 3),
                "agency_note": "Estudio nocturno no selecciona acciones de vigilia",
            }
        )


@app.get("/api/sleep-study/status")
def sleep_study_status():
    amb = brain.world.ambient()
    return jsonify(
        {
            "enabled": brain.experiment_flags.enable_sleep_study,
            "web_enabled": brain.experiment_flags.enable_sleep_web,
            "background": _sleep_bg.status() if _sleep_bg else {"active": False},
            "phase": amb.get("phase"),
            "clock": amb.get("clock"),
            "sleep_pressure": round(brain.brainstem.sleep_pressure, 3),
        }
    )


@app.get("/api/language")
def language_status():
    if _unified_session is not None:
        return jsonify(_unified_session.language_status())
    return jsonify(
        {
            **brain.language.status(),
            "network": brain.language_network.status(brain),
        }
    )


@app.get("/api/imagination/frame")
def imagination_frame():
    thought = brain.think(vision=brain._last_vision)
    im = brain.imagination.advance_stream(brain, thought=thought, vision=brain._last_vision)
    return jsonify(im or {"active": False})


@app.post("/api/think")
def think():
    thought = brain.think()
    return jsonify({"thought": thought, "recent": brain.thoughts.recent(6)})


@app.post("/api/interact")
def user_interact():
    data = request.get_json(force=True, silent=True) or {}
    action = str(data.get("action", "call"))
    target = str(data.get("target", "nexo"))
    message = str(data.get("message", ""))
    x = data.get("x")
    y = data.get("y")
    try:
        return jsonify(
            brain.user_interact(
                action=action,
                target=target,
                message=message,
                x=float(x) if x is not None else None,
                y=float(y) if y is not None else None,
            )
        )
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.post("/api/care")
def provide_care():
    return jsonify({"error": "Modo autónomo: Nexo cubre sus necesidades solo."}), 403


@app.post("/api/caregiver/vision")
def caregiver_vision():
    """Frame JPEG/base64 de la webcam del cuidador."""
    data = request.get_json(force=True, silent=True) or {}
    b64 = str(data.get("image_b64", "")).strip()
    if not b64:
        return jsonify({"error": "Falta image_b64"}), 400
    if "," in b64:
        b64 = b64.split(",", 1)[1]
    import base64

    try:
        raw = base64.b64decode(b64)
    except Exception:
        return jsonify({"error": "Base64 inválido"}), 400
    try:
        return jsonify(brain.ingest_caregiver_frame(raw))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.post("/api/caregiver/listening")
def caregiver_listening():
    data = request.get_json(force=True, silent=True) or {}
    return jsonify(brain.set_caregiver_listening(bool(data.get("active", False))))


@app.post("/api/caregiver/speak")
def caregiver_speak():
    """Voz transcrita o texto del cuidador → conversación con Nexo."""
    data = request.get_json(force=True, silent=True) or {}
    text = str(data.get("text", "")).strip()
    voice_from_sky = bool(data.get("voice_from_sky", False))
    if not text:
        return jsonify({"error": "Falta text"}), 400
    try:
        return jsonify(brain.caregiver_speak(text, voice_from_sky=voice_from_sky))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


@app.get("/api/caregiver/status")
def caregiver_status():
    return jsonify(brain.caregiver_status())


@app.get("/api/experience/journal")
def experience_journal():
    return jsonify(build_journal(brain))


@app.post("/api/caregiver/routine/echo")
def caregiver_routine_echo():
    """Sembrar eco de una rutina (texto introspectivo, no orden)."""
    data = request.get_json(force=True, silent=True) or {}
    text = str(data.get("text", "")).strip()
    if not text:
        return jsonify({"error": "Falta text"}), 400
    try:
        return jsonify(brain.inject_echo(text))
    except ValueError as e:
        return jsonify({"error": str(e)}), 400


def _recall_studied(brain, text: str) -> dict:
    import re

    from brain.collective_capacity import exclusive_mark

    body = exclusive_mark(text)
    skip = {
        "dejado", "nodo", "simple", "sample", "estudio", "sueno", "sueño",
        "colibri", "ixora", "nectar", "medianoche", "guarda",
    }
    token = next((word for word in re.findall(r"[A-Za-z]{6,}", body) if word.lower() not in skip), "")
    hits: list[str] = []
    store = getattr(getattr(brain, "hippocampus", None), "store", None)
    db = getattr(store, "_db", None)
    if token and db is not None:
        safe = token.lower().replace("%", "").replace("_", "")
        hits = [
            str(row[0])
            for row in db.execute(
                "SELECT label FROM memories WHERE lower(label) LIKE ? LIMIT 3",
                (f"%{safe}%",),
            ).fetchall()
        ]
    return {"token": token, "recalled": bool(hits), "labels": hits}


@app.post("/api/faint")
def faint():
    """Desmayo de prueba: duerme de verdad y estudia el estante de los nodos."""
    from dataclasses import replace

    from brain.node_offerings import peek_offering

    try:
        with _brain_lock:
            brain.experiment_flags = replace(
                brain.experiment_flags,
                enable_sleep_study=True,
                enable_sleep_web=False,
            )
            brain.configure_time({"hour": 23, "minute": 40, "realtime": False, "paused": False})
            brain.brainstem.sleep_pressure = max(float(brain.brainstem.sleep_pressure), 0.92)
            brain.persona.mood = "sleepy"
            held = peek_offering()
            studied = None
            if held:
                entry = brain.sleep_study._study_nodes(brain, phase="rem", source="desmayo")
                studied = entry.to_dict() if entry else None
            out = brain.sleep(cycles=1, steps_per_cycle=40)
            phrase = (studied or {}).get("snippet") or ""
            recall = _recall_studied(brain, phrase)
            if recall["recalled"]:
                brain.persona.message = f"Al desmayarme guardé: {recall['token']}."
            elif held:
                brain.persona.message = "Me desmayé, pero esa frase no quedó en la memoria."
            else:
                brain.persona.message = "Me desmayé. El estante de los nodos estaba vacío."
            brain.try_autosave()
        return jsonify(
            {
                "fainted": True,
                "slept": bool(out.get("slept")),
                "held": bool(held),
                "studied": studied,
                "phrase": phrase,
                "recall": recall,
                "learned": bool(recall["recalled"]),
                "message": brain.persona.message,
                "sleep_study": out.get("sleep_study"),
            }
        )
    except Exception as exc:
        return jsonify({"fainted": False, "error": str(exc)[:240]}), 500


@app.post("/api/sleep/force")
def sleep_force():
    """Demo/cuidador: induce sueño NREM/REM + estudio nocturno (no elige acciones de vigilia)."""
    data = request.get_json(force=True, silent=True) or {}
    cycles = max(1, min(int(data.get("cycles", 2)), 6))
    steps = max(40, min(int(data.get("steps_per_cycle", 100)), 180))
    try:
        with _brain_lock:
            brain.configure_time({"hour": 23, "minute": 15, "realtime": False, "paused": False})
            brain.brainstem.sleep_pressure = float(max(brain.brainstem.sleep_pressure, 0.88))
            brain.persona.mood = "sleepy"
            out = brain.sleep(cycles=cycles, steps_per_cycle=steps)
            brain.try_autosave()
        log = brain.sleep_study.to_dict()
        return jsonify(
            {
                "slept": bool(out.get("slept")),
                "cycles": cycles,
                "replays": int(out.get("replays") or 0),
                "swr_bursts": int(out.get("swr_bursts") or 0),
                "sleep_study": {
                    "count": int((out.get("sleep_study") or {}).get("count") or 0),
                },
                "sleep_study_log": log,
                "sleep_pressure": round(float(out.get("sleep_pressure") or 0), 3),
                "mood": str((out.get("character") or {}).get("mood", "sleepy")),
                "background": _sleep_bg.status() if _sleep_bg else {"active": False},
            }
        )
    except Exception as exc:
        return jsonify(
            {
                "slept": True,
                "warning": str(exc),
                "sleep_study_log": brain.sleep_study.to_dict(),
                "sleep_pressure": round(float(brain.brainstem.sleep_pressure), 3),
            }
        ), 200


@app.post("/api/sleep")
def sleep():
    return jsonify({"error": "Modo autónomo: Nexo duerme cuando su cuerpo lo exige."}), 403


if __name__ == "__main__":
    port = int(os.environ.get("CEREBRO_PORT", "5000"))
    app.run(host="127.0.0.1", port=port, debug=False, threaded=False)
