"""Multi-role web UI for the supply chain alert dashboard."""

from __future__ import annotations


def render_dashboard_page() -> str:
    return """<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>SAGE Supply Chain Alert Dashboard</title>
    <style>
      :root {
        --bg: #efe7db;
        --panel: rgba(255, 251, 246, 0.9);
        --panel-strong: rgba(255, 255, 255, 0.82);
        --ink: #1b2430;
        --muted: #596273;
        --line: rgba(36, 60, 72, 0.12);
        --accent: #0f766e;
        --accent-strong: #115e59;
        --accent-soft: rgba(15, 118, 110, 0.1);
        --warning: #ca8a04;
        --danger: #b42318;
        --lavender: rgba(61, 34, 97, 0.09);
        --shadow: 0 24px 70px rgba(36, 37, 45, 0.12);
      }

      * { box-sizing: border-box; }

      body {
        margin: 0;
        font-family: "Avenir Next", "PingFang SC", "Microsoft YaHei", sans-serif;
        color: var(--ink);
        background:
          radial-gradient(circle at top left, rgba(15, 118, 110, 0.18), transparent 26%),
          radial-gradient(circle at top right, rgba(202, 138, 4, 0.16), transparent 24%),
          linear-gradient(180deg, #fcf7f0 0%, var(--bg) 100%);
      }

      .shell {
        max-width: 1400px;
        margin: 0 auto;
        padding: 36px 18px 60px;
      }

      .hero {
        display: grid;
        gap: 18px;
        grid-template-columns: 1.25fr 0.85fr;
        margin-bottom: 20px;
      }

      .hero-card,
      .panel {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 26px;
        box-shadow: var(--shadow);
        backdrop-filter: blur(12px);
      }

      .hero-card { padding: 28px; }

      .eyebrow {
        margin: 0 0 10px;
        font-size: 12px;
        letter-spacing: 0.18em;
        text-transform: uppercase;
        color: var(--accent-strong);
      }

      h1 {
        margin: 0;
        font-size: clamp(32px, 5vw, 58px);
        line-height: 0.94;
        letter-spacing: -0.05em;
      }

      .hero-copy {
        margin: 16px 0 0;
        max-width: 56ch;
        color: var(--muted);
        line-height: 1.68;
      }

      .action-panel {
        display: flex;
        flex-direction: column;
        gap: 18px;
        justify-content: space-between;
        padding: 24px;
      }

      .action-row {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
      }

      button {
        border: 0;
        border-radius: 999px;
        padding: 12px 18px;
        font: inherit;
        cursor: pointer;
        transition: transform 140ms ease, opacity 140ms ease, background 140ms ease;
      }

      button:hover { transform: translateY(-1px); }
      button:disabled { cursor: wait; opacity: 0.58; transform: none; }
      .primary { background: var(--accent); color: white; }
      .secondary { background: var(--accent-soft); color: var(--accent-strong); }
      .ghost { background: rgba(27, 36, 48, 0.06); color: var(--ink); }

      .status-line {
        min-height: 24px;
        color: var(--muted);
        font-size: 14px;
      }

      .status-line.error { color: var(--danger); }

      .legend {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
        color: var(--muted);
        font-size: 13px;
      }

      .legend span {
        display: inline-flex;
        align-items: center;
        gap: 8px;
      }

      .legend-dot {
        width: 9px;
        height: 9px;
        border-radius: 999px;
      }

      .legend-high { background: var(--danger); }
      .legend-medium { background: var(--warning); }
      .legend-low { background: var(--accent); }

      .grid {
        display: grid;
        grid-template-columns: repeat(12, minmax(0, 1fr));
        gap: 18px;
      }

      .metrics {
        grid-column: 1 / -1;
        display: grid;
        grid-template-columns: repeat(6, minmax(0, 1fr));
        gap: 14px;
      }

      .panel { padding: 22px; }
      .panel h2 { margin: 0; font-size: 22px; letter-spacing: -0.03em; }

      .metric-card {
        padding: 18px;
        background: var(--panel-strong);
      }

      .metric-label { color: var(--muted); font-size: 13px; }
      .metric-value {
        margin-top: 12px;
        font-size: clamp(25px, 3.8vw, 38px);
        font-weight: 700;
        letter-spacing: -0.05em;
      }

      .role-panel { grid-column: 1 / -1; }
      .role-panel-head {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 16px;
        margin-bottom: 16px;
      }

      .role-panel-copy {
        max-width: 60ch;
        color: var(--muted);
        line-height: 1.7;
        margin: 10px 0 0;
      }

      .role-tabs {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        justify-content: flex-end;
      }

      .role-tab {
        background: rgba(27, 36, 48, 0.06);
        color: var(--ink);
        border: 1px solid transparent;
      }

      .role-tab.active {
        background: white;
        color: var(--accent-strong);
        border-color: rgba(15, 118, 110, 0.22);
        box-shadow: inset 0 0 0 1px rgba(15, 118, 110, 0.1);
      }

      .role-body {
        display: grid;
        gap: 16px;
        grid-template-columns: 1.1fr 0.9fr;
      }

      .briefing-card,
      .queue-card,
      .alert-card,
      .explanation-card,
      .supplier-card {
        border-radius: 20px;
        border: 1px solid rgba(36, 60, 72, 0.1);
        background: var(--panel-strong);
      }

      .briefing-card,
      .queue-card,
      .supplier-card {
        padding: 18px;
      }

      .narrative {
        color: var(--ink);
        line-height: 1.75;
        font-size: 15px;
      }

      .chip-row {
        display: flex;
        flex-wrap: wrap;
        gap: 8px;
        margin-top: 14px;
      }

      .chip {
        display: inline-flex;
        align-items: center;
        border-radius: 999px;
        padding: 8px 12px;
        font-size: 13px;
        background: var(--accent-soft);
        color: var(--accent-strong);
      }

      .summary-list,
      .queue-list {
        margin: 14px 0 0;
        padding-left: 18px;
        color: var(--muted);
      }

      .summary-list li + li,
      .queue-list li + li { margin-top: 8px; }

      .queue-grid {
        display: grid;
        gap: 12px;
      }

      .queue-card-head {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 12px;
      }

      .queue-card h3,
      .alert-title,
      .explanation-title,
      .supplier-card h3 {
        margin: 0;
        font-size: 17px;
      }

      .queue-card p,
      .meta,
      .summary-text,
      .explanation-copy,
      .empty-state {
        color: var(--muted);
        line-height: 1.7;
      }

      .queue-owner {
        font-size: 12px;
        color: var(--accent-strong);
        background: rgba(15, 118, 110, 0.08);
        border-radius: 999px;
        padding: 6px 10px;
      }

      .summary-panel,
      .alerts-panel,
      .suppliers-panel,
      .explanations-panel {
        min-width: 0;
      }

      .summary-panel,
      .alerts-panel { grid-column: span 6; }
      .suppliers-panel,
      .explanations-panel { grid-column: span 6; }

      .stack { display: grid; gap: 14px; }

      .alert-card,
      .explanation-card {
        padding: 16px;
      }

      .alert-top,
      .explanation-top {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 12px;
      }

      .risk-pill {
        display: inline-flex;
        align-items: center;
        padding: 6px 10px;
        border-radius: 999px;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 0.04em;
      }

      .risk-high { background: rgba(180, 35, 24, 0.12); color: var(--danger); }
      .risk-medium { background: rgba(202, 138, 4, 0.14); color: var(--warning); }
      .risk-low { background: rgba(15, 118, 110, 0.12); color: var(--accent-strong); }

      table {
        width: 100%;
        border-collapse: collapse;
      }

      th,
      td {
        padding: 10px 0;
        border-bottom: 1px solid rgba(36, 60, 72, 0.08);
        text-align: left;
        font-size: 14px;
      }

      th { color: var(--muted); font-weight: 600; }

      .supplier-grid {
        display: grid;
        gap: 12px;
      }

      .supplier-kpi {
        margin-top: 8px;
        display: grid;
        gap: 8px;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        color: var(--muted);
        font-size: 13px;
      }

      .gateway-note {
        margin-top: 10px;
        padding: 12px 14px;
        border-radius: 16px;
        background: var(--lavender);
        color: var(--muted);
      }

      .footer-note {
        margin-top: 24px;
        text-align: right;
        color: var(--muted);
        font-size: 13px;
      }

      @media (max-width: 1120px) {
        .hero,
        .role-body,
        .metrics,
        .summary-panel,
        .alerts-panel,
        .suppliers-panel,
        .explanations-panel {
          grid-template-columns: 1fr;
          grid-column: 1 / -1;
        }

        .metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); }
        .role-panel-head { flex-direction: column; }
        .role-tabs { justify-content: flex-start; }
      }

      @media (max-width: 720px) {
        .shell { padding: 22px 14px 40px; }
        .hero-card, .panel, .briefing-card, .queue-card, .supplier-card, .alert-card, .explanation-card {
          border-radius: 18px;
        }
        .metrics { grid-template-columns: 1fr 1fr; }
        .supplier-kpi { grid-template-columns: 1fr; }
      }
    </style>
  </head>
  <body>
    <main class="shell">
      <section class="hero">
        <article class="hero-card">
          <p class="eyebrow">Supply Chain Command Surface</p>
          <h1>供应链异常预警看板</h1>
          <p class="hero-copy">
            这个页面在同一套数据上切换多角色视角。运营总控、采购协调、仓配调度和供应商管理都能看到各自最该处理的问题、动作队列与结构化解释。
          </p>
        </article>
        <aside class="hero-card action-panel">
          <div>
            <p class="eyebrow">Actions</p>
            <div class="action-row">
              <button id="run-demo" class="primary">加载演示数据</button>
              <button id="refresh-board" class="secondary">刷新看板</button>
              <button id="load-explanations" class="ghost">生成中文解释</button>
            </div>
          </div>
          <div class="legend">
            <span><i class="legend-dot legend-high"></i>高风险</span>
            <span><i class="legend-dot legend-medium"></i>中风险</span>
            <span><i class="legend-dot legend-low"></i>低风险</span>
          </div>
          <div id="status-line" class="status-line">正在连接本地 API...</div>
        </aside>
      </section>

      <section class="grid">
        <div id="metrics" class="metrics"></div>

        <section class="panel role-panel">
          <div class="role-panel-head">
            <div>
              <p class="eyebrow">Role Lenses</p>
              <h2 id="role-title">运营总控</h2>
              <p id="role-description" class="role-panel-copy">等待数据加载。</p>
            </div>
            <div id="role-tabs" class="role-tabs"></div>
          </div>
          <div class="role-body">
            <article class="briefing-card">
              <h3>角色摘要</h3>
              <p id="role-narrative" class="narrative">等待数据加载。</p>
              <div id="role-priority" class="chip-row"></div>
              <ul id="role-bullets" class="summary-list"></ul>
            </article>
            <div id="role-queue" class="queue-grid"></div>
          </div>
        </section>

        <section class="panel summary-panel">
          <h2>全局态势</h2>
          <div id="summary-text" class="summary-text">等待数据加载。</div>
          <div id="shortage-chips" class="chip-row"></div>
        </section>

        <section class="panel alerts-panel">
          <h2 id="alerts-heading">角色关注预警</h2>
          <div id="alerts-list" class="stack"><div class="empty-state">还没有预警数据。</div></div>
        </section>

        <section class="panel suppliers-panel">
          <h2 id="suppliers-heading">角色关注供应商</h2>
          <div id="suppliers-table" class="empty-state">还没有供应商风险数据。</div>
        </section>

        <section class="panel explanations-panel">
          <h2>自然语言解释</h2>
          <div id="gateway-meta" class="summary-text">尚未请求解释。</div>
          <div id="dashboard-explanation" class="summary-text" style="margin-top: 12px;"></div>
          <div id="gateway-note" class="gateway-note">即使网关暂时不可用，角色摘要和动作队列仍会继续基于规则结果工作。</div>
          <div id="explanations-list" class="stack" style="margin-top: 16px;"></div>
        </section>
      </section>

      <p id="footer-note" class="footer-note"></p>
    </main>

    <script>
      const state = {
        dashboard: null,
        alerts: [],
        suppliers: [],
        explanations: null,
        currentRole: "command",
      };

      const roleConfigs = {
        command: {
          label: "运营总控",
          description: "跨部门总览当前风险、资源冲突和优先级排序。",
          headingAlerts: "全局最高优先级预警",
          headingSuppliers: "全局关键供应商",
        },
        procurement: {
          label: "采购协调",
          description: "聚焦订单积压、供应商集中度和替代供应商动作。",
          headingAlerts: "采购协调重点预警",
          headingSuppliers: "采购关注供应商",
        },
        logistics: {
          label: "仓配调度",
          description: "聚焦低库存、在途延迟、仓间调拨和履约稳定性。",
          headingAlerts: "仓配调度重点预警",
          headingSuppliers: "仓配影响供应商",
        },
        supplier: {
          label: "供应商管理",
          description: "聚焦履约恶化、准时率、违约频次和治理动作。",
          headingAlerts: "供应商管理重点预警",
          headingSuppliers: "供应商治理清单",
        },
      };

      const elements = {
        metrics: document.getElementById("metrics"),
        roleTabs: document.getElementById("role-tabs"),
        roleTitle: document.getElementById("role-title"),
        roleDescription: document.getElementById("role-description"),
        roleNarrative: document.getElementById("role-narrative"),
        rolePriority: document.getElementById("role-priority"),
        roleBullets: document.getElementById("role-bullets"),
        roleQueue: document.getElementById("role-queue"),
        summaryText: document.getElementById("summary-text"),
        shortageChips: document.getElementById("shortage-chips"),
        alertsHeading: document.getElementById("alerts-heading"),
        alertsList: document.getElementById("alerts-list"),
        suppliersHeading: document.getElementById("suppliers-heading"),
        suppliersTable: document.getElementById("suppliers-table"),
        gatewayMeta: document.getElementById("gateway-meta"),
        dashboardExplanation: document.getElementById("dashboard-explanation"),
        gatewayNote: document.getElementById("gateway-note"),
        explanationsList: document.getElementById("explanations-list"),
        statusLine: document.getElementById("status-line"),
        footerNote: document.getElementById("footer-note"),
        runDemo: document.getElementById("run-demo"),
        refreshBoard: document.getElementById("refresh-board"),
        loadExplanations: document.getElementById("loadExplanations") || document.getElementById("load-explanations"),
      };

      const metricConfig = [
        ["open_alert_count", "开放预警"],
        ["high_risk_alert_count", "高风险预警"],
        ["low_stock_sku_count", "低库存 SKU"],
        ["delayed_shipment_count", "延迟发货"],
        ["overdue_order_count", "逾期订单"],
        ["high_risk_supplier_count", "高风险供应商"],
      ];

      function setBusy(isBusy) {
        elements.runDemo.disabled = isBusy;
        elements.refreshBoard.disabled = isBusy;
        elements.loadExplanations.disabled = isBusy;
      }

      function setStatus(message, isError = false) {
        elements.statusLine.textContent = message;
        elements.statusLine.classList.toggle("error", isError);
      }

      function escapeHtml(value) {
        return String(value)
          .replaceAll("&", "&amp;")
          .replaceAll("<", "&lt;")
          .replaceAll(">", "&gt;")
          .replaceAll('"', "&quot;");
      }

      function riskClass(level) {
        const normalized = String(level || "low").toLowerCase();
        if (normalized === "high") return "risk-high";
        if (normalized === "medium") return "risk-medium";
        return "risk-low";
      }

      function riskRank(level) {
        const normalized = String(level || "low").toLowerCase();
        if (normalized === "high") return 3;
        if (normalized === "medium") return 2;
        return 1;
      }

      function formatNumber(value) {
        if (typeof value !== "number") return value ?? "-";
        return Number.isInteger(value) ? String(value) : value.toFixed(1);
      }

      function sortAlerts(alerts) {
        return [...alerts].sort((left, right) => {
          const riskDiff = riskRank(right.risk_level) - riskRank(left.risk_level);
          if (riskDiff !== 0) return riskDiff;
          return String(right.triggered_at || "").localeCompare(String(left.triggered_at || ""));
        });
      }

      function uniqueItems(items) {
        return [...new Set(items.filter(Boolean))];
      }

      function getRoleAlerts(roleId) {
        const alerts = sortAlerts(state.alerts);
        if (roleId === "command") return alerts;
        if (roleId === "procurement") {
          return alerts.filter((alert) => ["order_backlog", "supplier_concentration", "supplier_risk_deterioration"].includes(alert.rule_id) || (alert.alternative_suppliers || []).length > 0);
        }
        if (roleId === "logistics") {
          return alerts.filter((alert) => ["low_inventory", "shipment_delay", "shipment_stagnation"].includes(alert.rule_id) || alert.shipment_id || alert.warehouse);
        }
        return alerts.filter((alert) => ["supplier_risk_deterioration", "supplier_concentration"].includes(alert.rule_id) || alert.supplier_id);
      }

      function getRoleSuppliers(roleId) {
        const suppliers = [...state.suppliers].sort((left, right) => right.risk_score - left.risk_score);
        if (roleId === "command") return suppliers.slice(0, 5);
        if (roleId === "logistics") {
          const supplierIds = uniqueItems(getRoleAlerts(roleId).map((alert) => alert.supplier_id));
          return suppliers.filter((supplier) => supplierIds.includes(supplier.supplier_id)).slice(0, 5);
        }
        return suppliers.filter((supplier) => supplier.open_alert_count > 0).slice(0, 5);
      }

      function buildRoleBriefing(roleId) {
        const role = roleConfigs[roleId];
        const dashboard = state.dashboard;
        const alerts = getRoleAlerts(roleId);
        const suppliers = getRoleSuppliers(roleId);

        if (!dashboard) {
          return {
            role,
            narrative: "等待 dashboard 数据加载后再生成角色摘要。",
            chips: [],
            bullets: [],
            queue: [],
          };
        }

        const topAlert = alerts[0];
        const topSupplier = suppliers[0];
        const commonChips = [
          `角色预警 ${alerts.length}`,
          `高风险 ${alerts.filter((item) => item.risk_level === "high").length}`,
          `受影响订单 ${formatNumber(dashboard.impacted_order_count)}`,
        ];

        if (roleId === "command") {
          return {
            role,
            narrative: `当前共有 ${dashboard.open_alert_count} 条开放预警，其中 ${dashboard.high_risk_alert_count} 条为高风险。最需要跨部门协调的是 ${topAlert ? topAlert.title : "暂无高优先级事件"}。`,
            chips: commonChips,
            bullets: [
              topAlert ? `先拉通处理 ${topAlert.title}，避免影响继续扩散。` : "暂无需要升级的预警。",
              topSupplier ? `重点盯住供应商 ${topSupplier.supplier_id}，当前风险分 ${formatNumber(topSupplier.risk_score)}。` : "暂无重点供应商。",
              `今日需要关注的短缺 SKU：${(dashboard.top_shortage_skus || []).slice(0, 3).join(" / ") || "暂无"}`,
            ],
            queue: sortAlerts(alerts).slice(0, 3).map((alert) => ({
              owner: "运营总控",
              title: alert.title,
              detail: alert.summary,
            })),
          };
        }

        if (roleId === "procurement") {
          const alternativeSuppliers = uniqueItems(alerts.flatMap((alert) => alert.alternative_suppliers || [])).slice(0, 3);
          return {
            role,
            narrative: `采购侧当前最关键的是控制供应商集中度和订单积压。${topAlert ? `优先处理 ${topAlert.title}` : "当前没有采购侧高优先级告警"}，同步准备替代供应商和加急补货策略。`,
            chips: [...commonChips, `替代供应商 ${alternativeSuppliers.length}`],
            bullets: [
              alternativeSuppliers.length ? `可优先接触的替代供应商：${alternativeSuppliers.join(" / ")}` : "当前没有推荐的替代供应商。",
              topSupplier ? `优先复核 ${topSupplier.supplier_id} 的履约能力和可交付窗口。` : "当前没有采购侧需升级的供应商。",
              `建议先处理 ${alerts.filter((alert) => alert.rule_id === "order_backlog").length} 条订单积压相关预警。`,
            ],
            queue: alerts.slice(0, 3).map((alert) => ({
              owner: "采购协调",
              title: alert.title,
              detail: (alert.recommended_actions || []).slice(0, 2).join("；") || alert.summary,
            })),
          };
        }

        if (roleId === "logistics") {
          const warehouses = uniqueItems(alerts.map((alert) => alert.warehouse)).slice(0, 3);
          return {
            role,
            narrative: `仓配侧当前重点是稳住低库存和在途延迟。${topAlert ? `最先处理 ${topAlert.title}` : "当前没有仓配侧高优先级事件"}，同时避免单点仓库进一步积压。`,
            chips: [...commonChips, `关键仓 ${warehouses.length}`],
            bullets: [
              warehouses.length ? `优先关注仓库：${warehouses.join(" / ")}` : "当前没有识别到关键仓库。",
              `平均延迟时长 ${formatNumber(dashboard.average_delay_hours)} 小时，需要复核转运与 ETA。`,
              `当前建议调拨 ${formatNumber(dashboard.reallocation_suggestion_count)} 次。`,
            ],
            queue: alerts.slice(0, 3).map((alert) => ({
              owner: "仓配调度",
              title: alert.title,
              detail: `${alert.warehouse || "未指定仓"} · ${(alert.recommended_actions || []).slice(0, 2).join("；") || alert.summary}`,
            })),
          };
        }

        return {
          role,
          narrative: `供应商管理侧当前重点是压降高风险供应商暴露面。${topSupplier ? `当前头号关注对象是 ${topSupplier.supplier_id}` : "当前没有需要升级的供应商"}，需要同时处理履约和违约趋势。`,
          chips: [...commonChips, `重点供应商 ${suppliers.length}`],
          bullets: [
            topSupplier ? `${topSupplier.supplier_id} 准时率 ${formatNumber(topSupplier.on_time_rate)}，违约次数 ${topSupplier.breach_count_30d}。` : "暂无重点供应商。",
            `当前共有 ${alerts.filter((alert) => alert.rule_id === "supplier_risk_deterioration").length} 条履约恶化预警。`,
            `建议先复盘开放预警最多的供应商并安排 SLA 纠偏。`,
          ],
          queue: suppliers.slice(0, 3).map((supplier) => ({
            owner: "供应商管理",
            title: supplier.supplier_id,
            detail: `风险分 ${formatNumber(supplier.risk_score)}，准时率 ${formatNumber(supplier.on_time_rate)}，开放预警 ${supplier.open_alert_count}。`,
          })),
        };
      }

      function renderRoleTabs() {
        elements.roleTabs.innerHTML = Object.entries(roleConfigs).map(([roleId, role]) => `
          <button class="role-tab ${state.currentRole === roleId ? "active" : ""}" data-role="${roleId}">${role.label}</button>
        `).join("");
        elements.roleTabs.querySelectorAll("button[data-role]").forEach((button) => {
          button.addEventListener("click", () => {
            state.currentRole = button.dataset.role;
            renderAll();
          });
        });
      }

      function renderMetrics() {
        if (!state.dashboard) {
          elements.metrics.innerHTML = "";
          return;
        }
        elements.metrics.innerHTML = metricConfig.map(([key, label]) => `
          <article class="panel metric-card">
            <div class="metric-label">${label}</div>
            <div class="metric-value">${escapeHtml(formatNumber(state.dashboard[key]))}</div>
          </article>
        `).join("");
      }

      function renderSummary() {
        if (!state.dashboard) {
          elements.summaryText.textContent = "等待数据加载。";
          elements.shortageChips.innerHTML = "";
          return;
        }

        const bullets = [
          `平均延迟时长 ${formatNumber(state.dashboard.average_delay_hours)} 小时`,
          `受影响订单 ${formatNumber(state.dashboard.impacted_order_count)} 个`,
          `调拨建议 ${formatNumber(state.dashboard.reallocation_suggestion_count)} 条`,
          `替代供应商建议 ${formatNumber(state.dashboard.substitute_supplier_suggestion_count)} 条`,
        ];

        elements.summaryText.innerHTML = `
          <div>最新快照时间：${escapeHtml(state.dashboard.generated_at || "-")}</div>
          <ul class="summary-list">${bullets.map((item) => `<li>${escapeHtml(item)}</li>`).join("")}</ul>
        `;

        const shortages = state.dashboard.top_shortage_skus || [];
        elements.shortageChips.innerHTML = shortages.length
          ? shortages.map((item) => `<span class="chip">${escapeHtml(item)}</span>`).join("")
          : '<span class="chip">当前没有高优先级短缺 SKU</span>';
      }

      function renderRolePanel() {
        const briefing = buildRoleBriefing(state.currentRole);
        elements.roleTitle.textContent = briefing.role.label;
        elements.roleDescription.textContent = briefing.role.description;
        elements.roleNarrative.textContent = briefing.narrative;
        elements.rolePriority.innerHTML = briefing.chips.map((item) => `<span class="chip">${escapeHtml(item)}</span>`).join("");
        elements.roleBullets.innerHTML = briefing.bullets.map((item) => `<li>${escapeHtml(item)}</li>`).join("");
        elements.roleQueue.innerHTML = briefing.queue.length
          ? briefing.queue.map((item) => `
              <article class="queue-card">
                <div class="queue-card-head">
                  <h3>${escapeHtml(item.title)}</h3>
                  <span class="queue-owner">${escapeHtml(item.owner)}</span>
                </div>
                <p>${escapeHtml(item.detail)}</p>
              </article>
            `).join("")
          : '<article class="queue-card"><h3>当前没有动作队列</h3><p>数据加载后会为当前角色生成优先处理清单。</p></article>';
      }

      function renderAlerts() {
        const role = roleConfigs[state.currentRole];
        const alerts = getRoleAlerts(state.currentRole);
        elements.alertsHeading.textContent = role.headingAlerts;

        if (!alerts.length) {
          elements.alertsList.innerHTML = '<div class="empty-state">当前角色下还没有预警数据。</div>';
          return;
        }

        elements.alertsList.innerHTML = alerts.slice(0, 6).map((alert) => `
          <article class="alert-card">
            <div class="alert-top">
              <div>
                <h3 class="alert-title">${escapeHtml(alert.title)}</h3>
                <div class="meta">${escapeHtml(alert.rule_id)} · ${escapeHtml(alert.triggered_at)}</div>
              </div>
              <span class="risk-pill ${riskClass(alert.risk_level)}">${escapeHtml(alert.risk_level)}</span>
            </div>
            <p class="summary-text">${escapeHtml(alert.summary)}</p>
            <div class="meta">SKU: ${escapeHtml(alert.sku || "-")} · 仓: ${escapeHtml(alert.warehouse || "-")} · 供应商: ${escapeHtml(alert.supplier_id || "-")}</div>
            <div class="chip-row">${(alert.recommended_actions || []).slice(0, 3).map((item) => `<span class="chip">${escapeHtml(item)}</span>`).join("")}</div>
          </article>
        `).join("");
      }

      function renderSuppliers() {
        const role = roleConfigs[state.currentRole];
        const suppliers = getRoleSuppliers(state.currentRole);
        elements.suppliersHeading.textContent = role.headingSuppliers;

        if (!suppliers.length) {
          elements.suppliersTable.innerHTML = '当前角色下没有重点供应商。';
          return;
        }

        if (state.currentRole === "command") {
          elements.suppliersTable.innerHTML = `
            <table>
              <thead><tr><th>供应商</th><th>风险分</th><th>准时率</th><th>缺陷率</th><th>开放预警</th></tr></thead>
              <tbody>
                ${suppliers.map((supplier) => `
                  <tr>
                    <td>${escapeHtml(supplier.supplier_id)}</td>
                    <td>${escapeHtml(formatNumber(supplier.risk_score))}</td>
                    <td>${escapeHtml(formatNumber(supplier.on_time_rate))}</td>
                    <td>${escapeHtml(formatNumber(supplier.defect_rate))}</td>
                    <td>${escapeHtml(formatNumber(supplier.open_alert_count))}</td>
                  </tr>
                `).join("")}
              </tbody>
            </table>
          `;
          return;
        }

        elements.suppliersTable.innerHTML = `
          <div class="supplier-grid">
            ${suppliers.map((supplier) => `
              <article class="supplier-card">
                <h3>${escapeHtml(supplier.supplier_id)} · ${escapeHtml(supplier.supplier_name)}</h3>
                <div class="supplier-kpi">
                  <div>风险分：${escapeHtml(formatNumber(supplier.risk_score))}</div>
                  <div>开放预警：${escapeHtml(formatNumber(supplier.open_alert_count))}</div>
                  <div>准时率：${escapeHtml(formatNumber(supplier.on_time_rate))}</div>
                  <div>违约次数：${escapeHtml(formatNumber(supplier.breach_count_30d))}</div>
                </div>
              </article>
            `).join("")}
          </div>
        `;
      }

      function renderExplanations() {
        if (!state.explanations) {
          elements.gatewayMeta.textContent = "尚未请求解释。";
          elements.dashboardExplanation.textContent = "";
          elements.gatewayNote.textContent = "即使网关暂时不可用，角色摘要和动作队列仍会继续基于规则结果工作。";
          elements.explanationsList.innerHTML = "";
          return;
        }

        const gateway = state.explanations.gateway_status || {};
        const statusParts = [
          `reachable=${gateway.reachable ? "true" : "false"}`,
          `model=${gateway.model || "-"}`,
          `base_url=${gateway.base_url || "-"}`,
        ];
        if (gateway.error) statusParts.push(`error=${gateway.error}`);
        elements.gatewayMeta.textContent = statusParts.join(" | ");
        elements.dashboardExplanation.textContent = state.explanations.dashboard_summary || "当前没有可用的摘要。";

        if (gateway.error) {
          elements.gatewayNote.textContent = "网关解释当前不可用，但角色摘要和动作队列已经切到结构化规则模式，可继续推进处理。";
        } else {
          elements.gatewayNote.textContent = "当前角色可同时结合结构化规则摘要和自然语言解释来安排动作。";
        }

        const explanations = state.explanations.alert_explanations || [];
        elements.explanationsList.innerHTML = explanations.length
          ? explanations.map((item) => `
              <article class="explanation-card">
                <div class="explanation-top">
                  <h3 class="explanation-title">${escapeHtml(item.title)}</h3>
                  <span class="risk-pill ${riskClass(item.risk_level)}">${escapeHtml(item.risk_level)}</span>
                </div>
                <p class="explanation-copy">${escapeHtml(item.explanation)}</p>
              </article>
            `).join("")
          : '<div class="empty-state">当前没有解释内容。</div>';
      }

      function renderAll() {
        renderRoleTabs();
        renderMetrics();
        renderRolePanel();
        renderSummary();
        renderAlerts();
        renderSuppliers();
        renderExplanations();
        elements.footerNote.textContent = `数据时间戳：${state.dashboard?.generated_at || "-"}`;
      }

      async function fetchJson(url, options = {}) {
        const response = await fetch(url, { headers: { "Content-Type": "application/json" }, ...options });
        if (!response.ok) throw new Error(`${response.status} ${response.statusText}`);
        return response.json();
      }

      async function refreshBoard() {
        setBusy(true);
        setStatus("正在刷新 dashboard 数据...");
        try {
          const [dashboard, alerts, suppliers] = await Promise.all([
            fetchJson("/dashboard"),
            fetchJson("/alerts/open"),
            fetchJson("/suppliers/risk"),
          ]);
          state.dashboard = dashboard;
          state.alerts = alerts;
          state.suppliers = suppliers;
          renderAll();
          setStatus("多角色看板数据已刷新。");
        } catch (error) {
          setStatus(`刷新失败：${error.message}`, true);
        } finally {
          setBusy(false);
        }
      }

      async function runDemo() {
        setBusy(true);
        setStatus("正在写入演示数据并重算预警...");
        try {
          await fetchJson("/demo/reset-and-run", { method: "POST" });
          state.explanations = null;
          await refreshBoard();
          setStatus("演示数据已加载，多角色视角已经就绪。");
        } catch (error) {
          setStatus(`演示数据加载失败：${error.message}`, true);
          setBusy(false);
        }
      }

      async function loadExplanations() {
        setBusy(true);
        setStatus("正在生成中文解释...");
        try {
          state.explanations = await fetchJson("/alerts/explanations?max_alerts=3");
          renderExplanations();
          setStatus("中文解释已更新。若网关不可用，页面仍保留结构化角色摘要。");
        } catch (error) {
          setStatus(`解释生成失败：${error.message}`, true);
        } finally {
          setBusy(false);
        }
      }

      elements.runDemo.addEventListener("click", runDemo);
      elements.refreshBoard.addEventListener("click", refreshBoard);
      elements.loadExplanations.addEventListener("click", loadExplanations);
      renderAll();
      refreshBoard();
    </script>
  </body>
</html>
"""
