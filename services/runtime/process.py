"""Opt-in background process helpers (no shell, no silent install, no subprocess)."""

from __future__ import annotations

import os
import signal
import sys
import time
from pathlib import Path

from services.runtime.state import (
    RuntimeRecord,
    clear_runtime_record,
    default_record_path,
    load_runtime_record,
    save_runtime_record,
)


def pid_alive(pid: int) -> bool:
    if pid <= 0:
        return False
    if sys.platform == "win32":
        return _pid_alive_windows(pid)
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    except OSError:
        return False
    return True


def _pid_alive_windows(pid: int) -> bool:
    import ctypes

    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    STILL_ACTIVE = 259
    handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not handle:
        return False
    try:
        exit_code = ctypes.c_ulong()
        ok = ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(exit_code))
        if not ok:
            return False
        return int(exit_code.value) == STILL_ACTIVE
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


def _terminate_windows(pid: int, *, force: bool = False) -> None:
    import ctypes

    access = 0x0001  # PROCESS_TERMINATE
    handle = ctypes.windll.kernel32.OpenProcess(access, False, pid)
    if not handle:
        raise OSError(f"OpenProcess failed for pid {pid}: {ctypes.GetLastError()}")
    try:
        if force:
            if not ctypes.windll.kernel32.TerminateProcess(handle, 1):
                raise OSError(f"TerminateProcess failed: {ctypes.GetLastError()}")
        else:
            # Best-effort soft signal; many Win processes ignore SIGTERM.
            try:
                os.kill(pid, signal.SIGTERM)
            except OSError:
                if not ctypes.windll.kernel32.TerminateProcess(handle, 1):
                    raise OSError(f"TerminateProcess failed: {ctypes.GetLastError()}") from None
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


def _resolve_windows_exe(exe: str, env: dict[str, str]) -> str:
    if Path(exe).is_file():
        return str(Path(exe).resolve())
    path_dirs = env.get("PATH", os.defpath).split(os.pathsep)
    for folder in path_dirs:
        for candidate in (Path(folder) / exe, Path(folder) / f"{exe}.exe"):
            if candidate.is_file():
                return str(candidate.resolve())
    return exe


def _spawn_detached_windows(argv: list[str], *, cwd: str | None, env: dict[str, str]) -> int:
    """Detached CreateProcessW without importing subprocess."""
    import ctypes
    from ctypes import wintypes

    exe = _resolve_windows_exe(argv[0], env)
    parts: list[str] = []
    for i, part in enumerate([exe, *argv[1:]]):
        if i == 0:
            parts.append(f'"{part}"' if " " in part else part)
        elif any(ch in part for ch in ' \t"'):
            parts.append('"' + part.replace('"', '\\"') + '"')
        else:
            parts.append(part)
    cmdline = " ".join(parts)
    # Inherit parent environment; markers already set in os.environ copy applied via
    # a temporary update around CreateProcess (avoids fragile env blocks with NULs).
    old_env = {k: os.environ.get(k) for k in ("NEXO_RUNTIME_DETACHED", "NEXO_RUNTIME_FOREGROUND")}
    os.environ["NEXO_RUNTIME_DETACHED"] = "1"
    os.environ["NEXO_RUNTIME_FOREGROUND"] = "1"

    class STARTUPINFO(ctypes.Structure):
        _fields_ = [
            ("cb", wintypes.DWORD),
            ("lpReserved", wintypes.LPWSTR),
            ("lpDesktop", wintypes.LPWSTR),
            ("lpTitle", wintypes.LPWSTR),
            ("dwX", wintypes.DWORD),
            ("dwY", wintypes.DWORD),
            ("dwXSize", wintypes.DWORD),
            ("dwYSize", wintypes.DWORD),
            ("dwXCountChars", wintypes.DWORD),
            ("dwYCountChars", wintypes.DWORD),
            ("dwFillAttribute", wintypes.DWORD),
            ("dwFlags", wintypes.DWORD),
            ("wShowWindow", wintypes.WORD),
            ("cbReserved2", wintypes.WORD),
            ("lpReserved2", ctypes.POINTER(ctypes.c_byte)),
            ("hStdInput", wintypes.HANDLE),
            ("hStdOutput", wintypes.HANDLE),
            ("hStdError", wintypes.HANDLE),
        ]

    class PROCESS_INFORMATION(ctypes.Structure):
        _fields_ = [
            ("hProcess", wintypes.HANDLE),
            ("hThread", wintypes.HANDLE),
            ("dwProcessId", wintypes.DWORD),
            ("dwThreadId", wintypes.DWORD),
        ]

    # CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW (avoid DETACHED_PROCESS quirks with python.exe)
    creation_flags = 0x00000200 | 0x08000000
    si = STARTUPINFO()
    si.cb = ctypes.sizeof(STARTUPINFO)
    pi = PROCESS_INFORMATION()
    kernel32 = ctypes.windll.kernel32
    try:
        ok = kernel32.CreateProcessW(
            exe,
            ctypes.c_wchar_p(cmdline),
            None,
            None,
            False,
            creation_flags,
            None,
            ctypes.c_wchar_p(cwd) if cwd else None,
            ctypes.byref(si),
            ctypes.byref(pi),
        )
    finally:
        for key, previous in old_env.items():
            if previous is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = previous
    if not ok:
        raise OSError(f"CreateProcessW failed: {ctypes.GetLastError()}")
    pid = int(pi.dwProcessId)
    kernel32.CloseHandle(pi.hThread)
    kernel32.CloseHandle(pi.hProcess)
    return pid


def _spawn_detached(argv: list[str], *, cwd: Path | None = None) -> int:
    """
    Spawn argv[0] as a detached child and return its PID.
    Never invokes a shell. Caller must pass an explicit allowlisted argv.
    """
    if not argv:
        raise ValueError("empty argv")
    work = str(cwd) if cwd is not None else None
    env = os.environ.copy()
    env["NEXO_RUNTIME_DETACHED"] = "1"
    env["NEXO_RUNTIME_FOREGROUND"] = "1"

    if sys.platform == "win32":
        return _spawn_detached_windows(list(argv), cwd=work, env=env)

    pid = os.fork()
    if pid == 0:
        try:
            os.setsid()
            if work:
                os.chdir(work)
            os.environ.clear()
            os.environ.update(env)
            os.execvpe(argv[0], argv, env)
        except Exception:
            os._exit(1)
    return int(pid)


def spawn_background(
    *,
    service: str,
    argv: list[str],
    data_dir: Path | str,
    host: str | None = None,
    port: int | None = None,
    record_path: Path | str | None = None,
    cwd: Path | None = None,
    extra: dict | None = None,
) -> RuntimeRecord:
    """Start a background instance and persist a runtime record + optional pid file."""
    data = Path(data_dir)
    data.mkdir(parents=True, exist_ok=True)
    path = Path(record_path) if record_path else default_record_path(data, service)
    existing = load_runtime_record(path)
    if existing and pid_alive(existing.pid):
        raise RuntimeError(
            f"{service} already running as pid {existing.pid} (record: {path})"
        )

    pid = _spawn_detached(list(argv), cwd=cwd)
    record = RuntimeRecord(
        service=service,
        pid=pid,
        argv=list(argv),
        started_at=time.time(),
        data_dir=str(data.resolve()),
        host=host,
        port=port,
        extra=dict(extra or {}),
    )
    save_runtime_record(path, record)
    pid_file = data / f"{service}.pid"
    pid_file.write_text(str(pid) + "\n", encoding="utf-8")
    return record


def status_background(
    *,
    service: str,
    data_dir: Path | str,
    record_path: Path | str | None = None,
) -> dict:
    data = Path(data_dir)
    path = Path(record_path) if record_path else default_record_path(data, service)
    record = load_runtime_record(path)
    if record is None:
        return {"ok": True, "service": service, "running": False, "record": None}
    alive = pid_alive(record.pid)
    return {
        "ok": True,
        "service": service,
        "running": alive,
        "record": record.to_dict(),
        "record_path": str(path),
    }


def stop_background(
    *,
    service: str,
    data_dir: Path | str,
    record_path: Path | str | None = None,
    grace_seconds: float = 5.0,
) -> dict:
    data = Path(data_dir)
    path = Path(record_path) if record_path else default_record_path(data, service)
    record = load_runtime_record(path)
    if record is None:
        return {"ok": True, "service": service, "stopped": False, "reason": "no_record"}
    pid = record.pid
    if not pid_alive(pid):
        clear_runtime_record(path)
        pid_file = data / f"{service}.pid"
        if pid_file.is_file():
            pid_file.unlink()
        return {
            "ok": True,
            "service": service,
            "stopped": True,
            "already_dead": True,
            "pid": pid,
        }

    try:
        if sys.platform == "win32":
            _terminate_windows(pid, force=False)
        else:
            os.kill(pid, signal.SIGTERM)
    except OSError as exc:
        return {"ok": False, "service": service, "error": str(exc), "pid": pid}

    deadline = time.time() + grace_seconds
    while time.time() < deadline:
        if not pid_alive(pid):
            break
        time.sleep(0.1)

    force_killed = False
    if pid_alive(pid):
        try:
            if sys.platform == "win32":
                _terminate_windows(pid, force=True)
            else:
                os.kill(pid, signal.SIGKILL)
            force_killed = True
        except OSError:
            pass
        # brief wait after force
        deadline2 = time.time() + 1.0
        while time.time() < deadline2 and pid_alive(pid):
            time.sleep(0.05)

    clear_runtime_record(path)
    pid_file = data / f"{service}.pid"
    if pid_file.is_file():
        pid_file.unlink()
    return {
        "ok": True,
        "service": service,
        "stopped": not pid_alive(pid),
        "pid": pid,
        "force_killed": force_killed,
    }
