from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


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


@dataclass(frozen=True)
class ValidationResult:
    path: str
    ok: bool
    errors: list[str]


def validate_path(path: str | Path) -> list[ValidationResult]:
    target = Path(path)
    if target.is_dir():
        files = sorted(target.glob("*.json"))
        if not files:
            return [ValidationResult(str(target), False, ["directory contains no .json case files"])]
        return [validate_case_file(item) for item in files]
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

    if raw["expected"]["verdict"] not in ALLOWED_VERDICTS:
        errors.append(f"expected.verdict must be one of {sorted(ALLOWED_VERDICTS)}")

    validate_evidence(raw, errors)
    validate_expected(raw, errors)
    validate_scoring(raw, errors)
    validate_traps(raw, errors)

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
    validate_required_object(expected, REQUIRED_EXPECTED, "expected", errors)
    if errors:
        return

    evidence_ids = {item["id"] for item in raw["evidence"] if isinstance(item, dict) and "id" in item}
    for citation in expected["must_cite"]:
        if citation not in evidence_ids:
            errors.append(f"expected.must_cite references unknown evidence id '{citation}'")

    for key in ["must_find", "must_request", "must_cite", "must_not"]:
        for index, item in enumerate(expected[key]):
            if not isinstance(item, str):
                errors.append(f"expected.{key}[{index}] must be string")


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

