from __future__ import annotations

import argparse
import json
from pathlib import Path

from .runner import compare_agents, run_case


def main() -> None:
    parser = argparse.ArgumentParser(
        prog="claimpilot",
        description="Crash-test insurance claim AI agents.",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    run_parser = subparsers.add_parser("run", help="Run one claim case against an agent")
    run_parser.add_argument("case", help="Path to a ClaimPilot case JSON file")
    run_parser.add_argument("--agent", default="demo", choices=["demo", "risky", "command"])
    run_parser.add_argument("--agent-command", help="Shell command that reads JSON from stdin and prints a JSON decision")
    run_parser.add_argument("--out", default="runs", help="Directory for replay reports")
    run_parser.add_argument("--json", action="store_true", help="Print machine-readable run result")

    list_parser = subparsers.add_parser("list", help="List local case files")
    list_parser.add_argument("--cases-dir", default="cases")

    compare_parser = subparsers.add_parser("compare", help="Compare multiple built-in agents on one case")
    compare_parser.add_argument("case", help="Path to a ClaimPilot case JSON file")
    compare_parser.add_argument("agents", nargs="+", help="Built-in agents to compare, for example: demo risky")
    compare_parser.add_argument("--out", default="runs", help="Directory for leaderboard and replay reports")
    compare_parser.add_argument("--json", action="store_true", help="Print machine-readable comparison result")

    args = parser.parse_args()
    if args.command == "run":
        result = run_case(args.case, args.agent, args.out, args.agent_command)
        payload = {
            "case_id": result.case.id,
            "agent": result.agent_name,
            "verdict": result.decision.verdict,
            "score": result.score["percent"],
            "grade": result.score["grade"],
            "report": result.report_path,
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"Case:   {payload['case_id']}")
            print(f"Agent:  {payload['agent']}")
            print(f"Verdict:{payload['verdict']:>12}")
            print(f"Score:  {payload['score']}% ({payload['grade']})")
            print(f"Replay: {payload['report']}")
    elif args.command == "list":
        for path in sorted(Path(args.cases_dir).glob("*.json")):
            print(path)
    elif args.command == "compare":
        comparison = compare_agents(args.case, args.agents, args.out)
        payload = {
            "case_id": comparison["case"].id,
            "leaderboard": comparison["leaderboard"],
            "results": [
                {
                    "agent": item["agent"],
                    "verdict": item["decision"].verdict,
                    "score": item["score"]["percent"],
                    "grade": item["score"]["grade"],
                    "replay": item["replay"],
                }
                for item in comparison["results"]
            ],
        }
        if args.json:
            print(json.dumps(payload, ensure_ascii=False, indent=2))
        else:
            print(f"Case:        {payload['case_id']}")
            print(f"Leaderboard: {payload['leaderboard']}")
            print("")
            print("Agent        Score    Verdict")
            print("------------ -------- ------------")
            for item in payload["results"]:
                print(f"{item['agent']:<12} {item['score']:>5}%   {item['verdict']}")
