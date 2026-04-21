# 基于 SAGE 的客服工单分诊系统实现计划

说明：当前这个 Demo 的“实现计划 + 实际代码结构 + 运行方式”已经统一维护在 [apps/src/sage/apps/ticket_triage/README.md](../apps/src/sage/apps/ticket_triage/README.md)。

本文现在保留为方案入口和背景说明；如果这里的内容与代码不一致，以 [apps/src/sage/apps/ticket_triage/README.md](../apps/src/sage/apps/ticket_triage/README.md) 为准。

本文给出“客服工单分诊系统”这个 Demo 的落地方案。目标不是做一个只会分类的脚本，而是做一个显式调用 SAGE 接口、具备状态管理、可扩展为 API 服务的可运行演示应用。

## 1. 目标边界

这个软件第一版只解决五件事：

1. 接收来自邮件、表单和在线聊天的工单输入。
2. 识别工单主题、业务类型和紧急程度。
3. 基于 FAQ 或历史案例推荐自动回复草案。
4. 根据规则把工单路由到对应团队或人工坐席。
5. 持续记录工单状态，输出结构化分诊结果。

第一版不做复杂前端，不直接接企业 CRM，也不追求多渠道实时接入。核心目标是把 SAGE 的以下能力演示出来：

- 数据流式处理
- 状态化工单跟踪
- 明确可解释的算子链路
- CLI Demo 和 API Demo 双形态输出

## 2. 必须调用的 SAGE 接口

这个项目必须显式调用 SAGE 接口，不能只写普通 Python 函数把结果拼起来。建议第一版固定使用以下接口。

### 2.1 核心运行时接口

```python
from sage.foundation import BatchFunction, MapFunction, SinkFunction
from sage.runtime import BaseService, LocalEnvironment
```

用途如下：

- `BatchFunction`：作为工单事件源，批量读取演示邮件、表单和聊天消息。
- `MapFunction`：实现解析、分类、打分、案例召回、路由决策、回复建议等步骤。
- `SinkFunction`：汇总分诊结果，输出控制台摘要和结构化结果。
- `BaseService`：封装工单状态仓和知识库索引，让算子通过显式服务调用读写状态。
- `LocalEnvironment`：负责组织并执行整条 SAGE workflow。

### 2.2 建议保留的服务化接口

如果后续要把 Demo 暴露给网页或外部系统，建议保持与当前仓库其他示例一致的服务层结构：

```python
from sage.runtime import LocalEnvironment
```

第一版先通过 `service.py` 封装应用服务门面，再由 FastAPI 或其他 HTTP 适配层调用服务层。也就是说，对外提供 API 没问题，但业务主干必须跑在 SAGE runtime 上，而不是绕过 SAGE 直接写控制器逻辑。

### 2.3 可选的 LLM 增强接口

如果第二版要支持更自然的自动回复或复杂工单解释，可以额外接入：

```python
from sage.serving import SageServeConfig, probe_gateway
```

用途如下：

- 使用 `SageServeConfig` 组织网关配置。
- 使用 `probe_gateway` 在启动时显式检查模型网关是否可用。
- 仅在网关检查通过时启用“自动回复润色”或“升级原因解释”。

这里要坚持 fail-fast：如果用户开启了 LLM 模式但网关不可用，直接给出明确错误，而不是静默降级。

## 3. 推荐目录结构

建议按照当前 `sage-examples/apps` 的组织方式新增一个应用目录：

```text
apps/src/sage/apps/ticket_triage/
├── __init__.py
├── models.py
├── demo_data.py
├── state_store.py
├── operators.py
├── workflow.py
├── service.py
└── README.md

examples/
└── run_ticket_triage.py

apps/tests/ticket_triage/
├── test_workflow.py
├── test_service.py
└── test_routing_rules.py
```

对应职责：

- `models.py`：定义输入工单、分类结果、路由决策、回复草案、状态快照等模型。
- `demo_data.py`：提供离线可运行的示例邮件、表单工单、聊天消息和 FAQ 数据。
- `state_store.py`：保存工单状态、历史处理记录、知识库条目和路由统计。
- `operators.py`：实现所有 SAGE 算子。
- `workflow.py`：用 `LocalEnvironment + BaseService` 组织完整链路。
- `service.py`：封装高层应用服务门面，供 CLI 或 HTTP API 调用。
- `run_ticket_triage.py`：提供统一的演示入口。

## 4. 业务对象设计

第一版建议把模型控制在 10 个以内，重点突出“输入事件 - 分诊结果 - 状态快照”三层结构。

### 4.1 输入对象

建议定义以下输入模型：

- `TicketEvent`
- `KnowledgeBaseArticle`
- `HistoricalResolution`

其中 `TicketEvent` 建议包含这些字段：

- `ticket_id`
- `channel`，例如 `email`、`form`、`chat`
- `customer_id`
- `subject`
- `message`
- `created_at`
- `attachments`
- `language`

### 4.2 中间分析对象

建议定义：

- `NormalizedTicket`
- `IntentClassification`
- `UrgencyScore`
- `SimilarCaseMatch`
- `RoutingDecision`
- `ReplyDraft`

### 4.3 输出对象

建议定义：

- `TicketTriageResult`
- `TicketStatusSnapshot`
- `TeamQueueSummary`

## 5. 状态仓设计

这个项目天然适合做成“事件流 + 状态仓”。在 `state_store.py` 里建议维护以下索引：

- 工单快照索引：按 `ticket_id`
- 客户最近工单索引：按 `customer_id`
- FAQ 与知识条目索引：按 `article_id`
- 历史案例索引：按 `intent` 或标签
- 队列统计索引：按 `assigned_team`

建议服务名：

```python
STATE_SERVICE_NAME = "ticket_triage_state"
```

建议暴露给 SAGE 算子的服务方法：

- `save_ticket_snapshot`
- `get_ticket_snapshot`
- `list_customer_recent_tickets`
- `search_knowledge_articles`
- `search_similar_resolutions`
- `append_triage_result`
- `assign_team_queue`
- `list_queue_summary`
- `build_status_snapshot`

这个设计和当前仓库里学生提分示例的模式一致：由 `BaseService` 暴露明确的状态操作，再让 `MapFunction` 通过 `call_service(...)` 调用它们。

## 6. SAGE Pipeline 设计

### 6.1 第一版主链路

建议第一版采用单链路统一处理：

```text
TicketSource
  -> NormalizeTicketStep
  -> EnrichCustomerContextStep
  -> ClassifyIntentStep
  -> ScoreUrgencyStep
  -> RecallSimilarCasesStep
  -> DecideRouteStep
  -> DraftReplyStep
  -> PersistTicketStateStep
  -> ResultSink
```

每一步职责如下：

#### `TicketSource(BatchFunction)`

- 从 `demo_data.py` 输出演示工单。
- 支持邮件、表单、聊天三种输入来源。

#### `NormalizeTicketStep(MapFunction)`

- 统一字段结构。
- 清理空白、标准化优先级关键词、提取摘要。
- 生成 `NormalizedTicket`。

#### `EnrichCustomerContextStep(MapFunction)`

- 通过 `call_service(STATE_SERVICE_NAME, ...)` 拉取用户最近工单和当前未关闭工单。
- 为后续紧急度判断补充上下文。

#### `ClassifyIntentStep(MapFunction)`

- 识别工单类型，例如账单、登录故障、物流咨询、退款申请、投诉升级。
- 第一版优先用规则和关键词实现，确保稳定。

#### `ScoreUrgencyStep(MapFunction)`

- 综合渠道、关键词、历史重复报障次数、客户等级等信息给出紧急度分数。
- 输出 `UrgencyScore` 和说明原因。

#### `RecallSimilarCasesStep(MapFunction)`

- 从 FAQ 和历史案例中召回最相似的处理记录。
- 输出 `SimilarCaseMatch` 列表。

#### `DecideRouteStep(MapFunction)`

- 根据意图类型、紧急度和相似案例决定：
  - 自动回复
  - 转 L1 客服
  - 转技术支持
  - 转财务/订单团队
  - 升级到人工主管
- 输出 `RoutingDecision`。

#### `DraftReplyStep(MapFunction)`

- 先基于模板和召回结果生成自动回复草案。
- 如果启用了 LLM 模式，再通过 SAGE serving 接口补做润色或说明生成。
- 输出 `ReplyDraft`。

#### `PersistTicketStateStep(MapFunction)`

- 通过 `call_service(STATE_SERVICE_NAME, ...)` 写回工单快照、队列归属和处理建议。
- 输出最终 `TicketTriageResult`。

#### `ResultSink(SinkFunction)`

- 收集结果对象。
- 输出结构化 JSON 和控制台摘要。

### 6.2 推荐的最小工作流骨架

建议在 `workflow.py` 里采用这种结构：

```python
from sage.foundation import MapFunction, SinkFunction
from sage.runtime import BaseService, LocalEnvironment

STATE_SERVICE_NAME = "ticket_triage_state"


class TicketTriageStateService(BaseService):
    def __init__(self, store):
        super().__init__()
        self.store = store


def run_ticket_triage(events, store):
    results = []
    environment = LocalEnvironment("customer_support_ticket_triage")
    environment.register_service(STATE_SERVICE_NAME, TicketTriageStateService, store)
    (
        environment.from_batch(events)
        .map(NormalizeTicketStep)
        .map(EnrichCustomerContextStep)
        .map(ClassifyIntentStep)
        .map(ScoreUrgencyStep)
        .map(RecallSimilarCasesStep)
        .map(DecideRouteStep)
        .map(DraftReplyStep)
        .map(PersistTicketStateStep)
        .sink(ResultCollectorSink, results=results)
    )
    environment.submit(autostop=True)
    return results
```

这段骨架要表达两个关键点：

1. 整条处理链路运行在 `LocalEnvironment` 上。
2. 状态读写必须通过 `register_service(...)` 和 `call_service(...)` 完成。

这样才算真正“调用了 SAGE 接口”。

## 7. 第一版建议实现的规则

第一版不要一开始就上复杂分类模型，先做可解释规则版。

建议优先实现以下 8 条规则：

1. 消息中出现“无法登录”“账号锁定”“支付失败”等词，优先归为高优先级故障单。
2. 消息中出现“退款”“重复扣费”“发票”时，路由到订单或财务队列。
3. 消息中出现“投诉”“升级”“立即处理”“已经等待两天”时，提高紧急度。
4. 同一客户 24 小时内重复提交相似工单时，提高一个优先级档位。
5. 命中 FAQ 且置信度高于阈值时，生成自动回复建议。
6. 未命中 FAQ 且工单复杂度高时，直接转人工。
7. 高价值客户或 SLA 临近工单优先进入人工快速通道。
8. 带附件且包含“报错截图”“账单截图”等字段时，标记为需要人工复核。

这些规则已经足够让 Demo 展示“意图识别 + 紧急度打分 + 路由决策 + 状态更新”四个核心能力。

## 8. Service 层设计

建议 `service.py` 对外只暴露少量稳定方法：

- `ingest_tickets(events)`：批量导入并执行分诊。
- `run_demo(reset=True)`：跑一组内置演示数据。
- `get_ticket(ticket_id)`：获取单个工单状态。
- `list_queue_summary()`：查看队列摘要。
- `list_open_high_priority_tickets()`：查看高优先级工单。

这个服务层负责把 CLI、HTTP API 和 workflow 解耦。CLI 或 Web 层不直接操作算子，而是统一调用应用服务。

## 9. Demo 数据设计

建议第一版准备 12 到 20 条演示工单，覆盖以下场景：

- 登录失败
- 订单延迟
- 退款申请
- 重复扣费
- 发票问题
- 技术报错
- 客诉升级
- 多轮重复催办

每类场景至少准备：

- 1 条可自动回复的简单工单
- 1 条需要转人工的复杂工单
- 1 条需要升级处理的高优先级工单

这样演示时能清楚展示不同分流路径。

## 10. 输出形态设计

第一版建议同时输出三类结果：

1. 控制台摘要：展示工单编号、意图、优先级、路由团队、回复建议。
2. JSON 结果：方便后续接 API 或前端。
3. 队列快照：展示每个团队当前待处理工单数。

输出示例可以包含：

- `ticket_id`
- `intent`
- `priority`
- `assigned_team`
- `recommended_action`
- `reply_draft`
- `reason_trace`

其中 `reason_trace` 很重要，它可以明确告诉用户为什么这个工单被判定为高优先级、为什么被路由到某个团队，这正好体现 SAGE 链路可解释的优势。

## 11. 测试计划

建议至少补三类测试：

### 11.1 Workflow 测试

- 给定一组演示工单，确认 workflow 能跑通。
- 验证结果数量、优先级和路由字段存在。

### 11.2 规则测试

- 验证关键词命中后的意图分类。
- 验证重复报障后的紧急度升级。
- 验证 FAQ 命中后的自动回复推荐。

### 11.3 Service 测试

- 验证 `run_demo()` 输出结构正确。
- 验证状态仓中能查到最新工单快照和队列汇总。

## 12. 实现顺序建议

建议按下面顺序实现：

1. 先写 `models.py` 和 `demo_data.py`，保证输入输出结构清晰。
2. 再写 `state_store.py` 和 `BaseService`，把状态操作接口固定下来。
3. 实现 `NormalizeTicketStep`、`ClassifyIntentStep`、`ScoreUrgencyStep`、`DecideRouteStep` 四个核心算子。
4. 在 `workflow.py` 中用 `LocalEnvironment` 把链路串起来。
5. 在 `service.py` 里封装对外接口。
6. 最后补 `examples/run_ticket_triage.py` 和测试。

这个顺序可以最快做出一个能跑通、能解释、能扩展的 MVP。

## 13. 第一版 MVP 验收标准

只要满足下面几点，就可以认为第一版完成：

1. 能从演示数据批量导入工单。
2. 能显式通过 SAGE workflow 完成分类、打分、路由和状态更新。
3. 能输出结构化分诊结果和队列摘要。
4. 能通过服务层重复查询工单状态。
5. 代码结构与当前 `sage-examples` 仓库模式一致。

## 14. 后续可扩展方向

第一版跑通后，可以继续扩展：

- 接入真正的 FAQ 检索或向量召回。
- 引入 LLM 自动回复润色，但仍通过 SAGE serving 接口接入。
- 增加 FastAPI 或 Web 控制台。
- 增加 SLA 计时和超时预警。
- 增加客服团队负载均衡与转派规则。

整体上，这个 Demo 很适合展示 SAGE 在“多来源输入、状态化分析、规则与模型结合、服务化输出”上的完整能力。