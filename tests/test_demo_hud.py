"""Smoke demo HUD causal — sin importar app.py (evita estado disco/LSH)."""

from __future__ import annotations

import tempfile
from dataclasses import replace
from pathlib import Path

from flask import Flask, jsonify

from brain.causal_hud import build_causal_hud
from brain.experiment_flags import AblationFlags
from brain.mind import InfantApeBrain
from brain.profile import COMPACT_PROFILE, DEMO_LITE_PROFILE


def test_demo_lite_profile_builds_brain():
    sd = Path(tempfile.mkdtemp(prefix="nexo_demo_lite_"))
    flags = replace(
        AblationFlags(),
        enable_affordance_learning=True,
        enable_neural_telemetry=True,
        enable_counterfactual=True,
    )
    brain = InfantApeBrain(
        profile=DEMO_LITE_PROFILE,
        state_dir=sd,
        headless=True,
        auto_save=False,
        experiment_flags=flags,
    )
    hud = build_causal_hud(brain)
    assert "one_liner" in hud
    assert hud["agency_guard"]["deliberation_selects_actions"] is True


def test_causal_hud_flask_route_shape():
    sd = Path(tempfile.mkdtemp(prefix="nexo_hud_flask_"))
    brain = InfantApeBrain(
        profile=COMPACT_PROFILE,
        state_dir=sd,
        headless=True,
        auto_save=False,
        experiment_flags=replace(
            AblationFlags(),
            enable_affordance_learning=True,
            enable_counterfactual=True,
        ),
    )
    app = Flask(__name__)

    @app.get("/api/neural/causal/hud")
    def hud():
        return jsonify(build_causal_hud(brain))

    client = app.test_client()
    r = client.get("/api/neural/causal/hud")
    assert r.status_code == 200
    data = r.get_json()
    assert "choice_key" in data
    assert data["agency_guard"]["hud_selects_actions"] is False


def test_game_template_has_causal_panel():
    html = Path("templates/game.html").read_text(encoding="utf-8")
    assert 'id="causal-hud-panel"' in html
    assert 'id="causal-oneliner"' in html
    assert 'id="observatory-panel"' in html
    assert 'id="obs-oneliner"' in html
    js = Path("static/js/game.js").read_text(encoding="utf-8")
    assert "function renderCausalHud" in js
    assert "function renderObservatory" in js


def test_observatory_hud_route_shape():
    sd = Path(tempfile.mkdtemp(prefix="nexo_obs_flask_"))
    brain = InfantApeBrain(
        profile=COMPACT_PROFILE,
        state_dir=sd,
        headless=True,
        auto_save=False,
        experiment_flags=replace(
            AblationFlags(),
            enable_observatory_hud=True,
            enable_neural_telemetry=True,
            enable_td_reward=True,
        ),
    )
    app = Flask(__name__)

    @app.get("/api/neural/observatory")
    def observatory():
        from brain.observatory_hud import build_observatory_hud

        return jsonify({"enabled": True, "observatory": build_observatory_hud(brain)})

    client = app.test_client()
    r = client.get("/api/neural/observatory")
    assert r.status_code == 200
    data = r.get_json()
    obs = data["observatory"]
    assert "causal" in obs
    assert "study_tracks" in obs
    assert obs["agency_guard"]["observatory_selects_actions"] is False
