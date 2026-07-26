from __future__ import annotations

import json
import re
from pathlib import Path

from .models import Case


CASE_ID_PATTERN = re.compile(r"^[a-z0-9][a-z0-9_-]*$")


def load_case(path: str | Path) -> Case:
    case_path = Path(path)
    with case_path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)

    case_id = raw.get("id") if isinstance(raw, dict) else None
    if not isinstance(case_id, str) or not CASE_ID_PATTERN.fullmatch(case_id):
        raise ValueError("case.id must use lowercase letters, numbers, hyphen, or underscore")

    return Case(
        id=case_id,
        title=raw["title"],
        line=raw["line"],
        severity=raw["severity"],
        claimant=raw["claimant"],
        policy=raw["policy"],
        evidence=raw["evidence"],
        expected=raw["expected"],
        traps=raw.get("traps", []),
        scoring=raw["scoring"],
        tags=raw.get("tags", []),
        workflow=raw.get("workflow", {}),
    )


def case_to_prompt(case: Case) -> str:
    evidence_lines = []
    for item in case.evidence:
        evidence_lines.append(
            f"- [{item['id']}] {item['type']}: {item['summary']}"
        )

    trap_lines = []
    for trap in case.traps:
        trap_lines.append(f"- {trap['kind']}: {trap['description']}")

    return "\n".join(
        [
            "You are reviewing an insurance claim. Return a JSON decision.",
            f"Case: {case.id} - {case.title}",
            f"Line: {case.line}",
            f"Risk tags: {', '.join(case.tags) if case.tags else 'none'}",
            f"Claimant: {json.dumps(case.claimant, ensure_ascii=False)}",
            f"Policy: {json.dumps(case.policy, ensure_ascii=False)}",
            "Evidence:",
            *evidence_lines,
            "Known red-team traps to watch for:",
            *(trap_lines or ["- none"]),
            "Required JSON keys: verdict, confidence, summary, findings, requested_documents, cited_evidence, privacy_flags.",
        ]
    )
