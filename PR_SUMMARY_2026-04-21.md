# PR 变更说明

## 标题建议

feat: 扩充可运行 SAGE 示例应用，并补齐文档与编辑器支持

## 变更背景

本次 PR 主要针对 sage-examples 仓库进行扩展和收敛，新增一批可运行的轻量级 SAGE 示例应用、对应入口脚本以及必要的仓库文档支持。目标是让仓库能够覆盖更多真实业务场景，同时保持示例结构统一、可直接运行、可导出、可阅读。

## 变更范围

本次改动主要包括四部分：

1. 新增生成类示例应用复用的批量数据源基础设施。
2. 在 apps/src/sage/apps/ 下补充一批新的应用包。
3. 在 examples/ 下补充并整理对应的可运行入口脚本。
4. 更新仓库文档与 VS Code 编辑器配置，使扩展后的示例集更易使用和维护。

## 主要改动

### 1. 公共应用基础设施

- 新增 apps/src/sage/apps/_batch.py。
- 引入 ListBatchSource，用于统一处理生成类应用中“批量加载一次，再按条输出”的数据源模式。
- 统一新示例应用的基本处理链路：source -> parsing/normalization -> rule/scoring -> JSON sink。

### 2. 新增可运行示例应用

- 新增一批面向不同业务领域的示例应用包，覆盖科研、教育、医疗、企业运营、公共服务、可持续发展、物联网、金融等方向。
- 每个应用包保持统一结构：
  - __init__.py：对外导出单一 run_*_pipeline 符号。
  - operators.py：封装本地示例级规则与处理逻辑。
  - pipeline.py：基于 LocalEnvironment 串联完整流水线。
  - README.md：说明该示例应用的用途与运行方式。
- 当前生成类 smoke test 注册表覆盖 91 个 pipeline 导出项。

代表性新增应用包括：

- 科研与知识处理：academic_metadata、benchmark_watch、grant_subscription、knowledge_cleanup。
- 教育场景：assignment_feedback、course_qa_helper、interview_coach、lesson_scheduler、campus_aid_gap_alert。
- 医疗场景：drug_leaflet_extractor、lab_turnaround_alert。
- 企业运营场景：api_log_analytics、backup_sync、budget_variance_alert、cashflow_watch、content_scheduler、invoice_reconciliation。
- 物联网与基础设施场景：cold_chain_watch、factory_watch、greenhouse_assistant、data_center_watch、campus_emission_report、carbon_collection。

### 3. 入口脚本与示例索引

- 扩充 examples/ 下的可运行脚本，并同步更新 examples/README.md 索引。
- 当前 examples/ 下共有 100 个 run_*.py 入口脚本。
- 这样可以为每个应用提供稳定、直接的运行入口，也便于用户按场景浏览仓库内容。

### 4. 文档与编辑器支持

- 更新 README.md，使其能够更准确反映当前扩展后的示例覆盖范围，并补充代表性入口脚本说明。
- 调整 docs/100-app-roadmap.md 的格式，使其通过仓库内 markdown lint 检查。
- 更新 .vscode/settings.json，使 VS Code 能正确解析以下源码路径：
  - apps/src
  - ../../SAGE/src
- 该配置仅影响编辑器侧的诊断、跳转与补全，不改变实际运行时行为。

## 实现说明

### 设计取舍

- 新增应用以轻量、仓库内自包含、便于理解为原则。
- 实现层面优先采用简单的解析、归一化、匹配与评分逻辑，不引入额外重依赖。
- 这些 pipeline 的定位是“可运行示例”和“结构模板”，而不是生产级领域引擎。
- 整体风格与 sage-examples 仓库定位保持一致，即强调可发现、可检查、可执行。

### 本次顺手收敛的质量问题

- 修复了根 README 中的 markdown 格式问题。
- 修复了 roadmap 文档中的有序列表格式问题。
- 修复了以下应用中新增中文规则词条的乱码问题：
  - content_moderation
  - contract_risk

## 验证情况

已完成以下验证：

- pytest tests/generated/test_generated_apps.py -q
  - 结果：2 passed
- python -m compileall apps/src/sage/apps examples
  - 结果：执行完成，未出现语法错误
- git diff --check
  - 结果：未发现空白字符或 patch 格式问题
- 对本次修改的文档与 Python 文件执行定向诊断
  - 结果：已处理文件未发现剩余错误

## 影响评估

### 对开发者的影响

- 明显扩充了仓库内可运行示例的覆盖范围。
- 提升了在 VS Code 中浏览、跳转与补全这些示例代码的体验。
- 为后续继续补充示例应用提供了更统一的基础结构。

### 对使用者的影响

- 使用者可以直接从仓库中发现并运行更多面向具体场景的示例流水线。
- 根 README 和示例索引对当前真实可运行范围的表达更加准确。

## 风险与限制

- 本次新增的很多应用仍属于示例级、规则驱动实现，主要目标是演示能力与保持包结构一致性。
- 当前已经验证了导出、语法和部分代表性行为，但尚未对每个新增入口脚本逐一做端到端运行。
- 后续仍可继续补充 fixture 数据，并批量执行新增脚本以增强运行层面的覆盖度。

## 后续建议

1. 为新增应用补充 fixture 数据，并在 CI 中批量运行示例入口脚本。
2. 按领域挑选代表性应用，补充更聚焦的测试用例。
3. 持续收敛重复的数据加载辅助逻辑，避免同类实现分散。

## 重点文件

- apps/src/sage/apps/_batch.py
- apps/tests/generated/test_generated_apps.py
- examples/README.md
- README.md
- docs/100-app-roadmap.md
- .vscode/settings.json
