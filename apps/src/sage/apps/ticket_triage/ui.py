"""Chinese web UI for the ticket triage dashboard."""

from __future__ import annotations


def render_dashboard_page() -> str:
    return """<!DOCTYPE html>
<html lang="zh-CN">
  <head>
    <meta charset="utf-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1" />
    <title>SAGE 客服工单分诊看板</title>
    <style>
      :root {
        --bg: #f5ecdf;
        --panel: rgba(255, 252, 247, 0.92);
        --panel-strong: rgba(255, 255, 255, 0.94);
        --ink: #17212b;
        --muted: #5b6674;
        --line: rgba(23, 33, 43, 0.1);
        --accent: #0b6b60;
        --accent-strong: #084c44;
        --accent-soft: rgba(11, 107, 96, 0.1);
        --danger: #b42318;
        --warning: #c77d06;
        --info: #2563eb;
        --shadow: 0 24px 70px rgba(22, 25, 33, 0.12);
      }

      * { box-sizing: border-box; }

      body {
        margin: 0;
        font-family: "Avenir Next", "PingFang SC", "Microsoft YaHei", sans-serif;
        color: var(--ink);
        background:
          radial-gradient(circle at top left, rgba(11, 107, 96, 0.16), transparent 24%),
          radial-gradient(circle at right top, rgba(199, 125, 6, 0.16), transparent 20%),
          linear-gradient(180deg, #fdf9f2 0%, var(--bg) 100%);
      }

      .shell {
        max-width: 1440px;
        margin: 0 auto;
        padding: 34px 18px 60px;
      }

      .hero {
        display: grid;
        grid-template-columns: 1.25fr 0.95fr;
        gap: 18px;
        margin-bottom: 18px;
      }

      .hero-card,
      .panel {
        background: var(--panel);
        border: 1px solid var(--line);
        border-radius: 26px;
        box-shadow: var(--shadow);
        backdrop-filter: blur(14px);
      }

      .hero-card { padding: 28px; }

      .eyebrow {
        margin: 0 0 10px;
        font-size: 12px;
        letter-spacing: 0.16em;
        text-transform: uppercase;
        color: var(--accent-strong);
      }

      h1 {
        margin: 0;
        font-size: clamp(34px, 5vw, 60px);
        line-height: 0.95;
        letter-spacing: -0.05em;
      }

      .hero-copy {
        margin: 16px 0 0;
        max-width: 58ch;
        color: var(--muted);
        line-height: 1.7;
      }

      .action-panel {
        display: flex;
        flex-direction: column;
        gap: 16px;
        padding: 24px;
      }

      .action-row,
      .input-row {
        display: flex;
        flex-wrap: wrap;
        gap: 10px;
      }

      button,
      input,
      select,
      textarea {
        font: inherit;
      }

      button {
        border: 0;
        border-radius: 999px;
        padding: 12px 18px;
        cursor: pointer;
        transition: transform 140ms ease, opacity 140ms ease;
      }

      button:hover { transform: translateY(-1px); }
      button:disabled { opacity: 0.6; cursor: wait; transform: none; }
      .primary { background: var(--accent); color: white; }
      .secondary { background: var(--accent-soft); color: var(--accent-strong); }
      .ghost { background: rgba(23, 33, 43, 0.06); color: var(--ink); }

      .status-line {
        min-height: 24px;
        color: var(--muted);
        font-size: 14px;
      }

      .status-line.error { color: var(--danger); }

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

      .metric-card,
      .panel {
        padding: 20px;
      }

      .metric-card {
        background: var(--panel-strong);
        border-radius: 22px;
        border: 1px solid rgba(23, 33, 43, 0.08);
      }

      .metric-label {
        color: var(--muted);
        font-size: 13px;
      }

      .metric-value {
        margin-top: 12px;
        font-size: clamp(25px, 3.8vw, 38px);
        font-weight: 700;
        letter-spacing: -0.05em;
        overflow-wrap: anywhere;
        word-break: break-word;
        line-height: 1.05;
      }

      .metric-value.compact {
        font-size: clamp(18px, 2.6vw, 28px);
        letter-spacing: -0.03em;
        line-height: 1.15;
      }

      .section-title {
        display: flex;
        align-items: center;
        justify-content: space-between;
        gap: 14px;
        margin-bottom: 14px;
      }

      .section-title h2,
      .panel h2,
      .panel h3 {
        margin: 0;
        letter-spacing: -0.03em;
      }

      .section-copy {
        color: var(--muted);
        line-height: 1.7;
        margin: 8px 0 0;
      }

      .summary-panel { grid-column: span 4; }
      .queue-panel { grid-column: span 4; }
      .detail-panel { grid-column: span 4; }
      .results-panel { grid-column: span 8; }
      .priority-panel { grid-column: span 4; }
      .composer-panel { grid-column: 1 / -1; }

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

      .empty-state,
      .muted {
        color: var(--muted);
        line-height: 1.7;
      }

      .list {
        display: grid;
        gap: 12px;
      }

      .list-card {
        border-radius: 18px;
        padding: 16px;
        background: var(--panel-strong);
        border: 1px solid rgba(23, 33, 43, 0.08);
      }

      .list-head {
        display: flex;
        align-items: flex-start;
        justify-content: space-between;
        gap: 12px;
      }

      .pill {
        border-radius: 999px;
        padding: 6px 10px;
        font-size: 12px;
        font-weight: 600;
      }

      .pill.high { background: rgba(199, 125, 6, 0.12); color: var(--warning); }
      .pill.critical { background: rgba(180, 35, 24, 0.12); color: var(--danger); }
      .pill.medium { background: rgba(37, 99, 235, 0.12); color: var(--info); }
      .pill.low { background: rgba(11, 107, 96, 0.12); color: var(--accent-strong); }

      .meta {
        margin-top: 8px;
        color: var(--muted);
        font-size: 14px;
      }

      .reason-list,
      .detail-list {
        margin: 12px 0 0;
        padding-left: 18px;
        color: var(--muted);
      }

      .reason-list li + li,
      .detail-list li + li { margin-top: 8px; }

      .two-col {
        display: grid;
        grid-template-columns: repeat(2, minmax(0, 1fr));
        gap: 12px;
      }

      .field {
        display: grid;
        gap: 8px;
      }

      label {
        font-size: 13px;
        color: var(--muted);
      }

      input,
      select,
      textarea {
        width: 100%;
        border-radius: 16px;
        border: 1px solid rgba(23, 33, 43, 0.12);
        background: rgba(255, 255, 255, 0.86);
        padding: 12px 14px;
        color: var(--ink);
      }

      textarea {
        min-height: 120px;
        resize: vertical;
      }

      .table {
        width: 100%;
        border-collapse: collapse;
      }

      .table th,
      .table td {
        text-align: left;
        padding: 12px 10px;
        border-bottom: 1px solid rgba(23, 33, 43, 0.08);
        vertical-align: top;
      }

      .table th {
        font-size: 13px;
        color: var(--muted);
        font-weight: 600;
      }

      .clickable {
        color: var(--accent-strong);
        cursor: pointer;
        font-weight: 600;
      }

      .clickable:hover { text-decoration: underline; }

      @media (max-width: 1120px) {
        .hero,
        .metrics,
        .two-col,
        .summary-panel,
        .queue-panel,
        .detail-panel,
        .results-panel,
        .priority-panel,
        .composer-panel {
          grid-template-columns: 1fr;
          grid-column: 1 / -1;
        }

        .metrics {
          display: grid;
          grid-template-columns: repeat(2, minmax(0, 1fr));
        }
      }

      @media (max-width: 720px) {
        .metrics { grid-template-columns: 1fr; }
        .hero { grid-template-columns: 1fr; }
        .table { display: block; overflow-x: auto; }
      }
    </style>
  </head>
  <body>
    <div class="shell">
      <section class="hero">
        <div class="hero-card">
          <p class="eyebrow">SAGE Ticket Triage</p>
          <h1>客服工单分诊看板</h1>
          <p class="hero-copy">
            这个界面把工单分诊的规则链路、队列分布、优先级结果和单票明细串到同一个中文页面里，适合做 Demo 演示、接口联调和值班排查。
          </p>
          <div class="chip-row">
            <span class="chip">显式 SAGE workflow</span>
            <span class="chip">状态化工单跟踪</span>
            <span class="chip">中文可解释分诊</span>
          </div>
        </div>
        <div class="hero-card action-panel">
          <div>
            <div class="section-title">
              <h2>操作区</h2>
            </div>
            <p class="section-copy">先加载演示工单，再刷新看板；如果要验证自定义场景，可以直接在页面底部提交单条工单。</p>
          </div>
          <div class="action-row">
            <button id="load-demo" class="primary">加载演示数据</button>
            <button id="refresh-dashboard" class="secondary">刷新看板</button>
            <button id="load-ticket" class="ghost">查询工单</button>
          </div>
          <div class="input-row">
            <input id="ticket-search" placeholder="输入工单编号，例如 T-1001" />
          </div>
          <div id="status-line" class="status-line">等待操作。</div>
        </div>
      </section>

      <section class="grid">
        <div id="metrics" class="metrics"></div>

        <div class="panel summary-panel">
          <div class="section-title">
            <h2>看板摘要</h2>
          </div>
          <div id="dashboard-summary" class="empty-state">还没有加载数据。</div>
        </div>

        <div class="panel queue-panel">
          <div class="section-title">
            <h2>队列分布</h2>
          </div>
          <div id="queue-list" class="list">
            <div class="empty-state">加载演示数据后，这里会显示各队列的工单负载。</div>
          </div>
        </div>

        <div class="panel detail-panel">
          <div class="section-title">
            <h2>工单详情</h2>
          </div>
          <div id="ticket-detail" class="empty-state">请输入工单编号，或点击下方结果列表中的工单编号。</div>
        </div>

        <div class="panel results-panel">
          <div class="section-title">
            <h2>最近分诊结果</h2>
          </div>
          <div id="result-table-wrap" class="empty-state">暂时没有分诊结果。</div>
        </div>

        <div class="panel priority-panel">
          <div class="section-title">
            <h2>高优先级工单</h2>
          </div>
          <div id="priority-list" class="list">
            <div class="empty-state">暂无高优先级工单。</div>
          </div>
        </div>

        <div class="panel composer-panel">
          <div class="section-title">
            <div>
              <h2>提交单条工单</h2>
              <p class="section-copy">可以直接在页面里模拟一条新工单，验证分类、优先级和队列路由结果。</p>
            </div>
          </div>
          <form id="ticket-form">
            <div class="two-col">
              <div class="field">
                <label for="ticket-id">工单编号</label>
                <input id="ticket-id" name="ticket_id" placeholder="例如 T-CUSTOM-001" />
              </div>
              <div class="field">
                <label for="customer-id">客户编号</label>
                <input id="customer-id" name="customer_id" placeholder="例如 CUST-DEMO-1" />
              </div>
              <div class="field">
                <label for="channel">渠道</label>
                <select id="channel" name="channel">
                  <option value="email">email</option>
                  <option value="form">form</option>
                  <option value="chat">chat</option>
                </select>
              </div>
              <div class="field">
                <label for="customer-tier">客户等级</label>
                <select id="customer-tier" name="customer_tier">
                  <option value="standard">standard</option>
                  <option value="vip">vip</option>
                  <option value="enterprise">enterprise</option>
                </select>
              </div>
            </div>
            <div class="field" style="margin-top: 12px;">
              <label for="subject">主题</label>
              <input id="subject" name="subject" placeholder="例如 无法登录系统" />
            </div>
            <div class="field" style="margin-top: 12px;">
              <label for="message">工单内容</label>
              <textarea id="message" name="message" placeholder="请输入工单正文，例如：账号锁定导致无法登录，已经等待两天。"></textarea>
            </div>
            <div class="field" style="margin-top: 12px;">
              <label for="attachments">附件列表（可选，用逗号分隔）</label>
              <input id="attachments" name="attachments" placeholder="例如 error.png,bill.png" />
            </div>
            <div class="action-row" style="margin-top: 14px;">
              <button type="submit" class="primary">提交并分诊</button>
              <button type="button" id="fill-sample" class="ghost">填充示例</button>
            </div>
          </form>
        </div>
      </section>
    </div>

    <script>
      const statusLine = document.getElementById('status-line');
      const metricsEl = document.getElementById('metrics');
      const dashboardSummaryEl = document.getElementById('dashboard-summary');
      const queueListEl = document.getElementById('queue-list');
      const resultWrapEl = document.getElementById('result-table-wrap');
      const priorityListEl = document.getElementById('priority-list');
      const detailEl = document.getElementById('ticket-detail');
      const ticketSearchEl = document.getElementById('ticket-search');
      const ticketFormEl = document.getElementById('ticket-form');

      function setStatus(message, isError = false) {
        statusLine.textContent = message;
        statusLine.className = isError ? 'status-line error' : 'status-line';
      }

      function escapeHtml(value) {
        return String(value ?? '')
          .replaceAll('&', '&amp;')
          .replaceAll('<', '&lt;')
          .replaceAll('>', '&gt;')
          .replaceAll('"', '&quot;');
      }

      function priorityClass(priority) {
        return ['critical', 'high', 'medium', 'low'].includes(priority) ? priority : 'low';
      }

      function formatTeamName(teamName) {
        const mapping = {
          technical_support: '技术支持',
          billing_ops: '财务与订单',
          order_ops: '履约运营',
          duty_manager: '值班主管',
          l1_support: '一线客服',
        };
        return mapping[teamName] || teamName || '暂无';
      }

      function formatPriority(priority) {
        const mapping = {
          critical: '紧急',
          high: '高',
          medium: '中',
          low: '低',
        };
        return mapping[priority] || priority;
      }

      function formatMetricValue(value) {
        if (typeof value === 'number') {
          return { text: String(value), compact: false };
        }
        const text = String(value ?? '暂无');
        return {
          text: text.includes('_') ? formatTeamName(text) : text,
          compact: text.length > 8 || text.includes('_'),
        };
      }

      function renderMetrics(summary) {
        const cards = [
          ['工单总数', summary.total_ticket_count],
          ['高优先级', summary.high_priority_count],
          ['自动回复候选', summary.auto_reply_count],
          ['升级工单', summary.escalated_count],
          ['队列数量', summary.queue_count],
          ['最繁忙队列', summary.busiest_queue || '暂无'],
        ];
        metricsEl.innerHTML = cards
          .map(([label, value]) => {
            const resolved = formatMetricValue(value);
            return `
            <div class="metric-card">
              <div class="metric-label">${escapeHtml(label)}</div>
              <div class="metric-value ${resolved.compact ? 'compact' : ''}">${escapeHtml(resolved.text)}</div>
            </div>
          `;
          })
          .join('');
      }

      function renderSummary(summary) {
        const intentChips = Object.entries(summary.intent_distribution || {})
          .sort((a, b) => b[1] - a[1])
          .map(([intent, count]) => `<span class="chip">${escapeHtml(intent)}: ${count}</span>`)
          .join('');
        dashboardSummaryEl.innerHTML = `
          <p class="muted">
            当前共有 <strong>${summary.total_ticket_count}</strong> 张工单，
            其中高优先级 <strong>${summary.high_priority_count}</strong> 张，
            可自动回复 <strong>${summary.auto_reply_count}</strong> 张，
            升级处理 <strong>${summary.escalated_count}</strong> 张。
          </p>
          <p class="muted">
            当前最繁忙队列为 <strong>${escapeHtml(formatTeamName(summary.busiest_queue || '暂无'))}</strong>，
            最近处理的工单为 <strong>${escapeHtml(summary.latest_ticket_id || '暂无')}</strong>。
          </p>
          <div class="chip-row">${intentChips || '<span class="empty-state">暂无意图分布数据。</span>'}</div>
        `;
      }

      function renderQueues(queues) {
        if (!queues.length) {
          queueListEl.innerHTML = '<div class="empty-state">暂无队列数据。</div>';
          return;
        }
        queueListEl.innerHTML = queues.map((queue) => `
          <div class="list-card">
            <div class="list-head">
              <div>
                <h3>${escapeHtml(formatTeamName(queue.team_name))}</h3>
                <div class="meta">开放工单 ${queue.open_ticket_count}，高优先级 ${queue.high_priority_count}，自动回复候选 ${queue.auto_reply_candidate_count}</div>
              </div>
            </div>
          </div>
        `).join('');
      }

      function renderResults(results) {
        if (!results.length) {
          resultWrapEl.innerHTML = '<div class="empty-state">暂无分诊结果。</div>';
          return;
        }
        resultWrapEl.innerHTML = `
          <table class="table">
            <thead>
              <tr>
                <th>工单</th>
                <th>意图</th>
                <th>优先级</th>
                <th>队列</th>
                <th>动作</th>
                <th>自动回复</th>
              </tr>
            </thead>
            <tbody>
              ${results.map((item) => `
                <tr>
                  <td><span class="clickable" data-ticket-id="${escapeHtml(item.ticket_id)}">${escapeHtml(item.ticket_id)}</span></td>
                  <td>${escapeHtml(item.intent)}</td>
                  <td><span class="pill ${priorityClass(item.priority)}">${escapeHtml(formatPriority(item.priority))}</span></td>
                  <td>${escapeHtml(formatTeamName(item.assigned_team))}</td>
                  <td>${escapeHtml(item.recommended_action)}</td>
                  <td>${item.auto_reply ? '是' : '否'}</td>
                </tr>
              `).join('')}
            </tbody>
          </table>
        `;
        resultWrapEl.querySelectorAll('[data-ticket-id]').forEach((element) => {
          element.addEventListener('click', () => loadTicketDetail(element.dataset.ticketId));
        });
      }

      function renderPriorityList(tickets) {
        if (!tickets.length) {
          priorityListEl.innerHTML = '<div class="empty-state">暂无高优先级工单。</div>';
          return;
        }
        priorityListEl.innerHTML = tickets.map((ticket) => `
          <div class="list-card">
            <div class="list-head">
              <div>
                <h3><span class="clickable" data-ticket-id="${escapeHtml(ticket.ticket_id)}">${escapeHtml(ticket.ticket_id)}</span></h3>
                <div class="meta">${escapeHtml(ticket.intent)} · ${escapeHtml(formatTeamName(ticket.assigned_team))} · ${escapeHtml(ticket.recommended_action)}</div>
              </div>
              <span class="pill ${priorityClass(ticket.priority)}">${escapeHtml(formatPriority(ticket.priority))}</span>
            </div>
          </div>
        `).join('');
        priorityListEl.querySelectorAll('[data-ticket-id]').forEach((element) => {
          element.addEventListener('click', () => loadTicketDetail(element.dataset.ticketId));
        });
      }

      function renderTicketDetail(ticket) {
        detailEl.innerHTML = `
          <div class="list-card">
            <div class="list-head">
              <div>
                <h3>${escapeHtml(ticket.ticket_id)}</h3>
                <div class="meta">${escapeHtml(ticket.intent)} · ${escapeHtml(formatPriority(ticket.priority))} · ${escapeHtml(formatTeamName(ticket.assigned_team))}</div>
              </div>
              <span class="pill ${priorityClass(ticket.priority)}">${escapeHtml(formatPriority(ticket.priority))}</span>
            </div>
            <ul class="detail-list">
              <li>渠道：${escapeHtml(ticket.channel)}</li>
              <li>状态：${escapeHtml(ticket.status)}</li>
              <li>建议动作：${escapeHtml(ticket.recommended_action)}</li>
              <li>自动回复：${ticket.auto_reply ? '是' : '否'}</li>
              <li>最后更新时间：${escapeHtml(ticket.last_updated)}</li>
            </ul>
            <div class="meta">原因链路</div>
            <ul class="reason-list">
              ${(ticket.reason_trace || []).map((reason) => `<li>${escapeHtml(reason)}</li>`).join('') || '<li>暂无解释链。</li>'}
            </ul>
          </div>
        `;
      }

      async function fetchJson(url, options = {}) {
        const response = await fetch(url, options);
        if (!response.ok) {
          let detail = `${response.status} ${response.statusText}`;
          try {
            const payload = await response.json();
            detail = payload.detail || JSON.stringify(payload);
          } catch {
            detail = await response.text();
          }
          throw new Error(detail || '请求失败');
        }
        return response.json();
      }

      async function refreshDashboard() {
        setStatus('正在刷新看板...');
        try {
          const [summary, queues, results, highPriority] = await Promise.all([
            fetchJson('/dashboard'),
            fetchJson('/queues'),
            fetchJson('/tickets'),
            fetchJson('/tickets/high-priority'),
          ]);
          renderMetrics(summary);
          renderSummary(summary);
          renderQueues(queues);
          renderResults(results);
          renderPriorityList(highPriority);
          setStatus('看板已刷新。');
        } catch (error) {
          setStatus(`刷新失败：${error.message}`, true);
        }
      }

      async function loadDemo() {
        setStatus('正在加载演示数据...');
        try {
          const result = await fetchJson('/demo/reset-and-run', { method: 'POST' });
          await refreshDashboard();
          setStatus(`已加载演示数据，共处理 ${result.processed_event_count} 张工单。`);
        } catch (error) {
          setStatus(`加载失败：${error.message}`, true);
        }
      }

      async function loadTicketDetail(ticketId) {
        const resolvedTicketId = (ticketId || ticketSearchEl.value || '').trim();
        if (!resolvedTicketId) {
          setStatus('请输入工单编号。', true);
          return;
        }
        setStatus(`正在查询工单 ${resolvedTicketId} ...`);
        try {
          const ticket = await fetchJson(`/tickets/${encodeURIComponent(resolvedTicketId)}`);
          ticketSearchEl.value = resolvedTicketId;
          renderTicketDetail(ticket);
          setStatus(`工单 ${resolvedTicketId} 已加载。`);
        } catch (error) {
          setStatus(`查询失败：${error.message}`, true);
        }
      }

      function buildTicketPayload(formData) {
        const now = new Date().toISOString().slice(0, 19);
        const attachments = String(formData.get('attachments') || '')
          .split(',')
          .map((item) => item.trim())
          .filter(Boolean);
        return {
          ticket_id: String(formData.get('ticket_id') || '').trim() || `T-CUSTOM-${Date.now()}`,
          customer_id: String(formData.get('customer_id') || '').trim() || `CUST-${Date.now()}`,
          channel: String(formData.get('channel') || 'email'),
          customer_tier: String(formData.get('customer_tier') || 'standard'),
          subject: String(formData.get('subject') || '').trim(),
          message: String(formData.get('message') || '').trim(),
          attachments,
          created_at: now,
          language: 'zh',
        };
      }

      async function submitTicket(event) {
        event.preventDefault();
        const payload = buildTicketPayload(new FormData(ticketFormEl));
        if (!payload.subject || !payload.message) {
          setStatus('请至少填写主题和工单内容。', true);
          return;
        }
        setStatus(`正在提交工单 ${payload.ticket_id} ...`);
        try {
          const result = await fetchJson('/tickets/ingest', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify([payload]),
          });
          await refreshDashboard();
          if (result.triage_results && result.triage_results.length > 0) {
            await loadTicketDetail(result.triage_results[0].ticket_id);
          }
          setStatus(`工单 ${payload.ticket_id} 已提交并完成分诊。`);
        } catch (error) {
          setStatus(`提交失败：${error.message}`, true);
        }
      }

      function fillSampleTicket() {
        document.getElementById('ticket-id').value = `T-CUSTOM-${Date.now()}`;
        document.getElementById('customer-id').value = 'CUST-DEMO-UI';
        document.getElementById('channel').value = 'chat';
        document.getElementById('customer-tier').value = 'vip';
        document.getElementById('subject').value = '支付失败后重复扣费';
        document.getElementById('message').value = '系统提示支付失败，但银行卡被扣了两次，请尽快退款处理。';
        document.getElementById('attachments').value = 'payment-screenshot.png';
        setStatus('已填充一条示例工单。');
      }

      document.getElementById('load-demo').addEventListener('click', loadDemo);
      document.getElementById('refresh-dashboard').addEventListener('click', refreshDashboard);
      document.getElementById('load-ticket').addEventListener('click', () => loadTicketDetail());
      document.getElementById('fill-sample').addEventListener('click', fillSampleTicket);
      ticketFormEl.addEventListener('submit', submitTicket);

      refreshDashboard();
    </script>
  </body>
</html>
"""