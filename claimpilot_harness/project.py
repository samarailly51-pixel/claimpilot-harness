from __future__ import annotations

import json
from importlib import resources
from pathlib import Path
from typing import Any

from .experiments import load_profiles, run_arena
from .scorecard import write_project_artifacts

CONFIG_NAME = "claimpilot.json"
SUPPORTED_ADAPTERS = {"command", "http", "openai"}


def init_project(
    directory: str | Path = ".",
    name: str | None = None,
    adapter: str = "command",
    force: bool = False,
) -> dict[str, Any]:
    if adapter not in SUPPORTED_ADAPTERS:
        raise ValueError(f"unsupported starter adapter '{adapter}'")

    target = Path(directory).resolve()
    project_name = name or target.name or "claimpilot-agent"
    files: dict[Path, str] = {
        target / CONFIG_NAME: json.dumps(
            starter_config(project_name, adapter),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        target / "cases" / "starter-travel-injection.json": template_text("starter_case.json"),
        target / ".github" / "workflows" / "claimpilot.yml": template_text("claimpilot.yml"),
    }
    if adapter == "command":
        files[target / "claimpilot_agent.py"] = template_text("starter_agent.py")

    existing = [path for path in files if path.exists()]
    if existing and not force:
        joined = ", ".join(str(path.relative_to(target)) for path in existing)
        raise ValueError(f"refusing to overwrite existing files: {joined}; use --force to replace them")

    for path, content in files.items():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    return {
        "project": project_name,
        "directory": str(target),
        "adapter": adapter,
        "files": [str(path) for path in files],
    }


def starter_config(project_name: str, adapter: str) -> dict[str, Any]:
    profile: dict[str, Any] = {
        "id": "my-agent",
        "display_name": "My Claim Agent",
        "provider": "Custom",
        "adapter": adapter,
    }
    if adapter == "command":
        profile["command"] = "{python} claimpilot_agent.py"
    elif adapter == "http":
        profile.update({"url": "http://127.0.0.1:8000/review", "timeout": 90})
    else:
        profile.update(
            {
                "model": "replace-with-your-model",
                "base_url": "https://api.openai.com/v1",
                "api_key_env": "OPENAI_API_KEY",
            }
        )

    return {
        "schema_version": "1.0",
        "project": project_name,
        "cases": "cases",
        "output": "runs/claimpilot",
        "profiles": [profile],
        "quality_gate": {"min_average_score": 80, "min_pass_rate": 100},
        "scorecard_profile": "my-agent",
    }


def load_project_config(path: str | Path = CONFIG_NAME) -> tuple[Path, dict[str, Any]]:
    config_path = Path(path).resolve()
    if not config_path.is_file():
        raise ValueError(f"project config not found: {config_path}")
    try:
        config = json.loads(config_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise ValueError(f"project config is not valid JSON: {exc}") from exc
    if not isinstance(config, dict):
        raise ValueError("project config must be a JSON object")
    if config.get("schema_version") != "1.0":
        raise ValueError("project config schema_version must be '1.0'")
    if not isinstance(config.get("project"), str) or not config["project"].strip():
        raise ValueError("project config requires a non-empty project name")
    if not isinstance(config.get("cases", "cases"), str):
        raise ValueError("project config cases must be a path string")
    if not isinstance(config.get("output", "runs/claimpilot"), str):
        raise ValueError("project config output must be a path string")
    load_profiles(config_path)
    validate_quality_gate(config.get("quality_gate", {}))
    return config_path, config


def run_project(
    config_path: str | Path = CONFIG_NAME,
    output_dir: str | Path | None = None,
    allow_skipped: bool = False,
) -> dict[str, Any]:
    resolved_config, config = load_project_config(config_path)
    base_dir = resolved_config.parent
    cases_path = resolve_from(base_dir, config.get("cases", "cases"))
    out_dir = (
        Path(output_dir).resolve()
        if output_dir is not None
        else resolve_from(base_dir, config.get("output", "runs/claimpilot"))
    )

    arena = run_arena(
        cases_path,
        resolved_config,
        out_dir,
        skip_unavailable=allow_skipped,
    )
    gate_settings = config.get("quality_gate", {})
    quality_gate = evaluate_profile_gate(
        arena["profiles"],
        min_average_score=gate_settings.get("min_average_score"),
        min_pass_rate=gate_settings.get("min_pass_rate"),
    )
    artifacts = write_project_artifacts(
        config["project"],
        arena,
        quality_gate,
        out_dir,
        preferred_profile=config.get("scorecard_profile"),
    )

    payload = {
        "schema_version": "1.0",
        "project": config["project"],
        "config": str(resolved_config),
        "experiment_id": arena["experiment_id"],
        "generated_at": arena["generated_at"],
        "dataset_sha256": arena["dataset_sha256"],
        "total_cases": arena["total_cases"],
        "profiles": arena["profiles"],
        "results": arena["results"],
        "quality_gate": quality_gate,
        "artifacts": {key: Path(value).name for key, value in artifacts.items()},
        "disclosure": arena["disclosure"],
    }
    results_path = out_dir / "claimpilot-results.json"
    results_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {
        **payload,
        "results_file": str(results_path),
        "artifacts": artifacts,
    }


def render_scorecard_from_results(
    results_path: str | Path,
    output_dir: str | Path | None = None,
    preferred_profile: str | None = None,
) -> dict[str, str]:
    path = Path(results_path).resolve()
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError(f"unable to read ClaimPilot results: {exc}") from exc
    required = {
        "project",
        "profiles",
        "results",
        "experiment_id",
        "generated_at",
        "dataset_sha256",
        "total_cases",
        "quality_gate",
        "disclosure",
    }
    missing = sorted(required - set(payload))
    if missing:
        raise ValueError(f"results file is missing fields: {', '.join(missing)}")
    out_dir = Path(output_dir).resolve() if output_dir else path.parent
    return write_project_artifacts(
        payload["project"],
        payload,
        payload["quality_gate"],
        out_dir,
        preferred_profile=preferred_profile,
    )


def evaluate_profile_gate(
    profiles: list[dict[str, Any]],
    min_average_score: float | None = None,
    min_pass_rate: float | None = None,
) -> dict[str, Any]:
    failures = []
    measured = [item for item in profiles if item.get("status") == "measured"]
    if not measured:
        failures.append({"profile": "all", "reasons": ["no profiles were measured"]})
    for item in measured:
        reasons = []
        if min_average_score is not None and item["average_score"] < min_average_score:
            reasons.append(f"average_score {item['average_score']}% is below {min_average_score}%")
        if min_pass_rate is not None and item["pass_rate"] < min_pass_rate:
            reasons.append(f"pass_rate {item['pass_rate']}% is below {min_pass_rate}%")
        if reasons:
            failures.append({"profile": item["id"], "reasons": reasons})
    return {
        "ok": not failures,
        "min_average_score": min_average_score,
        "min_pass_rate": min_pass_rate,
        "failures": failures,
    }


def validate_quality_gate(raw: Any) -> None:
    if not isinstance(raw, dict):
        raise ValueError("quality_gate must be an object")
    for key in ("min_average_score", "min_pass_rate"):
        value = raw.get(key)
        if value is not None and (not isinstance(value, (int, float)) or not 0 <= value <= 100):
            raise ValueError(f"quality_gate.{key} must be a number from 0 to 100")


def resolve_from(base_dir: Path, value: str) -> Path:
    path = Path(value)
    return path.resolve() if path.is_absolute() else (base_dir / path).resolve()


def template_text(name: str) -> str:
    template = resources.files("claimpilot_harness").joinpath("templates", name)
    return template.read_text(encoding="utf-8")
