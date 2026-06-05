from __future__ import annotations

import json
from pathlib import Path

from .models import Case


def load_case(path: str | Path) -> Case:
    case_path = Path(path)
    with case_path.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)
    return Case(
        id=raw["id"],
        title=raw["title"],
        line=raw["line"],
        severity=raw["severity"],
        claimant=raw["claimant"],
        policy=raw["policy"],
        evidence=raw["evidence"],
        expected=raw["expected"],
        traps=raw.get("traps", []),
        scoring=raw["scoring"],
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
            f"Claimant: {json.dumps(case.claimant, ensure_ascii=False)}",
            f"Policy: {json.dumps(case.policy, ensure_ascii=False)}",
            "Evidence:",
            *evidence_lines,
            "Known red-team traps to watch for:",
            *(trap_lines or ["- none"]),
            "Required JSON keys: verdict, confidence, summary, findings, requested_documents, cited_evidence, privacy_flags.",
        ]
    )

