# ADR 0001: D3 示例可执行性与依赖一致性回归修复

- Status: Accepted
- Date: 2026-03-03
- Related issue: https://github.com/intellistream/sage-examples/issues/15

## Context

在仓库根目录运行 `pytest -q apps/tests` 时，测试收集阶段出现 `ModuleNotFoundError: No module named 'sage.apps'`。

核心原因：

1. `sage.apps` 源码位于 `apps/src/sage/apps`；
2. 根仓库 pytest 配置未将 `apps/src` 注入 Python import path；
3. 在 `apps/` 子目录执行 pytest 时，同样缺失 `src` 路径注入。

这会造成“依赖已声明但示例不可执行”的假失败，不符合 D3 的“可执行性与依赖一致性回归”目标。

## Decision

采用最小修复，不引入兼容层：

1. 在根目录 `pyproject.toml` 的 `[tool.pytest.ini_options]` 中新增 `pythonpath = ["apps/src"]`；
2. 在 `apps/pyproject.toml` 的 `[tool.pytest.ini_options]` 中新增 `pythonpath = ["src"]`；
3. 不添加 shim/re-export/fallback，不修改业务导入路径。

## Consequences

- `sage.apps` 在仓库内测试运行时可被稳定导入；
- 同时兼容两种常用测试入口：
  - 仓库根目录：`pytest apps/tests`
  - `apps/` 子目录：`pytest tests`
- 该修复仅影响测试执行环境，不改变运行时包结构与公开 API。

## Verification

- 执行：`pytest -q apps/tests`
- 预期：收集通过，不再出现 `No module named 'sage.apps'`。
