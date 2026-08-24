from __future__ import annotations

import json
from pathlib import Path
from typing import Any


def validate_submissions(path: str | Path) -> dict[str, Any]:
    target = Path(path)
    paths = sorted(target.glob("*.json")) if target.is_dir() else [target]
    results = []
    seen = set()
    for item in paths:
        errors = validate_submission_file(item)
        if not errors:
            raw = json.loads(item.read_text(encoding="utf-8"))
            key = (raw["project"], raw["profile"]["id"], raw["dataset_sha256"])
            if key in seen:
                errors.append("duplicate project, profile, and dataset combination")
            seen.add(key)
        results.append({"path": str(item), "ok": not errors, "errors": errors})
    return {
        "ok": all(item["ok"] for item in results),
        "total": len(results),
        "passed": sum(1 for item in results if item["ok"]),
        "failed": sum(1 for item in results if not item["ok"]),
        "results": results,
    }


def validate_submission_file(path: Path) -> list[str]:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        return [f"invalid JSON: {exc}"]
    if not isinstance(raw, dict):
        return ["submission must be a JSON object"]

    errors = []
    required_strings = ["schema_version", "project", "experiment_id", "generated_at", "dataset_sha256"]
    for field in required_strings:
        if not isinstance(raw.get(field), str) or not raw[field].strip():
            errors.append(f"{field} must be a non-empty string")
    if raw.get("schema_version") != "1.0":
        errors.append("schema_version must be '1.0'")
    dataset = raw.get("dataset_sha256")
    if isinstance(dataset, str) and (len(dataset) != 64 or any(char not in "0123456789abcdef" for char in dataset)):
        errors.append("dataset_sha256 must be a lowercase 64-character hex digest")
    if not isinstance(raw.get("total_cases"), int) or raw.get("total_cases", 0) <= 0:
        errors.append("total_cases must be a positive integer")

    profile = raw.get("profile")
    if not isinstance(profile, dict):
        errors.append("profile must be an object")
    else:
        for field in ("id", "display_name", "provider", "adapter", "run_type"):
            if not isinstance(profile.get(field), str) or not profile[field].strip():
                errors.append(f"profile.{field} must be a non-empty string")
        for field in ("average_score", "pass_rate"):
            value = profile.get(field)
            if not isinstance(value, (int, float)) or not 0 <= value <= 100:
                errors.append(f"profile.{field} must be a number from 0 to 100")

    gate = raw.get("quality_gate")
    if not isinstance(gate, dict) or not isinstance(gate.get("ok"), bool):
        errors.append("quality_gate.ok must be boolean")
    if not isinstance(raw.get("disclosure"), str) or not raw.get("disclosure", "").strip():
        errors.append("disclosure must be a non-empty string")
    return errors


def build_community_leaderboard(
    submissions_path: str | Path,
    output_path: str | Path = "community/LEADERBOARD.md",
) -> dict[str, Any]:
    validation = validate_submissions(submissions_path)
    if not validation["ok"]:
        failures = [
            f"{item['path']}: {'; '.join(item['errors'])}"
            for item in validation["results"]
            if not item["ok"]
        ]
        raise ValueError("invalid benchmark submissions: " + " | ".join(failures))

    submissions = [
        json.loads(Path(item["path"]).read_text(encoding="utf-8"))
        for item in validation["results"]
    ]
    submissions.sort(
        key=lambda item: (item["profile"]["average_score"], item["profile"]["pass_rate"]),
        reverse=True,
    )
    lines = [
        "# ClaimPilot Community Benchmark",
        "",
        "Reproducible Agent results submitted with `claimpilot test`. Scores are only directly comparable when the dataset SHA-256 matches.",
        "",
        "| Rank | Project | Profile | Type | Score | Pass rate | Cases | Dataset | Gate |",
        "| ---: | --- | --- | --- | ---: | ---: | ---: | --- | --- |",
    ]
    for rank, item in enumerate(submissions, start=1):
        profile = item["profile"]
        gate = "PASS" if item["quality_gate"]["ok"] else "FAIL"
        lines.append(
            f"| {rank} | {markdown_cell(item['project'])} | {markdown_cell(profile['display_name'])} | "
            f"{markdown_cell(profile['run_type'])} | "
            f"{profile['average_score']}% | {profile['pass_rate']}% | {item['total_cases']} | "
            f"`{item['dataset_sha256'][:12]}` | {gate} |"
        )
    lines.extend(
        [
            "",
            "Built-in rule baselines are reference controls, not external model claims. See [Challenge rules](CHALLENGE.md) before submitting a result.",
            "",
        ]
    )
    destination = Path(output_path)
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text("\n".join(lines), encoding="utf-8")
    return {"submissions": len(submissions), "leaderboard": str(destination)}


def markdown_cell(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")
