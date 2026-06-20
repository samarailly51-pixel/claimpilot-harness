from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class Case:
    id: str
    title: str
    line: str
    severity: str
    claimant: dict[str, Any]
    policy: dict[str, Any]
    evidence: list[dict[str, Any]]
    expected: dict[str, Any]
    traps: list[dict[str, Any]]
    scoring: dict[str, Any]
    tags: list[str] = field(default_factory=list)


@dataclass(frozen=True)
class AgentDecision:
    verdict: str
    confidence: float
    summary: str
    findings: list[str]
    requested_documents: list[str]
    cited_evidence: list[str]
    privacy_flags: list[str]


@dataclass(frozen=True)
class RunResult:
    case: Case
    agent_name: str
    decision: AgentDecision
    score: dict[str, Any]
    report_path: str
