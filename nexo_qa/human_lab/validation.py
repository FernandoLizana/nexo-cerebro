"""Human study and dataset validation."""

from __future__ import annotations

from nexo_qa.human_lab.models import HumanCalibrationDataset, HumanStudySpec, HumanTaskProtocol


def validate_study_spec(spec: HumanStudySpec) -> list[str]:
    errors: list[str] = []
    if not spec.study_id:
        errors.append("study_id required")
    if not spec.tasks:
        errors.append("at least one task required")
    if not spec.consent_version:
        errors.append("consent_version required")
    for task in spec.tasks:
        errors.extend(validate_task_protocol(task))
    return errors


def validate_task_protocol(task: HumanTaskProtocol) -> list[str]:
    errors: list[str] = []
    if not task.task_id:
        errors.append("task_id required")
    if not task.task_version:
        errors.append(f"{task.task_id}: task_version required")
    if not task.environment_version:
        errors.append(f"{task.task_id}: environment_version required")
    return errors


def validate_dataset(dataset: HumanCalibrationDataset) -> list[str]:
    errors: list[str] = []
    if not dataset.dataset_id:
        errors.append("dataset_id required")
    if dataset.run_count != len(dataset.runs):
        errors.append("run_count mismatch")
    return errors
