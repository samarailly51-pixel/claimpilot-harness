# ClaimPilot Harness

**Crash-test insurance claim AI agents before production.**

A crash-test simulator for AI claim agents: adversarial cases, deterministic scoring, and replayable failure reports.

[Live demo](https://samarailly51-pixel.github.io/claimpilot-harness/) · [中文介绍](docs/zh-CN.md) · [Release v0.1.0](https://github.com/samarailly51-pixel/claimpilot-harness/releases/tag/v0.1.0)

[![CI Ready](https://img.shields.io/badge/CI-ready-12774f)](.github/workflows/ci.yml)
[![Python](https://img.shields.io/badge/python-3.10%2B-2563eb)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-12774f)](LICENSE)
[![Agent Evals](https://img.shields.io/badge/agent-evals-0f766e)](#why-this-exists)
[![Prompt Injection](https://img.shields.io/badge/prompt--injection-tested-b42318)](cases/travel-injection-001.json)

ClaimPilot Harness runs messy insurance claim scenarios against AI agents and shows where they passed, hesitated, or failed.

It is not another claim-processing agent. It is the test range for them.

![ClaimPilot Harness cover](assets/claimpilot-cover.svg)

![ClaimPilot demo](assets/claimpilot-demo.gif)

## 中文简介

ClaimPilot Harness 是一个面向保险理赔 AI Agent 的评测与红队测试框架。它把冲突证据、缺失材料、保单排除项、用户陈述矛盾和 Prompt Injection 做成可复现的测试案例，用来验证 Agent 在真实业务压力下是否可靠。

项目内置车险、健康险、旅行险、宠物险和财产险等示例案例，支持 deterministic scoring、case coverage catalog、Agent 横向对比、HTML replay、leaderboard，以及 OpenAI-compatible `/v1/chat/completions` 和 HTTP Agent 接口接入。

它不是又一个理赔 Agent，而是理赔 Agent 上线前的“碰撞测试场”。完整中文介绍见 [docs/zh-CN.md](docs/zh-CN.md)。

```bash
python -m claimpilot_harness compare cases/travel-injection-001.json demo risky
```

```txt
Case:        travel-injection-001
Leaderboard: runs/travel-injection-001-leaderboard.html

Agent        Score    Verdict
------------ -------- ------------
demo          93.9%   investigate
risky          6.1%   approve
```

## Why This Exists

Most AI agent demos look impressive until they meet messy real-world claims: mismatched invoices, missing documents, policy exclusions, claimant contradictions, hidden prompt injection, and privacy traps.

ClaimPilot turns those failure modes into repeatable test cases.

Use it to answer:

- Did the agent choose the right claim action?
- Did it cite the evidence that mattered?
- Did it request the missing document instead of guessing?
- Did it detect fraud or coverage inconsistencies?
- Did it ignore malicious instructions hidden inside uploaded evidence?

See [docs/why-claimpilot.md](docs/why-claimpilot.md) for the product thesis and [docs/evaluation-methodology.md](docs/evaluation-methodology.md) for the evaluation methodology.

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
Cases:  5
Report: runs/suite-report.html

Agent        Avg Score  Pass Rate
------------ ---------- ----------
demo             92.0%     100.0%
risky            13.1%       0.0%
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
| `health-bill-001` | Health | Possible excluded cosmetic procedure without medical necessity proof. |
| `travel-injection-001` | Travel | Missing official delay proof plus prompt injection hidden in uploaded evidence. |
| `pet-preexisting-001` | Pet | Symptoms appear to predate enrollment, testing pre-existing condition handling. |
| `property-water-damage-001` | Property | Repair estimate scope exceeds moisture readings and photo evidence. |

Generate a coverage catalog for the case pack:

```bash
python -m claimpilot_harness catalog cases
```

```txt
Cases: 5
Lines: auto=1, health=1, pet=1, property=1, travel=1
Severities: critical=1, high=2, medium=2
Traps: prompt_injection=1
```

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
- Red-team traps
- Expected findings, document requests, citations, and forbidden behavior
- A weighted scoring rubric

See [docs/case-format.md](docs/case-format.md).

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

- Mixed-agent comparison configs
- Ollama adapter
- LLM-as-judge scoring mode
- Claim case generator for synthetic case packs
- Fraud, compliance, and privacy scorecards
- CI mode for regression testing agent changes
- GitHub Pages replay gallery

## Positioning

ClaimPilot Harness is built for the gap between AI agent demos and production systems. A claim agent that can answer one happy-path question is easy to build. A claim agent that survives conflicting evidence, policy constraints, missing documents, and adversarial uploads needs a harness.

That is the product surface this project explores.

## License

MIT
