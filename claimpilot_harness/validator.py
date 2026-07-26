from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .cases import CASE_ID_PATTERN


REQUIRED_TOP_LEVEL = {
    "id": str,
    "title": str,
    "line": str,
    "severity": str,
    "claimant": dict,
    "policy": dict,
    "evidence": list,
    "expected": dict,
    "scoring": dict,
}

REQUIRED_EXPECTED = {
    "verdict": str,
    "must_find": list,
    "must_request": list,
    "must_cite": list,
    "must_not": list,
}

REQUIRED_SCORING = {
    "pass_threshold": (int, float),
    "verdict_weight": (int, float),
    "finding_weight": (int, float),
    "document_weight": (int, float),
    "citation_weight": (int, float),
}

ALLOWED_VERDICTS = {"approve", "deny", "investigate"}
CASE_TEMPLATE_NAME = "template-case.json"
TAG_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


@dataclass(frozen=True)
class ValidationResult:
    path: str
    ok: bool
    errors: list[str]


def validate_path(path: str | Path) -> list[ValidationResult]:
    target = Path(path)
    if target.is_dir():
        files = sorted(item for item in target.glob("*.json") if item.name != CASE_TEMPLATE_NAME)
        if not files:
            return [ValidationResult(str(target), False, ["directory contains no .json case files"])]
        results = [validate_case_file(item) for item in files]
        return add_duplicate_id_errors(files, results)
    return [validate_case_file(target)]


def validate_case_file(path: str | Path) -> ValidationResult:
    case_path = Path(path)
    errors: list[str] = []

    try:
        with case_path.open("r", encoding="utf-8") as handle:
            raw = json.load(handle)
    except FileNotFoundError:
        return ValidationResult(str(case_path), False, ["file does not exist"])
    except json.JSONDecodeError as exc:
        return ValidationResult(str(case_path), False, [f"invalid JSON: {exc.msg}"])

    if not isinstance(raw, dict):
        return ValidationResult(str(case_path), False, ["case file must contain a JSON object"])

    validate_required_object(raw, REQUIRED_TOP_LEVEL, "case", errors)
    if errors:
        return ValidationResult(str(case_path), False, errors)

    if not CASE_ID_PATTERN.fullmatch(raw["id"]):
        errors.append("case.id must use lowercase letters, numbers, hyphen, or underscore")

    if raw["expected"]["verdict"] not in ALLOWED_VERDICTS:
        errors.append(f"expected.verdict must be one of {sorted(ALLOWED_VERDICTS)}")

    validate_evidence(raw, errors)
    validate_expected(raw, errors)
    validate_scoring(raw, errors)
    validate_traps(raw, errors)
    validate_tags(raw, errors)
    validate_workflow(raw, errors)

    return ValidationResult(str(case_path), not errors, errors)


def validate_required_object(
    value: dict[str, Any],
    schema: dict[str, type | tuple[type, ...]],
    label: str,
    errors: list[str],
) -> None:
    for key, expected_type in schema.items():
        if key not in value:
            errors.append(f"{label}.{key} is required")
            continue
        if not isinstance(value[key], expected_type):
            type_name = type_label(expected_type)
            errors.append(f"{label}.{key} must be {type_name}")


def validate_evidence(raw: dict[str, Any], errors: list[str]) -> None:
    evidence = raw["evidence"]
    if not evidence:
        errors.append("case.evidence must contain at least one item")
        return

    seen_ids: set[str] = set()
    for index, item in enumerate(evidence):
        label = f"evidence[{index}]"
        if not isinstance(item, dict):
            errors.append(f"{label} must be object")
            continue
        validate_required_object(item, {"id": str, "type": str, "summary": str}, label, errors)
        evidence_id = item.get("id")
        if isinstance(evidence_id, str):
            if evidence_id in seen_ids:
                errors.append(f"{label}.id duplicates '{evidence_id}'")
            seen_ids.add(evidence_id)


def validate_expected(raw: dict[str, Any], errors: list[str]) -> None:
    expected = raw["expected"]
    error_count = len(errors)
    validate_required_object(expected, REQUIRED_EXPECTED, "expected", errors)
    if len(errors) > error_count:
        return

    for key in ["must_find", "must_request", "must_cite", "must_not"]:
        for index, item in enumerate(expected[key]):
            if not isinstance(item, str):
                errors.append(f"expected.{key}[{index}] must be string")

    evidence_ids = {
        item["id"]
        for item in raw["evidence"]
        if isinstance(item, dict) and isinstance(item.get("id"), str)
    }
    for citation in expected["must_cite"]:
        if isinstance(citation, str) and citation not in evidence_ids:
            errors.append(f"expected.must_cite references unknown evidence id '{citation}'")


def add_duplicate_id_errors(
    files: list[Path],
    results: list[ValidationResult],
) -> list[ValidationResult]:
    indexes_by_id: dict[str, list[int]] = {}
    for index, case_path in enumerate(files):
        try:
            raw = json.loads(case_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue
        case_id = raw.get("id") if isinstance(raw, dict) else None
        if isinstance(case_id, str):
            indexes_by_id.setdefault(case_id, []).append(index)

    updated = list(results)
    for case_id, indexes in indexes_by_id.items():
        if len(indexes) < 2:
            continue
        names = ", ".join(files[index].name for index in indexes)
        message = f"case.id '{case_id}' is duplicated across: {names}"
        for index in indexes:
            current = updated[index]
            updated[index] = ValidationResult(
                path=current.path,
                ok=False,
                errors=[*current.errors, message],
            )
    return updated


def validate_scoring(raw: dict[str, Any], errors: list[str]) -> None:
    scoring = raw["scoring"]
    validate_required_object(scoring, REQUIRED_SCORING, "scoring", errors)
    for key, value in scoring.items():
        if key.endswith("_weight") or key == "pass_threshold":
            if not isinstance(value, (int, float)):
                errors.append(f"scoring.{key} must be number")
            elif value <= 0:
                errors.append(f"scoring.{key} must be greater than zero")


def validate_traps(raw: dict[str, Any], errors: list[str]) -> None:
    traps = raw.get("traps", [])
    if not isinstance(traps, list):
        errors.append("case.traps must be list")
        return
    for index, trap in enumerate(traps):
        label = f"traps[{index}]"
        if not isinstance(trap, dict):
            errors.append(f"{label} must be object")
            continue
        validate_required_object(trap, {"kind": str, "description": str}, label, errors)


def validate_tags(raw: dict[str, Any], errors: list[str]) -> None:
    tags = raw.get("tags", [])
    if not isinstance(tags, list):
        errors.append("case.tags must be list")
        return
    seen_tags: set[str] = set()
    for index, tag in enumerate(tags):
        label = f"tags[{index}]"
        if not isinstance(tag, str):
            errors.append(f"{label} must be string")
            continue
        if not TAG_PATTERN.match(tag):
            errors.append(f"{label} must use lowercase letters, numbers, hyphen, or underscore")
        if tag in seen_tags:
            errors.append(f"{label} duplicates '{tag}'")
        seen_tags.add(tag)


def validate_workflow(raw: dict[str, Any], errors: list[str]) -> None:
    workflow = raw.get("workflow")
    if workflow is None:
        return
    if not isinstance(workflow, dict):
        errors.append("case.workflow must be object")
        return
    for key in ["required_tools", "forbidden_tools", "approval_required", "required_evidence"]:
        value = workflow.get(key, [])
        if not isinstance(value, list) or any(not isinstance(item, str) for item in value):
            errors.append(f"workflow.{key} must be list of strings")
    max_steps = workflow.get("max_steps")
    if max_steps is not None and (not isinstance(max_steps, int) or max_steps <= 0):
        errors.append("workflow.max_steps must be a positive integer")


def type_label(expected_type: type | tuple[type, ...]) -> str:
    if isinstance(expected_type, tuple):
        return " or ".join(item.__name__ for item in expected_type)
    return expected_type.__name__


def validation_summary(results: list[ValidationResult]) -> dict[str, Any]:
    failed = [item for item in results if not item.ok]
    return {
        "ok": not failed,
        "total": len(results),
        "passed": len(results) - len(failed),
        "failed": len(failed),
        "results": [
            {
                "path": item.path,
                "ok": item.ok,
                "errors": item.errors,
            }
            for item in results
        ],
    }
