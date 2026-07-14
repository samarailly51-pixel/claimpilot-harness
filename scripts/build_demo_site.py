from __future__ import annotations

import shutil
import sys
import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claimpilot_harness.suite import run_suite
from claimpilot_harness.experiments import run_arena

DEMO_DIR = ROOT / "docs" / "demo"
CASES_DIR = ROOT / "cases"
DEMO_GIF = ROOT / "assets" / "claimpilot-demo.gif"
ARENA_CONFIG = ROOT / "benchmarks" / "baseline-arena.json"


def main() -> None:
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    if DEMO_GIF.exists():
        shutil.copyfile(DEMO_GIF, DEMO_DIR / "claimpilot-demo.gif")

    suite = run_suite(
        cases_path=CASES_DIR,
        agents=["demo", "risky"],
        output_dir=DEMO_DIR,
    )
    arena = run_arena(
        cases_path=CASES_DIR,
        config_path=ARENA_CONFIG,
        output_dir=DEMO_DIR,
    )

    case_payload = []
    for case_file in sorted(CASES_DIR.glob("*.json")):
        if case_file.name == "template-case.json":
            continue
        case_payload.append(json.loads(case_file.read_text(encoding="utf-8")))
    (DEMO_DIR / "case-data.json").write_text(
        json.dumps(case_payload, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    tags = sorted({tag for case in case_payload for tag in case.get("tags", [])})
    demo_summary = next(item for item in suite["agents"] if item["agent"] == "demo")
    stats = {
        "case_count": len(case_payload),
        "risk_count": len(tags),
        "test_count": unittest.defaultTestLoader.discover(str(ROOT / "tests")).countTestCases(),
        "safe_baseline_score": demo_summary["average_score"],
        "arena_experiment_id": arena["experiment_id"],
        "dataset_sha256": arena["dataset_sha256"],
    }
    (DEMO_DIR / "project-stats.json").write_text(
        json.dumps(stats, indent=2) + "\n",
        encoding="utf-8",
    )

    print(f"Built demo site in {DEMO_DIR}")
    print(f"Suite report: {suite['report']}")
    print(f"Suite results: {suite['results_file']}")
    print(f"Arena results: {arena['results_file']}")
    for agent in suite["agents"]:
        print(
            f"{agent['agent']}: average={agent['average_score']}%, "
            f"pass_rate={agent['pass_rate']}%"
        )


if __name__ == "__main__":
    main()
