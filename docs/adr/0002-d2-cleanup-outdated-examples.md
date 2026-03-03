# ADR 0002: D2 清理过时示例与兼容脚本

- Status: Accepted
- Date: 2026-03-03
- Related issue: https://github.com/intellistream/sage-examples/issues/14

## Context

`examples/` 目录存在以下边界问题：

1. 存在旧 API 演示脚本，不属于当前维护范围；
2. `examples/README.md` 文档内容损坏且包含无效入口（如 `examples/apps/...`）；
3. 顶层 README 仍暴露过时入口，造成“文档可见但实际不维护”的误导。

## Decision

执行最小边界收敛：

1. 删除过时脚本 `examples/run_runtime_api_layering.py`；
2. 重写 `examples/README.md`，仅保留可运行且受维护的入口；
3. 同步更新根 `README.md` 的示例列表，移除过时入口；
4. 不新增 shim/re-export/fallback，不保留兼容入口。

## Consequences

- `examples/` 只保留当前维护的可运行入口；
- 文档与实际脚本集合一致，降低误导与维护成本；
- 对外 API 无新增兼容层，符合 Wave D D2 约束。

## Verification

- 校验删除后入口脚本集合：`examples/run_*.py`
- 执行基础回归：`pytest -q examples/test_apps.py apps/tests/test_package.py`
