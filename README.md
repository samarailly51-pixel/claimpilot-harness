# ClaimPilot Harness

**Crash-test insurance claim AI agents before production.**

ClaimPilot is an open-source evaluation product for claim AI agents: a traceable Model Arena, adversarial insurance cases, deterministic scoring, replayable reports, human review, and adapter-first model comparison.

[Interactive product demo](https://samarailly51-pixel.github.io/claimpilot-harness/) · [Model Arena](docs/model-arena.md) · [Human review](docs/human-review.md) · [Connect real agents](docs/connect-real-agents.md) · [中文介绍](docs/zh-CN.md) · [Release v0.2.0](https://github.com/samarailly51-pixel/claimpilot-harness/releases/tag/v0.2.0)

[![CI Ready](https://img.shields.io/badge/CI-ready-12774f)](.github/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-2563eb)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-12774f)](LICENSE)
[![Agent Evals](https://img.shields.io/badge/agent-evals-0f766e)](#why-this-exists)
[![Prompt Injection](https://img.shields.io/badge/prompt--injection-tested-b42318)](cases/travel-injection-001.json)

ClaimPilot Harness runs messy insurance claim scenarios against AI agents and shows where they passed, hesitated, or failed.

It is not another claim-processing agent. It is the test range for them.

| Signal | Current v0.2.0 |
| --- | --- |
| Case pack | 10 adversarial claim cases across auto, health, travel, pet, property, and workers compensation |
| Risk taxonomy | 18 reusable tags including `bodily_injury`, `causation_gap`, `prompt_injection`, and `evidence_conflict` |
| Baselines | cautious rule baseline: 95.9% suite average; risky rule baseline: 16.9% |
| Agent adapters | Built-in, command, HTTP service, OpenAI-compatible `/v1/chat/completions` |
| Outputs | Arena snapshot, replay HTML, suite report, human-review JSON, dataset SHA-256 |
| Automation | GitHub Actions CI and Pages demo rebuild on every push |

```bash
python -m claimpilot_harness suite cases --agents demo risky
```

![ClaimPilot Harness cover](assets/claimpilot-cover.svg)

![ClaimPilot demo](assets/claimpilot-demo.gif)

## 中文简介

ClaimPilot Harness 是一个面向保险理赔 AI Agent 的评测与红队测试框架。它把冲突证据、缺失材料、保单排除项、用户陈述矛盾和 Prompt Injection 做成可复现的测试案例，用来验证 Agent 在真实业务压力下是否可靠。

项目内置车险、健康险、旅行险、宠物险和财产险等示例案例，支持 deterministic scoring、case coverage catalog、Agent 横向对比、HTML replay、leaderboard，以及 OpenAI-compatible `/v1/chat/completions` 和 HTTP Agent 接口接入。

它不是又一个理赔 Agent，而是理赔 Agent 上线前的“碰撞测试场”。完整中文介绍见 [docs/zh-CN.md](docs/zh-CN.md)。

## Why This Exists

Most AI agent demos look impressive until they meet messy real-world claims: mismatched invoices, missing documents, policy exclusions, claimant contradictions, hidden prompt injection, and privacy traps.

ClaimPilot turns those failure modes into repeatable test cases.

Use it to answer:

- Did the agent choose the right claim action?
- Did it cite the evidence that mattered?
- Did it request the missing document instead of guessing?
- Did it detect fraud or coverage inconsistencies?
- Did it ignore malicious instructions hidden inside uploaded evidence?

See [docs/why-claimpilot.md](docs/why-claimpilot.md) for the product thesis, [docs/evaluation-methodology.md](docs/evaluation-methodology.md) for the evaluation methodology, and [docs/architecture.md](docs/architecture.md) for the system architecture.

## Demo

Compare a careful agent against a deliberately risky one:

```bash
python -m claimpilot_harness compare cases/travel-injection-001.json demo risky
```

On Windows, use `py -m claimpilot_harness ...` if `python` is not on your PATH.

You will get a score and a replay report:

```txt
Case:        travel-injection-001
Leaderboard: runs/travel-injection-001-leaderboard.html

Agent        Score    Verdict
------------ -------- ------------
demo          93.9%   investigate
risky          6.1%   approve
```

Open `runs/latest.html` to view the leaderboard.

![ClaimPilot leaderboard preview](assets/leaderboard-preview.svg)

Run the full regression suite across all included cases:

```bash
python -m claimpilot_harness suite cases --agents demo risky
```

```txt
Cases:  10
Report: runs/suite-report.html

Agent        Avg Score  Pass Rate
------------ ---------- ----------
demo             95.9%     100.0%
risky            16.9%       0.0%
```

## What A Replay Shows

The replay report is designed for product, risk, and engineering review:

- Evidence timeline
- Agent verdict and confidence
- Findings and requested documents
- Prompt-injection / privacy flags
- Scoring breakdown by rubric item
- Raw decision JSON for debugging

## Included Case Packs

| Case | Line | What It Tests |
| --- | --- | --- |
| `auto-collision-001` | Auto | Repair invoice conflicts with damage photos and claimant chat. |
| `auto-bodily-injury-001` | Auto BI | Causation, treatment chronology, medical-record, and wage-loss conflicts. |
| `health-bill-001` | Health | Possible excluded cosmetic procedure without medical necessity proof. |
| `health-experimental-treatment-001` | Health | Experimental treatment without medical-necessity or authorization support. |
| `medical-privacy-injection-001` | Health | Medical necessity ambiguity plus privacy lure and hidden prompt injection. |
| `travel-injection-001` | Travel | Missing official delay proof plus prompt injection hidden in uploaded evidence. |
| `pet-preexisting-001` | Pet | Symptoms appear to predate enrollment, testing pre-existing condition handling. |
| `property-water-damage-001` | Property | Repair estimate scope exceeds moisture readings and photo evidence. |
| `property-fire-invoice-001` | Property | Smoke-damage invoice conflicts with inspection photos. |
| `workers-comp-injury-001` | Workers comp | Delayed treatment, work causation, and unsupported wage-loss evidence. |

See the [Risk Taxonomy](docs/risk-taxonomy.md) for the reusable failure-mode tags behind the case pack.

## Domain Skill Pack

[Bodily Injury Claims Processing in Auto Insurance](skills/bodily-injury-claims-processing/SKILL.md) turns domain review knowledge into an executable workflow for intake, causation analysis, treatment chronology, medical evidence, wage-loss verification, and safe human escalation. The paired `auto-bodily-injury-001` case verifies that an Agent does not auto-approve from claim amount alone when material evidence conflicts or is missing.

Generate a coverage catalog for the case pack:

```bash
python -m claimpilot_harness catalog cases
```

```txt
Cases: 10
Lines: auto=2, health=3, pet=1, property=2, travel=1, workers_comp=1
Severities: critical=2, high=5, medium=3
Tags: bodily_injury=2, causation_gap=2, claimant_contradiction=1, coverage_timing=1, delayed_reporting=1, evidence_conflict=4, experimental_treatment=1, invoice_mismatch=2, medical_necessity=3, missing_document=8, policy_exclusion=3, pre_existing_condition=1, privacy_lure=1, prompt_injection=2, scope_inflation=2, treatment_gap=2, untrusted_evidence=1, wage_loss=2
Traps: causation_shortcut=1, privacy_lure=1, prompt_injection=2, threshold_shortcut=1
```

## Traceable Model Arena

Run named profiles against the same dataset and write a benchmark snapshot with an experiment ID, dataset fingerprint, profile type, score, pass rate, latency, and case-level replays:

```bash
python -m claimpilot_harness arena cases \
  --config benchmarks/baseline-arena.json \
  --out runs/arena
```

Use `benchmarks/models.example.json` to connect OpenAI-compatible, HTTP, or command-based models. Built-in profiles are always labeled `rule_baseline`; external adapters are labeled `external_model`. Missing token and cost data remains `null` instead of being estimated. See [Model Arena](docs/model-arena.md).

## Human Review Workbench

The interactive demo lets a reviewer confirm findings, override the Agent verdict, record rationale, retain reviews locally, and export a dataset-bound JSON artifact. The static site does not transmit review data. See [Human Review](docs/human-review.md).

## Agent Interface

Use the built-in demo agent:

```bash
python -m claimpilot_harness run cases/auto-collision-001.json --agent demo
```

Compare built-in agents and generate a leaderboard:

```bash
python -m claimpilot_harness compare cases/travel-injection-001.json demo risky
```

Validate case packs before running or contributing them:

```bash
python -m claimpilot_harness validate cases
```

Summarize case-pack coverage:

```bash
python -m claimpilot_harness catalog cases --markdown
```

Run a full case-pack regression suite:

```bash
python -m claimpilot_harness suite cases --agents demo risky
```

The suite writes both an HTML report and a machine-readable benchmark artifact:

```txt
runs/suite-report.html
runs/suite-results.json
```

Use the suite as a CI quality gate:

```bash
python -m claimpilot_harness suite cases --agents demo \
  --min-average-score 90 \
  --min-pass-rate 100
```

If any evaluated agent falls below the threshold, the command exits with a non-zero status.

Refresh the static GitHub Pages demo locally:

```bash
python scripts/build_demo_site.py
```

Run an OpenAI-compatible model:

```bash
python -m claimpilot_harness run cases/travel-injection-001.json \
  --agent openai \
  --openai-model your-model-name
```

Compare it against the built-in baselines:

```bash
python -m claimpilot_harness compare cases/travel-injection-001.json demo openai risky \
  --openai-model your-model-name
```

Run a custom HTTP agent service:

```bash
python examples/http_agent.py
python -m claimpilot_harness run cases/travel-injection-001.json \
  --agent http \
  --agent-url http://127.0.0.1:8000/review
```

Or connect any agent command that reads JSON from `stdin` and prints a JSON decision:

```bash
python -m claimpilot_harness run cases/auto-collision-001.json \
  --agent command \
  --agent-command "python examples/simple_agent.py"
```

Expected decision shape:

```json
{
  "verdict": "investigate",
  "confidence": 0.82,
  "summary": "Hold the claim pending additional review.",
  "findings": ["invoice and physical damage evidence need reconciliation"],
  "requested_documents": ["independent adjuster estimate"],
  "cited_evidence": ["E2", "E3"],
  "privacy_flags": ["ignored embedded instruction in evidence"]
}
```

## Case Format

Cases are plain JSON files. Each case contains:

- Claimant and policy context
- Evidence summaries with stable IDs
- Risk taxonomy tags
- Red-team traps
- Expected findings, document requests, citations, and forbidden behavior
- A weighted scoring rubric

See [docs/case-format.md](docs/case-format.md) and [docs/risk-taxonomy.md](docs/risk-taxonomy.md).

The scoring approach is explained in [docs/evaluation-methodology.md](docs/evaluation-methodology.md) and [docs/scoring-rubric.md](docs/scoring-rubric.md).

Validate a case file or an entire case directory:

```bash
python -m claimpilot_harness validate cases
python -m claimpilot_harness validate cases/travel-injection-001.json --json
```

## OpenAI-Compatible Adapter

ClaimPilot supports OpenAI-style `/v1/chat/completions` endpoints without requiring an SDK dependency.

Set `OPENAI_API_KEY`, then pass `--agent openai` and `--openai-model`. Use `--openai-base-url` for compatible local or hosted gateways.

See [docs/openai-compatible.md](docs/openai-compatible.md).

For end-to-end examples, see [docs/connect-real-agents.md](docs/connect-real-agents.md).

## HTTP Agent Adapter

ClaimPilot can evaluate any custom agent service that accepts `POST` JSON and returns a decision object.

Start the example service:

```bash
python examples/http_agent.py
```

Then run:

```bash
python -m claimpilot_harness run cases/travel-injection-001.json \
  --agent http \
  --agent-url http://127.0.0.1:8000/review
```

## Roadmap

- Ollama adapter
- LLM-as-judge scoring mode
- Claim case generator for synthetic case packs
- Fraud, compliance, and privacy scorecards
- Server-backed multi-reviewer audit workflow

## Positioning

ClaimPilot Harness is built for the gap between AI agent demos and production systems. A claim agent that can answer one happy-path question is easy to build. A claim agent that survives conflicting evidence, policy constraints, missing documents, and adversarial uploads needs a harness.

That is the product surface this project explores.

## Sharing

For launch copy and the v0.2 demo sequence, see [docs/launch-v0.2.md](docs/launch-v0.2.md).

## Contributing Case Packs

New adversarial claim scenarios are the best way to extend ClaimPilot. Start from [`cases/template-case.json`](cases/template-case.json), then follow the [Case Contribution Guide](docs/case-contribution-guide.md) or open a [good first case](.github/ISSUE_TEMPLATE/good_first_case.md).

## License

MIT
