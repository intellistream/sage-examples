# Supply Chain Alert Dashboard MVP

这是一个基于 SAGE 本地运行时与显式状态服务实现的“供应链异常预警看板”第一版。

## 目标

- 接收采购订单、库存、物流、供应商履约等事件
- 用显式 SAGE 算子链检测可解释的规则异常
- 用状态仓维护库存、开放订单、物流和供应商画像
- 输出结构化预警列表与最终 dashboard 快照

## 核心设计

- models.py: 定义输入事件、标准化事件、异常信号、预警对象和 dashboard 快照
- demo_data.py: 提供离线可跑的演示事件流
- state_store.py: 维护库存、订单、物流、供应商和开放预警状态
- operators.py: 用 BatchFunction, MapFunction, SinkFunction 组织主链路
- workflow.py: 用 LocalEnvironment + BaseService 执行状态化工作流
- service.py: 暴露应用服务门面，并提供可选 FastAPI app factory

## 如何运行

在仓库根目录执行：

```bash
python examples/run_supply_chain_alert.py
```

也可以输出 JSON：

```bash
python examples/run_supply_chain_alert.py --json
python examples/run_supply_chain_alert.py --storage-path .sage/supply-chain-alert.json
```

启动 API 服务：

```bash
python examples/run_supply_chain_alert_api.py
python examples/run_supply_chain_alert_api.py --host 0.0.0.0 --port 8010
```

默认开放这些接口：

- GET /
- GET /health
- POST /events/ingest
- GET /dashboard
- GET /dashboard/ui
- GET /alerts/open
- GET /alerts/explanations
- GET /suppliers/risk
- POST /demo/reset-and-run

如果希望直接打开图形界面，可以在启动 API 后访问：

```bash
http://127.0.0.1:8000/dashboard/ui
http://127.0.0.1:8010/dashboard/ui
```

这个页面内置三个动作：

- 加载演示数据
- 刷新看板
- 生成中文解释

同时已经扩展成多角色 Web dashboard，页面里可以直接切换：

- 运营总控
- 采购协调
- 仓配调度
- 供应商管理

每个角色会看到不同的：

- 角色摘要
- 优先动作队列
- 角色关注预警
- 角色关注供应商

即使自然语言解释依赖的 gateway 暂时不可用，角色摘要和动作队列也会继续基于规则结果显示，不会整块空掉。

如果希望直接从 CLI 演示自然语言解释，可以执行：

```bash
python examples/run_supply_chain_alert.py --explain
python examples/run_supply_chain_alert.py --json --explain
```

## sage.serving 网关增强

这一层是可选增强，不参与底层规则判定。主链路仍然是本地 SAGE runtime + 显式状态服务；只有在 `probe_gateway(...)` 探测到网关可用时，才会调用 OpenAI-compatible 接口生成中文风险解释。

推荐通过环境变量配置：

```bash
export SAGE_SUPPLY_CHAIN_GATEWAY_HOST="127.0.0.1"
export SAGE_SUPPLY_CHAIN_GATEWAY_PORT="19000"
export SAGE_SUPPLY_CHAIN_MODEL="<optional-model-id>"
export SAGE_SUPPLY_CHAIN_API_KEY="EMPTY"
```

如果你们用的是远程 OpenAI-compatible gateway，也可以直接传完整 base URL：

```bash
export SAGE_SUPPLY_CHAIN_BASE_URL="https://api.sage.org.ai/v1"
export SAGE_SUPPLY_CHAIN_HEALTH_URL="https://api.sage.org.ai/health"
export SAGE_SUPPLY_CHAIN_MODEL="<optional-model-id>"
export SAGE_SUPPLY_CHAIN_API_KEY="<your-api-key>"
```

如果要直接验证远程解释链路，推荐先用这两组命令：

```bash
export SAGE_SUPPLY_CHAIN_BASE_URL="https://api.sage.org.ai/v1"
export SAGE_SUPPLY_CHAIN_HEALTH_URL="https://api.sage.org.ai/health"
export SAGE_SUPPLY_CHAIN_MODEL="Qwen/Qwen2.5-7B-Instruct"
export SAGE_SUPPLY_CHAIN_API_KEY="<your-api-key>"

python examples/run_supply_chain_alert.py --json --explain
```

如果要通过 HTTP API 查看解释结果，可以在同一组环境变量下启动服务：

```bash
python examples/run_supply_chain_alert_api.py --host 127.0.0.1 --port 8010
```

然后依次访问：

```bash
curl -X POST http://127.0.0.1:8010/demo/reset-and-run
curl "http://127.0.0.1:8010/alerts/explanations?max_alerts=1"
```

浏览器里直接打开 `http://127.0.0.1:8010/alerts/explanations?max_alerts=1` 也可以看到 JSON 形式的中文风险解释。
如果希望查看图形版 dashboard，也可以直接打开 `http://127.0.0.1:8010/dashboard/ui`。

说明：

- `SAGE_SUPPLY_CHAIN_MODEL` 可选；如果不设，会先从网关列模型再选择第一个
- `SAGE_SUPPLY_CHAIN_API_KEY` 默认会回退到 `SAGE_OPENAI_API_KEY` / `OPENAI_API_KEY`，本地网关一般可用 `EMPTY`
- `SAGE_SUPPLY_CHAIN_BASE_URL` 适合远程 HTTPS 网关；设置后会优先于本地 host/port 配置
- 网关不可达时，应用不会影响原有规则预警，只会明确返回“解释不可用”的状态和错误信息

## 当前 MVP 边界

- 主链路规则版异常检测不依赖外部大模型；自然语言解释为可选 gateway 增强
- 主链路固定在 LocalEnvironment，不启用 FlowNetEnvironment
- 状态存储默认为内存，可选写入本地 JSON 文件
- 提供应用服务门面、FastAPI app factory 和可选的自然语言解释入口

## 下一步可以扩展什么

- 接入真实订单/库存/物流数据源
- 用共享状态服务替换本地 JSON 状态仓
- 继续增强多角色 Web dashboard，例如自动轮询、角色级 SLA、按仓库/供应商过滤
- 补一个终端交互式 CLI 控制台，适合纯 SSH 环境排障和值班