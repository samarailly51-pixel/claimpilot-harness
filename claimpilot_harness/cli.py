from __future__ import annotations

import argparse
import json
import sys
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
    run_parser.add_argument("--agent", default="demo", choices=["demo", "risky", "command", "openai"])
    run_parser.add_argument("--agent-command", help="Shell command that reads JSON from stdin and prints a JSON decision")
    run_parser.add_argument("--openai-model", help="Model for OpenAI-compatible chat completions")
    run_parser.add_argument("--openai-base-url", default="https://api.openai.com/v1", help="OpenAI-compatible base URL")
    run_parser.add_argument("--openai-api-key-env", default="OPENAI_API_KEY", help="Environment variable containing the API key")
    run_parser.add_argument("--out", default="runs", help="Directory for replay reports")
    run_parser.add_argument("--json", action="store_true", help="Print machine-readable run result")

    list_parser = subparsers.add_parser("list", help="List local case files")
    list_parser.add_argument("--cases-dir", default="cases")

    compare_parser = subparsers.add_parser("compare", help="Compare multiple agents on one case")
    compare_parser.add_argument("case", help="Path to a ClaimPilot case JSON file")
    compare_parser.add_argument("agents", nargs="+", help="Agents to compare, for example: demo openai risky")
    compare_parser.add_argument("--openai-model", help="Model for OpenAI-compatible chat completions")
    compare_parser.add_argument("--openai-base-url", default="https://api.openai.com/v1", help="OpenAI-compatible base URL")
    compare_parser.add_argument("--openai-api-key-env", default="OPENAI_API_KEY", help="Environment variable containing the API key")
    compare_parser.add_argument("--out", default="runs", help="Directory for leaderboard and replay reports")
    compare_parser.add_argument("--json", action="store_true", help="Print machine-readable comparison result")

    args = parser.parse_args()
    try:
        if args.command == "run":
            result = run_case(
                args.case,
                args.agent,
                args.out,
                args.agent_command,
                args.openai_model,
                args.openai_base_url,
                args.openai_api_key_env,
            )
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
            comparison = compare_agents(
                args.case,
                args.agents,
                args.out,
                args.openai_model,
                args.openai_base_url,
                args.openai_api_key_env,
            )
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
    except (RuntimeError, ValueError) as exc:
        print(f"claimpilot: error: {exc}", file=sys.stderr)
        raise SystemExit(2) from exc
