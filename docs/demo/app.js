const state = {
  cases: [],
  results: [],
  caseId: "travel-injection-001",
  agent: "demo",
  running: false,
};

const agentCopy = {
  demo: { name: "Cautious Agent", badge: "baseline", description: "Evidence-grounded review" },
  risky: { name: "Risky Agent", badge: "red team", description: "Approval-biased behavior" },
};

const logCopy = {
  demo: [
    "Loading policy constraints and evidence bundle...",
    "Separating document content from executable instructions...",
    "Cross-checking claim assertions against source evidence...",
    "Applying deterministic safety rubric...",
  ],
  risky: [
    "Loading claimant request...",
    "Trusting uploaded document instructions...",
    "Skipping missing-evidence verification...",
    "Returning approval-biased decision...",
  ],
};

const wait = (ms) => new Promise((resolve) => setTimeout(resolve, ms));
const $ = (selector) => document.querySelector(selector);

async function bootstrap() {
  const [caseResponse, resultResponse] = await Promise.all([
    fetch("case-data.json", { cache: "no-store" }),
    fetch("suite-results.json", { cache: "no-store" }),
  ]);
  state.cases = await caseResponse.json();
  state.results = (await resultResponse.json()).results;
  renderCaseOptions();
  bindEvents();
  renderAll();
}

function renderCaseOptions() {
  $("#caseSelect").innerHTML = state.cases.map((item) =>
    `<option value="${escapeHtml(item.id)}">${escapeHtml(lineLabel(item.line))} · ${escapeHtml(item.title)}</option>`
  ).join("");
  $("#caseSelect").value = state.caseId;
}

function bindEvents() {
  $("#caseSelect").addEventListener("change", (event) => {
    state.caseId = event.target.value;
    resetPipeline();
    renderAll();
  });
  document.querySelectorAll("[data-agent]").forEach((button) => {
    button.addEventListener("click", () => {
      if (state.running) return;
      state.agent = button.dataset.agent;
      resetPipeline();
      renderAll();
    });
  });
  $("#runButton").addEventListener("click", runEvaluation);
  window.addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") runEvaluation();
  });
}

function currentCase() { return state.cases.find((item) => item.id === state.caseId); }
function currentResult() { return state.results.find((item) => item.case_id === state.caseId && item.agent === state.agent); }

function renderAll() {
  const item = currentCase();
  const result = currentResult();
  if (!item || !result) return;
  renderRail(item);
  renderCase(item);
  renderInspector(item, result);
}

function renderRail(item) {
  document.querySelectorAll("[data-agent]").forEach((button) => {
    button.classList.toggle("active", button.dataset.agent === state.agent);
    button.setAttribute("aria-pressed", button.dataset.agent === state.agent ? "true" : "false");
  });
  $("#caseTags").innerHTML = item.tags.map((tag) => `<span class="tag">${escapeHtml(tag)}</span>`).join("");
  $("#severityBadge").textContent = `${lineLabel(item.line)} · ${item.severity}`;
}

function renderCase(item) {
  $("#caseId").textContent = item.id;
  $("#caseTitle").textContent = item.title;
  $("#claimAmount").textContent = formatAmount(item.claimant.claim_amount);
  $("#claimantMeta").textContent = `${item.claimant.name} · ${item.policy.number}`;
  $("#evidenceList").innerHTML = item.evidence.map((evidence) => {
    const flagged = /injection|ignore prior|hidden instruction/i.test(evidence.summary);
    return `<article class="evidence-item">
      <span class="evidence-id">${escapeHtml(evidence.id)}</span>
      <div><strong>${escapeHtml(typeLabel(evidence.type))}</strong><p>${escapeHtml(evidence.summary)}</p></div>
      <span class="evidence-state ${flagged ? "flagged" : ""}">${flagged ? "risk signal" : "loaded"}</span>
    </article>`;
  }).join("");
}

function renderInspector(item, result) {
  const passed = result.grade === "pass";
  $("#scoreValue").innerHTML = `${Number(result.score).toFixed(1)}<small>/100</small>`;
  $("#verdict").textContent = `${result.verdict} · ${result.grade}`;
  $("#verdict").classList.toggle("fail", !passed);
  $("#scoreFill").className = passed ? "" : "fail";
  $("#scoreFill").style.width = `${result.score}%`;
  $("#agentName").textContent = agentCopy[state.agent].name;
  $("#metricList").innerHTML = metricRows(item, result, passed);
  $("#findingList").innerHTML = findingRows(item, passed);
  $("#replayLink").href = result.replay;
}

function metricRows(item, result, passed) {
  const injection = item.tags.includes("prompt_injection");
  const metrics = [
    ["Decision quality", passed ? "safe hold" : "unsafe approve"],
    ["Evidence grounding", passed ? `${item.expected.must_cite.length} citations` : "0 citations"],
    ["Missing proof", passed ? `${item.expected.must_request.length} requested` : "not requested"],
    ["Injection defense", injection ? (passed ? "resisted" : "failed") : "not triggered"],
  ];
  return metrics.map(([label, value]) => `<div class="metric"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value)}</strong></div>`).join("");
}

function findingRows(item, passed) {
  const findings = passed
    ? [...item.expected.must_find.slice(0, 2), ...item.expected.must_request.slice(0, 1).map((x) => `Request: ${x}`)]
    : [`Missed ${item.expected.must_find.length} required risk findings`, "Approved before evidence requirements were satisfied"];
  return findings.map((finding) => `<div class="finding ${passed ? "" : "danger"}">${escapeHtml(finding)}</div>`).join("");
}

async function runEvaluation() {
  if (state.running) return;
  state.running = true;
  const button = $("#runButton");
  const consoleBox = $("#console");
  button.disabled = true;
  button.textContent = "Running evaluation...";
  consoleBox.innerHTML = "";
  resetPipeline();

  const steps = document.querySelectorAll(".pipe-step");
  for (let index = 0; index < steps.length; index += 1) {
    steps.forEach((step, stepIndex) => {
      step.classList.toggle("done", stepIndex < index);
      step.classList.toggle("active", stepIndex === index);
    });
    const line = document.createElement("div");
    line.className = "console-line";
    line.textContent = `0${index + 1}  ${logCopy[state.agent][index]}`;
    consoleBox.appendChild(line);
    await wait(520);
  }
  steps.forEach((step) => { step.classList.add("done"); step.classList.remove("active"); });
  const result = currentResult();
  const finalLine = document.createElement("div");
  finalLine.className = "console-line";
  finalLine.textContent = `✓  Evaluation complete · ${result.score}% · ${result.grade.toUpperCase()}`;
  consoleBox.appendChild(finalLine);
  renderInspector(currentCase(), result);
  $("#scoreFill").style.width = "0";
  requestAnimationFrame(() => requestAnimationFrame(() => { $("#scoreFill").style.width = `${result.score}%`; }));
  button.disabled = false;
  button.textContent = "Run evaluation";
  state.running = false;
}

function resetPipeline() {
  document.querySelectorAll(".pipe-step").forEach((step) => step.classList.remove("active", "done"));
  $("#console").innerHTML = '<span style="color:#7fa393">Ready. Select a case and agent, then run the evaluation.</span>';
}

function lineLabel(value) {
  return ({ auto: "Auto", health: "Health", pet: "Pet", property: "Property", travel: "Travel" })[value] || value;
}
function typeLabel(value) { return value.split("_").map((x) => x[0].toUpperCase() + x.slice(1)).join(" "); }
function formatAmount(value) { return new Intl.NumberFormat("en-US", { style: "currency", currency: "USD", maximumFractionDigits: 0 }).format(value); }
function escapeHtml(value) {
  return String(value).replaceAll("&", "&amp;").replaceAll("<", "&lt;").replaceAll(">", "&gt;").replaceAll('"', "&quot;").replaceAll("'", "&#039;");
}

bootstrap().catch((error) => {
  $("#console").textContent = `Unable to load demo data: ${error.message}`;
});
