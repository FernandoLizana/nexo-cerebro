"""Interaction modes: config/params merge, loopback, background lifecycle."""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from services.ctl.cli import main as ctl_main
from services.runtime.config import load_params_file, merge_params
from services.runtime.loopback import assert_loopback_host, is_loopback_host
from services.runtime.process import pid_alive, spawn_background, status_background, stop_background
from services.runtime.state import RuntimeRecord, save_runtime_record, load_runtime_record

ROOT = Path(__file__).resolve().parents[1]


def test_loopback_policy() -> None:
    assert is_loopback_host("127.0.0.1")
    assert is_loopback_host("localhost")
    with pytest.raises(ValueError):
        assert_loopback_host("0.0.0.0")


def test_merge_params_allowlist(tmp_path: Path) -> None:
    cfg = tmp_path / "p.yaml"
    cfg.write_text("port: 9000\nhost: 127.0.0.1\nevil_bind: 0.0.0.0\n", encoding="utf-8")
    loaded = load_params_file(cfg)
    merged = merge_params(loaded, {"port": 8766}, allow=frozenset({"host", "port"}))
    assert merged == {"host": "127.0.0.1", "port": 8766}
    assert "evil_bind" not in merged


def test_dashboard_config_file_exists() -> None:
    path = ROOT / "configs" / "swarm" / "dashboard.local.yaml"
    data = load_params_file(path)
    assert data["host"] == "127.0.0.1"
    assert int(data["port"]) == 8765


def test_ctl_list_and_help_modes() -> None:
    assert ctl_main(["list"]) == 0
    assert ctl_main(["help-modes"]) == 0


def test_ctl_run_node_with_params(tmp_path: Path) -> None:
    data_dir = tmp_path / "node"
    code = ctl_main(
        [
            "run",
            "node",
            "--",
            "start",
            "--data-dir",
            str(data_dir),
            "--name",
            "ctl-test",
        ]
    )
    assert code == 0
    assert (data_dir / "node_state.json").is_file()
    assert ctl_main(["run", "node", "--", "status", "--data-dir", str(data_dir)]) == 0
    assert ctl_main(["run", "node", "--", "stop", "--data-dir", str(data_dir)]) == 0


def test_background_record_lifecycle(tmp_path: Path) -> None:
    # Use a short-lived python -c that sleeps; kill via stop_background.
    import sys

    data = tmp_path / "rt"
    argv = [sys.executable, "-c", "import time; time.sleep(30)"]
    record = spawn_background(
        service="testd",
        argv=argv,
        data_dir=data,
        cwd=tmp_path,
    )
    assert pid_alive(record.pid)
    st = status_background(service="testd", data_dir=data)
    assert st["running"] is True
    stopped = stop_background(service="testd", data_dir=data, grace_seconds=3.0)
    assert stopped["ok"] is True
    assert status_background(service="testd", data_dir=data)["running"] is False


def test_node_cli_config_and_params(tmp_path: Path) -> None:
    from services.node.cli import main as node_main

    cfg = tmp_path / "node.yaml"
    cfg.write_text(
        f"data_dir: {tmp_path.as_posix()}/nd\nname: from-config\ncpu_max: 33\n",
        encoding="utf-8",
    )
    assert node_main(["--config", str(cfg), "start"]) == 0
    state = json.loads((tmp_path / "nd" / "node_state.json").read_text(encoding="utf-8"))
    # public status should exist; name is in identity/state depending on schema
    assert state.get("state") in {"RUNNING", "running", "Running"} or "state" in state
    assert (
        node_main(
            [
                "--params",
                json.dumps({"data_dir": str(tmp_path / "nd2"), "name": "from-params"}),
                "start",
            ]
        )
        == 0
    )


def test_dashboard_refuses_non_loopback_via_params() -> None:
    from services.dashboard.cli import main as dash_main

    code = dash_main(["run", "--params", '{"host":"0.0.0.0"}'])
    assert code == 2


def test_runtime_record_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "x.runtime.json"
    rec = RuntimeRecord(
        service="dashboard",
        pid=os.getpid(),
        argv=["python", "-m", "services.dashboard.cli"],
        started_at=1.0,
        data_dir=str(tmp_path),
        host="127.0.0.1",
        port=8765,
    )
    save_runtime_record(path, rec)
    loaded = load_runtime_record(path)
    assert loaded is not None
    assert loaded.service == "dashboard"
    assert loaded.port == 8765
