from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .agents import run_agent
from .cases import load_case
from .replay import render_replay, render_suite_report
from .scorer import score_decision

CASE_TEMPLATE_NAME = "template-case.json"


def run_suite(
    cases_path: str | Path,
    agents: list[str],
    output_dir: str | Path = "runs",
    agent_url: str | None = None,
    agent_timeout: int = 90,
    openai_model: str | None = None,
    openai_base_url: str = "https://api.openai.com/v1",
    openai_api_key_env: str = "OPENAI_API_KEY",
) -> dict[str, Any]:
    case_paths = discover_cases(cases_path)
    if not case_paths:
        raise ValueError("suite requires at least one case JSON file")

    rows = []
    for case_path in case_paths:
        case = load_case(case_path)
        for agent in agents:
            decision = run_agent(
                case,
                agent=agent,
                http_url=agent_url,
                http_timeout=agent_timeout,
                openai_model=openai_model,
                openai_base_url=openai_base_url,
                openai_api_key_env=openai_api_key_env,
            )
            score = score_decision(case, decision)
            replay_path = render_replay(case, agent, decision, score, output_dir, update_latest=False)
            rows.append(
                {
                    "case_id": case.id,
                    "case_title": case.title,
                    "line": case.line,
                    "severity": case.severity,
                    "agent": agent,
                    "verdict": decision.verdict,
                    "score": score,
                    "replay": str(replay_path),
                }
            )

    agents_summary = summarize_agents(rows, agents)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    report_path = render_suite_report(rows, agents_summary, out_dir)
    results_path = out_dir / "suite-results.json"
    payload = {
        "total_cases": len(case_paths),
        "agents": agents_summary,
        "results": compact_results(rows, out_dir),
        "report": artifact_path(report_path, out_dir),
    }
    results_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return {
        **payload,
        "results_file": str(results_path),
    }


def discover_cases(path: str | Path) -> list[Path]:
    target = Path(path)
    if target.is_dir():
        return sorted(item for item in target.glob("*.json") if item.name != CASE_TEMPLATE_NAME)
    return [target]


def summarize_agents(rows: list[dict[str, Any]], agents: list[str]) -> list[dict[str, Any]]:
    summary = []
    for agent in agents:
        agent_rows = [row for row in rows if row["agent"] == agent]
        if not agent_rows:
            continue
        scores = [row["score"]["percent"] for row in agent_rows]
        passed = sum(1 for row in agent_rows if row["score"]["grade"] == "pass")
        summary.append(
            {
                "agent": agent,
                "average_score": round(sum(scores) / len(scores), 1),
                "passed": passed,
                "failed": len(agent_rows) - passed,
                "pass_rate": round((passed / len(agent_rows)) * 100, 1),
            }
        )
    return sorted(summary, key=lambda item: item["average_score"], reverse=True)


def evaluate_quality_gate(
    agents_summary: list[dict[str, Any]],
    min_average_score: float | None = None,
    min_pass_rate: float | None = None,
) -> dict[str, Any]:
    failures = []
    for item in agents_summary:
        reasons = []
        if min_average_score is not None and item["average_score"] < min_average_score:
            reasons.append(
                f"average_score {item['average_score']}% is below {min_average_score}%"
            )
        if min_pass_rate is not None and item["pass_rate"] < min_pass_rate:
            reasons.append(f"pass_rate {item['pass_rate']}% is below {min_pass_rate}%")
        if reasons:
            failures.append({"agent": item["agent"], "reasons": reasons})

    return {
        "ok": not failures,
        "min_average_score": min_average_score,
        "min_pass_rate": min_pass_rate,
        "failures": failures,
    }


def compact_results(rows: list[dict[str, Any]], base_dir: Path) -> list[dict[str, Any]]:
    return [
        {
            "case_id": item["case_id"],
            "case_title": item["case_title"],
            "line": item["line"],
            "severity": item["severity"],
            "agent": item["agent"],
            "verdict": item["verdict"],
            "score": item["score"]["percent"],
            "grade": item["score"]["grade"],
            "earned": item["score"]["earned"],
            "total": item["score"]["total"],
            "replay": artifact_path(Path(item["replay"]), base_dir),
        }
        for item in rows
    ]


def artifact_path(path: Path, base_dir: Path) -> str:
    try:
        return path.resolve().relative_to(base_dir.resolve()).as_posix()
    except ValueError:
        return str(path)
