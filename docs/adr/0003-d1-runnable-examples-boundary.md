# ADR 0003: D1 边界收敛（只保留可运行样例）

- Status: Accepted
- Date: 2026-03-03
- Related issue: https://github.com/intellistream/sage-examples/issues/13

## Context

D1 目标要求示例仓库聚焦“可运行样例”，避免把核心实现逻辑带入 `examples/` 入口层。

在实践中，这类边界容易回归：

1. 入口脚本可能直接导入 `sage.kernel/platform/middleware` 等底层模块；
1. 已删除的过时入口可能被误加回仓库。

## Decision

新增回归门禁测试（`examples/test_apps.py`）：

1. `test_examples_boundary_no_core_layer_imports`：静态扫描 `examples/run_*.py`，禁止直接导入核心实现层包；
1. `test_deprecated_entries_removed`：锁定已移除入口 `run_runtime_api_layering.py`，防止回归。

## Consequences

- `examples/` 入口层职责被自动化约束为“应用演示入口”；
- 核心实现逻辑保持在 `apps/src/sage/apps/`；
- 不新增任何兼容层（shim/re-export/fallback）。

## Verification

- `pytest -q examples/test_apps.py apps/tests/test_package.py`
- `ruff check .`
