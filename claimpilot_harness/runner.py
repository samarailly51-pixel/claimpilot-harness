from __future__ import annotations

from pathlib import Path

from .agents import run_agent
from .cases import load_case
from .models import RunResult
from .replay import render_leaderboard, render_replay
from .scorer import score_decision


def run_case(
    case_path: str | Path,
    agent: str,
    output_dir: str | Path = "runs",
    agent_command: str | None = None,
) -> RunResult:
    case = load_case(case_path)
    decision = run_agent(case, agent=agent, command=agent_command)
    score = score_decision(case, decision)
    report = render_replay(case, agent, decision, score, output_dir)
    return RunResult(case, agent, decision, score, str(report))


def compare_agents(
    case_path: str | Path,
    agents: list[str],
    output_dir: str | Path = "runs",
) -> dict:
    case = load_case(case_path)
    results = []
    for agent in agents:
        decision = run_agent(case, agent=agent)
        score = score_decision(case, decision)
        replay_path = render_replay(case, agent, decision, score, output_dir, update_latest=False)
        results.append(
            {
                "agent": agent,
                "decision": decision,
                "score": score,
                "replay": str(replay_path),
            }
        )
    leaderboard = render_leaderboard(case, results, output_dir)
    return {
        "case": case,
        "results": sorted(results, key=lambda item: item["score"]["percent"], reverse=True),
        "leaderboard": str(leaderboard),
    }
