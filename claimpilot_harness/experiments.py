from __future__ import annotations

import hashlib
import json
import os
import re
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .agents import run_agent
from .cases import load_case
from .replay import render_replay
from .scorer import score_decision
from .suite import discover_cases

PROFILE_ID = re.compile(r"^[a-z0-9][a-z0-9_-]*$")
ADAPTERS = {"demo", "risky", "openai", "http", "command"}


def run_arena(
    cases_path: str | Path,
    config_path: str | Path,
    output_dir: str | Path = "runs/arena",
    skip_unavailable: bool = True,
) -> dict[str, Any]:
    case_paths = discover_cases(cases_path)
    if not case_paths:
        raise ValueError("arena requires at least one case JSON file")

    profiles = load_profiles(config_path)
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    results: list[dict[str, Any]] = []
    profile_summaries: list[dict[str, Any]] = []

    for profile in profiles:
        availability = profile_availability(profile)
        if not availability["available"]:
            if not skip_unavailable:
                raise ValueError(f"profile '{profile['id']}' is unavailable: {availability['reason']}")
            profile_summaries.append(profile_summary(profile, [], "skipped", availability["reason"]))
            continue

        profile_results = []
        for case_path in case_paths:
            case = load_case(case_path)
            started = time.perf_counter()
            decision = run_profile(case, profile)
            latency_ms = round((time.perf_counter() - started) * 1000, 1)
            score = score_decision(case, decision)
            replay = render_replay(case, profile["id"], decision, score, out_dir, update_latest=False)
            row = {
                "case_id": case.id,
                "case_title": case.title,
                "line": case.line,
                "severity": case.severity,
                "profile_id": profile["id"],
                "verdict": decision.verdict,
                "score": score["percent"],
                "grade": score["grade"],
                "latency_ms": latency_ms,
                "input_tokens": None,
                "output_tokens": None,
                "cost_usd": None,
                "replay": replay.resolve().relative_to(out_dir.resolve()).as_posix(),
            }
            results.append(row)
            profile_results.append(row)
        profile_summaries.append(profile_summary(profile, profile_results, "measured", None))

    payload = {
        "schema_version": "1.0",
        "experiment_id": datetime.now(timezone.utc).strftime("arena-%Y%m%dT%H%M%SZ"),
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "dataset_sha256": dataset_hash(case_paths),
        "total_cases": len(case_paths),
        "profiles": profile_summaries,
        "results": results,
        "disclosure": (
            "Built-in profiles are deterministic rule baselines. Profiles using openai, http, or command "
            "adapters are external model runs. Missing token or cost fields are reported as null, never estimated."
        ),
    }
    output_path = out_dir / "arena-results.json"
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {**payload, "results_file": str(output_path)}


def load_profiles(path: str | Path) -> list[dict[str, Any]]:
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    profiles = raw.get("profiles") if isinstance(raw, dict) else None
    if not isinstance(profiles, list) or not profiles:
        raise ValueError("arena config must contain a non-empty profiles list")

    enabled = []
    seen = set()
    for profile in profiles:
        if not isinstance(profile, dict):
            raise ValueError("each arena profile must be an object")
        profile_id = profile.get("id")
        adapter = profile.get("adapter")
        if not isinstance(profile_id, str) or not PROFILE_ID.fullmatch(profile_id):
            raise ValueError("profile id must use lowercase letters, numbers, hyphen, or underscore")
        if profile_id in seen:
            raise ValueError(f"duplicate profile id '{profile_id}'")
        if adapter not in ADAPTERS:
            raise ValueError(f"profile '{profile_id}' has unsupported adapter '{adapter}'")
        seen.add(profile_id)
        if profile.get("enabled", True):
            enabled.append(profile)
    if not enabled:
        raise ValueError("arena config has no enabled profiles")
    return enabled


def profile_availability(profile: dict[str, Any]) -> dict[str, Any]:
    adapter = profile["adapter"]
    if adapter == "openai":
        key_env = profile.get("api_key_env", "OPENAI_API_KEY")
        if not profile.get("model"):
            return {"available": False, "reason": "model is not configured"}
        if not os.getenv(key_env):
            return {"available": False, "reason": f"{key_env} is not set"}
    if adapter == "http" and not profile.get("url"):
        return {"available": False, "reason": "url is not configured"}
    if adapter == "command" and not profile.get("command"):
        return {"available": False, "reason": "command is not configured"}
    return {"available": True, "reason": None}


def run_profile(case: Any, profile: dict[str, Any]) -> Any:
    return run_agent(
        case,
        agent=profile["adapter"],
        command=profile.get("command"),
        http_url=profile.get("url"),
        http_timeout=int(profile.get("timeout", 90)),
        openai_model=profile.get("model"),
        openai_base_url=profile.get("base_url", "https://api.openai.com/v1"),
        openai_api_key_env=profile.get("api_key_env", "OPENAI_API_KEY"),
    )


def profile_summary(
    profile: dict[str, Any],
    rows: list[dict[str, Any]],
    status: str,
    reason: str | None,
) -> dict[str, Any]:
    scores = [item["score"] for item in rows]
    passed = sum(1 for item in rows if item["grade"] == "pass")
    latencies = [item["latency_ms"] for item in rows]
    adapter = profile["adapter"]
    return {
        "id": profile["id"],
        "display_name": profile.get("display_name", profile["id"]),
        "provider": profile.get("provider", "ClaimPilot" if adapter in {"demo", "risky"} else "custom"),
        "model": profile.get("model"),
        "adapter": adapter,
        "run_type": "rule_baseline" if adapter in {"demo", "risky"} else "external_model",
        "status": status,
        "unavailable_reason": reason,
        "average_score": round(sum(scores) / len(scores), 1) if scores else None,
        "pass_rate": round((passed / len(rows)) * 100, 1) if rows else None,
        "median_latency_ms": median(latencies) if latencies else None,
        "cases_run": len(rows),
    }


def dataset_hash(paths: list[Path]) -> str:
    digest = hashlib.sha256()
    for path in sorted(paths):
        digest.update(path.name.encode("utf-8"))
        digest.update(path.read_bytes())
    return digest.hexdigest()


def median(values: list[float]) -> float:
    ordered = sorted(values)
    middle = len(ordered) // 2
    if len(ordered) % 2:
        return ordered[middle]
    return round((ordered[middle - 1] + ordered[middle]) / 2, 1)
