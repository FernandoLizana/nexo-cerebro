"""Perceptual diff between consecutive scenes."""

from __future__ import annotations

from nexo_qa.perception.models import PerceptualDiff, PerceptualScene


def diff_scenes(previous: PerceptualScene | None, current: PerceptualScene) -> PerceptualDiff:
    if previous is None:
        return PerceptualDiff(
            appeared=tuple(p.percept_id for p in current.percepts),
            disappeared=(),
            moved=(),
            text_changed=(),
            state_changed=(),
            salience_changed=(),
            focus_changed=bool(current.focused_percept_id),
        )
    prev_by_element = {p.source_element_id: p for p in previous.percepts}
    curr_by_element = {p.source_element_id: p for p in current.percepts}
    appeared = tuple(pid for eid, p in curr_by_element.items() if eid not in prev_by_element for pid in [p.percept_id])
    disappeared = tuple(
        pid for eid, p in prev_by_element.items() if eid not in curr_by_element for pid in [p.percept_id]
    )
    moved: list[str] = []
    text_changed: list[str] = []
    state_changed: list[str] = []
    salience_changed: list[str] = []
    for eid, curr in curr_by_element.items():
        prev = prev_by_element.get(eid)
        if not prev:
            continue
        if curr.bounding_box != prev.bounding_box:
            moved.append(curr.percept_id)
        if curr.text != prev.text:
            text_changed.append(curr.percept_id)
        if curr.state != prev.state:
            state_changed.append(curr.percept_id)
        if abs(curr.salience_score - prev.salience_score) > 0.05:
            salience_changed.append(curr.percept_id)
    focus_changed = previous.focused_percept_id != current.focused_percept_id
    return PerceptualDiff(
        appeared=appeared,
        disappeared=disappeared,
        moved=tuple(moved),
        text_changed=tuple(text_changed),
        state_changed=tuple(state_changed),
        salience_changed=tuple(salience_changed),
        focus_changed=focus_changed,
    )
