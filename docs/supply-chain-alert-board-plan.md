# 基于 SAGE 的供应链异常预警看板实现计划

本文给出“供应链异常预警看板”这个 Demo 的落地方案，重点不是只做一个静态报表，而是做一个真正基于 SAGE 数据流和状态服务的可运行演示应用。

## 1. 目标边界

这个软件第一版只解决四件事：

1. 接收供应链事件数据。
1. 识别订单、库存、物流、供应商履约中的异常。
1. 评估异常对订单履约和库存安全的影响。
1. 生成看板摘要、风险预警和处置建议。

第一版不追求真实 ERP 对接，不做复杂前端，也不做企业级权限系统。核心目标是把 SAGE 的以下能力演示出来：

- 数据流处理
- 状态化分析
- 明确的可解释算子链路
- 可扩展为 API 服务

## 2. 必须调用的 SAGE 接口

这个项目必须显式调用 SAGE 接口，不能只写普通 Python 脚本后把结果打印出来。建议第一版固定使用以下接口：

### 2.1 核心运行时接口

```python
from sage.foundation import BatchFunction, MapFunction, SinkFunction
from sage.runtime import BaseService, LocalEnvironment
```

用途如下：

- `BatchFunction`：作为事件源，批量读取演示订单、库存、物流、供应商数据。
- `MapFunction`：实现清洗、异常检测、影响评估、处置建议等处理步骤。
- `SinkFunction`：收集预警结果和看板快照。
- `BaseService`：挂载状态仓服务，给各个算子读写共享业务状态。
- `LocalEnvironment`：组织并执行整条 SAGE pipeline。

### 2.2 可选的扩展运行时接口

```python
from sage.runtime import FlowNetEnvironment
```

用途如下：

- 第二版或第三版需要模拟更高吞吐量时，再把本地运行切到 FlowNet-first 的分布式模式。
- 第一版建议不要直接上分布式，先用 `LocalEnvironment` 把链路跑通。

### 2.3 可选的 SAGE 网关接口

如果要做 LLM 增强版的异常解释或处置建议，可以接入：

```python
from sage.serving import SageServeConfig, probe_gateway
```

用途如下：

- 先用 `SageServeConfig` 生成网关配置。
- 再用 `probe_gateway` 探测外部 OpenAI-compatible 网关是否可用。
- 网关健康时，再启用“风险解释生成”或“采购协调建议生成”。

也就是说，这个应用的主干一定是 SAGE runtime；LLM 只是挂在后面的增强能力。

## 3. 推荐目录结构

建议按照当前 `sage-examples/apps` 里的模式落地到一个新应用目录：

```text
apps/src/sage/apps/supply_chain_alert/
├── __init__.py
├── models.py
├── demo_data.py
├── state_store.py
├── operators.py
├── workflow.py
├── service.py
└── README.md

examples/
└── run_supply_chain_alert.py

apps/tests/supply_chain_alert/
├── test_workflow.py
├── test_service.py
└── test_detection.py
```

对应职责：

- `models.py`：事件、风险、影响、建议、看板快照的数据结构。
- `demo_data.py`：构造离线可跑的订单、库存、物流、供应商演示数据。
- `state_store.py`：保存当前库存、未完成订单、物流状态、供应商风险分数。
- `operators.py`：SAGE 算子实现。
- `workflow.py`：基于 `LocalEnvironment + BaseService` 组织完整工作流。
- `service.py`：高层应用服务门面，向 CLI 或 FastAPI 暴露接口。
- `run_supply_chain_alert.py`：直接运行 Demo。

## 4. 业务对象设计

第一版建议先把数据对象控制在 8 个以内，避免模型层太重。

### 4.1 输入事件模型

建议定义以下输入对象：

- `PurchaseOrderEvent`
- `InventoryEvent`
- `ShipmentEvent`
- `SupplierPerformanceEvent`

字段示例：

- 订单：订单号、SKU、数量、承诺交期、仓库、供应商
- 库存：SKU、仓库、现有库存、安全库存、更新时间
- 物流：运单号、订单号、当前位置、状态、预计到达时间、延迟小时数
- 供应商：供应商 ID、准时率、缺陷率、过去 30 天违约次数

### 4.2 中间分析对象

建议定义：

- `NormalizedSupplyEvent`
- `AnomalySignal`
- `ImpactAssessment`
- `MitigationSuggestion`

### 4.3 看板输出对象

建议定义：

- `OpenAlert`
- `DashboardSnapshot`
- `SupplierRiskSummary`

## 5. 状态仓设计

这个项目适合做成“事件流 + 状态仓”的结构，而不是一次性离线计算。建议在 `state_store.py` 中维护：

- 当前库存索引：按 `warehouse + sku`
- 未关闭订单索引：按 `order_id`
- 物流状态索引：按 `shipment_id`
- 供应商表现索引：按 `supplier_id`
- 当前开放告警列表：按 `alert_id`

建议服务名：

```python
STATE_SERVICE_NAME = "supply_chain_state"
```

建议暴露给 SAGE 算子的服务方法：

- `upsert_inventory`
- `upsert_purchase_order`
- `upsert_shipment`
- `upsert_supplier_performance`
- `get_inventory_snapshot`
- `get_open_orders`
- `get_shipment`
- `get_supplier_profile`
- `save_alert`
- `list_open_alerts`
- `build_dashboard_snapshot`

这一层直接复用当前仓库里“学生提分”示例的模式最稳：由 `BaseService` 暴露状态操作，MapFunction 用 `call_service(...)` 读写状态。

## 6. SAGE Pipeline 设计

### 6.1 第一版主链路

建议第一版采用单链路、统一输入事件的方式：

```text
DemoEventSource
  -> NormalizeEventStep
  -> UpdateStateStep
  -> DetectAnomalyStep
  -> AssessImpactStep
  -> RecommendMitigationStep
  -> AlertSink
```

每一步职责如下：

#### `DemoEventSource(BatchFunction)`

- 从 `demo_data.py` 按时间顺序吐出演示事件。
- 输出订单、库存、物流、供应商四类混合事件。

#### `NormalizeEventStep(MapFunction)`

- 把不同来源事件转成统一的 `NormalizedSupplyEvent`。
- 处理缺省值、时间格式和枚举映射。

#### `UpdateStateStep(MapFunction)`

- 通过 `call_service(STATE_SERVICE_NAME, ...)` 更新库存、订单和物流状态。
- 让后续算子总是基于最新状态做判断。

#### `DetectAnomalyStep(MapFunction)`

- 检测以下异常：
  - 库存低于安全阈值
  - 订单即将到期但未发货
  - 物流延迟超阈值
  - 供应商近期履约恶化
- 输出一个或多个 `AnomalySignal`。

#### `AssessImpactStep(MapFunction)`

- 估算异常影响范围：
  - 影响订单数
  - 影响 SKU 数
  - 预计缺货天数
  - 风险等级
- 输出 `ImpactAssessment`。

#### `RecommendMitigationStep(MapFunction)`

- 结合当前库存和供应商表现，生成处置建议：
  - 加急补货
  - 转仓调拨
  - 切换替代供应商
  - 调整承诺交期
- 输出 `MitigationSuggestion`。

#### `AlertSink(SinkFunction)`

- 汇总开放告警。
- 生成控制台摘要和结构化 JSON 输出。

### 6.2 推荐的最小工作流骨架

建议在 `workflow.py` 中采用这种结构：

```python
from sage.foundation import MapFunction, SinkFunction
from sage.runtime import BaseService, LocalEnvironment
```

工作流 runner 负责：

1. 构建 `LocalEnvironment("supply_chain_alert")`
1. 注册 `SupplyChainStateService`
1. 通过 `environment.from_batch(...)` 启动事件源
1. 串接多个 `.map(...)`
1. 用 `.sink(...)` 收集结果
1. 调用 `environment.submit(autostop=True)` 执行

这部分建议严格对齐当前仓库里
[sage-examples/apps/src/sage/apps/student_improvement/workflow.py](sage-examples/apps/src/sage/apps/student_improvement/workflow.py)
的模式。

## 7. 第一版建议实现的异常规则

第一版不要一开始就做复杂机器学习，先做规则版，确保演示稳定。

建议最先实现这 6 条规则：

1. 安全库存不足：现有库存 < 安全库存。
1. 在途延迟：物流预计到达时间晚于承诺到货时间。
1. 发货停滞：运单状态超过设定小时数未变化。
1. 订单积压：未发货订单数量超过阈值。
1. 单一供应商过度依赖：关键 SKU 的供应集中度过高。
1. 供应商风险恶化：准时率下降且违约次数上升。

这些规则都很适合拆成显式 `MapFunction` 逻辑，演示时也容易解释“为什么触发”。

## 8. 看板指标设计

第一版控制在 8 到 10 个核心指标即可：

- 开放预警总数
- 高风险预警数
- 即将缺货 SKU 数
- 延迟运单数
- 超期未发货订单数
- 高风险供应商数
- 平均延迟小时数
- 建议调拨次数
- 建议替代采购次数

建议在 `DashboardSnapshot` 中一次性输出这些统计，便于 CLI 和 API 统一使用。

## 9. 应用服务层设计

建议做一个高层服务门面：

```text
SupplyChainAlertApplicationService
```

建议提供的方法：

- `run_demo()`：导入整套演示事件并返回最终看板快照
- `ingest_events(events)`：接收一批外部事件并运行 pipeline
- `get_dashboard()`：获取当前看板摘要
- `list_open_alerts()`：查看当前开放预警
- `get_supplier_risk_summary()`：查看供应商风险画像

### 9.1 FastAPI 可选接口

如果要像学生提分示例一样提供 API，可加：

- `POST /events/ingest`
- `GET /dashboard`
- `GET /alerts/open`
- `GET /suppliers/risk`
- `POST /demo/reset-and-run`

这部分建议参考
[sage-examples/apps/src/sage/apps/student_improvement/service.py](sage-examples/apps/src/sage/apps/student_improvement/service.py)
的做法。

## 10. LLM 增强点，且要通过 SAGE 网关接口接入

如果你希望 Demo 更像“智能预警看板”，可以加一个可选步骤：风险解释增强。

### 10.1 使用方式

先探测 SAGE 网关：

```python
from sage.serving import SageServeConfig, probe_gateway

gateway_config = SageServeConfig()
probe = probe_gateway(gateway_config)
```

只有当 `probe.ok` 为真时，才开启以下能力：

- 把规则触发结果转成自然语言风险摘要
- 生成采购协调建议
- 生成给运营团队的日报摘要

### 10.2 注意点

- 不要把整个应用逻辑依赖到 LLM 上。
- 规则预警必须在没有 LLM 的情况下也能独立运行。
- LLM 只负责“解释”和“润色”，不负责底层告警判定。

这样可以保证 Demo 稳定，同时满足“调用 SAGE 接口”的要求。

## 11. 推荐的开发分阶段计划

### 阶段 1：离线 MVP

目标：1 到 2 天内可跑通。

实现内容：

- `models.py`
- `demo_data.py`
- `state_store.py`
- `operators.py`
- `workflow.py`
- `examples/run_supply_chain_alert.py`

验收标准：

- 运行一次脚本能输出看板摘要
- 至少能触发 3 类不同异常
- 输出结构化 JSON 和控制台摘要

### 阶段 2：服务化

目标：把 Demo 包装成可查询的应用。

实现内容：

- `service.py`
- FastAPI app factory
- 查询开放预警和供应商风险接口

验收标准：

- 可以通过 API 获取 dashboard 和 alerts
- 重复导入事件后状态能持续更新

### 阶段 3：智能解释增强

目标：给预警增加管理层可读性。

实现内容：

- 接入 `SageServeConfig`
- 用 `probe_gateway` 做网关探测
- 增加可选的摘要解释模块

验收标准：

- 网关可用时返回自然语言解释
- 网关不可用时应用仍能正常运行

### 阶段 4：规模化模拟

目标：演示更大规模事件处理。

实现内容：

- 增加更长时间窗口的事件流
- 视需要切换到 `FlowNetEnvironment`

验收标准：

- 能稳定处理更大规模模拟事件
- 结果和本地版规则保持一致

## 12. 建议先写的测试

第一批测试建议如下：

1. 低库存是否能正确触发预警。
1. 延迟物流是否能正确计算影响等级。
1. 替代供应商推荐是否按风险分数排序。
1. 状态仓是否能在多批事件导入后保持一致。
1. 没有网关时，LLM 增强分支是否自动关闭。

## 13. 推荐的演示脚本表现形式

为了让 Demo 更像产品，不建议只打印原始对象，建议输出三段：

### 第一段：运行配置

- 模拟仓库数量
- 供应商数量
- 订单数量
- 事件总数

### 第二段：实时预警摘要

- 当前事件类型
- 触发规则
- 风险等级
- 建议动作

### 第三段：最终看板

- 风险总览
- 影响订单总数
- Top 风险供应商
- Top 缺货 SKU

## 14. 一句话总结实现路线

最稳的实现路线是：

用 `BatchFunction` 构造供应链事件流，用 `MapFunction` 做标准化、状态更新、异常检测、影响评估和建议生成，用 `SinkFunction` 输出看板结果，用
`BaseService` 持有共享状态，用 `LocalEnvironment` 执行主链路，再在可选阶段通过 `SageServeConfig + probe_gateway` 接入 SAGE
网关做风险解释增强。
