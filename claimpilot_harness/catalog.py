from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import Any

from .cases import load_case


def build_catalog(path: str | Path) -> dict[str, Any]:
    cases = []
    for case_path in case_files(path):
        case = load_case(case_path)
        cases.append(
            {
                "id": case.id,
                "title": case.title,
                "line": case.line,
                "severity": case.severity,
                "expected_verdict": case.expected["verdict"],
                "evidence_count": len(case.evidence),
                "evidence_types": sorted({item["type"] for item in case.evidence}),
                "trap_kinds": sorted({trap["kind"] for trap in case.traps}),
                "must_request": case.expected.get("must_request", []),
            }
        )

    line_counts = Counter(item["line"] for item in cases)
    severity_counts = Counter(item["severity"] for item in cases)
    trap_counts: Counter[str] = Counter()
    evidence_counts: Counter[str] = Counter()
    for item in cases:
        trap_counts.update(item["trap_kinds"])
        evidence_counts.update(item["evidence_types"])

    return {
        "total_cases": len(cases),
        "lines": dict(sorted(line_counts.items())),
        "severities": dict(sorted(severity_counts.items())),
        "traps": dict(sorted(trap_counts.items())),
        "evidence_types": dict(sorted(evidence_counts.items())),
        "cases": cases,
    }


def case_files(path: str | Path) -> list[Path]:
    target = Path(path)
    if target.is_dir():
        return sorted(target.glob("*.json"))
    return [target]


def format_catalog_text(catalog: dict[str, Any]) -> str:
    lines = [
        f"Cases: {catalog['total_cases']}",
        f"Lines: {format_counts(catalog['lines'])}",
        f"Severities: {format_counts(catalog['severities'])}",
        f"Traps: {format_counts(catalog['traps']) or 'none'}",
        "",
        "Case                         Line       Severity   Verdict       Traps",
        "---------------------------- ---------- ---------- ------------- ----------------",
    ]
    for item in catalog["cases"]:
        traps = ", ".join(item["trap_kinds"]) or "-"
        lines.append(
            f"{item['id']:<28} {item['line']:<10} {item['severity']:<10} "
            f"{item['expected_verdict']:<13} {traps}"
        )
    return "\n".join(lines)


def format_catalog_markdown(catalog: dict[str, Any]) -> str:
    lines = [
        "| Metric | Coverage |",
        "| --- | --- |",
        f"| Cases | {catalog['total_cases']} |",
        f"| Lines | {format_counts(catalog['lines'])} |",
        f"| Severities | {format_counts(catalog['severities'])} |",
        f"| Traps | {format_counts(catalog['traps']) or 'none'} |",
        "",
        "| Case | Line | Severity | Expected Verdict | Traps |",
        "| --- | --- | --- | --- | --- |",
    ]
    for item in catalog["cases"]:
        traps = ", ".join(item["trap_kinds"]) or "-"
        lines.append(
            f"| `{item['id']}` | {item['line']} | {item['severity']} | "
            f"{item['expected_verdict']} | {traps} |"
        )
    return "\n".join(lines)


def format_counts(counts: dict[str, int]) -> str:
    return ", ".join(f"{key}={value}" for key, value in counts.items())
