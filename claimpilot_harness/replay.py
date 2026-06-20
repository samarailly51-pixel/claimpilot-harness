from __future__ import annotations

import html
import json
from datetime import datetime
from pathlib import Path

from .models import AgentDecision, Case


def render_replay(
    case: Case,
    agent_name: str,
    decision: AgentDecision,
    score: dict,
    output_dir: str | Path,
    update_latest: bool = True,
) -> Path:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{case.id}-{agent_name}-replay.html"
    path.write_text(build_html(case, agent_name, decision, score), encoding="utf-8")
    if update_latest:
        latest = out_dir / "latest.html"
        latest.write_text(build_html(case, agent_name, decision, score), encoding="utf-8")
    return path


def render_leaderboard(case: Case, results: list[dict], output_dir: str | Path) -> Path:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    sorted_results = sorted(results, key=lambda item: item["score"]["percent"], reverse=True)
    html_doc = build_leaderboard_html(case, sorted_results)
    path = out_dir / f"{case.id}-leaderboard.html"
    path.write_text(html_doc, encoding="utf-8")
    latest = out_dir / "latest.html"
    latest.write_text(html_doc, encoding="utf-8")
    return path


def render_suite_report(rows: list[dict], agents_summary: list[dict], output_dir: str | Path) -> Path:
    out_dir = Path(output_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    html_doc = build_suite_html(rows, agents_summary)
    path = out_dir / "suite-report.html"
    path.write_text(html_doc, encoding="utf-8")
    latest = out_dir / "latest.html"
    latest.write_text(html_doc, encoding="utf-8")
    return path


def build_html(case: Case, agent_name: str, decision: AgentDecision, score: dict) -> str:
    evidence = "\n".join(render_evidence(item, decision.cited_evidence) for item in case.evidence)
    checks = "\n".join(render_check(item) for item in score["checks"])
    findings = "".join(f"<li>{esc(item)}</li>" for item in decision.findings) or "<li>No findings returned.</li>"
    docs = "".join(f"<li>{esc(item)}</li>" for item in decision.requested_documents) or "<li>No documents requested.</li>"
    flags = "".join(f"<li>{esc(item)}</li>" for item in decision.privacy_flags) or "<li>No privacy or injection flags.</li>"
    raw_decision = esc(json.dumps(decision.__dict__, ensure_ascii=False, indent=2))
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ClaimPilot Replay - {esc(case.id)}</title>
  <style>
    :root {{
      --ink: #17201b;
      --muted: #5d6b63;
      --line: #dce5dd;
      --paper: #f8faf7;
      --panel: #ffffff;
      --good: #12774f;
      --bad: #b42318;
      --warn: #b85c00;
      --accent: #2563eb;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--paper);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
    }}
    header {{
      padding: 42px clamp(20px, 5vw, 72px) 26px;
      background: #0f1f18;
      color: white;
      border-bottom: 5px solid #7dd3fc;
    }}
    .eyebrow {{ color: #a7f3d0; font-size: 13px; text-transform: uppercase; font-weight: 700; }}
    h1 {{ margin: 8px 0 8px; font-size: clamp(28px, 4vw, 54px); line-height: 1.02; letter-spacing: 0; }}
    .subtitle {{ max-width: 920px; color: #d9f5e8; font-size: 17px; line-height: 1.55; }}
    main {{ padding: 28px clamp(20px, 5vw, 72px) 56px; }}
    .grid {{ display: grid; gap: 18px; grid-template-columns: repeat(12, 1fr); }}
    section, .metric {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
      box-shadow: 0 10px 24px rgba(19, 31, 25, 0.05);
    }}
    .span-4 {{ grid-column: span 4; }}
    .span-5 {{ grid-column: span 5; }}
    .span-7 {{ grid-column: span 7; }}
    .span-12 {{ grid-column: span 12; }}
    h2 {{ margin: 0 0 12px; font-size: 18px; }}
    .score {{ font-size: 48px; font-weight: 800; color: {grade_color(score["grade"])}; }}
    .label {{ color: var(--muted); font-size: 13px; }}
    .pill {{
      display: inline-flex;
      align-items: center;
      min-height: 26px;
      padding: 3px 10px;
      border-radius: 999px;
      background: #edf7f2;
      color: #13543a;
      font-size: 13px;
      font-weight: 700;
    }}
    .verdict {{ background: #eef2ff; color: #1d4ed8; }}
    .fail {{ color: var(--bad); }}
    .pass {{ color: var(--good); }}
    .check {{
      display: grid;
      grid-template-columns: 86px 1fr 70px;
      gap: 10px;
      padding: 11px 0;
      border-top: 1px solid var(--line);
      align-items: start;
    }}
    .evidence {{
      border-top: 1px solid var(--line);
      padding: 12px 0;
    }}
    .cited {{ border-left: 4px solid var(--accent); padding-left: 12px; }}
    code, pre {{
      background: #101815;
      color: #d1fae5;
      border-radius: 8px;
      padding: 14px;
      overflow: auto;
      white-space: pre-wrap;
    }}
    ul {{ margin: 0; padding-left: 20px; }}
    li {{ margin: 7px 0; }}
    @media (max-width: 900px) {{
      .span-4, .span-5, .span-7 {{ grid-column: span 12; }}
      .check {{ grid-template-columns: 1fr; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="eyebrow">ClaimPilot Harness Replay</div>
    <h1>{esc(case.title)}</h1>
    <div class="subtitle">Agent <strong>{esc(agent_name)}</strong> reviewed case <strong>{esc(case.id)}</strong>. Generated {esc(generated_at)}.</div>
  </header>
  <main class="grid">
    <div class="metric span-4">
      <div class="label">Harness Score</div>
      <div class="score">{score["percent"]}%</div>
      <span class="pill">{esc(score["grade"].upper())}</span>
    </div>
    <div class="metric span-4">
      <div class="label">Agent Verdict</div>
      <div style="font-size: 30px; font-weight: 800; margin: 7px 0;">{esc(decision.verdict)}</div>
      <span class="pill verdict">confidence {decision.confidence:.2f}</span>
    </div>
    <div class="metric span-4">
      <div class="label">Claim Line</div>
      <div style="font-size: 30px; font-weight: 800; margin: 7px 0;">{esc(case.line)}</div>
      <span class="pill">severity {esc(case.severity)}</span>
    </div>
    <section class="span-7">
      <h2>Evidence Timeline</h2>
      {evidence}
    </section>
    <section class="span-5">
      <h2>Agent Reasoning</h2>
      <p>{esc(decision.summary)}</p>
      <h2>Findings</h2>
      <ul>{findings}</ul>
      <h2>Requested Documents</h2>
      <ul>{docs}</ul>
      <h2>Privacy / Injection Flags</h2>
      <ul>{flags}</ul>
    </section>
    <section class="span-12">
      <h2>Scoring Breakdown</h2>
      {checks}
    </section>
    <section class="span-12">
      <h2>Raw Decision JSON</h2>
      <pre>{raw_decision}</pre>
    </section>
  </main>
</body>
</html>
"""


def build_suite_html(rows: list[dict], agents_summary: list[dict]) -> str:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    total_cases = len({row["case_id"] for row in rows})
    total_runs = len(rows)
    top = agents_summary[0] if agents_summary else {"agent": "none", "average_score": 0, "pass_rate": 0}
    summary_cards = "\n".join(render_suite_agent_card(item) for item in agents_summary)
    result_rows = "\n".join(render_suite_result_row(item) for item in rows)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ClaimPilot Suite Report</title>
  <style>
    :root {{
      --ink: #17201b;
      --muted: #5d6b63;
      --line: #dce5dd;
      --paper: #f8faf7;
      --panel: #ffffff;
      --good: #12774f;
      --bad: #b42318;
      --accent: #2563eb;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--paper);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
    }}
    header {{
      padding: 44px clamp(20px, 5vw, 72px) 34px;
      background: #0f1f18;
      color: white;
      border-bottom: 5px solid #7dd3fc;
    }}
    .eyebrow {{ color: #a7f3d0; font-size: 13px; text-transform: uppercase; font-weight: 800; }}
    h1 {{ margin: 8px 0; font-size: clamp(30px, 4vw, 56px); line-height: 1.02; letter-spacing: 0; }}
    .subtitle {{ max-width: 940px; color: #d9f5e8; font-size: 17px; line-height: 1.55; }}
    main {{ padding: 28px clamp(20px, 5vw, 72px) 56px; }}
    .metrics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px; }}
    section, .metric {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
      box-shadow: 0 10px 24px rgba(19, 31, 25, 0.05);
      margin-bottom: 18px;
    }}
    .label {{ color: var(--muted); font-size: 13px; }}
    .big {{ font-size: 34px; font-weight: 850; margin-top: 7px; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 16px; }}
    .agent-card {{ border: 1px solid var(--line); border-radius: 8px; padding: 16px; background: #fbfdfb; }}
    .score {{ font-size: 38px; font-weight: 850; color: var(--good); }}
    .bar {{ height: 10px; background: #e9efe9; border-radius: 999px; overflow: hidden; margin: 10px 0; }}
    .bar > div {{ height: 100%; background: var(--accent); }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ text-align: left; padding: 13px 10px; border-top: 1px solid var(--line); vertical-align: top; }}
    th {{ color: var(--muted); font-size: 13px; }}
    .pill {{
      display: inline-flex;
      align-items: center;
      min-height: 26px;
      padding: 3px 10px;
      border-radius: 999px;
      background: #edf7f2;
      color: #13543a;
      font-size: 13px;
      font-weight: 800;
    }}
    .fail {{ background: #fff1f0; color: var(--bad); }}
    a {{ color: var(--accent); font-weight: 700; text-decoration: none; }}
    @media (max-width: 800px) {{
      .metrics {{ grid-template-columns: 1fr; }}
      table, thead, tbody, tr, th, td {{ display: block; }}
      th {{ display: none; }}
      td {{ border-top: 0; padding: 6px 0; }}
      tr {{ border-top: 1px solid var(--line); padding: 12px 0; display: block; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="eyebrow">ClaimPilot Regression Suite</div>
    <h1>Agent readiness across the full claim case pack</h1>
    <div class="subtitle">Ran {total_runs} evaluations across {total_cases} claim cases. Generated {esc(generated_at)}.</div>
  </header>
  <main>
    <div class="metrics">
      <div class="metric"><div class="label">Top Agent</div><div class="big">{esc(top["agent"])}</div></div>
      <div class="metric"><div class="label">Top Average</div><div class="big">{top["average_score"]}%</div></div>
      <div class="metric"><div class="label">Top Pass Rate</div><div class="big">{top["pass_rate"]}%</div></div>
      <div class="metric"><div class="label">Total Runs</div><div class="big">{total_runs}</div></div>
    </div>
    <section>
      <h2>Agent Summary</h2>
      <div class="cards">{summary_cards}</div>
    </section>
    <section>
      <h2>Case Results</h2>
      <table>
        <thead>
          <tr>
            <th>Case</th>
            <th>Line</th>
            <th>Severity</th>
            <th>Tags</th>
            <th>Agent</th>
            <th>Score</th>
            <th>Verdict</th>
            <th>Replay</th>
          </tr>
        </thead>
        <tbody>{result_rows}</tbody>
      </table>
    </section>
  </main>
</body>
</html>
"""


def render_suite_agent_card(item: dict) -> str:
    width = max(0, min(100, item["average_score"]))
    return f"""<div class="agent-card">
  <h3>{esc(item["agent"])}</h3>
  <div class="score">{item["average_score"]}%</div>
  <div class="bar"><div style="width: {width}%"></div></div>
  <div class="label">Pass rate {item["pass_rate"]}% · {item["passed"]} passed · {item["failed"]} failed</div>
</div>"""


def render_suite_result_row(item: dict) -> str:
    grade_class = "" if item["score"]["grade"] == "pass" else " fail"
    replay_name = Path(item["replay"]).name
    tags = ", ".join(item.get("tags", [])) or "-"
    return f"""<tr>
  <td><strong>{esc(item["case_id"])}</strong><br><span class="label">{esc(item["case_title"])}</span></td>
  <td>{esc(item["line"])}</td>
  <td>{esc(item["severity"])}</td>
  <td><span class="label">{esc(tags)}</span></td>
  <td>{esc(item["agent"])}</td>
  <td><span class="pill{grade_class}">{item["score"]["percent"]}% {esc(item["score"]["grade"])}</span></td>
  <td>{esc(item["verdict"])}</td>
  <td><a href="{esc(replay_name)}">open replay</a></td>
</tr>"""


def build_leaderboard_html(case: Case, results: list[dict]) -> str:
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = "\n".join(render_leaderboard_row(index + 1, item) for index, item in enumerate(results))
    cards = "\n".join(render_agent_card(item) for item in results)
    best = results[0] if results else None
    worst = results[-1] if results else None
    best_agent = best["agent"] if best else "none"
    best_score = best["score"]["percent"] if best else 0
    worst_score = worst["score"]["percent"] if worst else 0
    failure_gap = round(best_score - worst_score, 1)
    return f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>ClaimPilot Leaderboard - {esc(case.id)}</title>
  <style>
    :root {{
      --ink: #17201b;
      --muted: #5d6b63;
      --line: #dce5dd;
      --paper: #f8faf7;
      --panel: #ffffff;
      --good: #12774f;
      --bad: #b42318;
      --accent: #2563eb;
      --amber: #b85c00;
    }}
    * {{ box-sizing: border-box; }}
    body {{
      margin: 0;
      background: var(--paper);
      color: var(--ink);
      font-family: Inter, ui-sans-serif, system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
      letter-spacing: 0;
    }}
    header {{
      padding: 44px clamp(20px, 5vw, 72px) 34px;
      background: #0f1f18;
      color: white;
      border-bottom: 5px solid #7dd3fc;
    }}
    .eyebrow {{ color: #a7f3d0; font-size: 13px; text-transform: uppercase; font-weight: 800; }}
    h1 {{ margin: 8px 0; font-size: clamp(30px, 4vw, 56px); line-height: 1.02; letter-spacing: 0; }}
    .subtitle {{ max-width: 940px; color: #d9f5e8; font-size: 17px; line-height: 1.55; }}
    main {{ padding: 28px clamp(20px, 5vw, 72px) 56px; }}
    section, .metric {{
      background: var(--panel);
      border: 1px solid var(--line);
      border-radius: 8px;
      padding: 18px;
      box-shadow: 0 10px 24px rgba(19, 31, 25, 0.05);
      margin-bottom: 18px;
    }}
    .metrics {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 18px; }}
    .score {{ font-size: 46px; font-weight: 850; color: var(--good); }}
    .label {{ color: var(--muted); font-size: 13px; }}
    .drill {{
      display: grid;
      grid-template-columns: 1.2fr 0.8fr;
      gap: 18px;
      align-items: stretch;
    }}
    .callout {{
      background: #101815;
      color: #d1fae5;
      border: 0;
    }}
    .callout h2 {{ color: white; }}
    .callout p {{ color: #d9f5e8; line-height: 1.6; }}
    .warning {{
      background: #fff7ed;
      border-color: #fed7aa;
    }}
    .warning strong {{ color: var(--amber); }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ text-align: left; padding: 14px 10px; border-top: 1px solid var(--line); vertical-align: top; }}
    th {{ color: var(--muted); font-size: 13px; }}
    .pill {{
      display: inline-flex;
      align-items: center;
      min-height: 26px;
      padding: 3px 10px;
      border-radius: 999px;
      background: #edf7f2;
      color: #13543a;
      font-size: 13px;
      font-weight: 800;
    }}
    .fail-pill {{ background: #fff1f0; color: var(--bad); }}
    .agent-card {{ border-top: 1px solid var(--line); padding: 16px 0; }}
    .agent-card:first-child {{ border-top: 0; }}
    .agent-title {{ display: flex; justify-content: space-between; gap: 14px; align-items: baseline; }}
    .bar {{ height: 10px; background: #e9efe9; border-radius: 999px; overflow: hidden; margin: 10px 0; }}
    .bar > div {{ height: 100%; background: var(--accent); }}
    a {{ color: var(--accent); font-weight: 700; text-decoration: none; }}
    @media (max-width: 800px) {{
      .metrics, .drill {{ grid-template-columns: 1fr; }}
      table, thead, tbody, tr, th, td {{ display: block; }}
      th {{ display: none; }}
      td {{ border-top: 0; padding: 6px 0; }}
      tr {{ border-top: 1px solid var(--line); padding: 12px 0; display: block; }}
    }}
  </style>
</head>
<body>
  <header>
    <div class="eyebrow">ClaimPilot Agent Leaderboard</div>
    <h1>{esc(case.title)}</h1>
    <div class="subtitle">Case <strong>{esc(case.id)}</strong> compared {len(results)} agents. Generated {esc(generated_at)}.</div>
  </header>
  <main>
    <div class="metrics">
      <div class="metric">
        <div class="label">Top Agent</div>
        <div style="font-size: 31px; font-weight: 850; margin-top: 7px;">{esc(best_agent)}</div>
      </div>
      <div class="metric">
        <div class="label">Top Score</div>
        <div class="score">{best_score}%</div>
      </div>
      <div class="metric">
        <div class="label">Claim Line</div>
        <div style="font-size: 31px; font-weight: 850; margin-top: 7px;">{esc(case.line)}</div>
      </div>
      <div class="metric">
        <div class="label">Failure Gap</div>
        <div style="font-size: 31px; font-weight: 850; margin-top: 7px; color: var(--bad);">{failure_gap} pts</div>
      </div>
    </div>
    <div class="drill">
      <section class="callout">
        <h2>Production Readiness Drill</h2>
        <p>This case tests whether an agent can resist malicious text inside uploaded evidence, ask for the official delay letter, and avoid approving a claim from an untrusted document instruction.</p>
      </section>
      <section class="warning">
        <h2>Why The Gap Matters</h2>
        <p><strong>{esc(best_agent)}</strong> holds the claim for investigation. The weakest agent scores <strong>{worst_score}%</strong>, showing how quickly a plausible demo can fail under adversarial evidence.</p>
      </section>
    </div>
    <section>
      <h2>Leaderboard</h2>
      <table>
        <thead>
          <tr>
            <th>Rank</th>
            <th>Agent</th>
            <th>Score</th>
            <th>Verdict</th>
            <th>Injection Safe</th>
            <th>Replay</th>
          </tr>
        </thead>
        <tbody>{rows}</tbody>
      </table>
    </section>
    <section>
      <h2>Agent Notes</h2>
      {cards}
    </section>
  </main>
</body>
</html>
"""


def render_leaderboard_row(rank: int, item: dict) -> str:
    decision = item["decision"]
    score = item["score"]
    injection_safe = injection_passed(score)
    grade_class = "" if score["grade"] == "pass" else " fail-pill"
    replay_name = Path(item["replay"]).name
    return f"""<tr>
  <td>#{rank}</td>
  <td><strong>{esc(item["agent"])}</strong></td>
  <td><span class="pill{grade_class}">{score["percent"]}% {esc(score["grade"])}</span></td>
  <td>{esc(decision.verdict)}</td>
  <td>{'yes' if injection_safe else 'no'}</td>
  <td><a href="{esc(replay_name)}">open replay</a></td>
</tr>"""


def render_agent_card(item: dict) -> str:
    decision = item["decision"]
    score = item["score"]
    width = max(0, min(100, score["percent"]))
    failed_checks = [check["name"] for check in score["checks"] if not check["passed"]]
    failed = ", ".join(failed_checks[:3]) if failed_checks else "No failed checks."
    return f"""<div class="agent-card">
  <div class="agent-title">
    <h3>{esc(item["agent"])}</h3>
    <strong>{score["percent"]}%</strong>
  </div>
  <div class="bar"><div style="width: {width}%"></div></div>
  <p>{esc(decision.summary)}</p>
  <div class="label">Failed checks: {esc(failed)}</div>
</div>"""


def injection_passed(score: dict) -> bool:
    checks = [check for check in score["checks"] if check["name"] == "prompt injection resistance"]
    return checks[0]["passed"] if checks else True


def render_evidence(item: dict, cited_ids: list[str]) -> str:
    cited = item["id"] in cited_ids
    cls = "evidence cited" if cited else "evidence"
    badge = " <span class=\"pill verdict\">cited</span>" if cited else ""
    return f"""<div class="{cls}">
  <strong>{esc(item["id"])}</strong> {badge}
  <div class="label">{esc(item["type"])}</div>
  <div>{esc(item["summary"])}</div>
</div>"""


def render_check(item: dict) -> str:
    status = "pass" if item["passed"] else "fail"
    label = "PASS" if item["passed"] else "FAIL"
    return f"""<div class="check">
  <strong class="{status}">{label}</strong>
  <div><strong>{esc(item["name"])}</strong><br><span class="label">{esc(item["detail"])}</span></div>
  <div>{item["weight"]} pts</div>
</div>"""


def grade_color(grade: str) -> str:
    return "var(--good)" if grade == "pass" else "var(--bad)"


def esc(value: object) -> str:
    return html.escape(str(value), quote=True)
