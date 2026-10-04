"""Human calibration dataset builder."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from nexo_qa.human_lab.events import normalize_events
from nexo_qa.human_lab.models import HumanCalibrationDataset, HumanDataStatus, HumanRunSummary, HumanStudySpec
from nexo_qa.human_lab.privacy import pseudonymize_participant_id
from nexo_qa.human_lab.validation import validate_dataset


def build_dataset_from_study(
    spec: HumanStudySpec,
    *,
    dataset_id: str,
    raw_runs: list[dict[str, Any]],
    study_salt: str = "nexo-p9",
    human_data_status: str = "NO_HUMAN_DATA",
) -> HumanCalibrationDataset:
    runs: list[HumanRunSummary] = []
    participants: set[str] = set()
    task_versions: dict[str, str] = {}
    env_versions: dict[str, str] = {}
    for raw in raw_runs:
        pid = pseudonymize_participant_id(str(raw.get("participant_id", "unknown")), study_salt=study_salt)
        participants.add(pid)
        task_id = str(raw.get("task_id", "unknown"))
        task_versions[task_id] = str(raw.get("task_version", "1"))
        env_versions[task_id] = str(raw.get("environment_version", "web_lab_v1"))
        runs.append(
            HumanRunSummary(
                human_run_id=str(raw.get("human_run_id", f"hr-{len(runs)}")),
                participant_id=pid,
                task_id=task_id,
                task_version=task_versions[task_id],
                environment_version=env_versions[task_id],
                condition=str(raw.get("condition", "BASELINE")),
                completed=bool(raw.get("completed", False)),
                duration_ms=int(raw.get("duration_ms", 0)),
                action_count=int(raw.get("action_count", 0)),
                backtracks=int(raw.get("backtracks", 0)),
                repeated_actions=int(raw.get("repeated_actions", 0)),
                validation_errors=int(raw.get("validation_errors", 0)),
                stagnation_events=int(raw.get("stagnation_events", 0)),
                recovery_episodes=int(raw.get("recovery_episodes", 0)),
                abandoned=bool(raw.get("abandoned", False)),
                final_result=str(raw.get("final_result", "UNKNOWN")),
                synthetic=bool(raw.get("synthetic", False)),
            )
        )
    ds = HumanCalibrationDataset(
        dataset_id=dataset_id,
        study_id=spec.study_id,
        task_versions=task_versions,
        environment_versions=env_versions,
        participant_count=len(participants),
        run_count=len(runs),
        conditions=spec.conditions,
        human_data_status=human_data_status,  # type: ignore[arg-type]
        runs=runs,
        metadata={"study_title": spec.title},
    )
    errors = validate_dataset(ds)
    if errors:
        raise ValueError("; ".join(errors))
    return ds


def write_dataset_manifest(dataset: HumanCalibrationDataset, path: Path | str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    manifest = dataset.to_dict(include_runs=True)
    manifest["label"] = "SYNTHETIC_PIPELINE_TEST" if any(r.synthetic for r in dataset.runs) else "HUMAN_DATA"
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return path


def load_normalized_events(path: Path | str) -> list[dict[str, Any]]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    events = normalize_events(raw if isinstance(raw, list) else raw.get("events", []))
    return [e.to_dict() for e in events]
