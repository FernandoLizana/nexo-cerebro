"""
Reloj del mundo + percepción temporal (corteza temporal simplificada).

Modos:
- realtime: hora del PC (por defecto)
- simulated: el cuidador mueve el tiempo desde la línea temporal
"""

from __future__ import annotations

import math
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import Any

import numpy as np

ROOM_HERO_ZONE: dict[str, dict[str, str]] = {
    "jardín": {"key": "threshold", "name": "Umbral", "desc": "El borde entre lo conocido y lo abierto."},
    "casa": {"key": "ordinary_world", "name": "Mundo ordinario", "desc": "El hogar cotidiano."},
    "escritorio": {"key": "mentor", "name": "Mentor", "desc": "Libros y cartas que enseñan."},
    "sala_tv": {"key": "call", "name": "Llamada", "desc": "Voces del exterior que invitan."},
    "cocina": {"key": "ordeal", "name": "Prueba", "desc": "El cuerpo pide sustento."},
    "dormitorio": {"key": "reward", "name": "Recompensa", "desc": "Descanso tras el esfuerzo."},
    "baño": {"key": "return", "name": "Regreso", "desc": "Purificación antes de volver."},
}

SEASONS: tuple[str, ...] = ("primavera", "verano", "otoño", "invierno")

PHASE_LABELS_ES: dict[str, str] = {
    "dawn": "amanecer",
    "day": "día",
    "dusk": "atardecer",
    "night": "noche",
}


def _season_for_month(month: int) -> str:
    if month in (3, 4, 5):
        return "primavera"
    if month in (6, 7, 8):
        return "verano"
    if month in (9, 10, 11):
        return "otoño"
    return "invierno"


def phase_from_hour(hour: int) -> str:
    if 5 <= hour < 7:
        return "dawn"
    if 7 <= hour < 20:
        return "day"
    if 20 <= hour < 22:
        return "dusk"
    return "night"


def light_level_from_hour(hour: int, minute: int = 0) -> float:
    t = (hour * 60 + minute) / (24 * 60)
    base = 0.5 + 0.5 * math.cos(2 * math.pi * (t - 0.25))
    if hour >= 22 or hour < 5:
        return float(max(0.08, base * 0.55))
    if 5 <= hour < 7:
        return float(max(0.25, base * 0.85))
    if 20 <= hour < 22:
        return float(max(0.2, base * 0.75))
    return float(max(0.35, base))


def circadian_profile(ambient: dict) -> dict[str, float | str]:
    """
    Perfil corporal de 24h: alerta diurna, somnolencia nocturna, cortisol matinal.

    No selecciona acciones. Sus salidas son moduladores suaves para cuerpo,
    tronco encefálico e hipotálamo.
    """
    hour = int(ambient.get("hour", 12))
    minute = int(ambient.get("minute", 0))
    phase = str(ambient.get("phase", phase_from_hour(hour)))
    t = ((hour * 60 + minute) % 1440) / 1440.0

    # Máximo de alerta alrededor de las 14:00; mínimo alrededor de las 02:00.
    alert = 0.5 + 0.5 * math.cos(2 * math.pi * (t - 14 / 24))
    # Cortisol matinal: pico 08:00, valle 02:00.
    cortisol = 0.5 + 0.5 * math.cos(2 * math.pi * (t - 8 / 24))
    at_night = phase == "night" or hour >= 22 or hour < 5
    dusk = phase == "dusk" or 20 <= hour < 22
    dawn = phase == "dawn" or 5 <= hour < 7

    sleep_drive = 1.0 - alert
    if at_night:
        sleep_drive = min(1.0, sleep_drive + 0.22)
    elif dusk:
        sleep_drive = min(1.0, sleep_drive + 0.1)
    elif dawn:
        sleep_drive = max(0.0, sleep_drive - 0.08)

    body_temp_target = 0.50 + 0.04 * math.cos(2 * math.pi * (t - 17 / 24))
    return {
        "phase": phase,
        "alertness": float(max(0.0, min(1.0, alert))),
        "sleep_drive": float(max(0.0, min(1.0, sleep_drive))),
        "cortisol_target": float(max(0.0, min(1.0, 0.15 + 0.55 * cortisol))),
        "body_temp_target": float(max(0.42, min(0.62, body_temp_target))),
        "is_night": float(1.0 if at_night else 0.0),
    }


def apply_circadian_drives(drives: dict[str, float], ambient: dict) -> None:
    phase = ambient.get("phase", "day")
    hour = int(ambient.get("hour", 12))

    def bump(key: str, delta: float) -> None:
        drives[key] = float(max(0.0, min(1.0, drives.get(key, 0.0) + delta)))

    at_night = phase == "night" or hour >= 22 or hour < 5
    early = 5 <= hour < 9
    morning = 7 <= hour < 11
    midday = 11 <= hour < 15
    afternoon = 15 <= hour < 18
    evening = 18 <= hour < 22

    if at_night:
        bump("seek_rest", 0.34)
        bump("sleep_need", 0.28)
        bump("seek_warmth", 0.2)
        bump("seek_stimulus", -0.14)
        bump("seek_curiosity", -0.1)
    elif phase == "dawn" or early:
        bump("seek_food", 0.24)
        bump("seek_hygiene", 0.14)
        bump("seek_warmth", 0.08)
    elif morning:
        bump("seek_curiosity", 0.08)
        bump("seek_food", 0.1)
    elif midday:
        bump("seek_rest", 0.08)
        bump("seek_food", 0.06)
    elif afternoon:
        bump("seek_stimulus", 0.06)
        bump("seek_companion", 0.08)
    elif evening or phase == "dusk":
        bump("seek_stimulus", 0.22)
        bump("seek_companion", 0.16)
        bump("seek_food", 0.12)
        bump("seek_rest", 0.06)


@dataclass
class WorldClock:
    """Reloj del hogar: hora real del PC o tiempo simulado controlado."""

    tick: int = 0
    ticks_per_day: int = 200
    realtime: bool = True
    paused: bool = False
    time_scale: float = 1.0
    sim_day_offset: int = 0
    sim_minute: int = 0
    turbo: bool = False
    learning_multiplier: float = 1.0
    minutes_per_tick: float = 7.2

    def current_dt(self) -> datetime:
        if self.realtime:
            return datetime.now()
        h, m = divmod(int(self.sim_minute) % 1440, 60)
        base = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        base += timedelta(days=int(self.sim_day_offset))
        return base.replace(hour=h, minute=m)

    def advance(self, n: int = 1) -> None:
        self.tick = max(0, self.tick + max(1, n))
        if self.realtime or self.paused:
            return
        delta = float(n) * self.minutes_per_tick * self.time_scale
        self.sim_minute = int(self.sim_minute + delta)
        while self.sim_minute >= 1440:
            self.sim_minute -= 1440
            self.sim_day_offset += 1
        while self.sim_minute < 0:
            self.sim_minute += 1440
            self.sim_day_offset = max(0, self.sim_day_offset - 1)

    def set_sim_time(self, hour: int, minute: int = 0) -> None:
        self.realtime = False
        self.sim_minute = int(np.clip(hour, 0, 23)) * 60 + int(np.clip(minute, 0, 59))

    def seek_minutes(self, delta: int) -> None:
        self.realtime = False
        self.sim_minute += int(delta)

    def use_realtime(self) -> None:
        self.realtime = True
        self.paused = False

    @property
    def day_index(self) -> int:
        return self.current_dt().toordinal()

    @property
    def time_of_day(self) -> float:
        dt = self.current_dt()
        return (dt.hour * 3600 + dt.minute * 60 + dt.second) / 86400.0

    def phase(self) -> str:
        return phase_from_hour(self.current_dt().hour)

    def light_level(self) -> float:
        dt = self.current_dt()
        return light_level_from_hour(dt.hour, dt.minute)

    def season(self) -> str:
        return _season_for_month(self.current_dt().month)

    def clock_label(self) -> str:
        return self.current_dt().strftime("%H:%M")

    def local_hour(self) -> int:
        return self.current_dt().hour

    def to_dict(self) -> dict[str, Any]:
        dt = self.current_dt()
        return {
            "tick": self.tick,
            "ticks_per_day": self.ticks_per_day,
            "realtime": self.realtime,
            "paused": self.paused,
            "time_scale": round(self.time_scale, 2),
            "sim_day_offset": self.sim_day_offset,
            "sim_minute": self.sim_minute,
            "minutes_per_tick": round(self.minutes_per_tick, 2),
            "turbo": self.turbo,
            "learning_multiplier": round(self.learning_multiplier, 2),
            "time_of_day": round(self.time_of_day, 3),
            "phase": self.phase(),
            "phase_label": PHASE_LABELS_ES.get(self.phase(), self.phase()),
            "light_level": round(self.light_level(), 3),
            "season": self.season(),
            "day": self.day_index,
            "clock": self.clock_label(),
            "hour": dt.hour,
            "minute": dt.minute,
            "weekday": dt.strftime("%A").lower(),
        }

    @classmethod
    def from_dict(cls, data: dict | None) -> WorldClock:
        if not data:
            return cls()
        return cls(
            tick=int(data.get("tick", 0)),
            ticks_per_day=int(data.get("ticks_per_day", 200)),
            realtime=bool(data.get("realtime", True)),
            paused=bool(data.get("paused", False)),
            time_scale=float(data.get("time_scale", 1.0)),
            sim_day_offset=int(data.get("sim_day_offset", 0)),
            sim_minute=int(data.get("sim_minute", 0)),
            minutes_per_tick=float(data.get("minutes_per_tick", 7.2)),
            turbo=bool(data.get("turbo", False)),
            learning_multiplier=float(data.get("learning_multiplier", 1.0)),
        )


def hero_zone_for_room(room: str) -> dict[str, str]:
    return dict(ROOM_HERO_ZONE.get(room, ROOM_HERO_ZONE["casa"]))


def ambient_temperature(room: str, *, phase: str, season: str, base: float, hour: int = 12) -> float:
    temp = base
    if room == "jardín":
        if phase == "night" or hour >= 22 or hour < 5:
            temp -= 0.26
        elif phase == "dawn" or 5 <= hour < 7:
            temp -= 0.1
        elif phase == "dusk" or 20 <= hour < 22:
            temp -= 0.12
        if season == "invierno":
            temp -= 0.14
        elif season == "verano":
            temp += 0.1
    elif room in ("casa", "dormitorio", "baño"):
        if phase == "night" or hour >= 22 or hour < 6:
            temp += 0.06
    return float(max(0.05, min(0.95, temp)))
