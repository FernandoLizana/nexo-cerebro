"""
Evita pipelines duplicados: mata procesos experimentales huérfanos al arrancar.

Variables:
  CEREBRO_PIPELINE_ROOT_PID — PID del orquestador (run_all / run_e1_parallel).
  CEREBRO_SKIP_PROCESS_GUARD=1 — desactiva limpieza (debug).
"""

from __future__ import annotations

import argparse
import os
import re
import signal
import subprocess
import sys
import time

EXPERIMENT_CMD = re.compile(r"experiments\.run_", re.I)
SPAWN_CMD = re.compile(r"multiprocessing\.spawn.*spawn_main", re.I)
SPAWN_PARENT = re.compile(r"parent_pid=(\d+)", re.I)

ROOT_ENV = "CEREBRO_PIPELINE_ROOT_PID"
SKIP_ENV = "CEREBRO_SKIP_PROCESS_GUARD"


def _guard_disabled() -> bool:
    return os.environ.get(SKIP_ENV, "").strip().lower() in ("1", "true", "yes")


def _list_python_processes() -> list[tuple[int, str]]:
    if sys.platform == "win32":
        return _list_python_processes_windows()
    return _list_python_processes_posix()


def _list_python_processes_windows() -> list[tuple[int, str]]:
    script = (
        "Get-CimInstance Win32_Process -Filter \"Name='python.exe'\" | "
        "Where-Object { $_.CommandLine } | "
        "ForEach-Object { \"$($_.ProcessId)`t$($_.CommandLine)\" }"
    )
    try:
        proc = subprocess.run(
            ["powershell", "-NoProfile", "-Command", script],
            capture_output=True,
            text=True,
            timeout=45,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    rows: list[tuple[int, str]] = []
    for line in proc.stdout.splitlines():
        if not line.strip():
            continue
        pid_s, _, cmd = line.partition("\t")
        try:
            rows.append((int(pid_s.strip()), cmd.strip()))
        except ValueError:
            continue
    return rows


def _list_python_processes_posix() -> list[tuple[int, str]]:
    try:
        proc = subprocess.run(
            ["ps", "-ax", "-o", "pid=,command="],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return []
    rows: list[tuple[int, str]] = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        parts = line.split(None, 1)
        if len(parts) != 2:
            continue
        try:
            rows.append((int(parts[0]), parts[1]))
        except ValueError:
            continue
    return rows


def pipeline_root_pid() -> int | None:
    raw = os.environ.get(ROOT_ENV, "").strip()
    if not raw:
        return None
    try:
        return int(raw)
    except ValueError:
        return None


def _keep_pids(*, orchestrator: bool) -> set[int]:
    keep = {os.getpid()}
    ppid = os.getppid()
    if ppid > 0:
        keep.add(ppid)
    root = pipeline_root_pid()
    if root and root > 0:
        keep.add(root)
    if orchestrator:
        # Conservar solo este árbol (self + launcher/padre); matar otros pipelines.
        return keep
    return keep


def _spawn_parent_pid(cmdline: str) -> int | None:
    m = SPAWN_PARENT.search(cmdline)
    if not m:
        return None
    try:
        return int(m.group(1))
    except ValueError:
        return None


def find_stale_processes(*, orchestrator: bool = False) -> list[tuple[int, str, str]]:
    """Devuelve (pid, kind, cmdline) de procesos a terminar."""
    keep = _keep_pids(orchestrator=orchestrator)
    stale: list[tuple[int, str, str]] = []
    for pid, cmd in _list_python_processes():
        if pid in keep:
            continue
        if EXPERIMENT_CMD.search(cmd):
            root = pipeline_root_pid()
            if root and pid == root:
                continue
            if pid == os.getppid():
                continue
            stale.append((pid, "experiment", cmd))
            continue
        if SPAWN_CMD.search(cmd):
            parent = _spawn_parent_pid(cmd)
            if parent is None or parent not in keep:
                stale.append((pid, "spawn_worker", cmd))
    return stale


def kill_stale_processes(*, orchestrator: bool = False, dry_run: bool = False) -> list[int]:
    killed: list[int] = []
    for pid, kind, cmd in find_stale_processes(orchestrator=orchestrator):
        short = cmd if len(cmd) <= 120 else cmd[:117] + "..."
        if dry_run:
            print(f"  [dry-run] matar {kind} pid={pid}: {short}", flush=True)
            killed.append(pid)
            continue
        if _terminate_pid(pid):
            print(f"  matado {kind} pid={pid}: {short}", flush=True)
            killed.append(pid)
    if killed and not dry_run:
        time.sleep(0.4)
    return killed


def _terminate_pid(pid: int) -> bool:
    if sys.platform == "win32":
        try:
            subprocess.run(
                ["taskkill", "/PID", str(pid), "/F"],
                capture_output=True,
                timeout=15,
                check=False,
            )
            return True
        except (OSError, subprocess.TimeoutExpired):
            return False
    try:
        os.kill(pid, signal.SIGTERM)
        return True
    except OSError:
        return False


def register_pipeline_root() -> None:
    os.environ[ROOT_ENV] = str(os.getpid())


def ensure_clean_pipeline(*, orchestrator: bool = True) -> list[int]:
    """Al inicio de run_all o invocación standalone: solo queda este árbol."""
    if _guard_disabled():
        return []
    if orchestrator:
        register_pipeline_root()
    stale = find_stale_processes(orchestrator=orchestrator)
    if not stale:
        return []
    print(f"process_guard: {len(stale)} proceso(s) residual(es) — limpiando…", flush=True)
    return kill_stale_processes(orchestrator=orchestrator)


def ensure_pipeline_hygiene() -> list[int]:
    """Dentro del pipeline: mata duplicados pero conserva orquestador + padre."""
    if _guard_disabled():
        return []
    stale = find_stale_processes(orchestrator=False)
    if not stale:
        return []
    print(f"process_guard: {len(stale)} duplicado(s) fuera del pipeline — limpiando…", flush=True)
    return kill_stale_processes(orchestrator=False)


def pipeline_env(extra: dict[str, str] | None = None) -> dict[str, str]:
    env = os.environ.copy()
    if ROOT_ENV not in env:
        env[ROOT_ENV] = str(os.getpid())
    if extra:
        env.update(extra)
    return env


def main() -> None:
    parser = argparse.ArgumentParser(description="Mata procesos experiments.run_* huérfanos")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "--orchestrator",
        action="store_true",
        help="Modo agresivo (solo conserva PID actual)",
    )
    args = parser.parse_args()
    if args.orchestrator:
        register_pipeline_root()
    stale = find_stale_processes(orchestrator=args.orchestrator)
    if not stale:
        print("process_guard: nada que limpiar")
        return
    print(f"process_guard: {len(stale)} candidato(s)")
    killed = kill_stale_processes(orchestrator=args.orchestrator, dry_run=args.dry_run)
    print(f"process_guard: {len(killed)} terminado(s)")


if __name__ == "__main__":
    main()
