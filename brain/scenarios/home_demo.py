"""Escenarios de dominio demo (separación núcleo / contenido)."""

from __future__ import annotations

# Esquemas específicos de demo educativa — no parte del núcleo cognitivo mínimo.
DOMAIN_ACTION_SCHEMAS: tuple[dict[str, str], ...] = (
    {"key": "clinical", "drive": "seek_curiosity", "label": "neurología clínica (UDD)", "target": "desk"},
    {"key": "biopsych", "drive": "seek_curiosity", "label": "biological psychology", "target": "desk"},
    {"key": "infant", "drive": "seek_curiosity", "label": "libro infantil del cerebro", "target": "desk"},
    {"key": "study", "drive": "seek_curiosity", "label": "estudiar neurociencia", "target": "desk"},
)
