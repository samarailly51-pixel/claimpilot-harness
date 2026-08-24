from __future__ import annotations

import html
import json
from pathlib import Path
from typing import Any


def write_project_artifacts(
    project_name: str,
    arena: dict[str, Any],
    quality_gate: dict[str, Any],
    output_dir: str | Path,
    preferred_profile: str | None = None,
) -> dict[str, str]:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    profile = select_profile(arena["profiles"], preferred_profile)

    scorecard_path = out_dir / "claimpilot-scorecard.svg"
    markdown_path = out_dir / "claimpilot-scorecard.md"
    report_path = out_dir / "claimpilot-report.html"
    submission_path = out_dir / "claimpilot-submission.json"

    scorecard_path.write_text(
        render_scorecard_svg(project_name, profile, arena, quality_gate),
        encoding="utf-8",
    )
    markdown_path.write_text(
        render_scorecard_markdown(project_name, profile, arena, quality_gate),
        encoding="utf-8",
    )
    report_path.write_text(
        render_project_report(project_name, arena, quality_gate),
        encoding="utf-8",
    )
    submission_path.write_text(
        json.dumps(
            benchmark_submission(project_name, profile, arena, quality_gate),
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    (out_dir / "latest.html").write_text(report_path.read_text(encoding="utf-8"), encoding="utf-8")

    return {
        "report": str(report_path),
        "scorecard": str(scorecard_path),
        "scorecard_markdown": str(markdown_path),
        "submission": str(submission_path),
    }


def select_profile(profiles: list[dict[str, Any]], preferred_profile: str | None = None) -> dict[str, Any]:
    measured = [item for item in profiles if item.get("status") == "measured"]
    if preferred_profile:
        for item in measured:
            if item.get("id") == preferred_profile:
                return item
        raise ValueError(f"scorecard profile '{preferred_profile}' was not measured")
    external = [item for item in measured if item.get("run_type") == "external_model"]
    candidates = external or measured
    if not candidates:
        raise ValueError("scorecard requires at least one measured profile")
    return candidates[0]


def benchmark_submission(
    project_name: str,
    profile: dict[str, Any],
    arena: dict[str, Any],
    quality_gate: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": "1.0",
        "project": project_name,
        "experiment_id": arena["experiment_id"],
        "generated_at": arena["generated_at"],
        "dataset_sha256": arena["dataset_sha256"],
        "total_cases": arena["total_cases"],
        "profile": {
            "id": profile["id"],
            "display_name": profile["display_name"],
            "provider": profile["provider"],
            "model": profile.get("model"),
            "adapter": profile["adapter"],
            "run_type": profile["run_type"],
            "average_score": profile["average_score"],
            "pass_rate": profile["pass_rate"],
            "median_latency_ms": profile["median_latency_ms"],
        },
        "quality_gate": quality_gate,
        "disclosure": arena["disclosure"],
    }


def render_scorecard_svg(
    project_name: str,
    profile: dict[str, Any],
    arena: dict[str, Any],
    quality_gate: dict[str, Any],
) -> str:
    score = float(profile["average_score"] or 0)
    pass_rate = float(profile["pass_rate"] or 0)
    bar_width = round(5.2 * max(0, min(score, 100)), 1)
    gate_ok = bool(quality_gate["ok"])
    gate_color = "#137a52" if gate_ok else "#b42318"
    gate_bg = "#e8f6ef" if gate_ok else "#fdecea"
    gate_label = "QUALITY GATE PASS" if gate_ok else "QUALITY GATE FAIL"
    safe_project = html.escape(project_name)
    safe_profile = html.escape(str(profile["display_name"]))
    dataset = html.escape(str(arena["dataset_sha256"])[:12])
    model = profile.get("model") or profile["adapter"]
    safe_model = html.escape(str(model))
    case_label = "case" if arena["total_cases"] == 1 else "cases"
    return f"""<svg xmlns="http://www.w3.org/2000/svg" width="800" height="280" viewBox="0 0 800 280" role="img" aria-label="ClaimPilot benchmark scorecard for {safe_project}">
  <rect width="800" height="280" fill="#f7faf8"/>
  <rect x="1" y="1" width="798" height="278" rx="8" fill="none" stroke="#cbd8d1" stroke-width="2"/>
  <rect x="0" y="0" width="12" height="280" fill="#137a52"/>
  <text x="42" y="48" fill="#17352b" font-family="Arial, sans-serif" font-size="16" font-weight="700">CLAIMPILOT BENCHMARK</text>
  <text x="42" y="82" fill="#10251f" font-family="Arial, sans-serif" font-size="25" font-weight="700">{safe_project}</text>
  <text x="42" y="111" fill="#526b62" font-family="Arial, sans-serif" font-size="15">{safe_profile} · {safe_model}</text>
  <rect x="596" y="34" width="168" height="32" rx="6" fill="{gate_bg}"/>
  <text x="680" y="55" text-anchor="middle" fill="{gate_color}" font-family="Arial, sans-serif" font-size="12" font-weight="700">{gate_label}</text>
  <text x="42" y="166" fill="#137a52" font-family="Arial, sans-serif" font-size="48" font-weight="700">{score:.1f}</text>
  <text x="184" y="164" fill="#526b62" font-family="Arial, sans-serif" font-size="16">/ 100 safety score</text>
  <rect x="42" y="184" width="520" height="12" rx="6" fill="#dce7e1"/>
  <rect x="42" y="184" width="{bar_width}" height="12" rx="6" fill="{gate_color}"/>
  <text x="598" y="164" fill="#10251f" font-family="Arial, sans-serif" font-size="26" font-weight="700">{pass_rate:.1f}%</text>
  <text x="598" y="188" fill="#526b62" font-family="Arial, sans-serif" font-size="13">case pass rate</text>
  <line x1="42" y1="220" x2="758" y2="220" stroke="#d5e1db"/>
  <text x="42" y="250" fill="#526b62" font-family="Arial, sans-serif" font-size="13">{arena['total_cases']} adversarial {case_label}</text>
  <text x="276" y="250" fill="#526b62" font-family="Arial, sans-serif" font-size="13">dataset {dataset}</text>
  <text x="758" y="250" text-anchor="end" fill="#137a52" font-family="Arial, sans-serif" font-size="13" font-weight="700">claimpilot-harness</text>
</svg>
"""


def render_scorecard_markdown(
    project_name: str,
    profile: dict[str, Any],
    arena: dict[str, Any],
    quality_gate: dict[str, Any],
) -> str:
    gate = "PASS" if quality_gate["ok"] else "FAIL"
    safe_project = markdown_text(project_name)
    safe_profile = markdown_text(profile["display_name"])
    return f"""# {safe_project} · ClaimPilot Benchmark

![ClaimPilot benchmark scorecard](claimpilot-scorecard.svg)

| Signal | Result |
| --- | ---: |
| Profile | {safe_profile} |
| Safety score | {profile['average_score']}% |
| Case pass rate | {profile['pass_rate']}% |
| Cases | {arena['total_cases']} |
| Quality gate | **{gate}** |
| Dataset SHA-256 | `{arena['dataset_sha256']}` |

Generated with [ClaimPilot Harness](https://github.com/samarailly51-pixel/claimpilot-harness).
Reproduce with `claimpilot test` from the project root.
"""


def markdown_text(value: Any) -> str:
    return str(value).replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def render_project_report(
    project_name: str,
    arena: dict[str, Any],
    quality_gate: dict[str, Any],
) -> str:
    gate_ok = bool(quality_gate["ok"])
    gate_label = "PASS" if gate_ok else "FAIL"
    profile_rows = "".join(render_profile_row(item) for item in arena["profiles"])
    result_rows = "".join(render_result_row(item) for item in arena["results"])
    failures = "".join(
        f"<li><strong>{html.escape(item['profile'])}</strong>: {html.escape('; '.join(item['reasons']))}</li>"
        for item in quality_gate["failures"]
    )
    failure_block = f"<ul class=\"failures\">{failures}</ul>" if failures else ""
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{html.escape(project_name)} · ClaimPilot Benchmark</title>
  <style>
    :root {{ color-scheme: light; --ink:#10251f; --muted:#5c7068; --line:#d6e1dc; --good:#137a52; --bad:#b42318; --paper:#f6f9f7; }}
    * {{ box-sizing:border-box; }} body {{ margin:0; background:var(--paper); color:var(--ink); font:15px/1.55 Arial,sans-serif; }}
    main {{ width:min(1100px,calc(100% - 32px)); margin:38px auto 64px; }}
    header {{ display:grid; grid-template-columns:1fr auto; gap:24px; align-items:end; border-bottom:2px solid var(--ink); padding-bottom:22px; }}
    .eyebrow {{ color:var(--good); font-size:12px; font-weight:800; text-transform:uppercase; }} h1 {{ margin:5px 0 6px; font-size:clamp(30px,5vw,52px); line-height:1.05; }}
    .meta {{ color:var(--muted); }} .gate {{ padding:9px 13px; border:1px solid currentColor; color:{'#137a52' if gate_ok else '#b42318'}; font-weight:800; }}
    section {{ margin-top:34px; }} h2 {{ margin:0 0 12px; font-size:20px; }} .summary {{ display:grid; grid-template-columns:repeat(3,1fr); border:1px solid var(--line); background:white; }}
    .metric {{ padding:20px; border-right:1px solid var(--line); }} .metric:last-child {{ border-right:0; }} .metric strong {{ display:block; font-size:28px; }} .metric span {{ color:var(--muted); font-size:12px; text-transform:uppercase; }}
    .table-wrap {{ overflow-x:auto; border:1px solid var(--line); background:white; }} table {{ width:100%; border-collapse:collapse; min-width:720px; }} th,td {{ padding:12px 14px; border-bottom:1px solid var(--line); text-align:left; }} th {{ color:var(--muted); font-size:11px; text-transform:uppercase; }} tr:last-child td {{ border-bottom:0; }}
    a {{ color:var(--good); }} code {{ font-family:Consolas,monospace; font-size:12px; }} .failures {{ color:var(--bad); }} footer {{ margin-top:34px; color:var(--muted); font-size:12px; }}
    @media(max-width:680px) {{ header {{ grid-template-columns:1fr; }} .summary {{ grid-template-columns:1fr; }} .metric {{ border-right:0; border-bottom:1px solid var(--line); }} .metric:last-child {{ border-bottom:0; }} }}
  </style>
</head>
<body><main>
  <header><div><div class="eyebrow">ClaimPilot agent reliability report</div><h1>{html.escape(project_name)}</h1><div class="meta">Experiment {html.escape(arena['experiment_id'])} · Dataset <code>{html.escape(arena['dataset_sha256'][:16])}</code></div></div><div class="gate">QUALITY GATE {gate_label}</div></header>
  <section><div class="summary"><div class="metric"><strong>{arena['total_cases']}</strong><span>Adversarial cases</span></div><div class="metric"><strong>{len([p for p in arena['profiles'] if p['status'] == 'measured'])}</strong><span>Measured profiles</span></div><div class="metric"><strong>{gate_label}</strong><span>Release decision</span></div></div>{failure_block}</section>
  <section><h2>Profiles</h2><div class="table-wrap"><table><thead><tr><th>Profile</th><th>Adapter</th><th>Status</th><th>Avg score</th><th>Pass rate</th><th>Median latency</th></tr></thead><tbody>{profile_rows}</tbody></table></div></section>
  <section><h2>Case results</h2><div class="table-wrap"><table><thead><tr><th>Case</th><th>Profile</th><th>Line</th><th>Verdict</th><th>Score</th><th>Replay</th></tr></thead><tbody>{result_rows}</tbody></table></div></section>
  <footer>{html.escape(arena['disclosure'])}</footer>
</main></body></html>
"""


def render_profile_row(item: dict[str, Any]) -> str:
    average = "-" if item["average_score"] is None else f"{item['average_score']}%"
    pass_rate = "-" if item["pass_rate"] is None else f"{item['pass_rate']}%"
    latency = "-" if item["median_latency_ms"] is None else f"{item['median_latency_ms']} ms"
    return (
        "<tr>"
        f"<td><strong>{html.escape(item['display_name'])}</strong></td>"
        f"<td>{html.escape(item['adapter'])}</td><td>{html.escape(item['status'])}</td>"
        f"<td>{average}</td><td>{pass_rate}</td><td>{latency}</td>"
        "</tr>"
    )


def render_result_row(item: dict[str, Any]) -> str:
    replay = html.escape(item["replay"], quote=True)
    return (
        "<tr>"
        f"<td><strong>{html.escape(item['case_title'])}</strong><br><code>{html.escape(item['case_id'])}</code></td>"
        f"<td>{html.escape(item['profile_id'])}</td><td>{html.escape(item['line'])}</td>"
        f"<td>{html.escape(item['verdict'])}</td><td>{item['score']}%</td>"
        f"<td><a href=\"{replay}\">Open replay</a></td>"
        "</tr>"
    )
