from __future__ import annotations

import shutil
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from claimpilot_harness.suite import run_suite

DEMO_DIR = ROOT / "docs" / "demo"
CASES_DIR = ROOT / "cases"
DEMO_GIF = ROOT / "assets" / "claimpilot-demo.gif"


def main() -> None:
    DEMO_DIR.mkdir(parents=True, exist_ok=True)
    if DEMO_GIF.exists():
        shutil.copyfile(DEMO_GIF, DEMO_DIR / "claimpilot-demo.gif")

    suite = run_suite(
        cases_path=CASES_DIR,
        agents=["demo", "risky"],
        output_dir=DEMO_DIR,
    )

    print(f"Built demo site in {DEMO_DIR}")
    print(f"Suite report: {suite['report']}")
    for agent in suite["agents"]:
        print(
            f"{agent['agent']}: average={agent['average_score']}%, "
            f"pass_rate={agent['pass_rate']}%"
        )


if __name__ == "__main__":
    main()
