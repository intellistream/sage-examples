const state = {
  apps: [],
  instances: [],
  experiments: null,
  ports: null,
  settings: null,
  activeAppId: null,
  activeInstanceId: null,
  activeInstanceDetail: null,
  activeInstanceTab: "overview",
  validation: null,
  search: "",
  requestResult: null,
  metricsHistory: [],
  requestRoute: "app",
  toastTimer: null,
};

const refs = {
  sidebarRoot: document.getElementById("sidebar-root"),
  sidebarPython: document.getElementById("sidebar-python"),
  sidebarPortRange: document.getElementById("sidebar-port-range"),
  searchInput: document.getElementById("search-input"),
  launchShortcut: document.getElementById("launch-shortcut"),
  summaryCards: document.getElementById("summary-cards"),
  overviewInstances: document.getElementById("overview-instances"),
  recentActivity: document.getElementById("recent-activity"),
  catalogCount: document.getElementById("catalog-count"),
  catalogGrid: document.getElementById("catalog-grid"),
  launchAppSelect: document.getElementById("launch-app-select"),
  launchHost: document.getElementById("launch-host"),
  launchAutoPort: document.getElementById("launch-auto-port"),
  launchPort: document.getElementById("launch-port"),
  launchStoragePath: document.getElementById("launch-storage-path"),
  dynamicArgs: document.getElementById("dynamic-args"),
  launchEnvHints: document.getElementById("launch-env-hints"),
  launchEnv: document.getElementById("launch-env"),
  launchArgs: document.getElementById("launch-args"),
  launchTimeout: document.getElementById("launch-timeout"),
  launchServiceMode: document.getElementById("launch-service-mode"),
  launchAllowDuplicate: document.getElementById("launch-allow-duplicate"),
  launchAppFacts: document.getElementById("launch-app-facts"),
  dryRunButton: document.getElementById("dry-run-button"),
  copyCommandButton: document.getElementById("copy-command-button"),
  launchButton: document.getElementById("launch-button"),
  endpointPreview: document.getElementById("endpoint-preview"),
  commandPreview: document.getElementById("command-preview"),
  environmentPreview: document.getElementById("environment-preview"),
  preflightChecks: document.getElementById("preflight-checks"),
  requestRoute: document.getElementById("request-route"),
  requestPayloadMode: document.getElementById("request-payload-mode"),
  requestTemplate: document.getElementById("request-template"),
  requestArgument: document.getElementById("request-argument"),
  requestFilename: document.getElementById("request-filename"),
  requestTimeout: document.getElementById("request-timeout"),
  requestExtraArgs: document.getElementById("request-extra-args"),
  requestEnv: document.getElementById("request-env"),
  requestContent: document.getElementById("request-content"),
  requestTargetFacts: document.getElementById("request-target-facts"),
  requestTemplateHint: document.getElementById("request-template-hint"),
  applyRequestTemplateButton: document.getElementById("apply-request-template"),
  copyRequestCurlButton: document.getElementById("copy-request-curl"),
  sendRequestButton: document.getElementById("send-request-button"),
  requestCurlPreview: document.getElementById("request-curl-preview"),
  requestResultSummary: document.getElementById("request-result-summary"),
  requestResultBody: document.getElementById("request-result-body"),
  instancesTable: document.getElementById("instances-table"),
  instanceDetail: document.getElementById("instance-detail"),
  compatibilityTable: document.getElementById("compatibility-table"),
  portsUsed: document.getElementById("ports-used"),
  portsAvailable: document.getElementById("ports-available"),
  experimentSummary: document.getElementById("experiment-summary"),
  experimentLog: document.getElementById("experiment-log"),
  clearExperimentsButton: document.getElementById("clear-experiments-button"),
  settingsGrid: document.getElementById("settings-grid"),
  toast: document.getElementById("toast"),
};

let validationTimer = null;

const REQUEST_TEMPLATES = {
  retrieval: {
    label: "Retrieval-only",
    description: "Inject direct source material and inspect the most basic request path through the selected pipeline.",
    defaultPayloadMode: "source",
  },
  tool: {
    label: "Tool-backed",
    description: "Ask for a transformed or action-oriented output so the pipeline does more than simply echo the input.",
    defaultPayloadMode: "prompt",
  },
  follow_up: {
    label: "Follow-up",
    description: "Submit a refinement request that assumes a prior answer exists and asks for the next decision or revision.",
    defaultPayloadMode: "prompt",
  },
};

function escapeHtml(value) {
  return String(value ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  if (!response.ok) {
    let detail = `${response.status} ${response.statusText}`;
    try {
      const payload = await response.json();
      detail = payload.detail || detail;
    } catch {
      const text = await response.text();
      if (text) {
        detail = text;
      }
    }
    throw new Error(detail);
  }
  return response.json();
}

function showToast(message, { error = false } = {}) {
  refs.toast.textContent = message;
  refs.toast.classList.add("is-visible");
  refs.toast.classList.toggle("is-error", error);
  clearTimeout(state.toastTimer);
  state.toastTimer = setTimeout(() => {
    refs.toast.classList.remove("is-visible", "is-error");
  }, 2600);
}

function formatDateTime(value) {
  if (!value) {
    return "-";
  }
  const date = new Date(value);
  return `${date.toLocaleDateString("zh-CN")} ${date.toLocaleTimeString("zh-CN", { hour12: false })}`;
}

function formatDuration(seconds) {
  if (seconds == null) {
    return "-";
  }
  if (seconds < 60) {
    return `${Math.round(seconds)}s`;
  }
  const minutes = Math.floor(seconds / 60);
  const remainingSeconds = Math.round(seconds % 60);
  if (minutes < 60) {
    return `${minutes}m ${remainingSeconds}s`;
  }
  const hours = Math.floor(minutes / 60);
  const remainingMinutes = minutes % 60;
  return `${hours}h ${remainingMinutes}m`;
}

function statusBadgeClass(status) {
  const normalized = (status || "neutral").toLowerCase();
  if (["running", "passed", "verified", "completed"].includes(normalized)) return "badge-running";
  if (["starting", "degraded", "partial"].includes(normalized)) return "badge-starting";
  if (["failed", "incompatible"].includes(normalized)) return "badge-failed";
  if (["stopped"].includes(normalized)) return "badge-neutral";
  if (["discovered", "skipped", "warning", "untested"].includes(normalized)) return "badge-warning";
  return "badge-neutral";
}

function renderBadge(label, status = "neutral") {
  return `<span class="badge ${statusBadgeClass(status)}">${escapeHtml(label)}</span>`;
}

function renderKeyValueRows(rows) {
  return rows
    .map(
      ([label, value]) => `
        <div class="kv-row"><span>${escapeHtml(label)}</span><strong>${escapeHtml(value ?? "-")}</strong></div>
      `,
    )
    .join("");
}

function parseEnvText(value) {
  return value
    .split(/\n+/)
    .map((line) => line.trim())
    .filter(Boolean)
    .reduce((accumulator, line) => {
      const index = line.indexOf("=");
      if (index === -1) {
        return accumulator;
      }
      const key = line.slice(0, index).trim();
      const envValue = line.slice(index + 1).trim();
      if (key) {
        accumulator[key] = envValue;
      }
      return accumulator;
    }, {});
}

function parseArgsText(value) {
  return value
    .split(/\n+/)
    .map((line) => line.trim())
    .filter(Boolean);
}

function maskEnvValue(key, value) {
  if (!key) {
    return value;
  }
  if (/(key|secret|token|password)/i.test(key)) {
    return value ? "••••••" : "";
  }
  return value;
}

function currentApp() {
  return state.apps.find((app) => app.id === state.activeAppId) || null;
}

function currentInstanceSummary() {
  return state.instances.find((item) => item.instance_id === state.activeInstanceId) || null;
}

function currentServiceInstance() {
  const active = currentInstanceSummary();
  if (active?.service_mode) {
    if (state.activeInstanceDetail?.instance_id === active.instance_id) {
      return { ...active, ...state.activeInstanceDetail };
    }
    return active;
  }
  const fallback = state.instances.find((item) => item.service_mode && ["running", "degraded"].includes(item.status))
    || state.instances.find((item) => item.service_mode);
  if (!fallback) {
    return null;
  }
  if (state.activeInstanceDetail?.instance_id === fallback.instance_id) {
    return { ...fallback, ...state.activeInstanceDetail };
  }
  return fallback;
}

function isOutputLikeArgument(argument) {
  const name = String(argument?.primary_name || "").toLowerCase();
  return /(out|output|result|report|dest|destination|save|write|export)/.test(name);
}

function inlineInputCandidates(app) {
  return (app?.arguments || []).filter((argument) => argument.kind === "path" && !argument.positional && !isOutputLikeArgument(argument));
}

function preferredInlineArgument(app) {
  const candidates = inlineInputCandidates(app);
  const required = candidates.filter((argument) => argument.required);
  if (required.length === 1) {
    return required[0];
  }
  if (candidates.length === 1) {
    return candidates[0];
  }
  return [...required, ...candidates].find((argument) => /(input|source|file|document|prompt|text|content|data)/.test(argument.primary_name.toLowerCase())) || null;
}

function basenamePath(value) {
  return String(value || "").split(/[\\/]/).pop() || "";
}

function inferRequestFilename(app, payloadMode, route) {
  if (route === "openai") {
    return "prompt.txt";
  }
  const preferred = preferredInlineArgument(app);
  const candidate = basenamePath(preferred?.opc_default_value || preferred?.default || "");
  if (candidate) {
    return candidate;
  }
  return payloadMode === "source" ? "source.txt" : "prompt.txt";
}

function naturalLanguageTemplate(templateKey, app) {
  const appName = app?.name || "selected pipeline";
  const purpose = app?.purpose || "process the attached material";
  if (templateKey === "tool") {
    return `You are exercising ${appName}.\nUsing the attached material, produce:\n- a concise summary\n- a prioritized action list\n- a small JSON block named \"next_actions\"\n\nContext: ${purpose}`;
  }
  if (templateKey === "follow_up") {
    return `Assume this is a follow-up turn for ${appName}.\nUsing the attached material and the prior result, rewrite the answer for an operations lead and call out unresolved questions.\n\nContext: ${purpose}`;
  }
  return `Read the attached material for ${appName}.\nReturn:\n1. Three key facts\n2. One potential risk\n3. One short recommended next step\n\nContext: ${purpose}`;
}

function structuredTemplateForExtension(extension, app) {
  if (extension === "csv") {
    return "name,age,segment\nAlice,30,enterprise\nBob,,smb\nChen,41,education\n";
  }
  if (extension === "json") {
    return JSON.stringify(
      [
        { ticket_id: "T-314", severity: "high", summary: "Delayed shipment on a priority order." },
        { ticket_id: "T-271", severity: "medium", summary: "Customer requested a billing correction." },
      ],
      null,
      2,
    );
  }
  if (["md", "txt", "log"].includes(extension)) {
    return `Operational note for ${app?.name || "the selected pipeline"}\n\nCustomer: Acme Foods\nIssue: Cold-chain alert triggered twice overnight for warehouse 3.\nObserved impact: Two pallets may need manual inspection before dispatch.\nImmediate context: On-call operator already reset the sensor once.`;
  }
  if (extension === "html") {
    return "<html><body><h1>Incident Update</h1><p>Shipment monitoring flagged a repeated temperature deviation in warehouse 3.</p></body></html>";
  }
  return `Source material for ${app?.name || "the selected pipeline"}.\nThe system should inspect this content, surface the most important facts, and identify the next operational step.`;
}

function buildRequestTemplateContent(templateKey, { route, payloadMode, filename, app }) {
  if (route === "openai" || payloadMode === "prompt") {
    return naturalLanguageTemplate(templateKey, app);
  }
  const extension = String(filename || "").includes(".") ? String(filename).split(".").pop().toLowerCase() : "txt";
  return structuredTemplateForExtension(extension, app);
}

function requestRouteLabel(route) {
  if (route === "instance") {
    return "Service invoke";
  }
  if (route === "openai") {
    return "OpenAI chat";
  }
  return "App one-shot";
}

function resolveRequestContext() {
  const app = currentApp();
  const serviceInstance = currentServiceInstance();
  const options = [];
  if (app && app.execution_mode !== "http") {
    options.push({ value: "app", label: `App one-shot · ${app.name}` });
  }
  if (serviceInstance?.service_mode) {
    options.push({ value: "instance", label: `Service invoke · ${serviceInstance.instance_id}` });
  }
  if (serviceInstance?.service_mode && serviceInstance.openai_model) {
    options.push({ value: "openai", label: `OpenAI chat · ${serviceInstance.openai_model}` });
  }
  if (!options.some((option) => option.value === state.requestRoute)) {
    state.requestRoute = options[0]?.value || "app";
  }
  return { app, serviceInstance, options, route: state.requestRoute };
}

function requestEndpointPath(context) {
  if (context.route === "instance") {
    return `/api/instances/${context.serviceInstance.instance_id}/invoke`;
  }
  if (context.route === "openai") {
    return "/v1/chat/completions";
  }
  return `/api/apps/${context.app.id}/invoke`;
}

function buildRequestSubmission(context, { preview = false } = {}) {
  if (!context.options.length) {
    return { error: "No invoke route is currently available." };
  }

  if (context.route === "openai") {
    const content = refs.requestContent.value.trim();
    if (!content && !preview) {
      return { error: "Enter request content before sending an OpenAI-style prompt." };
    }
    return {
      path: "/v1/chat/completions",
      body: {
        model: context.serviceInstance.openai_model,
        messages: [{ role: "user", content: content || "<prompt>" }],
        temperature: 0,
      },
    };
  }

  const payloadMode = refs.requestPayloadMode.value || "prompt";
  const content = refs.requestContent.value.trim();
  const filename = refs.requestFilename.value.trim();
  const argument = refs.requestArgument.value.trim();
  const body = {
    extra_args: parseArgsText(refs.requestExtraArgs.value),
    env: parseEnvText(refs.requestEnv.value),
    timeout_seconds: Number(refs.requestTimeout.value || 30) || 30,
    capture_output_preview_chars: 12000,
  };
  const effectiveContent = content || (preview ? `<${payloadMode}>` : "");

  if (effectiveContent) {
    body[payloadMode] = effectiveContent;
    if (filename) {
      body[`${payloadMode}_filename`] = filename;
    }
    if (argument) {
      body[`${payloadMode}_argument`] = argument;
    }
  } else if (!body.extra_args.length && !preview) {
    return { error: "Provide request content or explicit extra args before invoking." };
  }

  return {
    path: requestEndpointPath(context),
    body,
  };
}

function buildCurlPreview(context) {
  const submission = buildRequestSubmission(context, { preview: true });
  if (submission.error || !submission.path) {
    return "Select a batch/CLI app or a service-mode instance to build a request preview.";
  }
  return [
    `curl -s \"${window.location.origin}${submission.path}\" \\\n+  -H \"Content-Type: application/json\" \\\n+  --data @- <<'JSON'`,
    JSON.stringify(submission.body, null, 2),
    "JSON",
  ].join("\n");
}

function renderArtifactCards(items, { emptyLabel, type }) {
  if (!items.length) {
    return `<div class="empty-state">${escapeHtml(emptyLabel)}</div>`;
  }
  return `
    <div class="artifact-grid">
      ${items
        .map((item) => {
          const preview = item.json_preview
            ? `<pre class="command-block">${escapeHtml(JSON.stringify(item.json_preview, null, 2))}</pre>`
            : item.content_preview
              ? `<pre class="command-block">${escapeHtml(item.content_preview)}</pre>`
              : item.value_preview
                ? `<pre class="command-block">${escapeHtml(item.value_preview)}</pre>`
                : "";
          const rows = [];
          if (item.path) {
            rows.push(`<div class="mono-line">${escapeHtml(item.path)}</div>`);
          }
          if (item.size_bytes != null) {
            rows.push(`<div>${escapeHtml(`${item.size_bytes} bytes`)}</div>`);
          }
          if (item.exists === false) {
            rows.push(`<div>${escapeHtml("Artifact path does not exist.")}</div>`);
          }
          return `
            <article class="artifact-card">
              <div class="trace-record-head">
                <strong>${escapeHtml(item.argument || type)}</strong>
                ${renderBadge(type === "input" ? "input" : "artifact", "neutral")}
              </div>
              ${rows.join("")}
              ${preview}
            </article>
          `;
        })
        .join("")}
    </div>
  `;
}

function timestampToken(value = new Date().toISOString()) {
  return String(value).replace(/[:.]/g, "-").replace(/[^0-9TZ-]/g, "");
}

function safeSlug(value) {
  const normalized = String(value || "sage").toLowerCase().replace(/[^a-z0-9]+/g, "-");
  return normalized.replace(/^-+|-+$/g, "") || "sage";
}

function downloadJson(filename, payload) {
  const blob = new Blob([JSON.stringify(payload, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = filename;
  anchor.click();
  setTimeout(() => URL.revokeObjectURL(url), 0);
}

function formatMetricNumber(value, { digits = 1, suffix = "" } = {}) {
  if (value == null || Number.isNaN(Number(value))) {
    return "-";
  }
  return `${Number(value).toFixed(digits)}${suffix}`;
}

function summarizeMetrics(metrics) {
  const stages = metrics?.stages || [];
  if (!stages.length) {
    return {
      stageCount: 0,
      busiestStage: null,
      slowestStage: null,
      maxQueueStage: null,
      totalInvocations: 0,
      totalErrors: 0,
    };
  }
  return stages.reduce(
    (summary, stage) => {
      summary.stageCount += 1;
      summary.totalInvocations += stage.invocations || 0;
      summary.totalErrors += stage.errors || 0;
      if (!summary.busiestStage || (stage.throughput_items_per_sec || 0) > (summary.busiestStage.throughput_items_per_sec || 0)) {
        summary.busiestStage = stage;
      }
      if (!summary.slowestStage || (stage.p95_latency_ms || 0) > (summary.slowestStage.p95_latency_ms || 0)) {
        summary.slowestStage = stage;
      }
      if (!summary.maxQueueStage || (stage.max_queue_depth || 0) > (summary.maxQueueStage.max_queue_depth || 0)) {
        summary.maxQueueStage = stage;
      }
      return summary;
    },
    {
      stageCount: 0,
      busiestStage: null,
      slowestStage: null,
      maxQueueStage: null,
      totalInvocations: 0,
      totalErrors: 0,
    },
  );
}

function metricsRunIdentity(run) {
  if (!run) {
    return "";
  }
  return run.metricsPath || [
    run.appId || "unknown",
    run.instanceId || "no-instance",
    run.routeLabel || "unknown-route",
    run.submittedAt || "unknown-time",
    run.metrics?.wall_time_ms ?? "unknown-wall-time",
  ].join(":");
}

function buildRequestMetricsRun(entry) {
  if (!entry) {
    return null;
  }
  const invokeResult = entry.route === "openai" ? (entry.result.opc_result || {}) : entry.result;
  if (!invokeResult?.metrics?.stages?.length) {
    return null;
  }
  return {
    appId: entry.targetAppId || null,
    appName: entry.targetAppName || null,
    instanceId: entry.targetInstanceId || null,
    routeLabel: entry.routeLabel,
    submittedAt: entry.submittedAt,
    targetLabel: entry.targetLabel,
    metricsPath: invokeResult.metrics_path || "",
    metrics: invokeResult.metrics,
    durationMs: invokeResult.duration_ms ?? null,
    success: invokeResult.success ?? null,
  };
}

function buildInstanceMetricsRun(detail) {
  if (!detail) {
    return null;
  }
  const result = detail.last_result || {};
  const metrics = detail.metrics || result.metrics || null;
  if (!metrics?.stages?.length) {
    return null;
  }
  return {
    appId: detail.app_id,
    appName: detail.app_name,
    instanceId: detail.instance_id,
    routeLabel: detail.service_mode ? "Instance runtime" : "Batch runtime",
    submittedAt: detail.ended_at || detail.started_at || new Date().toISOString(),
    targetLabel: `${detail.app_name} · ${detail.instance_id}`,
    metricsPath: detail.metrics_path || result.metrics_path || "",
    metrics,
    durationMs: result.duration_ms ?? null,
    success: result.success ?? (detail.status === "completed"),
  };
}

function registerMetricsRun(run) {
  if (!run?.metrics?.stages?.length) {
    return;
  }
  const identity = metricsRunIdentity(run);
  if (!identity || state.metricsHistory.some((item) => metricsRunIdentity(item) === identity)) {
    return;
  }
  state.metricsHistory = [run, ...state.metricsHistory].slice(0, 18);
}

function findComparableMetricsRun(currentRun) {
  if (!currentRun) {
    return null;
  }
  const currentIdentity = metricsRunIdentity(currentRun);
  return state.metricsHistory.find((run) => {
    if (metricsRunIdentity(run) === currentIdentity) {
      return false;
    }
    if (currentRun.instanceId && run.instanceId === currentRun.instanceId) {
      return true;
    }
    return Boolean(currentRun.appId) && run.appId === currentRun.appId;
  }) || null;
}

function formatSignedDelta(value, { digits = 2, suffix = "" } = {}) {
  if (value == null || Number.isNaN(Number(value))) {
    return "-";
  }
  const numeric = Number(value);
  return `${numeric > 0 ? "+" : ""}${numeric.toFixed(digits)}${suffix}`;
}

function deltaTone(value, { goodDirection = "down" } = {}) {
  if (value == null || Number.isNaN(Number(value)) || Math.abs(Number(value)) < 0.0001) {
    return "delta-neutral";
  }
  const improved = goodDirection === "down" ? Number(value) < 0 : Number(value) > 0;
  return improved ? "delta-improved" : "delta-regressed";
}

function renderDeltaChip(value, { digits = 2, suffix = "", goodDirection = "down", emptyLabel = "no baseline" } = {}) {
  if (value == null || Number.isNaN(Number(value))) {
    return `<span class="delta-chip delta-neutral">${escapeHtml(emptyLabel)}</span>`;
  }
  return `<span class="delta-chip ${deltaTone(value, { goodDirection })}">${escapeHtml(formatSignedDelta(value, { digits, suffix }))}</span>`;
}

function stageDelta(currentValue, previousValue) {
  if (currentValue == null || previousValue == null) {
    return null;
  }
  return Number(currentValue) - Number(previousValue);
}

function renderMetricCell(currentValue, deltaValue, { digits = 2, suffix = "", goodDirection = "down" } = {}) {
  return `
    <div class="metric-cell">
      <strong class="metric-current">${escapeHtml(formatMetricNumber(currentValue, { digits, suffix }))}</strong>
      ${renderDeltaChip(deltaValue, { digits, suffix, goodDirection })}
    </div>
  `;
}

function renderMetricsDag(metrics, summary, previousRun = null) {
  const previousStages = new Map((previousRun?.metrics?.stages || []).map((stage) => [stage.stage_name, stage]));
  const edges = metrics.stages.flatMap((stage) => (stage.downstreams || []).map((downstream) => `${stage.stage_name} -> ${downstream}`));

  return `
    <div class="info-block">
      <p class="eyebrow">Operator DAG</p>
      <div class="metrics-dag-grid">
        ${metrics.stages.map((stage) => {
          const previousStage = previousStages.get(stage.stage_name) || null;
          const badges = [];
          if (summary.slowestStage?.stage_name === stage.stage_name) {
            badges.push(renderBadge("p95 bottleneck", "warning"));
          }
          if (summary.maxQueueStage?.stage_name === stage.stage_name && (stage.max_queue_depth || 0) > 0) {
            badges.push(renderBadge("queue hotspot", "partial"));
          }
          if (summary.busiestStage?.stage_name === stage.stage_name && stage.throughput_items_per_sec != null) {
            badges.push(renderBadge("throughput leader", "verified"));
          }
          if ((stage.errors || 0) > 0) {
            badges.push(renderBadge(`${stage.errors} errors`, "failed"));
          }
          return `
            <article class="dag-stage-card">
              <div class="dag-stage-head">
                <div>
                  <strong>${escapeHtml(stage.stage_name)}</strong>
                  <div class="trace-meta">${escapeHtml(stage.op_type || stage.transformation_type || "stage")}</div>
                </div>
                <div class="tag-row">${badges.join("") || renderBadge(`parallelism ${stage.parallelism ?? 1}`, "neutral")}</div>
              </div>
              <div class="dag-stage-stats">
                ${renderMetricCell(stage.p95_latency_ms, stageDelta(stage.p95_latency_ms, previousStage?.p95_latency_ms), { digits: 2, suffix: " ms", goodDirection: "down" })}
                ${renderMetricCell(stage.throughput_items_per_sec, stageDelta(stage.throughput_items_per_sec, previousStage?.throughput_items_per_sec), { digits: 2, suffix: " items/s", goodDirection: "up" })}
                ${renderMetricCell(stage.max_queue_depth, stageDelta(stage.max_queue_depth, previousStage?.max_queue_depth), { digits: 0, suffix: "", goodDirection: "down" })}
              </div>
              <div class="dag-stage-links">
                <div><span>Upstreams</span><strong>${escapeHtml((stage.upstreams || []).join(", ") || "source")}</strong></div>
                <div><span>Downstreams</span><strong>${escapeHtml((stage.downstreams || []).join(", ") || "sink")}</strong></div>
              </div>
            </article>
          `;
        }).join("")}
      </div>
      ${edges.length ? `<div class="dag-edge-list">${edges.map((edge) => `<span class="dag-edge-chip">${escapeHtml(edge)}</span>`).join("")}</div>` : ""}
    </div>
  `;
}

function renderMetricsComparison(currentRun, previousRun) {
  if (!currentRun?.metrics?.stages?.length) {
    return "";
  }
  if (!previousRun?.metrics?.stages?.length) {
    return `
      <div class="info-block">
        <p class="eyebrow">Run-to-Run Comparison</p>
        <div class="empty-state">Run the same app again to compare operator latency, throughput, and queue pressure against the prior execution.</div>
      </div>
    `;
  }

  const previousStages = new Map(previousRun.metrics.stages.map((stage) => [stage.stage_name, stage]));
  const currentStages = new Map(currentRun.metrics.stages.map((stage) => [stage.stage_name, stage]));
  const rows = currentRun.metrics.stages.map((stage) => {
    const previousStage = previousStages.get(stage.stage_name) || null;
    return {
      stage,
      previousStage,
      avgDelta: stageDelta(stage.avg_latency_ms, previousStage?.avg_latency_ms),
      p95Delta: stageDelta(stage.p95_latency_ms, previousStage?.p95_latency_ms),
      throughputDelta: stageDelta(stage.throughput_items_per_sec, previousStage?.throughput_items_per_sec),
      queueDelta: stageDelta(stage.max_queue_depth, previousStage?.max_queue_depth),
    };
  });
  const addedStages = currentRun.metrics.stages.filter((stage) => !previousStages.has(stage.stage_name)).map((stage) => stage.stage_name);
  const removedStages = previousRun.metrics.stages.filter((stage) => !currentStages.has(stage.stage_name)).map((stage) => stage.stage_name);
  const biggestLatencyRegression = rows.filter((row) => row.p95Delta != null && row.p95Delta > 0).sort((left, right) => right.p95Delta - left.p95Delta)[0] || null;
  const biggestThroughputDrop = rows.filter((row) => row.throughputDelta != null && row.throughputDelta < 0).sort((left, right) => left.throughputDelta - right.throughputDelta)[0] || null;
  const biggestQueueIncrease = rows.filter((row) => row.queueDelta != null && row.queueDelta > 0).sort((left, right) => right.queueDelta - left.queueDelta)[0] || null;
  const comparisonRows = [
    ["Baseline", `${previousRun.targetLabel} · ${formatDateTime(previousRun.submittedAt)}`],
    ["Current", `${currentRun.targetLabel} · ${formatDateTime(currentRun.submittedAt)}`],
    ["Wall time delta", formatSignedDelta(stageDelta(currentRun.metrics.wall_time_ms, previousRun.metrics.wall_time_ms), { digits: 1, suffix: " ms" })],
    ["Stage count delta", formatSignedDelta(stageDelta(currentRun.metrics.pipeline_stage_count, previousRun.metrics.pipeline_stage_count), { digits: 0 })],
    ["Added stages", addedStages.length ? addedStages.join(", ") : "none"],
    ["Removed stages", removedStages.length ? removedStages.join(", ") : "none"],
  ];
  const highlights = [
    ["Largest p95 shift", biggestLatencyRegression ? `${biggestLatencyRegression.stage.stage_name} · ${formatSignedDelta(biggestLatencyRegression.p95Delta, { digits: 2, suffix: " ms" })}` : "No regression"],
    ["Biggest throughput drop", biggestThroughputDrop ? `${biggestThroughputDrop.stage.stage_name} · ${formatSignedDelta(biggestThroughputDrop.throughputDelta, { digits: 2, suffix: " items/s" })}` : "No drop"],
    ["Largest queue increase", biggestQueueIncrease ? `${biggestQueueIncrease.stage.stage_name} · ${formatSignedDelta(biggestQueueIncrease.queueDelta, { digits: 0 })}` : "No increase"],
  ];

  return `
    <div class="info-block">
      <p class="eyebrow">Run-to-Run Comparison</p>
      <div class="split-grid two-up metrics-layout">
        <div class="key-value-list">${renderKeyValueRows(comparisonRows)}</div>
        <div class="metrics-overview-grid">
          ${highlights.map(([label, value]) => `
            <article class="metric-card metric-card-contrast">
              <div class="summary-label">${escapeHtml(label)}</div>
              <div class="metric-card-value">${escapeHtml(value)}</div>
            </article>
          `).join("")}
        </div>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Stage</th>
              <th>Avg latency</th>
              <th>P95 latency</th>
              <th>Throughput</th>
              <th>Queue peak</th>
            </tr>
          </thead>
          <tbody>
            ${rows.map((row) => `
              <tr>
                <td>
                  <div><strong>${escapeHtml(row.stage.stage_name)}</strong></div>
                  <div class="trace-meta">${escapeHtml(row.previousStage ? "matched to prior run" : "new in current run")}</div>
                </td>
                <td>${renderMetricCell(row.stage.avg_latency_ms, row.avgDelta, { digits: 2, suffix: " ms", goodDirection: "down" })}</td>
                <td>${renderMetricCell(row.stage.p95_latency_ms, row.p95Delta, { digits: 2, suffix: " ms", goodDirection: "down" })}</td>
                <td>${renderMetricCell(row.stage.throughput_items_per_sec, row.throughputDelta, { digits: 2, suffix: " items/s", goodDirection: "up" })}</td>
                <td>${renderMetricCell(row.stage.max_queue_depth, row.queueDelta, { digits: 0, suffix: "", goodDirection: "down" })}</td>
              </tr>
            `).join("")}
          </tbody>
        </table>
      </div>
    </div>
  `;
}

function renderMetricsBlock(metrics, { title = "Operator Metrics", metricsPath = "", emptyLabel = "No operator metrics were captured for this run yet.", currentRun = null } = {}) {
  if (!metrics?.stages?.length) {
    return `
      <div class="info-block">
        <p class="eyebrow">${escapeHtml(title)}</p>
        <div class="empty-state">${escapeHtml(emptyLabel)}</div>
      </div>
    `;
  }

  const summary = summarizeMetrics(metrics);
  const overviewRows = [
    ["Status", metrics.status || "-"],
    ["Schema", metrics.schema_version || "-"],
    ["Pipeline stages", metrics.pipeline_stage_count ?? summary.stageCount],
    ["Source stages", metrics.source_stage_count ?? "-"],
    ["Wall time", formatMetricNumber(metrics.wall_time_ms, { digits: 1, suffix: " ms" })],
    ["Invocations", summary.totalInvocations],
    ["Errors", summary.totalErrors],
    ["Metrics path", metricsPath || "-"],
  ];
  const highlightCards = [
    ["Fastest throughput", summary.busiestStage ? `${summary.busiestStage.stage_name} · ${formatMetricNumber(summary.busiestStage.throughput_items_per_sec, { digits: 2, suffix: " items/s" })}` : "-"],
    ["Highest p95", summary.slowestStage ? `${summary.slowestStage.stage_name} · ${formatMetricNumber(summary.slowestStage.p95_latency_ms, { digits: 2, suffix: " ms" })}` : "-"],
    ["Queue peak", summary.maxQueueStage ? `${summary.maxQueueStage.stage_name} · ${summary.maxQueueStage.max_queue_depth}` : "-"],
  ];
  const previousRun = currentRun ? findComparableMetricsRun(currentRun) : null;

  return `
    <div class="info-block">
      <p class="eyebrow">${escapeHtml(title)}</p>
      <div class="split-grid two-up metrics-layout">
        <div class="key-value-list">${renderKeyValueRows(overviewRows)}</div>
        <div class="metrics-overview-grid">
          ${highlightCards
            .map(
              ([label, value]) => `
                <article class="metric-card">
                  <div class="summary-label">${escapeHtml(label)}</div>
                  <div class="metric-card-value">${escapeHtml(value)}</div>
                </article>
              `,
            )
            .join("")}
        </div>
      </div>
      <div class="table-wrap">
        <table>
          <thead>
            <tr>
              <th>Stage</th>
              <th>Type</th>
              <th>Invocations</th>
              <th>Avg</th>
              <th>P95</th>
              <th>Throughput</th>
              <th>Errors</th>
              <th>Queue</th>
            </tr>
          </thead>
          <tbody>
            ${metrics.stages
              .map(
                (stage) => `
                  <tr>
                    <td>
                      <div><strong>${escapeHtml(stage.stage_name)}</strong></div>
                      <div class="trace-meta">parallelism ${escapeHtml(stage.parallelism ?? 1)}</div>
                    </td>
                    <td>${escapeHtml(stage.op_type || stage.transformation_type || "-")}</td>
                    <td>${escapeHtml(stage.invocations ?? 0)}</td>
                    <td>${escapeHtml(formatMetricNumber(stage.avg_latency_ms, { digits: 2, suffix: " ms" }))}</td>
                    <td>${escapeHtml(formatMetricNumber(stage.p95_latency_ms, { digits: 2, suffix: " ms" }))}</td>
                    <td>${escapeHtml(formatMetricNumber(stage.throughput_items_per_sec, { digits: 2, suffix: " items/s" }))}</td>
                    <td>${escapeHtml(stage.errors ?? 0)}</td>
                    <td>${escapeHtml(`${stage.last_queue_depth ?? 0} / ${stage.max_queue_depth ?? 0}`)}</td>
                  </tr>
                `,
              )
              .join("")}
          </tbody>
        </table>
      </div>
    </div>
    ${renderMetricsDag(metrics, summary, previousRun)}
    ${renderMetricsComparison(currentRun, previousRun)}
  `;
}

function renderInvokeOutcome(result, { assistantText = "", usage = null, includeMetrics = true, metricsRun = null } = {}) {
  const blocks = [];
  if (assistantText) {
    blocks.push(`
      <div class="info-block">
        <p class="eyebrow">Assistant Output</p>
        <pre class="command-block">${escapeHtml(assistantText)}</pre>
      </div>
    `);
  }
  if (usage) {
    blocks.push(`
      <div class="info-block">
        <p class="eyebrow">Usage</p>
        <div class="key-value-list">${renderKeyValueRows([
          ["Prompt tokens", usage.prompt_tokens ?? "-"],
          ["Completion tokens", usage.completion_tokens ?? "-"],
          ["Total tokens", usage.total_tokens ?? "-"],
        ])}</div>
      </div>
    `);
  }
  if (result.command_preview) {
    blocks.push(`
      <div class="info-block">
        <p class="eyebrow">Command Preview</p>
        <pre class="command-block">${escapeHtml(result.command_preview)}</pre>
      </div>
    `);
  }
  if (result.request?.url || result.http_status != null || result.response_json != null || result.response_text_preview) {
    const responseBody = result.response_json != null
      ? JSON.stringify(result.response_json, null, 2)
      : (result.response_text_preview || "");
    blocks.push(`
      <div class="info-block">
        <p class="eyebrow">HTTP Response</p>
        <div class="key-value-list">${renderKeyValueRows([
          ["Method", result.request?.method || "-"],
          ["URL", result.request?.url || "-"],
          ["Status", result.http_status ?? "-"],
        ])}</div>
        ${responseBody
          ? `<pre class="command-block">${escapeHtml(responseBody)}</pre>`
          : `<div class="empty-state">No HTTP response body was captured.</div>`}
      </div>
    `);
  }
  blocks.push(`
    <div class="info-block">
      <p class="eyebrow">Materialized Inputs</p>
      ${renderArtifactCards(result.materialized_inputs || [], { emptyLabel: "No inline inputs were materialized for this request.", type: "input" })}
    </div>
  `);
  blocks.push(`
    <div class="info-block">
      <p class="eyebrow">Output Artifacts</p>
      ${renderArtifactCards(result.output_artifacts || [], { emptyLabel: "No output artifacts were captured.", type: "artifact" })}
    </div>
  `);
  if (includeMetrics) {
    blocks.push(
      renderMetricsBlock(result.metrics, {
        title: "Operator Metrics",
        metricsPath: result.metrics_path,
        emptyLabel: "This run did not emit stage-level metrics.",
        currentRun: metricsRun,
      }),
    );
  }
  if (result.stdout) {
    blocks.push(`
      <div class="info-block">
        <p class="eyebrow">Stdout</p>
        <pre class="command-block">${escapeHtml(result.stdout)}</pre>
      </div>
    `);
  }
  if (result.stderr) {
    blocks.push(`
      <div class="info-block">
        <p class="eyebrow">Stderr</p>
        <pre class="command-block">${escapeHtml(result.stderr)}</pre>
      </div>
    `);
  }
  return blocks.join("");
}

function renderRequestResult() {
  if (!state.requestResult) {
    refs.requestResultSummary.innerHTML = `<div class="empty-state">Run a request from this panel to capture a result bundle.</div>`;
    refs.requestResultBody.innerHTML = `<div class="empty-state">Result artifacts, stdout/stderr, and OpenAI responses will appear here.</div>`;
    return;
  }

  const entry = state.requestResult;
  const isOpenAI = entry.route === "openai";
  const invokeResult = isOpenAI ? (entry.result.opc_result || {}) : entry.result;
  const assistantText = isOpenAI
    ? (entry.result.choices?.[0]?.message?.content || entry.result.choices?.[0]?.text || "")
    : "";
  const success = isOpenAI ? (invokeResult.success !== false) : Boolean(invokeResult.success);
  const summaryRows = [
    ["Route", entry.routeLabel],
    ["Request class", REQUEST_TEMPLATES[entry.templateKey]?.label || entry.templateKey],
    ["Target", entry.targetLabel],
    ["Submitted", formatDateTime(entry.submittedAt)],
    ["Status", success ? "passed" : "failed"],
    ["Duration", invokeResult.duration_ms == null ? "-" : `${invokeResult.duration_ms} ms`],
    ["Return code", invokeResult.return_code ?? "-"],
    ["Stage metrics", invokeResult.metrics?.stages?.length ?? 0],
    ["Metrics status", invokeResult.metrics?.status || "-"],
  ];
  if (isOpenAI) {
    summaryRows.push(["Model", entry.result.model || "-"]);
  }
  const currentRun = buildRequestMetricsRun(entry);
  refs.requestResultSummary.innerHTML = `
    <div class="key-value-list">${renderKeyValueRows(summaryRows)}</div>
    <div class="mini-actions">
      <button class="secondary-button" data-action="export-request-result">Export Result</button>
      ${invokeResult.metrics ? `<button class="secondary-button" data-action="export-request-metrics">Export Metrics</button>` : ""}
    </div>
  `;
  refs.requestResultBody.innerHTML = renderInvokeOutcome(invokeResult, {
    assistantText,
    usage: isOpenAI ? entry.result.usage : null,
    metricsRun: currentRun,
  });
}

function renderRequestLab() {
  const context = resolveRequestContext();
  if (context.route === "openai" && refs.requestPayloadMode.value !== "prompt") {
    refs.requestPayloadMode.value = "prompt";
  }
  refs.requestPayloadMode.disabled = context.route === "openai";
  refs.requestArgument.disabled = context.route === "openai";
  refs.requestFilename.disabled = context.route === "openai";

  if (!context.options.length) {
    refs.requestRoute.innerHTML = `<option value="">No invoke target available</option>`;
    refs.requestTargetFacts.innerHTML = `<div class="empty-state">Pick a batch/CLI app for one-shot invoke, or launch a service-mode instance to unlock reusable invoke and OpenAI routes.</div>`;
    refs.requestTemplateHint.innerHTML = `<div class="empty-state">The request lab becomes active once OPC has a non-HTTP invoke surface.</div>`;
    refs.requestCurlPreview.textContent = "No request route is available for the current selection.";
    renderRequestResult();
    return;
  }

  refs.requestRoute.innerHTML = context.options
    .map(
      (option) => `<option value="${escapeHtml(option.value)}" ${option.value === context.route ? "selected" : ""}>${escapeHtml(option.label)}</option>`,
    )
    .join("");
  refs.requestRoute.value = context.route;

  const app = context.app;
  const preferredArgument = preferredInlineArgument(app);
  const candidates = inlineInputCandidates(app);
  refs.requestArgument.placeholder = preferredArgument?.primary_name || (candidates.length ? candidates.map((item) => item.primary_name).join(", ") : "Optional target argument");
  refs.requestFilename.placeholder = inferRequestFilename(app, refs.requestPayloadMode.value || "prompt", context.route);

  const targetRows = [
    ["Route", requestRouteLabel(context.route)],
    ["Selected app", app?.name || "None"],
    ["Execution mode", app?.execution_mode || "-"],
    ["Suggested inline argument", preferredArgument?.primary_name || "Auto when unambiguous"],
    ["Suggested filename", inferRequestFilename(app, refs.requestPayloadMode.value || "prompt", context.route)],
  ];
  if (context.route !== "app" && context.serviceInstance) {
    targetRows.push(["Service instance", context.serviceInstance.instance_id]);
  }
  if (context.route === "openai" && context.serviceInstance?.openai_model) {
    targetRows.push(["OpenAI model", context.serviceInstance.openai_model]);
  }
  refs.requestTargetFacts.innerHTML = `
    <div class="key-value-list">${renderKeyValueRows(targetRows)}</div>
    ${candidates.length > 1 && !preferredArgument ? `<div class="empty-state">Multiple inline input candidates detected: ${escapeHtml(candidates.map((item) => item.primary_name).join(", "))}. Set Argument Override before running the request.</div>` : ""}
    ${app?.execution_mode === "http" ? `<div class="empty-state">${escapeHtml(app.demo_run_path
      ? `The selected app is HTTP-first, so one-shot invoke is unavailable. Launch it normally and use Run Demo Flow from Instance Detail to call ${app.demo_run_path}.`
      : "The selected app is HTTP-first, so one-shot invoke is unavailable. Launch it normally or switch to a service-mode instance for request replay.")}</div>` : ""}
  `;

  const template = REQUEST_TEMPLATES[refs.requestTemplate.value] || REQUEST_TEMPLATES.retrieval;
  const payloadMode = refs.requestPayloadMode.value || template.defaultPayloadMode;
  refs.requestTemplateHint.innerHTML = `
    <div>${escapeHtml(template.description)}</div>
    <div>${escapeHtml(context.route === "openai"
      ? "This route sends the content as an OpenAI chat message and still surfaces the underlying OPC invoke result."
      : payloadMode === "source"
        ? "This route materializes the content as inline source and maps it onto a CLI/path argument when possible."
        : "This route sends the content as prompt text so you can exercise a single-turn request path without creating input files manually.")}</div>
  `;
  refs.requestCurlPreview.textContent = buildCurlPreview(context);
  renderRequestResult();
}

function applyRequestTemplate({ announce = true } = {}) {
  const context = resolveRequestContext();
  const template = REQUEST_TEMPLATES[refs.requestTemplate.value] || REQUEST_TEMPLATES.retrieval;
  const payloadMode = context.route === "openai" ? "prompt" : (template.defaultPayloadMode || refs.requestPayloadMode.value || "prompt");
  const filename = inferRequestFilename(context.app, payloadMode, context.route);
  const preferredArgument = preferredInlineArgument(context.app);

  refs.requestPayloadMode.value = payloadMode;
  refs.requestArgument.value = preferredArgument?.primary_name || "";
  refs.requestFilename.value = filename;
  refs.requestContent.value = buildRequestTemplateContent(refs.requestTemplate.value, {
    route: context.route,
    payloadMode,
    filename,
    app: context.app,
  });
  refs.requestTimeout.value = context.route === "openai" ? 45 : 30;
  renderRequestLab();
  if (announce) {
    showToast(`${template.label} template loaded.`);
  }
}

async function sendRequest() {
  const context = resolveRequestContext();
  const submission = buildRequestSubmission(context);
  if (submission.error) {
    showToast(submission.error, { error: true });
    return;
  }

  try {
    if (context.route !== "app" && context.serviceInstance) {
      state.activeInstanceId = context.serviceInstance.instance_id;
      state.activeInstanceTab = "trace";
    }
    const result = await fetchJson(submission.path, {
      method: "POST",
      body: JSON.stringify(submission.body),
    });
    const invokeSucceeded = context.route === "openai" ? (result.opc_result?.success !== false) : Boolean(result.success);
    state.requestResult = {
      route: context.route,
      routeLabel: requestRouteLabel(context.route),
      templateKey: refs.requestTemplate.value,
      payloadMode: refs.requestPayloadMode.value,
      submittedAt: new Date().toISOString(),
      targetLabel: context.route === "app"
        ? `${context.app.name} · ${context.app.id}`
        : context.route === "openai"
          ? `${context.serviceInstance.app_name} · ${context.serviceInstance.openai_model}`
          : `${context.serviceInstance.app_name} · ${context.serviceInstance.instance_id}`,
      targetAppId: context.app?.id || context.serviceInstance?.app_id || null,
      targetAppName: context.app?.name || context.serviceInstance?.app_name || null,
      targetInstanceId: context.route === "app" ? null : context.serviceInstance?.instance_id || null,
      requestPath: submission.path,
      result,
    };
    registerMetricsRun(buildRequestMetricsRun(state.requestResult));
    if (context.route !== "app") {
      state.activeInstanceTab = result.opc_result?.metrics || result.metrics ? "metrics" : "trace";
    }
    showToast(
      context.route === "openai"
        ? `OpenAI-style request completed for ${context.serviceInstance.openai_model}`
        : `Request completed via ${requestRouteLabel(context.route).toLowerCase()}.`,
      { error: !invokeSucceeded },
    );
    await refreshData({ withValidation: false });
  } catch (error) {
    showToast(error.message, { error: true });
  }
}

function dynamicArgumentsForApp(app) {
  if (!app?.arguments) {
    return [];
  }
  return app.arguments.filter((argument) => !["--host", "--port", "--storage-path"].includes(argument.primary_name));
}

function collectDynamicArgs() {
  const entries = [];
  const fields = refs.dynamicArgs.querySelectorAll("[data-arg-primary]");
  fields.forEach((field) => {
    const primaryName = field.dataset.argPrimary;
    const positional = field.dataset.argPositional === "true";
    const action = field.dataset.argAction;
    const rawValue = field.type === "checkbox" ? String(field.checked) : field.value.trim();
    if (action === "store_true" || action === "store_false") {
      const shouldInclude = action === "store_true" ? field.checked : !field.checked;
      if (shouldInclude) {
        entries.push(primaryName);
      }
      return;
    }
    if (!rawValue) {
      return;
    }
    if (positional) {
      entries.push(rawValue);
      return;
    }
    entries.push(primaryName, rawValue);
  });
  return entries;
}

function collectLaunchPayload() {
  const dynamicArgs = collectDynamicArgs();
  return {
    host: refs.launchHost.value.trim() || "127.0.0.1",
    auto_port: refs.launchAutoPort.checked,
    port: refs.launchAutoPort.checked ? null : Number(refs.launchPort.value || 0) || null,
    storage_path: refs.launchStoragePath.value.trim() || null,
    env: parseEnvText(refs.launchEnv.value),
    extra_args: [...dynamicArgs, ...parseArgsText(refs.launchArgs.value)],
    service_mode: refs.launchServiceMode.checked,
    allow_duplicate: refs.launchAllowDuplicate.checked,
    startup_timeout_seconds: Number(refs.launchTimeout.value || 12),
  };
}

function pickInitialApp() {
  if (state.activeAppId && state.apps.some((app) => app.id === state.activeAppId)) {
    return;
  }
  const preferred = state.apps.find((app) => app.verified) || state.apps[0] || null;
  state.activeAppId = preferred ? preferred.id : null;
  syncLaunchFormToApp();
}

function syncLaunchFormToApp() {
  const app = currentApp();
  if (!app) {
    return;
  }
  refs.launchAppSelect.value = app.id;
  refs.launchHost.value = app.default_host || "127.0.0.1";
  refs.launchAutoPort.checked = true;
  refs.launchPort.disabled = true;
  refs.launchPort.value = app.port?.default || "";
  refs.launchStoragePath.value = app.filesystem?.outputs || "";
  refs.launchEnv.value = "";
  refs.launchArgs.value = "";
  refs.launchTimeout.value = 12;
  refs.launchServiceMode.checked = false;
  refs.launchAllowDuplicate.checked = false;
  renderDynamicArgs();
  scheduleValidation();
}

function describeIoProfile(app) {
  const notes = [];
  if (app.filesystem?.notes) {
    notes.push(app.filesystem.notes);
  }
  if (app.filesystem?.outputs) {
    notes.push(`State/output path: ${app.filesystem.outputs}`);
  }
  const pathArgs = (app.arguments || [])
    .filter((argument) => argument.kind === "path")
    .map((argument) => argument.primary_name);
  if (!notes.length && pathArgs.length) {
    notes.push(`Path arguments: ${pathArgs.join(", ")}`);
  }
  if (!notes.length && app.filesystem?.requires_workspace && app.filesystem?.default_workspace) {
    notes.push(`Uses workspace storage under ${app.filesystem.default_workspace}`);
  }
  return notes[0] || "No declared file or state contract.";
}

function describeExecutionProfile(app) {
  if (app.web_ui?.starts_own_ui) {
    return "HTTP app with its own UI";
  }
  if (app.port?.configurable || app.health_path) {
    return "HTTP app";
  }
  return app.execution_mode || "cli";
}

function appCapabilityTags(app) {
  const tags = [];
  if (app.port?.configurable) tags.push(renderBadge("Port configurable", "partial"));
  if (app.web_ui?.starts_own_ui) tags.push(renderBadge("Own Web UI", app.verified ? "verified" : "partial"));
  if (app.openai?.compatible) tags.push(renderBadge("OpenAI API", "verified"));
  if (app.dataset?.required) tags.push(renderBadge("Needs Dataset", "warning"));
  if (app.verified) tags.push(renderBadge("Verified", "verified"));
  if (!tags.length) tags.push(renderBadge("CLI", "neutral"));
  return tags.join("");
}

function renderSummaryCards() {
  const running = state.instances.filter((instance) => ["starting", "running", "degraded"].includes(instance.status)).length;
  const failed = state.instances.filter((instance) => instance.status === "failed").length;
  const verifiedApps = state.apps.filter((app) => app.verified).length;
  const openaiApps = state.apps.filter((app) => app.openai?.compatible).length;
  const webUiApps = state.apps.filter((app) => app.web_ui?.starts_own_ui).length;
  const availablePorts = state.ports ? state.ports.available_count : 0;
  const experimentEvents = state.experiments?.summary?.total_events || 0;
  const cards = [
    ["Running instances", running, "Active live processes under control plane"],
    ["Failed instances", failed, "Exited with non-zero status"],
    ["Apps discovered", state.apps.length, "Scanned from sage-examples/examples"],
    ["Experiment events", experimentEvents, "Automatic records for launch, invoke, and control actions"],
    ["Verified apps", verifiedApps, "Manifests with runtime validation"],
    ["Web UI apps", webUiApps, "Apps exposing their own browser UI"],
    ["Available ports", availablePorts, "Free ports in managed pool"],
    ["OpenAI-compatible apps", openaiApps, "Currently declared by manifests"],
  ];
  refs.summaryCards.innerHTML = cards
    .map(
      ([label, value, caption]) => `
        <article class="summary-card">
          <div class="summary-label">${escapeHtml(label)}</div>
          <div class="summary-value">${escapeHtml(value)}</div>
          <div class="summary-caption">${escapeHtml(caption)}</div>
        </article>
      `,
    )
    .join("");
}

function renderOverviewInstances() {
  if (!state.instances.length) {
    refs.overviewInstances.innerHTML = `<div class="empty-state">No app instances are running. Launch an app from the catalog.</div>`;
    return;
  }
  refs.overviewInstances.innerHTML = `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Instance</th>
            <th>App</th>
            <th>Status</th>
            <th>Endpoint</th>
            <th>Uptime</th>
          </tr>
        </thead>
        <tbody>
          ${state.instances
            .slice(0, 6)
            .map(
              (instance) => `
                <tr>
                  <td><button class="instance-link" data-action="select-instance" data-instance-id="${escapeHtml(instance.instance_id)}">${escapeHtml(instance.instance_id)}</button></td>
                  <td>${escapeHtml(instance.app_name)}</td>
                  <td>${renderBadge(instance.status, instance.status)}</td>
                  <td class="mono-line">${escapeHtml(instance.endpoint || "-")}</td>
                  <td>${escapeHtml(formatDuration(instance.uptime_seconds))}</td>
                </tr>
              `,
            )
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

function collectRecentEvents() {
  return state.instances
    .flatMap((instance) => (instance.events || []).map((event) => ({ ...event, instance_id: instance.instance_id, app_name: instance.app_name })))
    .sort((left, right) => new Date(right.timestamp) - new Date(left.timestamp))
    .slice(0, 8);
}

function renderRecentActivity() {
  const events = collectRecentEvents();
  if (!events.length) {
    refs.recentActivity.innerHTML = `<div class="empty-state">No lifecycle events yet. Launch an app to populate the activity stream.</div>`;
    return;
  }
  refs.recentActivity.innerHTML = `
    <div class="activity-list">
      ${events
        .map(
          (event) => `
            <div class="activity-item">
              <div class="activity-title">
                <strong>${escapeHtml(event.message)}</strong>
                ${renderBadge(event.kind.replaceAll("_", " "), event.kind.includes("timeout") ? "warning" : "neutral")}
              </div>
              <div>${escapeHtml(event.app_name)} · ${escapeHtml(event.instance_id)}</div>
              <div>${escapeHtml(formatDateTime(event.timestamp))}</div>
            </div>
          `,
        )
        .join("")}
    </div>
  `;
}

function renderCatalog() {
  const query = state.search.trim().toLowerCase();
  const filteredApps = state.apps.filter((app) => {
    if (!query) return true;
    return `${app.name} ${app.id} ${app.purpose}`.toLowerCase().includes(query);
  });

  refs.catalogCount.textContent = `${filteredApps.length} visible`;
  if (!filteredApps.length) {
    refs.catalogGrid.innerHTML = `<div class="empty-state">No apps match the current filter.</div>`;
    return;
  }

  refs.catalogGrid.innerHTML = filteredApps
    .map(
      (app) => {
        const ioProfile = describeIoProfile(app);
        const executionProfile = describeExecutionProfile(app);
        return `
        <article class="catalog-card">
          <div>
            <div class="tag-row">${renderBadge(app.verification_status, app.verification_status)}</div>
            <h4>${escapeHtml(app.name)}</h4>
            <p>${escapeHtml(app.purpose)}</p>
          </div>

          <div class="tag-row">${appCapabilityTags(app)}</div>

          <div class="key-value-list">
            <div class="kv-row"><span>Default port</span><strong>${escapeHtml(app.port?.default || "-")}</strong></div>
            <div class="kv-row"><span>Execution</span><strong>${escapeHtml(executionProfile)}</strong></div>
            <div class="kv-row"><span>Input / Output</span><strong>${escapeHtml(ioProfile)}</strong></div>
            <div class="kv-row"><span>Verification</span><strong>${escapeHtml(app.status_notes || app.verification_status)}</strong></div>
          </div>

          <div class="action-row">
            <button class="primary-button" data-action="prepare-launch" data-app-id="${escapeHtml(app.id)}">Launch</button>
            <button class="secondary-button" data-action="show-app" data-app-id="${escapeHtml(app.id)}">Details</button>
          </div>
        </article>
      `;
      },
    )
    .join("");
}

function renderLaunchFacts() {
  const app = currentApp();
  if (!app) {
    refs.launchAppFacts.innerHTML = `<div class="empty-state">Select an app from the catalog first.</div>`;
    return;
  }
  const examples = app.examples?.length
    ? `<div class="kv-row"><span>Example</span><strong>${escapeHtml(app.examples[0])}</strong></div>`
    : "";
  const envVars = app.environment_variables?.length
    ? `<div class="kv-row"><span>Environment</span><strong>${escapeHtml(app.environment_variables.join(", "))}</strong></div>`
    : "";
  const requiredArgs = app.arguments?.filter((argument) => argument.required).map((argument) => argument.primary_name) || [];
  refs.launchAppFacts.innerHTML = `
    <div class="tag-row">${appCapabilityTags(app)}</div>
    <div class="kv-row"><span>Description</span><strong>${escapeHtml(app.purpose)}</strong></div>
    <div class="kv-row"><span>Execution mode</span><strong>${escapeHtml(app.execution_mode || "cli")}</strong></div>
    <div class="kv-row"><span>Usage</span><strong>${escapeHtml(app.usage || `python ${app.script_path}`)}</strong></div>
    <div class="kv-row"><span>Required args</span><strong>${escapeHtml(requiredArgs.length ? requiredArgs.join(", ") : "None")}</strong></div>
    <div class="kv-row"><span>Input / Output</span><strong>${escapeHtml(describeIoProfile(app))}</strong></div>
    <div class="kv-row"><span>Dataset</span><strong>${escapeHtml(app.dataset?.notes || (app.dataset?.required ? "Required" : "Not required"))}</strong></div>
    <div class="kv-row"><span>Own UI</span><strong>${escapeHtml(app.web_ui?.starts_own_ui ? "Available" : "None declared")}</strong></div>
    ${envVars}
    ${examples}
  `;
}

function renderDynamicArgs() {
  const app = currentApp();
  if (!app) {
    refs.dynamicArgs.innerHTML = `<div class="empty-state">Select an app to inspect its detected arguments.</div>`;
    refs.launchEnvHints.textContent = "";
    return;
  }

  const argumentsToRender = dynamicArgumentsForApp(app);
  refs.launchEnvHints.textContent = app.environment_variables?.length
    ? `Documented environment variables: ${app.environment_variables.join(", ")}`
    : "No documented environment variables detected for this script.";

  if (!argumentsToRender.length) {
    refs.dynamicArgs.innerHTML = `<div class="empty-state">No additional script-specific arguments were detected. Use Custom Args only if you need to override behavior manually.</div>`;
    return;
  }

  refs.dynamicArgs.innerHTML = argumentsToRender
    .map((argument, index) => {
      const fieldId = `dynamic-arg-${index}`;
      const defaultValue = argument.opc_default_value || (argument.default && argument.default !== "None" ? argument.default : "");
      const meta = [
        argument.required ? renderBadge("required", "warning") : renderBadge("optional", "neutral"),
        argument.kind ? renderBadge(argument.kind, "neutral") : "",
        argument.opc_default_value ? renderBadge("autofilled", "verified") : "",
      ].join("");
      const defaultHint = argument.opc_default_value
        ? `<div>${escapeHtml(`Default path: ${argument.opc_default_value}`)}</div><div>${escapeHtml(`Source: ${argument.opc_default_origin || "opc"}`)}</div>`
        : "";

      let control = "";
      if (argument.action === "store_true" || argument.action === "store_false") {
        const checked = argument.action === "store_false" ? "checked" : "";
        control = `
          <label class="checkbox-field">
            <input id="${fieldId}" data-arg-primary="${escapeHtml(argument.primary_name)}" data-arg-action="${escapeHtml(argument.action)}" data-arg-positional="false" type="checkbox" ${checked} />
            <span>${escapeHtml(argument.help || argument.primary_name)}</span>
          </label>
        `;
      } else if (argument.choices?.length) {
        control = `
          <select id="${fieldId}" data-arg-primary="${escapeHtml(argument.primary_name)}" data-arg-action="${escapeHtml(argument.action || "")}" data-arg-positional="${escapeHtml(String(argument.positional))}">
            <option value="">Use default</option>
            ${argument.choices
              .map((choice) => `<option value="${escapeHtml(choice)}" ${choice === defaultValue ? "selected" : ""}>${escapeHtml(choice)}</option>`)
              .join("")}
          </select>
        `;
      } else {
        const inputType = argument.kind === "int" || argument.kind === "float" ? "number" : "text";
        control = `
          <input
            id="${fieldId}"
            type="${inputType}"
            data-arg-primary="${escapeHtml(argument.primary_name)}"
            data-arg-action="${escapeHtml(argument.action || "")}" 
            data-arg-positional="${escapeHtml(String(argument.positional))}"
            placeholder="${escapeHtml(argument.value_name || argument.primary_name)}"
            value="${escapeHtml(defaultValue)}"
          />
        `;
      }

      return `
        <div class="dynamic-arg-card">
          <div class="dynamic-arg-header">
            <strong>${escapeHtml(argument.primary_name)}</strong>
            <div class="dynamic-arg-meta">${meta}</div>
          </div>
          <div>${escapeHtml(argument.help || "No help text found in script.")}</div>
          ${defaultHint}
          ${control}
        </div>
      `;
    })
    .join("");
}

function renderValidationPreview() {
  if (!state.validation) {
    refs.endpointPreview.textContent = "Waiting for validation...";
    refs.commandPreview.textContent = "Waiting for validation...";
    refs.environmentPreview.innerHTML = `<div class="empty-state">No environment preview yet.</div>`;
    refs.preflightChecks.innerHTML = `<div class="empty-state">No checks yet.</div>`;
    return;
  }

  const endpoint = state.validation.invoke_path_preview
    ? `Service mode will expose ${state.validation.invoke_path_preview} after launch.`
    : (state.validation.endpoint_preview || "This app does not declare a direct HTTP endpoint.");
  const appUiPreview = state.validation.app_ui_preview
    ? `<div class="kv-row"><span>App UI</span><strong>${escapeHtml(state.validation.app_ui_preview)}</strong></div>`
    : `<div class="kv-row"><span>App UI</span><strong>Not declared</strong></div>`;
  const invokePreview = state.validation.invoke_path_preview
    ? `<div class="kv-row"><span>Invoke Path</span><strong>${escapeHtml(state.validation.invoke_path_preview)}</strong></div>`
    : "";

  refs.endpointPreview.innerHTML = `
    <span>${escapeHtml(endpoint)}</span>
    <div class="mini-actions">
      ${state.validation.endpoint_preview ? `<button class="ghost-button" data-action="copy-endpoint" data-endpoint="${escapeHtml(state.validation.endpoint_preview)}">Copy</button>` : ""}
      ${state.validation.app_ui_preview ? `<button class="ghost-button" data-action="open-url" data-url="${escapeHtml(state.validation.app_ui_preview)}">Open App UI</button>` : ""}
    </div>
  `;
  refs.commandPreview.textContent = state.validation.command_preview;
  const envRows = Object.entries(state.validation.environment_preview || {});
  refs.environmentPreview.innerHTML = envRows.length
    ? `${envRows
        .map(
          ([key, value]) => `<div class="kv-row"><span>${escapeHtml(key)}</span><strong>${escapeHtml(maskEnvValue(key, value))}</strong></div>`,
        )
        .join("")}${appUiPreview}${invokePreview}`
    : `<div class="empty-state">No extra environment variables for this launch.</div>${appUiPreview}${invokePreview}`;
  refs.preflightChecks.innerHTML = (state.validation.checks || [])
    .map(
      (check) => `
        <div class="check-item">
          <div class="check-title">
            <strong>${escapeHtml(check.name.replaceAll("_", " "))}</strong>
            ${renderBadge(check.passed ? "passed" : "failed", check.passed ? "passed" : "failed")}
          </div>
          <div>${escapeHtml(check.detail)}</div>
        </div>
      `,
    )
    .join("");
}

function renderArgumentsTable(app) {
  if (!app?.arguments?.length) {
    return `<div class="empty-state">No argument catalog detected for this pipeline.</div>`;
  }
  return `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Argument</th>
            <th>Kind</th>
            <th>Required</th>
            <th>Default</th>
            <th>Help</th>
          </tr>
        </thead>
        <tbody>
          ${app.arguments
            .map(
              (argument) => `
                <tr>
                  <td class="mono-line">${escapeHtml(argument.primary_name)}</td>
                  <td>${escapeHtml(argument.kind || "string")}</td>
                  <td>${escapeHtml(argument.required ? "yes" : "no")}</td>
                  <td class="mono-line">${escapeHtml(argument.opc_default_value || argument.default || "-")}</td>
                  <td>${escapeHtml(argument.help || "-")}</td>
                </tr>
              `,
            )
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderInstanceSpec(detail) {
  const app = state.apps.find((item) => item.id === detail.app_id);
  if (!app) {
    return `<div class="detail-section"><div class="empty-state">App definition metadata is unavailable for this instance.</div></div>`;
  }
  const preferredArgument = preferredInlineArgument(app);
  const candidates = inlineInputCandidates(app);
  const contractRows = [
    ["Purpose", app.purpose],
    ["Script", app.script_path],
    ["Working dir", app.working_dir],
    ["Execution mode", app.execution_mode || "cli"],
    ["Verification", app.verification_status],
    ["Usage", app.usage || `python ${app.script_path}`],
  ];
  const invocationRows = [
    ["Endpoint", detail.endpoint || "-"],
    ["Invoke path", detail.invoke_path || "-"],
    ["OpenAI model", detail.openai_model || "-"],
    ["OpenAI chat path", detail.openai_chat_path || "-"],
    ["App UI", detail.app_ui_url || "-"],
  ];
  const inputRows = [
    ["Suggested inline argument", preferredArgument?.primary_name || "-"],
    ["Inline candidates", candidates.length ? candidates.map((item) => item.primary_name).join(", ") : "None"],
    ["Suggested filename", inferRequestFilename(app, "source", "app")],
    ["Default input path", preferredArgument?.opc_default_value || "-"],
    ["Filesystem", describeIoProfile(app)],
    ["Dataset", app.dataset?.notes || (app.dataset?.required ? "Required" : "Not required")],
  ];
  const envHtml = app.environment_variables?.length
    ? app.environment_variables.map((name) => renderBadge(name, "neutral")).join("")
    : `<div class="empty-state">No documented environment variables.</div>`;
  const exampleHtml = app.examples?.length
    ? `<div class="detail-trace-list">${app.examples.map((example) => `<div class="artifact-card mono-line">${escapeHtml(example)}</div>`).join("")}</div>`
    : `<div class="empty-state">No CLI examples detected for this app.</div>`;

  return `
    <div class="detail-section">
      <div class="split-grid two-up">
        <div class="info-block">
          <p class="eyebrow">Pipeline Contract</p>
          <div class="key-value-list">${renderKeyValueRows(contractRows)}</div>
        </div>
        <div class="info-block">
          <p class="eyebrow">Invocation Surfaces</p>
          <div class="key-value-list">${renderKeyValueRows(invocationRows)}</div>
        </div>
      </div>

      <div class="split-grid two-up">
        <div class="info-block">
          <p class="eyebrow">Input Contract</p>
          <div class="key-value-list">${renderKeyValueRows(inputRows)}</div>
        </div>
        <div class="info-block">
          <p class="eyebrow">Environment + Examples</p>
          <div class="tag-row">${envHtml}</div>
          ${exampleHtml}
        </div>
      </div>

      <div class="info-block">
        <p class="eyebrow">Detected Arguments</p>
        ${renderArgumentsTable(app)}
      </div>
    </div>
  `;
}

function renderInstanceTrace(detail) {
  const experimentRecords = (state.experiments?.records || []).filter(
    (record) => record.instance_id === detail.instance_id || (!record.instance_id && record.app_id === detail.app_id),
  );
  const matchingRequest = state.requestResult
    && ((state.requestResult.targetInstanceId && state.requestResult.targetInstanceId === detail.instance_id)
      || (!state.requestResult.targetInstanceId && state.requestResult.targetAppId === detail.app_id))
    ? state.requestResult
    : null;
  const lifecycleHtml = (detail.events || []).length
    ? `<div class="detail-trace-list">${detail.events
        .slice()
        .reverse()
        .map((event) => `
          <article class="trace-record">
            <div class="trace-record-head">
              <strong>${escapeHtml(event.message)}</strong>
              ${renderBadge(event.kind.replaceAll("_", " "), "neutral")}
            </div>
            <div class="trace-meta">${escapeHtml(formatDateTime(event.timestamp))}</div>
            ${event.details && Object.keys(event.details).length ? `<pre class="command-block">${escapeHtml(JSON.stringify(event.details, null, 2))}</pre>` : ""}
          </article>
        `)
        .join("")}</div>`
    : `<div class="empty-state">No lifecycle events recorded for this instance yet.</div>`;
  const experimentHtml = experimentRecords.length
    ? `<div class="detail-trace-list">${experimentRecords
        .map(
          (record) => `
            <article class="trace-record">
              <div class="trace-record-head">
                <strong>${escapeHtml(record.summary)}</strong>
                ${renderBadge(record.status, record.status)}
              </div>
              <div class="trace-meta">${escapeHtml(`${record.kind} · ${formatDateTime(record.timestamp)}`)}</div>
              <div class="trace-meta">${escapeHtml([record.app_name, record.instance_id].filter(Boolean).join(" · "))}</div>
              ${record.details && Object.keys(record.details).length ? `<pre class="command-block">${escapeHtml(JSON.stringify(record.details, null, 2))}</pre>` : ""}
            </article>
          `,
        )
        .join("")}</div>`
    : `<div class="empty-state">No experiment records captured for this instance yet.</div>`;
  const requestRows = matchingRequest
    ? renderKeyValueRows([
        ["Last request route", matchingRequest.routeLabel],
        ["Last request class", REQUEST_TEMPLATES[matchingRequest.templateKey]?.label || matchingRequest.templateKey],
        ["Last request at", formatDateTime(matchingRequest.submittedAt)],
      ])
    : "";

  return `
    <div class="detail-section">
      <div class="info-block">
        <p class="eyebrow">Trace Summary</p>
        <div class="key-value-list">${renderKeyValueRows([
          ["Lifecycle events", detail.events?.length || 0],
          ["Experiment records", experimentRecords.length],
          ["Current status", detail.status],
          ["Started", formatDateTime(detail.started_at)],
          ["Metrics stages", detail.metrics?.stages?.length ?? detail.last_result?.metrics?.stages?.length ?? 0],
        ])}</div>
        ${requestRows ? `<div class="key-value-list">${requestRows}</div>` : ""}
      </div>

      <div class="split-grid two-up">
        <div class="info-block">
          <p class="eyebrow">Lifecycle Timeline</p>
          ${lifecycleHtml}
        </div>
        <div class="info-block">
          <p class="eyebrow">Experiment Trace</p>
          ${experimentHtml}
        </div>
      </div>
    </div>
  `;
}

function renderInstanceMetrics(detail) {
  const app = state.apps.find((item) => item.id === detail.app_id);
  const metrics = detail.metrics || detail.last_result?.metrics || null;
  const result = detail.last_result || null;
  const currentRun = buildInstanceMetricsRun(detail);
  const demoHint = app?.demo_run_path && detail.endpoint && ["running", "degraded"].includes(detail.status)
    ? `No stage metrics have been exported for this instance yet. Use Run Demo Flow to call ${app.demo_run_path}, or hit the app endpoint directly.`
    : "No stage metrics have been exported for this instance yet. Run a request or wait for the batch process to finish.";
  const summaryRows = [
    ["Metrics captured", metrics?.stages?.length ? "yes" : "no"],
    ["Metrics status", metrics?.status || "-"],
    ["Stage count", metrics?.stages?.length ?? 0],
    ["Metrics path", detail.metrics_path || result?.metrics_path || "-"],
    ["Last result", result ? (result.success ? "passed" : "failed") : "-"] ,
    ["Last exit/status", result?.return_code ?? result?.http_status ?? "-"],
  ];

  return `
    <div class="detail-section">
      <div class="info-block">
        <p class="eyebrow">Metrics Summary</p>
        <div class="key-value-list">${renderKeyValueRows(summaryRows)}</div>
      </div>
      ${renderMetricsBlock(metrics, {
        title: "Operator Telemetry",
        metricsPath: detail.metrics_path || result?.metrics_path || "",
        emptyLabel: demoHint,
        currentRun,
      })}
      ${result ? renderInvokeOutcome(result, { includeMetrics: false }) : ""}
    </div>
  `;
}

function renderInstancesTable() {
  if (!state.instances.length) {
    refs.instancesTable.innerHTML = `<div class="empty-state">No app instances are running. Launch an app from the catalog.</div>`;
    return;
  }
  refs.instancesTable.innerHTML = `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Instance</th>
            <th>App</th>
            <th>Status</th>
            <th>Endpoint</th>
            <th>Port</th>
            <th>App UI</th>
            <th>Uptime</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody>
          ${state.instances
            .map(
              (instance) => `
                <tr>
                  <td><button class="instance-link" data-action="select-instance" data-instance-id="${escapeHtml(instance.instance_id)}">${escapeHtml(instance.instance_id)}</button></td>
                  <td>${escapeHtml(instance.app_name)}</td>
                  <td>${renderBadge(instance.status, instance.status)}</td>
                  <td class="mono-line">${escapeHtml(instance.endpoint || "-")}</td>
                  <td class="mono-line">${escapeHtml(instance.port || "-")}</td>
                  <td>${instance.app_ui_url ? `<button class="text-button" data-action="open-url" data-url="${escapeHtml(instance.app_ui_url)}">Open App UI</button>` : "-"}</td>
                  <td>${escapeHtml(formatDuration(instance.uptime_seconds))}</td>
                  <td>
                    <div class="mini-actions">
                      <button class="ghost-button" data-action="copy-endpoint" data-endpoint="${escapeHtml(instance.endpoint || "")}">Copy endpoint</button>
                      <button class="ghost-button" data-action="restart-instance" data-instance-id="${escapeHtml(instance.instance_id)}">Restart</button>
                      <button class="danger-button" data-action="stop-instance" data-instance-id="${escapeHtml(instance.instance_id)}">Stop</button>
                    </div>
                  </td>
                </tr>
              `,
            )
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderInstanceDetail() {
  const detail = state.activeInstanceDetail;
  if (!detail) {
    refs.instanceDetail.innerHTML = `<div class="empty-state">Choose an instance from the table to inspect its command, logs, compatibility report, and lifecycle events.</div>`;
    return;
  }
  const app = state.apps.find((item) => item.id === detail.app_id);
  const canRunDemo = Boolean(app?.demo_run_path && detail.endpoint && ["running", "degraded"].includes(detail.status));

  const tabs = [
    ["overview", "Overview"],
    ["spec", "Spec"],
    ["metrics", "Metrics"],
    ["trace", "Trace"],
    ["compatibility", "Compatibility"],
    ["logs", "Logs"],
    ["config", "Configuration"],
  ];

  refs.instanceDetail.innerHTML = `
    <div class="detail-header">
      <div>
        <p class="eyebrow">Instance Detail</p>
        <h4>${escapeHtml(detail.app_name)} · ${escapeHtml(detail.instance_id)}</h4>
      </div>
      ${renderBadge(detail.status, detail.status)}
    </div>

    <div class="detail-toolbar">
      ${detail.endpoint ? `<button class="secondary-button" data-action="copy-endpoint" data-endpoint="${escapeHtml(detail.endpoint)}">Copy Endpoint</button>` : ""}
      ${detail.invoke_path ? `<button class="secondary-button" data-action="copy-text" data-text="${escapeHtml(detail.invoke_path)}">Copy Invoke Path</button>` : ""}
      ${detail.openai_model ? `<button class="secondary-button" data-action="copy-text" data-text="${escapeHtml(detail.openai_model)}">Copy OpenAI Model</button>` : ""}
      ${detail.app_ui_url ? `<button class="secondary-button" data-action="open-url" data-url="${escapeHtml(detail.app_ui_url)}">Open App UI</button>` : ""}
      ${canRunDemo ? `<button class="secondary-button" data-action="run-instance-demo" data-instance-id="${escapeHtml(detail.instance_id)}">Run Demo Flow</button>` : ""}
      ${detail.last_result ? `<button class="secondary-button" data-action="export-instance-result" data-instance-id="${escapeHtml(detail.instance_id)}">Export Result</button>` : ""}
      ${(detail.metrics || detail.last_result?.metrics) ? `<button class="secondary-button" data-action="export-instance-metrics" data-instance-id="${escapeHtml(detail.instance_id)}">Export Metrics</button>` : ""}
      <button class="secondary-button" data-action="clone-launch" data-instance-id="${escapeHtml(detail.instance_id)}">Clone Launch</button>
      <button class="secondary-button" data-action="run-compatibility" data-instance-id="${escapeHtml(detail.instance_id)}">Run Compatibility</button>
      <button class="ghost-button" data-action="restart-instance" data-instance-id="${escapeHtml(detail.instance_id)}">Restart</button>
      <button class="danger-button" data-action="stop-instance" data-instance-id="${escapeHtml(detail.instance_id)}">Stop</button>
    </div>

    <div class="detail-tabs">
      ${tabs
        .map(
          ([key, label]) => `
            <button class="${state.activeInstanceTab === key ? "is-active" : ""}" data-action="switch-instance-tab" data-tab="${escapeHtml(key)}">${escapeHtml(label)}</button>
          `,
        )
        .join("")}
    </div>

    ${renderActiveInstanceTab(detail)}
  `;
}

function renderActiveInstanceTab(detail) {
  if (state.activeInstanceTab === "spec") {
    return renderInstanceSpec(detail);
  }

  if (state.activeInstanceTab === "metrics") {
    return renderInstanceMetrics(detail);
  }

  if (state.activeInstanceTab === "trace") {
    return renderInstanceTrace(detail);
  }

  if (state.activeInstanceTab === "compatibility") {
    const tests = detail.compatibility || [];
    if (!tests.length) {
      return `<div class="detail-section"><div class="empty-state">No compatibility result yet. Run Compatibility to execute probes against this instance.</div></div>`;
    }
    return `
      <div class="detail-section">
        <div class="table-wrap">
          <table>
            <thead>
              <tr>
                <th>Test</th>
                <th>Status</th>
                <th>Latency</th>
                <th>Last Run</th>
                <th>Details</th>
              </tr>
            </thead>
            <tbody>
              ${tests
                .map(
                  (test) => `
                    <tr>
                      <td>${escapeHtml(test.name)}</td>
                      <td>${renderBadge(test.status, test.status)}</td>
                      <td>${escapeHtml(test.latency_ms == null ? "-" : `${test.latency_ms} ms`)}</td>
                      <td>${escapeHtml(formatDateTime(test.last_run))}</td>
                      <td>${escapeHtml(test.details)}</td>
                    </tr>
                  `,
                )
                .join("")}
            </tbody>
          </table>
        </div>
      </div>
    `;
  }

  if (state.activeInstanceTab === "logs") {
    const logs = detail.logs || [];
    return `
      <div class="detail-section">
        <div class="log-toolbar">
          <label>
            <span>Stream</span>
            <select id="log-stream-filter">
              <option value="merged">merged</option>
              <option value="stdout">stdout</option>
              <option value="stderr">stderr</option>
            </select>
          </label>
        </div>
        <pre class="log-block">${escapeHtml(
          logs.map((line) => `[${line.timestamp}] ${line.stream.toUpperCase()} ${line.message}`).join("\n") || "No log lines captured yet.",
        )}</pre>
      </div>
    `;
  }

  if (state.activeInstanceTab === "config") {
    const envRows = Object.entries(detail.env || {}).filter(([key]) => key === "PYTHONPATH" || /(key|secret|token|password)/i.test(key) || key.startsWith("SAGE_"));
    return `
      <div class="detail-section">
        <div class="info-block">
          <p class="eyebrow">Effective Launch Config</p>
          <div class="kv-row"><span>Working dir</span><strong>${escapeHtml(detail.working_dir)}</strong></div>
          <div class="kv-row"><span>PID</span><strong>${escapeHtml(detail.pid || "-")}</strong></div>
          <div class="kv-row"><span>Command</span><strong>${escapeHtml(detail.command.join(" "))}</strong></div>
        </div>
        <div class="info-block">
          <p class="eyebrow">Environment</p>
          ${envRows.length
            ? envRows
                .map(([key, value]) => `<div class="kv-row"><span>${escapeHtml(key)}</span><strong>${escapeHtml(maskEnvValue(key, value))}</strong></div>`)
                .join("")
            : `<div class="empty-state">No extra environment variables recorded for this launch.</div>`}
        </div>
      </div>
    `;
  }

  return `
    <div class="detail-section">
      <div class="info-block">
        <p class="eyebrow">Runtime</p>
        <div class="kv-row"><span>Status</span><strong>${escapeHtml(detail.status)}</strong></div>
        <div class="kv-row"><span>Endpoint</span><strong>${escapeHtml(detail.endpoint || "-")}</strong></div>
        <div class="kv-row"><span>Invoke path</span><strong>${escapeHtml(detail.invoke_path || "-")}</strong></div>
        <div class="kv-row"><span>OpenAI model</span><strong>${escapeHtml(detail.openai_model || "-")}</strong></div>
        <div class="kv-row"><span>OpenAI models path</span><strong>${escapeHtml(detail.openai_models_path || "-")}</strong></div>
        <div class="kv-row"><span>OpenAI chat path</span><strong>${escapeHtml(detail.openai_chat_path || "-")}</strong></div>
        <div class="kv-row"><span>OpenAI completions path</span><strong>${escapeHtml(detail.openai_completions_path || "-")}</strong></div>
        <div class="kv-row"><span>App UI</span><strong>${escapeHtml(detail.app_ui_url || "-")}</strong></div>
        <div class="kv-row"><span>Port</span><strong>${escapeHtml(detail.port || "-")}</strong></div>
        <div class="kv-row"><span>Started</span><strong>${escapeHtml(formatDateTime(detail.started_at))}</strong></div>
        <div class="kv-row"><span>Ended</span><strong>${escapeHtml(formatDateTime(detail.ended_at))}</strong></div>
        <div class="kv-row"><span>Uptime</span><strong>${escapeHtml(formatDuration(detail.uptime_seconds))}</strong></div>
        <div class="kv-row"><span>Exit code</span><strong>${escapeHtml(detail.exit_code ?? "-")}</strong></div>
        <div class="kv-row"><span>Last error</span><strong>${escapeHtml(detail.last_error || "-")}</strong></div>
        <div class="kv-row"><span>Metrics stages</span><strong>${escapeHtml(detail.metrics?.stages?.length ?? detail.last_result?.metrics?.stages?.length ?? "-")}</strong></div>
        <div class="kv-row"><span>Metrics status</span><strong>${escapeHtml(detail.metrics?.status || detail.last_result?.metrics?.status || "-")}</strong></div>
      </div>

      <div class="info-block">
        <p class="eyebrow">Lifecycle Events</p>
        <div class="detail-timeline">
          ${(detail.events || [])
            .slice()
            .reverse()
            .map(
              (event) => `
                <div class="timeline-item">
                  <div class="timeline-title">
                    <strong>${escapeHtml(event.message)}</strong>
                    ${renderBadge(event.kind.replaceAll("_", " "), "neutral")}
                  </div>
                  <div>${escapeHtml(formatDateTime(event.timestamp))}</div>
                </div>
              `,
            )
            .join("")}
        </div>
      </div>
    </div>
  `;
}

function renderCompatibilityTable() {
  if (!state.apps.length) {
    refs.compatibilityTable.innerHTML = `<div class="empty-state">No apps discovered yet.</div>`;
    return;
  }
  const instanceByAppId = new Map(state.instances.map((instance) => [instance.app_id, instance]));
  refs.compatibilityTable.innerHTML = `
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>App</th>
            <th>Terminal Start</th>
            <th>Port Override</th>
            <th>HTTP</th>
            <th>Own Web UI</th>
            <th>OpenAI API</th>
            <th>File I/O</th>
            <th>Dataset</th>
            <th>Stop/Restart</th>
            <th>Overall</th>
          </tr>
        </thead>
        <tbody>
          ${state.apps
            .map((app) => {
              const instance = instanceByAppId.get(app.id);
              const overall = instance && instance.compatibility?.length
                ? deriveCompatibilityOverall(instance.compatibility)
                : app.verification_status;
              const httpCapable = Boolean(app.port?.required || app.web_ui?.starts_own_ui || app.health_path);
              return `
                <tr>
                  <td>${escapeHtml(app.name)}</td>
                  <td>${renderBadge(app.verified ? "verified" : "discovered", app.verified ? "verified" : "discovered")}</td>
                  <td>${escapeHtml(app.port?.configurable ? "yes" : "no")}</td>
                  <td>${escapeHtml(httpCapable ? "yes" : "no")}</td>
                  <td>${escapeHtml(app.web_ui?.starts_own_ui ? "yes" : "no")}</td>
                  <td>${escapeHtml(app.openai?.compatible ? "yes" : "no")}</td>
                  <td>${escapeHtml(app.filesystem?.requires_workspace ? "yes" : "no")}</td>
                  <td>${escapeHtml(app.dataset?.required ? "yes" : "no")}</td>
                  <td>yes</td>
                  <td>${renderBadge(overall, overall)}</td>
                </tr>
              `;
            })
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

function deriveCompatibilityOverall(tests) {
  const statuses = new Set((tests || []).map((test) => test.status));
  if (statuses.has("failed")) return "failed";
  if (statuses.has("passed") && statuses.has("skipped")) return "partial";
  if (statuses.has("passed")) return "passed";
  if (statuses.has("skipped")) return "skipped";
  return "unknown";
}

function renderExperiments() {
  if (!state.experiments) {
    refs.experimentSummary.innerHTML = `<div class="empty-state">Loading experiment data...</div>`;
    refs.experimentLog.innerHTML = `<div class="empty-state">Loading experiment data...</div>`;
    return;
  }

  const summary = state.experiments.summary || {};
  const cards = [
    ["Captured events", summary.total_events || 0, "Automatic records emitted by launch, invoke, stop, restart, and compatibility flows"],
    ["Apps exercised", summary.apps_exercised || 0, "Distinct apps that already appear in the experiment trace"],
    ["Launches", summary.launches || 0, "Launch attempts recorded by the runtime"],
    ["Invocations", summary.invocations || 0, "One-shot app calls and service-mode invokes"],
    ["Control actions", summary.control_actions || 0, "Stop, restart, and compatibility operations"],
    ["Failures", summary.failures || 0, "Recorded operations whose status is failed"],
  ];
  refs.experimentSummary.innerHTML = cards
    .map(
      ([label, value, caption]) => `
        <article class="experiment-card">
          <div class="summary-label">${escapeHtml(label)}</div>
          <h4>${escapeHtml(value)}</h4>
          <p>${escapeHtml(caption)}</p>
        </article>
      `,
    )
    .join("");

  const records = state.experiments.records || [];
  if (!records.length) {
    refs.experimentLog.innerHTML = `<div class="empty-state">No experiment trace yet. Launch or stop an instance, run compatibility, or invoke a pipeline to start collecting runtime evidence.</div>`;
    return;
  }

  refs.experimentLog.innerHTML = `
    <div class="info-block">
      <p class="eyebrow">Capture Policy</p>
      <div>${escapeHtml(summary.capture_policy || "")}</div>
      <div class="kv-row"><span>Last event</span><strong>${escapeHtml(formatDateTime(summary.last_event_at))}</strong></div>
    </div>
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th>Time</th>
            <th>Kind</th>
            <th>Status</th>
            <th>App</th>
            <th>Instance</th>
            <th>Summary</th>
          </tr>
        </thead>
        <tbody>
          ${records
            .slice(0, 40)
            .map(
              (record) => `
                <tr>
                  <td>${escapeHtml(formatDateTime(record.timestamp))}</td>
                  <td>${renderBadge(record.kind, "neutral")}</td>
                  <td>${renderBadge(record.status, record.status)}</td>
                  <td>${escapeHtml(record.app_name || record.app_id || "-")}</td>
                  <td class="mono-line">${escapeHtml(record.instance_id || "-")}</td>
                  <td>${escapeHtml(record.summary)}</td>
                </tr>
              `,
            )
            .join("")}
        </tbody>
      </table>
    </div>
  `;
}

function renderPorts() {
  if (!state.ports) {
    refs.portsUsed.innerHTML = `<div class="empty-state">Loading ports...</div>`;
    refs.portsAvailable.innerHTML = `<div class="empty-state">Loading ports...</div>`;
    return;
  }
  refs.portsUsed.innerHTML = state.ports.used.length
    ? `<div class="port-list">${state.ports.used
        .map(
          (item) => `
            <div class="port-item">
              <div class="timeline-title">
                <strong>${escapeHtml(item.port)}</strong>
                ${renderBadge(item.status, item.status)}
              </div>
              <div>${escapeHtml(item.app_name)} · ${escapeHtml(item.instance_id)}</div>
            </div>
          `,
        )
        .join("")}</div>`
    : `<div class="empty-state">No managed ports are currently occupied.</div>`;

  refs.portsAvailable.innerHTML = `
    <div class="info-block">
      <div class="kv-row"><span>Range</span><strong>${escapeHtml(`${state.ports.range_start} - ${state.ports.range_end}`)}</strong></div>
      <div class="kv-row"><span>Free count</span><strong>${escapeHtml(state.ports.available_count)}</strong></div>
      <div class="kv-row"><span>Preview</span><strong>${escapeHtml(state.ports.available_preview.join(", ") || "-")}</strong></div>
    </div>
  `;
}

function renderSettings() {
  if (!state.settings) {
    refs.settingsGrid.innerHTML = `<div class="empty-state">Loading settings...</div>`;
    return;
  }
  refs.sidebarRoot.textContent = state.settings.root_dir;
  refs.sidebarPython.textContent = state.settings.python_executable;
  refs.sidebarPortRange.textContent = `${state.settings.allowed_port_range[0]}-${state.settings.allowed_port_range[1]}`;
  const entries = [
    ["Root directory", state.settings.root_dir],
    ["Python executable", state.settings.python_executable],
    ["Allowed port range", state.settings.allowed_port_range.join(" - ")],
    ["Default host", state.settings.default_host],
    ["Log retention", `${state.settings.log_retention_lines} lines`],
    ["Runtime notes", state.settings.notes],
  ];
  refs.settingsGrid.innerHTML = entries
    .map(
      ([label, value]) => `
        <div class="setting-card">
          <h4>${escapeHtml(label)}</h4>
          <div class="mono-line">${escapeHtml(value)}</div>
        </div>
      `,
    )
    .join("");
}

async function refreshData({ withValidation = true } = {}) {
  const [appsPayload, instancesPayload, portsPayload, settingsPayload, experimentsPayload] = await Promise.all([
    fetchJson("/api/apps"),
    fetchJson("/api/instances"),
    fetchJson("/api/ports"),
    fetchJson("/api/settings"),
    fetchJson("/api/experiments"),
  ]);

  state.apps = appsPayload.apps || [];
  state.instances = instancesPayload.instances || [];
  state.ports = portsPayload;
  state.settings = settingsPayload;
  state.experiments = experimentsPayload;

  if (!state.activeAppId) {
    pickInitialApp();
  }
  if (state.activeInstanceId && !state.instances.some((item) => item.instance_id === state.activeInstanceId)) {
    state.activeInstanceId = null;
    state.activeInstanceDetail = null;
  }
  if (!state.activeInstanceId && state.instances.length) {
    state.activeInstanceId = state.instances[0].instance_id;
  }
  if (state.activeInstanceId) {
    state.activeInstanceDetail = await fetchJson(`/api/instances/${state.activeInstanceId}`);
    registerMetricsRun(buildInstanceMetricsRun(state.activeInstanceDetail));
  }

  renderSummaryCards();
  renderOverviewInstances();
  renderRecentActivity();
  renderCatalog();
  renderLaunchFormOptions();
  renderLaunchFacts();
  renderDynamicArgs();
  renderRequestLab();
  renderInstancesTable();
  renderInstanceDetail();
  renderCompatibilityTable();
  renderExperiments();
  renderPorts();
  renderSettings();

  if (withValidation && state.activeAppId) {
    scheduleValidation();
  }
}

function renderLaunchFormOptions() {
  refs.launchAppSelect.innerHTML = state.apps
    .map(
      (app) => `<option value="${escapeHtml(app.id)}" ${app.id === state.activeAppId ? "selected" : ""}>${escapeHtml(app.name)}</option>`,
    )
    .join("");
}

async function runValidation() {
  if (!state.activeAppId) {
    return;
  }
  try {
    state.validation = await fetchJson(`/api/apps/${state.activeAppId}/validate`, {
      method: "POST",
      body: JSON.stringify(collectLaunchPayload()),
    });
    renderValidationPreview();
  } catch (error) {
    showToast(error.message, { error: true });
  }
}

function scheduleValidation() {
  clearTimeout(validationTimer);
  validationTimer = setTimeout(() => {
    runValidation();
  }, 220);
  refs.launchPort.disabled = refs.launchAutoPort.checked;
}

async function launchApp() {
  if (!state.activeAppId) {
    showToast("Select an app before launching.", { error: true });
    return;
  }
  try {
    const payload = collectLaunchPayload();
    const result = await fetchJson(`/api/apps/${state.activeAppId}/launch`, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    state.activeInstanceId = result.instance_id;
    state.activeInstanceTab = "overview";
    showToast(`Launched ${result.app_name}`);
    await refreshData({ withValidation: false });
  } catch (error) {
    showToast(error.message, { error: true });
  }
}

async function stopInstance(instanceId) {
  if (!window.confirm("Stop this instance?")) {
    return;
  }
  try {
    await fetchJson(`/api/instances/${instanceId}/stop`, { method: "POST" });
    showToast(`Stopped ${instanceId}`);
    await refreshData({ withValidation: false });
  } catch (error) {
    showToast(error.message, { error: true });
  }
}

async function restartInstance(instanceId) {
  try {
    const result = await fetchJson(`/api/instances/${instanceId}/restart`, { method: "POST" });
    state.activeInstanceId = result.instance_id;
    showToast(`Restarted ${result.app_name}`);
    await refreshData({ withValidation: false });
  } catch (error) {
    showToast(error.message, { error: true });
  }
}

async function clearExperiments() {
  if (!window.confirm("Clear all captured experiment records?")) {
    return;
  }
  try {
    await fetchJson("/api/experiments/reset", { method: "POST" });
    showToast("Experiment records cleared.");
    await refreshData({ withValidation: false });
  } catch (error) {
    showToast(error.message, { error: true });
  }
}

async function runCompatibility(instanceId) {
  try {
    await fetchJson(`/api/instances/${instanceId}/compatibility`, { method: "POST" });
    showToast(`Compatibility check completed for ${instanceId}`);
    await refreshData({ withValidation: false });
    state.activeInstanceTab = "compatibility";
    renderInstanceDetail();
  } catch (error) {
    showToast(error.message, { error: true });
  }
}

async function runInstanceDemo(instanceId) {
  try {
    await fetchJson(`/api/instances/${instanceId}/demo-run`, { method: "POST" });
    showToast(`Demo flow completed for ${instanceId}`);
    await refreshData({ withValidation: false });
    state.activeInstanceTab = "metrics";
    renderInstanceDetail();
  } catch (error) {
    showToast(error.message, { error: true });
  }
}

function cloneLaunch(instanceId) {
  const instance = state.instances.find((item) => item.instance_id === instanceId);
  if (!instance) {
    return;
  }
  state.activeAppId = instance.app_id;
  renderLaunchFormOptions();
  refs.launchHost.value = instance.launch_config.host || "127.0.0.1";
  refs.launchAutoPort.checked = Boolean(instance.launch_config.auto_port);
  refs.launchPort.disabled = refs.launchAutoPort.checked;
  refs.launchPort.value = instance.launch_config.port || instance.port || "";
  refs.launchStoragePath.value = instance.launch_config.storage_path || "";
  refs.launchEnv.value = Object.entries(instance.launch_config.env || {})
    .map(([key, value]) => `${key}=${value}`)
    .join("\n");
  refs.launchArgs.value = (instance.launch_config.extra_args || []).join("\n");
  refs.launchAllowDuplicate.checked = false;
  refs.launchTimeout.value = instance.launch_config.startup_timeout_seconds || 12;
  renderLaunchFacts();
  renderRequestLab();
  scheduleValidation();
  document.getElementById("launch").scrollIntoView({ behavior: "smooth", block: "start" });
}

function exportRequestBundle(kind) {
  if (!state.requestResult) {
    showToast("No request result is available to export.", { error: true });
    return;
  }
  const invokeResult = state.requestResult.route === "openai" ? (state.requestResult.result.opc_result || {}) : state.requestResult.result;
  const payload = kind === "metrics" ? invokeResult.metrics : state.requestResult;
  if (!payload) {
    showToast("No metrics bundle is available for this request.", { error: true });
    return;
  }
  const filename = kind === "metrics"
    ? `sage-request-metrics-${safeSlug(state.requestResult.targetAppId || state.requestResult.targetLabel)}-${timestampToken(state.requestResult.submittedAt)}.json`
    : `sage-request-result-${safeSlug(state.requestResult.targetAppId || state.requestResult.targetLabel)}-${timestampToken(state.requestResult.submittedAt)}.json`;
  downloadJson(filename, payload);
  showToast(kind === "metrics" ? "Metrics bundle exported." : "Request result exported.");
}

function exportInstanceBundle(instanceId, kind) {
  const detail = state.activeInstanceDetail?.instance_id === instanceId
    ? state.activeInstanceDetail
    : state.instances.find((item) => item.instance_id === instanceId);
  if (!detail) {
    showToast("Instance detail is not available for export.", { error: true });
    return;
  }
  const payload = kind === "metrics" ? (detail.metrics || detail.last_result?.metrics) : detail.last_result;
  if (!payload) {
    showToast(kind === "metrics" ? "No metrics have been captured for this instance yet." : "No result bundle has been captured for this instance yet.", { error: true });
    return;
  }
  const filename = kind === "metrics"
    ? `sage-instance-metrics-${safeSlug(detail.app_id)}-${safeSlug(detail.instance_id)}.json`
    : `sage-instance-result-${safeSlug(detail.app_id)}-${safeSlug(detail.instance_id)}.json`;
  downloadJson(filename, payload);
  showToast(kind === "metrics" ? "Instance metrics exported." : "Instance result exported.");
}

async function copyText(value) {
  if (!value) {
    return;
  }
  try {
    await navigator.clipboard.writeText(value);
    showToast("Copied to clipboard.");
  } catch {
    showToast("Clipboard write failed.", { error: true });
  }
}

function selectInstance(instanceId) {
  state.activeInstanceId = instanceId;
  refreshData({ withValidation: false }).catch((error) => {
    showToast(error.message, { error: true });
  });
  document.getElementById("instances").scrollIntoView({ behavior: "smooth", block: "start" });
}

function prepareLaunch(appId) {
  state.activeAppId = appId;
  syncLaunchFormToApp();
  renderLaunchFormOptions();
  renderLaunchFacts();
  renderRequestLab();
  document.getElementById("launch").scrollIntoView({ behavior: "smooth", block: "start" });
}

async function showApp(appId) {
  const app = state.apps.find((item) => item.id === appId);
  if (!app) {
    return;
  }
  state.activeAppId = appId;
  renderLaunchFormOptions();
  renderLaunchFacts();
  renderRequestLab();
  showToast(`${app.name}: ${app.purpose}`);
}

function attachEventListeners() {
  refs.searchInput.addEventListener("input", (event) => {
    state.search = event.target.value;
    renderCatalog();
  });

  refs.launchShortcut.addEventListener("click", () => {
    document.getElementById("launch").scrollIntoView({ behavior: "smooth", block: "start" });
  });

  refs.launchAppSelect.addEventListener("change", (event) => {
    state.activeAppId = event.target.value;
    syncLaunchFormToApp();
    renderLaunchFacts();
  });

  [
    refs.launchHost,
    refs.launchPort,
    refs.launchStoragePath,
    refs.launchEnv,
    refs.launchArgs,
    refs.launchTimeout,
    refs.launchServiceMode,
    refs.launchAllowDuplicate,
  ].forEach((element) => {
    element.addEventListener("input", scheduleValidation);
    element.addEventListener("change", scheduleValidation);
  });

  refs.launchAutoPort.addEventListener("change", scheduleValidation);
  refs.dynamicArgs.addEventListener("input", scheduleValidation);
  refs.dynamicArgs.addEventListener("change", scheduleValidation);
  refs.dryRunButton.addEventListener("click", runValidation);
  refs.copyCommandButton.addEventListener("click", () => copyText(state.validation?.command_preview || ""));
  refs.launchButton.addEventListener("click", launchApp);
  refs.clearExperimentsButton.addEventListener("click", clearExperiments);

  refs.requestRoute.addEventListener("change", (event) => {
    state.requestRoute = event.target.value;
    renderRequestLab();
  });
  refs.requestPayloadMode.addEventListener("change", renderRequestLab);
  refs.requestTemplate.addEventListener("change", renderRequestLab);
  [
    refs.requestArgument,
    refs.requestFilename,
    refs.requestTimeout,
    refs.requestExtraArgs,
    refs.requestEnv,
    refs.requestContent,
  ].forEach((element) => {
    element.addEventListener("input", renderRequestLab);
    element.addEventListener("change", renderRequestLab);
  });
  refs.applyRequestTemplateButton.addEventListener("click", () => applyRequestTemplate());
  refs.copyRequestCurlButton.addEventListener("click", () => copyText(refs.requestCurlPreview.textContent || ""));
  refs.sendRequestButton.addEventListener("click", sendRequest);

  document.body.addEventListener("click", (event) => {
    const target = event.target.closest("[data-action]");
    if (!target) {
      return;
    }
    const { action, appId, instanceId, endpoint, url, tab } = target.dataset;
    switch (action) {
      case "prepare-launch":
        prepareLaunch(appId);
        break;
      case "show-app":
        showApp(appId);
        break;
      case "select-instance":
        selectInstance(instanceId);
        break;
      case "copy-endpoint":
        copyText(endpoint);
        break;
      case "copy-text":
        copyText(target.dataset.text || "");
        break;
      case "export-request-result":
        exportRequestBundle("result");
        break;
      case "export-request-metrics":
        exportRequestBundle("metrics");
        break;
      case "open-url":
        window.open(url, "_blank", "noopener,noreferrer");
        break;
      case "stop-instance":
        stopInstance(instanceId);
        break;
      case "restart-instance":
        restartInstance(instanceId);
        break;
      case "run-compatibility":
        runCompatibility(instanceId);
        break;
      case "run-instance-demo":
        runInstanceDemo(instanceId);
        break;
      case "clone-launch":
        cloneLaunch(instanceId);
        break;
      case "export-instance-result":
        exportInstanceBundle(instanceId, "result");
        break;
      case "export-instance-metrics":
        exportInstanceBundle(instanceId, "metrics");
        break;
      case "switch-instance-tab":
        state.activeInstanceTab = tab;
        renderInstanceDetail();
        break;
      default:
        break;
    }
  });
}

async function bootstrap() {
  attachEventListeners();
  await refreshData();
  applyRequestTemplate({ announce: false });
  renderValidationPreview();
  setInterval(() => {
    refreshData({ withValidation: false }).catch((error) => {
      showToast(error.message, { error: true });
    });
  }, 4000);
}

bootstrap().catch((error) => {
  showToast(error.message, { error: true });
});