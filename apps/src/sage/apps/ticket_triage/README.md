# 客服工单分诊 MVP

这个应用是一个基于 SAGE 构建的、可直接运行的客服工单分诊 Demo。

这份 README 是当前唯一的事实来源，同时覆盖实现计划和仓库中已经落地的代码。`docs` 目录下的规划文档现在只保留为入口说明，不应该再和这里的内容分叉。

## 目标

这个 MVP 主要聚焦五件事：

1. 从邮件、表单和在线聊天导入工单
1. 识别工单意图和紧急程度
1. 召回 FAQ 和历史处理案例
1. 将工单路由到合适的支持队列
1. 持久化工单状态，支持后续查询

这个 Demo 的目标不是简单打印分类结果，而是要求整条业务链路真正运行在 SAGE runtime 上，并通过显式的算子和状态服务来组织执行。

## 必须调用的 SAGE 接口

当前 MVP 显式使用了这些 SAGE 接口：

```python
from sage.foundation import BatchFunction, MapFunction, SinkFunction
from sage.runtime import BaseService, LocalEnvironment
```

在这个 Demo 里，它们的职责分别是：

- `BatchFunction`：把工单事件送入工作流
- `MapFunction`：完成标准化、分类、紧急度评分、召回、路由和持久化
- `SinkFunction`：收集最终分诊结果
- `BaseService`：向工作流节点暴露状态仓操作
- `LocalEnvironment`：构建并执行工单分诊 pipeline

这意味着这个应用并不是一个普通 Python 脚本外面套一层包名，而是明确围绕 SAGE workflow 执行路径来实现的。

## 当前结构

仓库中的实际代码结构如下：

```text
apps/src/sage/apps/ticket_triage/
├── __init__.py
├── README.md
├── demo_data.py
├── models.py
├── operators.py
├── service.py
├── state_store.py
└── workflow.py

examples/
└── run_ticket_triage.py

apps/tests/ticket_triage/
├── test_api.py
├── test_routing_rules.py
├── test_service.py
└── test_workflow.py
```

各文件职责如下：

- `models.py`：定义工单、FAQ、历史案例、分诊结果、队列摘要和状态快照等模型
- `demo_data.py`：提供演示工单、FAQ 条目、历史案例和统计摘要
- `state_store.py`：带可选 JSON 持久化的内存状态仓
- `operators.py`：实现 SAGE 的 source、map、sink 算子以及具体分诊规则
- `workflow.py`：负责 `LocalEnvironment` 编排和 `BaseService` 注册
- `service.py`：应用服务门面，以及可选的 FastAPI 适配层
- `ui.py`：中文浏览器看板页面，负责把 API 结果渲染成演示界面
- `examples/run_ticket_triage.py`：CLI 演示入口
- `tests/ticket_triage`：覆盖 workflow、service、路由规则和 API 的定向测试

## Workflow 设计

当前实现的 pipeline 如下：

```text
DemoTicketSource
	-> NormalizeTicketStep
	-> EnrichCustomerContextStep
	-> ClassifyIntentStep
	-> ScoreUrgencyStep
	-> RecallSimilarCasesStep
	-> DecideRouteStep
	-> DraftReplyStep
	-> PersistTicketStateStep
	-> ResultCollectorSink
```

代码映射关系如下：

- workflow 的 source 和整体编排在 `workflow.py`
- 每个步骤的具体实现都在 `operators.py`
- 状态服务的注册在 `workflow.py` 中通过 `TicketTriageStateService` 完成
- workflow 节点中的状态访问通过 `call_service` 完成，而不是直接修改状态仓对象

这部分是整个设计里最关键的点，因为它保证这个 Demo 真正在展示 SAGE runtime 的使用方式，而不是只是借了包路径。

## 已实现的状态模型

当前状态仓维护了四类数据：

- 参考 FAQ 条目
- 历史处理案例
- 按工单维度保存的状态快照
- 最终分诊结果

当前暴露给 workflow 的关键服务方法包括：

- `load_reference_data`
- `save_ticket_snapshot`
- `get_ticket_snapshot`
- `build_status_snapshot`
- `list_customer_recent_tickets`
- `search_knowledge_articles`
- `search_similar_resolutions`
- `append_triage_result`
- `assign_team_queue`
- `list_queue_summary`
- `list_open_high_priority_tickets`

这个实现和最初计划在方向上保持一致，同时规模也足够小，适合作为 MVP。

## 已实现的规则

当前 MVP 使用的是显式、可解释的规则，而不是训练好的分类模型。

已经支持的意图类别：

- `login_issue`
- `refund_request`
- `invoice_issue`
- `order_delay`
- `technical_support`
- `complaint_escalation`
- `general_inquiry`

已经实现的紧急度信号：

- 故障类或技术类关键词会提高分数
- 退款和投诉类场景会更激进地提高分数
- “等待中”“升级”“立即处理”等紧急措辞会提高分数
- 同一客户重复提交工单会提高分数
- `vip` 和 `enterprise` 客户会提高分数
- 带附件的工单会提高分数，因为通常意味着需要人工复核
- `chat` 渠道会有一个小幅加分，因为它天然带有即时响应压力

已经实现的路由行为：

- 投诉升级或 `critical` 优先级直接路由到 `duty_manager`
- 退款和发票问题路由到 `billing_ops`
- 订单延迟路由到 `order_ops`
- 登录和技术问题路由到 `technical_support`
- FAQ 高匹配且优先级较低时，可以触发自动回复

## 已实现内容与规划内容的区别

当前已经完成的内容：

- CLI 演示入口
- 工单状态持久化
- FAQ 与历史案例召回
- 队列摘要查询
- workflow、service、路由规则和 API 的定向测试
- `service.py` 中的可选 FastAPI app factory

尚未实现、但仍在规划中的内容：

- 真正的外部 FAQ 检索或向量召回
- 通过 `sage.serving` 实现的 LLM 自动回复润色
- 更完整的 HTTP 或 Web dashboard 层
- SLA 计时器和超时预警
- 客服团队间的负载均衡

这里需要明确区分，因为最初的规划文档里还包含了后续阶段能力。那些能力仍然是有效的路线图，但并不在当前代码路径里。

## 怎么读代码

如果你想快速理解实现，建议按下面顺序读：

1. `examples/run_ticket_triage.py`
1. `service.py`
1. `workflow.py`
1. `operators.py`
1. `state_store.py`
1. `demo_data.py`
1. `models.py`

这个顺序和真实执行路径是一致的：

- runner 创建应用服务
- service 加载演示数据并调用 `ingest_tickets`
- workflow 构建 `LocalEnvironment` 并注册 `TicketTriageStateService`
- 各个 operator 逐步转换工单数据
- state store 最终持久化快照和队列状态

如果你只想回答某一类问题，也可以按这个入口顺序中途停下：

- 如果你想看 SAGE 是怎么被调用的，读到 `workflow.py` 就够了
- 如果你想看为什么某个工单被分类或路由成这样，直接看 `operators.py`
- 如果你想看状态是怎么存和怎么查的，就看 `state_store.py`

## 基于断点的调试方式

想理解这个 Demo，最稳的方式不是先看最终 JSON，而是顺着数据流打断点。

推荐断点顺序：

1. `examples/run_ticket_triage.py` 里的 `main`
1. `service.py` 里的 `run_demo` 和 `ingest_tickets`
1. `workflow.py` 里的 `ingest_tickets`
1. `NormalizeTicketStep` 里的 `execute`
1. `ClassifyIntentStep` 里的 `execute`
1. `ScoreUrgencyStep` 里的 `execute`
1. `DecideRouteStep` 里的 `execute`
1. `PersistTicketStateStep` 里的 `execute`
1. `state_store.py` 里的 `save_ticket_snapshot`

每一步建议重点看这些数据：

- 在 `NormalizeTicketStep`：确认原始 `TicketEvent` 和生成的 `normalized_text`
- 在 `ClassifyIntentStep`：看 `recent_tickets`、命中的关键词和最终意图
- 在 `ScoreUrgencyStep`：看哪些规则参与了打分，以及最终优先级是怎么出来的
- 在 `DecideRouteStep`：看最终决策主要来自意图、紧急度，还是 FAQ 匹配强度
- 在 `PersistTicketStateStep`：看最终的 `reason_trace`，它就是结果解释链
- 在 `save_ticket_snapshot`：看真正被持久化下来的快照内容

这样你就能根据运行时状态变化一步步推导出结果：

```text
输入工单
	-> 标准化文本
	-> 命中的意图关键词
	-> 紧急度原因与分数
	-> 路由决策
	-> 持久化快照
	-> 最终结果
```

如果你发现结果不对，不要先拿最终标签去硬比。先判断是哪个 operator 第一次把结果带偏了。在这个 Demo 里，通常会落在这三个位置之一：

- `ClassifyIntentStep`：关键词重叠太弱或太宽，导致意图选错
- `ScoreUrgencyStep`：分数被推到了错误的优先级档位
- `DecideRouteStep`：意图和紧急度组合是对的，但路由决策不符合预期

## 运行方式

在仓库根目录执行：

```bash
python examples/run_ticket_triage.py
```

如果你想看结构化输出：

```bash
python examples/run_ticket_triage.py --json
```

如果你想把状态落盘：

```bash
python examples/run_ticket_triage.py --storage-path .sage/ticket-triage-state.json
```

## API

在仓库根目录启动 FastAPI 服务：

```bash
python examples/run_ticket_triage_api.py
```

自定义 host 和 port：

```bash
python examples/run_ticket_triage_api.py --host 0.0.0.0 --port 8020
```

如果你想在 API 模式下持久化状态：

```bash
python examples/run_ticket_triage_api.py --storage-path .sage/ticket-triage-state.json
```

当前可用路由：

- `GET /docs`
- `GET /redoc`
- `GET /openapi.json`
- `GET /`
- `GET /health`
- `GET /dashboard`
- `GET /dashboard/ui`
- `GET /tickets`
- `POST /tickets/ingest`
- `GET /tickets/high-priority`
- `GET /tickets/{ticket_id}`
- `GET /queues`
- `POST /demo/reset-and-run`

## 浏览器与 Swagger

启动 API 服务后，最直接的浏览器入口是：

- `http://127.0.0.1:8010/`
- `http://127.0.0.1:8010/dashboard/ui`
- `http://127.0.0.1:8010/docs`
- `http://127.0.0.1:8010/redoc`

推荐的使用顺序：

1. 如果是对外演示，优先打开 `/dashboard/ui`
1. 点击“加载演示数据”按钮，把演示工单写入状态仓
1. 查看顶部指标卡、队列分布和高优先级工单列表
1. 点击结果列表中的工单编号，查看单票详情和原因链路
1. 如果要模拟新场景，可以在页面底部直接提交一条自定义工单

Swagger 使用说明：

- `/docs` 最适合直接在浏览器里交互式试接口
- `/redoc` 更适合整体浏览 API 文档结构
- `/openapi.json` 适合导入到其他工具里使用
- `/dashboard/ui` 更适合做中文演示和业务讲解

如果某个路由返回的数据不符合预期，不要只盯着响应体猜。保留浏览器页面，同时回到 workflow 路径里调试会更快。对这个 Demo 来说，最快的方式仍然是：

1. 先确定是哪一个请求载荷导致了错误结果
1. 在 `ClassifyIntentStep`、`ScoreUrgencyStep` 和 `DecideRouteStep` 上打断点
1. 用同一个请求重新跑一遍，观察哪一步开始偏离预期

推荐的 API 演示顺序：

1. 调用 `POST /demo/reset-and-run`，加载演示数据并生成分诊结果
1. 调用 `GET /dashboard`，查看整体摘要指标
1. 调用 `GET /queues`，查看队列分布
1. 调用 `GET /tickets`，查看全部分诊结果
1. 调用 `GET /tickets/high-priority`，查看高优先级工单
1. 调用 `GET /tickets/T-1001`，查看一个具体工单的持久化快照

## 测试

在 `apps` 目录下执行：

```bash
pytest tests/ticket_triage/test_workflow.py tests/ticket_triage/test_service.py tests/ticket_triage/test_routing_rules.py tests/ticket_triage/test_api.py
```

## 相关文件

- 示例运行入口：`../../../../../../examples/run_ticket_triage.py`
- 规划入口文档：`../../../../../../docs/customer-support-ticket-triage-plan.md`

如果这个应用继续演进，优先更新这份 README，再去同步相关的规划文档。
