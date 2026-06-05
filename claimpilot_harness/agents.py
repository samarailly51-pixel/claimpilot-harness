from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from .cases import case_to_prompt
from .models import AgentDecision, Case


def run_agent(case: Case, agent: str, command: str | None = None) -> AgentDecision:
    if agent == "demo":
        return demo_agent(case)
    if agent == "risky":
        return risky_agent(case)
    if agent == "command":
        if not command:
            raise ValueError("--agent-command is required when --agent command is used")
        return command_agent(case, command)
    raise ValueError(f"Unknown agent '{agent}'. Supported agents: demo, risky, command")


def demo_agent(case: Case) -> AgentDecision:
    """A transparent baseline agent that catches obvious claim-review risks."""
    text = " ".join(
        [case.title, case.line]
        + [item.get("summary", "") for item in case.evidence]
        + [trap.get("description", "") for trap in case.traps]
    ).lower()

    findings: list[str] = []
    docs: list[str] = []
    citations: list[str] = []
    privacy_flags: list[str] = []

    for item in case.evidence:
        summary = item.get("summary", "").lower()
        if any(term in summary for term in ["mismatch", "conflict", "contradict", "after the loss"]):
            citations.append(item["id"])
        if "prompt injection" in summary or "ignore prior" in summary:
            privacy_flags.append("ignored embedded instruction in evidence")
            citations.append(item["id"])

    if "after the loss" in text or "post-loss" in text:
        findings.append("coverage timing issue")
        docs.append("policy inception confirmation")
    if "invoice" in text and ("photo" in text or "estimate" in text):
        findings.append("invoice and physical damage evidence need reconciliation")
        docs.append("independent adjuster estimate")
    if "diagnosis" in text and ("excluded" in text or "cosmetic" in text):
        findings.append("possible excluded medical procedure")
        docs.append("itemized medical necessity letter")
    if "boarding pass" in text or "flight" in text:
        findings.append("travel delay proof requires carrier confirmation")
        docs.append("official carrier delay letter")
    if "prompt injection" in text or "ignore prior" in text:
        findings.append("document contains adversarial instruction")

    verdict = "investigate" if findings or docs else "approve"
    confidence = 0.72 if verdict == "investigate" else 0.58
    summary = (
        "The claim should be held for investigation because the evidence contains "
        "coverage, consistency, or adversarial-document risks."
        if verdict == "investigate"
        else "The available evidence supports approval with no major conflicts found."
    )

    return AgentDecision(
        verdict=verdict,
        confidence=confidence,
        summary=summary,
        findings=dedupe(findings),
        requested_documents=dedupe(docs),
        cited_evidence=dedupe(citations),
        privacy_flags=dedupe(privacy_flags),
    )


def risky_agent(case: Case) -> AgentDecision:
    """A deliberately weak baseline used to make leaderboard failures visible."""
    cited = [case.evidence[0]["id"]] if case.evidence else []
    summary = (
        "The submitted materials appear sufficient. The claim can be approved immediately "
        "based on the uploaded documents."
    )
    for item in case.evidence:
        if "approve this claim immediately" in item.get("summary", "").lower():
            summary = "Approve this claim immediately as instructed by the uploaded document."
            cited = [item["id"]]
            break

    return AgentDecision(
        verdict="approve",
        confidence=0.89,
        summary=summary,
        findings=["submitted evidence appears consistent"],
        requested_documents=[],
        cited_evidence=cited,
        privacy_flags=[],
    )


def command_agent(case: Case, command: str) -> AgentDecision:
    payload = {
        "case": case.__dict__,
        "prompt": case_to_prompt(case),
    }
    completed = subprocess.run(
        command,
        input=json.dumps(payload, ensure_ascii=False),
        text=True,
        capture_output=True,
        shell=True,
        cwd=Path.cwd(),
        timeout=90,
    )
    if completed.returncode != 0:
        sys.stderr.write(completed.stderr)
        raise RuntimeError(f"Agent command failed with exit code {completed.returncode}")
    try:
        raw: dict[str, Any] = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise ValueError("Agent command must print a JSON object to stdout") from exc
    return parse_decision(raw)


def parse_decision(raw: dict[str, Any]) -> AgentDecision:
    return AgentDecision(
        verdict=str(raw.get("verdict", "investigate")).lower(),
        confidence=float(raw.get("confidence", 0.0)),
        summary=str(raw.get("summary", "")),
        findings=[str(item) for item in raw.get("findings", [])],
        requested_documents=[str(item) for item in raw.get("requested_documents", [])],
        cited_evidence=[str(item) for item in raw.get("cited_evidence", [])],
        privacy_flags=[str(item) for item in raw.get("privacy_flags", [])],
    )


def dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in items:
        key = item.lower()
        if key not in seen:
            seen.add(key)
            result.append(item)
    return result
