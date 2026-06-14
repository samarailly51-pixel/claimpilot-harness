from __future__ import annotations

from pathlib import Path
from typing import Any

from .agents import run_agent
from .cases import load_case
from .replay import render_replay, render_suite_report
from .scorer import score_decision


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
    report_path = render_suite_report(rows, agents_summary, output_dir)
    return {
        "total_cases": len(case_paths),
        "agents": agents_summary,
        "results": rows,
        "report": str(report_path),
    }


def discover_cases(path: str | Path) -> list[Path]:
    target = Path(path)
    if target.is_dir():
        return sorted(target.glob("*.json"))
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
