"""
Worker en segundo plano: estudio nocturno mientras Nexo «duerme» entre ticks.

Corre en hilo daemon con lock compartido; no interfiere con el loop de vigilia.
"""

from __future__ import annotations

import os
import threading
import time
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from .mind import InfantApeBrain
    from .sleep_study import SleepStudyEngine


class SleepBackgroundWorker:
    def __init__(
        self,
        brain: InfantApeBrain,
        engine: SleepStudyEngine,
        lock: threading.Lock,
        *,
        interval_s: float = 55.0,
    ) -> None:
        self._brain = brain
        self._engine = engine
        self._lock = lock
        self._interval = max(20.0, interval_s)
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._last_result: dict | None = None
        self._running = False

    @property
    def active(self) -> bool:
        return self._running and self._thread is not None and self._thread.is_alive()

    def status(self) -> dict:
        return {
            "active": self.active,
            "interval_s": self._interval,
            "last_result": self._last_result,
            "enabled": self._engine.enabled(self._brain),
        }

    def start(self) -> None:
        if self._thread and self._thread.is_alive():
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._loop, name="nexo-sleep-study", daemon=True)
        self._thread.start()
        self._running = True

    def stop(self) -> None:
        self._stop.set()
        self._running = False

    def _loop(self) -> None:
        while not self._stop.is_set():
            if self._engine.enabled(self._brain):
                if self._lock.acquire(blocking=False):
                    try:
                        result = self._engine.run_background_pass(self._brain)
                        if result:
                            self._last_result = result
                    finally:
                        self._lock.release()
            self._stop.wait(self._interval)


def maybe_start_sleep_background(
    brain: InfantApeBrain,
    engine: SleepStudyEngine,
    lock: threading.Lock,
) -> SleepBackgroundWorker | None:
    if not engine.enabled(brain):
        return None
    if os.environ.get("CEREBRO_SLEEP_BACKGROUND", "1").strip().lower() in ("0", "false", "off", "no"):
        return None
    interval = float(os.environ.get("CEREBRO_SLEEP_BACKGROUND_INTERVAL", "55"))
    worker = SleepBackgroundWorker(brain, engine, lock, interval_s=interval)
    worker.start()
    return worker
