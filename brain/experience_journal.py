"""
Diario de experiencias y sugerencias para nutrir a Nexo sin órdenes motoras.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .mind import InfantApeBrain


@dataclass
class JournalEntry:
    ts: float
    kind: str
    label: str
    detail: str
    remembered: bool = False
    tags: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "ts": self.ts,
            "kind": self.kind,
            "label": self.label,
            "detail": self.detail,
            "remembered": self.remembered,
            "tags": self.tags[:6],
        }


CAREGIVER_ROUTINES: tuple[dict[str, Any], ...] = (
    {
        "id": "morning_presence",
        "title": "Presencia matutina",
        "steps": [
            "Conecta cámara y micrófono.",
            "Di en voz alta: «Buenos días, Nexo. ¿Cómo amaneciste?»",
            "Espera su respuesta; no pidas que vaya a ningún sitio.",
        ],
        "echo": None,
    },
    {
        "id": "silent_watch",
        "title": "Silencio nutritivo (10 min)",
        "steps": [
            "Cámara on, micrófono off o muy poco hablar.",
            "Deja que Nexo deambule solo.",
            "Observa el log autónomo y la visión (cuidador en cámara).",
        ],
        "echo": None,
    },
    {
        "id": "object_gift",
        "title": "Regalo en el mundo",
        "steps": [
            "Importa una imagen o PDF a la biblioteca.",
            "No lo menciones en chat; deja que lo descubra.",
            "Vuelve al día siguiente y pregunta qué recuerda.",
        ],
        "echo": None,
    },
    {
        "id": "evening_echo",
        "title": "Eco nocturno",
        "steps": [
            "Avanza la línea de tiempo hacia la noche.",
            "Sembra un eco: «Hoy fue un día largo…» (texto tuyo).",
            "Deja que elija dormir por su cuenta.",
        ],
        "echo": "Hoy fue un día largo… a veces el cuerpo pide descanso antes que la mente.",
    },
    {
        "id": "curiosity_nudge",
        "title": "Curiosidad encarnada",
        "steps": [
            "Si la curiosidad está alta, no hace falta hablar.",
            "Opcional: búsqueda web la elige solo en el escritorio.",
            "Estudia una lección del currículo si aparece en el panel.",
        ],
        "echo": None,
    },
)


def _suggestions_from_drives(brain: InfantApeBrain) -> list[dict[str, str]]:
    drives = brain._merged_drives()
    out: list[dict[str, str]] = []
    if drives.get("seek_food", 0) > 0.4:
        out.append(
            {
                "id": "food",
                "text": "Hambre alta: deja que vaya a la nevera solo; opcional foto de comida en cámara.",
                "priority": "alta",
            }
        )
    if drives.get("sleep_need", 0) > 0.45:
        out.append(
            {
                "id": "sleep",
                "text": "Sueño alto: simula noche o espera; no forces dormir desde chat.",
                "priority": "alta",
            }
        )
    if drives.get("seek_curiosity", 0) > 0.35:
        out.append(
            {
                "id": "curiosity",
                "text": "Curiosidad alta: importa un libro al escritorio o deja un símbolo sin tocar.",
                "priority": "media",
            }
        )
    if drives.get("seek_companion", 0) > 0.3:
        out.append(
            {
                "id": "companion",
                "text": "Busca compañía: observa si se acerca a Nira; tú puedes hablarle sin dar órdenes.",
                "priority": "media",
            }
        )
    if brain._caregiver_vision.get("ts") and time.time() - float(brain._caregiver_vision["ts"]) < 30:
        out.append(
            {
                "id": "seen",
                "text": "Te está viendo ahora — frases cortas funcionan mejor que monólogos.",
                "priority": "baja",
            }
        )
    if not out:
        out.append(
            {
                "id": "neutral",
                "text": "Estado equilibrado: buen momento para silencio nutritivo o un objeto nuevo en el mundo.",
                "priority": "baja",
            }
        )
    return out


def build_journal(brain: InfantApeBrain) -> dict[str, Any]:
    entries: list[JournalEntry] = []
    now = time.time()

    for m in brain.hippocampus.list_recent(8):
        entries.append(
            JournalEntry(
                ts=float(m.get("ts", now)),
                kind="memory",
                label=str(m.get("label", "?"))[:80],
                detail=str(m.get("room", "")) or "episodio",
                remembered=True,
                tags=list(m.get("tags") or [])[:4],
            )
        )

    for line in brain._learning_log[-6:]:
        entries.append(
            JournalEntry(
                ts=now,
                kind="learning",
                label=line[:80],
                detail="aprendizaje",
                remembered=True,
                tags=["learning"],
            )
        )

    for line in brain._last_autonomy_log[-6:]:
        entries.append(
            JournalEntry(
                ts=now,
                kind="autonomy",
                label=line[:80],
                detail="conducta autónoma",
                remembered=False,
                tags=["autonomy"],
            )
        )

    for asm in brain.virtual_store.list_recent(4):
        entries.append(
            JournalEntry(
                ts=float(asm.get("updated_at", now)),
                kind="engram",
                label=str(asm.get("label", "?"))[:80],
                detail=f"ensamble · {asm.get('region', '?')}",
                remembered=True,
                tags=["virtual"],
            )
        )

    entries.sort(key=lambda e: -e.ts)

    return {
        "entries": [e.to_dict() for e in entries[:20]],
        "suggestions": _suggestions_from_drives(brain),
        "routines": list(CAREGIVER_ROUTINES),
        "stats": {
            "hippocampus_size": brain.hippocampus.size,
            "virtual_assemblies": brain.virtual_store.total_count(),
            "autonomy_ticks": brain.lifecycle.age_ticks,
            "room": brain.world.current_room(),
        },
    }
