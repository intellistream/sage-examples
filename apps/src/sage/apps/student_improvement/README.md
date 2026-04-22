# Student Improvement MVP

这是一个基于 SAGE 本地运行时与显式状态服务实现的“个性化提分系统”MVP。

## 目标

- 初始化课程知识结构
- 连续导入学生考试/练习结果
- 自动生成错题诊断与标准解法
- 持续更新学生掌握度、薄弱点排序、学习路径与动态错题集
- 基于课本章节、知识点与前置依赖生成知识图谱，并按学生掌握情况标注节点状态

## 核心设计

- `models.py`：定义学生档案、课程知识、考试记录、错题、诊断结果等结构化对象
- `state_store.py`：分离管理课程、考试历史、错题集、学生档案和诊断结果
- `workflow.py`：用 `LocalEnvironment + MapFunction + BaseService` 组织状态化工作流
- `service.py`：暴露应用服务门面，并提供可选 FastAPI app factory
- `knowledge_base.py`：从教材结构生成知识图谱快照，输出 `nodes/edges` 并附带掌握度标记

## 如何运行

在仓库根目录执行：

```bash
python examples/run_student_improvement.py
```

默认会启动一个持续运行的交互式 app，并保持运行直到用户主动选择退出。

可选参数：

```bash
python examples/run_student_improvement.py --storage-path .sage/student_improvement_state.json
python examples/run_student_improvement.py --once
python examples/run_student_improvement.py --json
```

## 可选 LLM 增强

app 支持通过 OpenAI-compatible 接口接入你们本地或私有部署的大模型，但不会把 key 硬编码到仓库里。

推荐在仓库根目录放一个本地 `.env` 文件：

```bash
cat > .env <<'EOF'
SAGE_OPENAI_BASE_URL="https://api.sage.org.ai/v1"
SAGE_OPENAI_API_KEY="<your-api-key>"
SAGE_OPENAI_MODEL="<optional-model-id>"
EOF
```

app 启动时会自动读取当前工作目录或项目路径下的 `.env`。如果你更习惯手工导出环境变量，也同样支持：

```bash
export SAGE_OPENAI_BASE_URL="https://api.sage.org.ai/v1"
export SAGE_OPENAI_API_KEY="<your-api-key>"
export SAGE_OPENAI_MODEL="<optional-model-id>"
```

进入 app 后可用菜单：

- `5` 测试模型连接并列出可用模型
- `6` 基于当前学生状态生成 AI 增强学习建议

## 演示数据

- 学科：八年级数学
- 知识点：分式化简、一元一次方程、因式分解、整式展开、一次函数
- 样例学生：`stu-demo-001`
- 样例考试：2 份，分别用于展示首次诊断和增量更新后的状态变化

## 当前 MVP 边界

- 使用规则与启发式诊断，不依赖外部大模型即可运行
- 使用内存状态存储，支持可选 JSON 文件持久化
- 提供应用服务门面、交互式 console app 和 FastAPI app factory，但不内置 ASGI 服务器启动脚本
- 当前未接入 NeuroMem；知识状态依然由应用内显式状态仓维护
- 不包含前端界面、权限系统和复杂教育测评算法

## 后续如何增强

- 将错因分析和解法生成替换为 LLM 增强版本
- 把本地状态仓替换为真正的 shared state / service backend
- 增加更丰富的题型解析、标签体系和长期学习轨迹建模
