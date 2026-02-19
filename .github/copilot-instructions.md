# SAGE Examples Copilot Instructions

## 🚨 Runtime Direction (Cross-Repo)

- `sageFlownet` is the runtime component that replaces `Ray` in the SAGE ecosystem.
- Example code involving distributed execution or scheduling should align with Flownet-style runtime usage.
- Do NOT introduce new `ray` imports/dependencies in examples.

## 🚨 Installation Consistency (Cross-Repo)

- 在 conda 环境中，**必须**使用 `python -m pip`，不要直接使用 `pip`。
- 当示例依赖 SAGE 主仓库能力时，优先要求用户先在 `SAGE/` 执行 `./quickstart.sh --dev --yes`。
- SAGE quickstart 已负责安装核心独立 PyPI 依赖（如 `isagellm`、`isage-flownet`、`isage-vdb` 等），不要再建议通过 extras 手动补装“核心依赖”。
- `git push` 前必须确认本仓库 `pre-push` hooks 行为；部分仓库会在 push 时自动更新版本号并触发 PyPI/TestPyPI 发布。

## Overview

**sage-examples** 是 SAGE 框架的示例代码仓库，包含完整的教程和应用案例。这个仓库从 SAGE 主仓库独立出来，专注于提供学习资源和生产应用示例。

## 🚨 CRITICAL Principles

### ❌ NEVER MANUAL PIP INSTALL - ALWAYS USE pyproject.toml

**所有依赖必须声明在 pyproject.toml 中，禁止使用手动 `pip install` 命令。**

#### ❌ FORBIDDEN Operations:

```bash
pip install transformers              # ❌ 手动安装
pip install torch==2.7.0              # ❌ 手动版本
pip install sage-libs                 # ❌ 手动依赖
```

#### ✅ CORRECT Operations:

```toml
# 在 pyproject.toml 或 requirements.txt 中声明
dependencies = [
    "isage-libs>=0.2.0",          # ✅ 声明在 pyproject.toml
    "isagellm>=0.2.0",            # ✅ 版本约束
    "transformers>=4.52.0",       # ✅ 可选依赖
]
```

```bash
# 然后安装包
pip install -e .
# 或
pip install -r requirements.txt
```

**Why**: 确保可重现性，在 git 中跟踪依赖变更，防止版本冲突，维护单一信息源。

### ❌ NO FALLBACK LOGIC - PROJECT-WIDE RULE

**禁止在代码的任何地方使用 try-except fallback 模式。**

这是**项目级原则**，不仅适用于版本管理。Fallback 会隐藏问题，使调试更加困难。

#### ❌ BAD Examples (不要这样做):

```python
# 版本导入
try:
    from ._version import __version__
except ImportError:
    __version__ = "unknown"  # ❌ NO - 隐藏缺失文件

# 配置加载
try:
    config = load_config("config.yaml")
except FileNotFoundError:
    config = {}  # ❌ NO - 隐藏缺失配置

# 环境变量
api_key = os.getenv("API_KEY") or "default_key"  # ❌ NO - 隐藏缺失变量
```

#### ✅ GOOD Examples (这样做):

```python
# 让异常传播并提供清晰的错误信息
config = load_config("config.yaml")  # 如果缺失则 FileNotFoundError
api_key = os.environ["API_KEY"]  # 如果缺失则 KeyError

# 或提供有用的错误信息
if not os.path.exists("config.yaml"):
    raise FileNotFoundError(
        "config.yaml not found. Please create it from config.yaml.template"
    )
```

**Rationale**: 快速失败，明确报错。静默 fallback 会隐藏 bug，使调试更困难，在生产环境中不可接受。

## SAGE Dependencies

### Core Dependencies

sage-examples 依赖于 SAGE 核心包（通过 PyPI 安装）：

```toml
# 核心包（必需）
dependencies = [
    "isage-common>=0.2.0",        # L1: Foundation
    "isagellm>=0.2.0",            # L1: LLM control plane + client
    "isage-libs>=0.2.0",          # L3: Algorithms, RAG, Agents
]

# 中间件包（可选，用于高级示例）
[project.optional-dependencies]
middleware = [
    "isage-middleware>=0.2.0",    # L4: Operators (C++ extensions)
]

# 应用包（可选，用于应用示例）
apps = [
    "isage-apps>=0.2.0",          # L5: Production applications
]

# 完整安装
full = [
    "isage-middleware>=0.2.0",
    "isage-apps>=0.2.0",
    "isage-vdb>=0.2.0",           # Vector database
    "isage-benchmark>=0.2.0",     # Benchmark tools
]
```

### SAGE Architecture Reference

SAGE 采用 6 层分层架构（L1-L6）：

```
L6: sage-cli, sage-studio, sage-tools, sage-llm-gateway, sage-edge
L5: sage-apps
L4: sage-middleware
L3: sage-kernel, sage-libs
L2: sage-platform
L1: sage-common
```

**PyPI Package Names**:
- `isage-common` (sage-common)
- `isagellm` (sageLLM unified inference engine)
- `isage-libs` (sage-libs)
- `isage-middleware` (sage-middleware)
- `isage-apps` (sage-apps)
- `isage-vdb` (SageVDB 向量数据库)
- `isage-benchmark` (benchmark 工具)

**注意**: 由于 'sage' 在 PyPI 已被占用，所有包名使用 'isage-' 前缀。

## Directory Structure

```
sage-examples/
├── apps/                   # 🎯 生产应用示例（运行入口）
│   ├── run_video_intelligence.py
│   ├── run_medical_diagnosis.py
│   ├── run_smart_home.py
│   └── README.md
│
├── tutorials/              # 📚 教程（按架构分层）
│   ├── hello_world.py
│   ├── QUICK_START.md
│   ├── README.md
│   ├── L1-common/         # 基础层教程
│   ├── L2-platform/       # 平台层教程
│   ├── L3-kernel/         # 核心层教程（执行引擎）
│   ├── L3-libs/           # 核心层教程（RAG、Agents）
│   ├── L4-middleware/     # 中间件层教程
│   ├── L5-apps/           # 应用层教程
│   ├── L6-interface/      # 接口层教程
│   ├── config/            # 配置示例
│   └── docs/              # 文档
│
├── sage-apps/             # sage-apps 包的独立开发
│   ├── pyproject.toml
│   ├── src/sage/apps/
│   └── tests/
│
├── requirements.txt       # Python 依赖
├── README.md
└── LICENSE
```

## How Copilot Should Learn SAGE Examples

### Documentation-First Approach

在回答问题或修改代码之前，Copilot **必须先依赖项目文档/README，而不是猜测**。

**在进行任何非平凡工作之前，Copilot 应该至少浏览：**

- Root overview: `README.md` (示例总览、快速开始)
- Tutorials overview: `tutorials/README.md` (教程结构、学习路径)
- Examples overview: `examples/README.md` (应用列表、使用方法)
- Quick start: `tutorials/QUICK_START.md` (5分钟快速入门)

**在处理特定层级/主题时，Copilot 应该额外阅读：**

- 对应层级的 README，例如：
  - `tutorials/L1-common/README.md`
  - `tutorials/L2-platform/README.md`
  - `tutorials/L3-kernel/README.md` / `L3-libs/README.md`
  - `tutorials/L4-middleware/README.md`
  - `tutorials/L5-apps/README.md`
  - `tutorials/L6-interface/README.md`

**🔍 遇到困难或不确定时：**

- **首先**检查相关文档是否存在
- **使用工具**如 `grep_search` 或 `semantic_search` 在文档中查找
- **先阅读后行动** - 文档是为了指导你，不是可选参考
- **常见文档位置：**
  - 教程文档：`tutorials/docs/`
  - 配置示例：`tutorials/config/`
  - 应用说明：`examples/README.md`
  - 快速入门：`tutorials/QUICK_START.md`

**规则**: 不要猜测架构决策或策略。阅读文档。文档就是为此而存在的。

## SAGE Examples Scope

### What sage-examples Contains

**✅ 包含内容：**

1. **Examples (examples/)**: 应用示例运行入口
   - 视频智能分析
   - 医疗诊断系统
   - 智能家居
   - 文章监控
   - 自动扩展聊天

3. **sage-apps Package (sage-apps/)**: 独立开发的应用包
   - 源代码：`src/sage/apps/`
   - 测试：`tests/`
   - 打包配置：`pyproject.toml`

### What sage-examples Does NOT Contain

**❌ 不包含内容（在其他仓库）：**

1. **核心框架代码**: 在 `SAGE/packages/` 中
2. **教程代码**: 独立仓库 `sage-tutorials`
3. **工具和脚本**: 在 `SAGE/tools/` 中
4. **CI/CD 配置**: 在 `SAGE/.github/` 中
5. **开发者文档**: 在 `SAGE-Pub` 或 `SAGE/.sage/docs/` 中
6. **Benchmark 框架**: 独立仓库 `sage-benchmark` (迁移中，当前仍在 `SAGE/benchmark/`)

### Relationship with SAGE Main Repository

```
┌──────────────────────────────────────────────┐
│ SAGE Main Repository                         │
│ (intellistream/SAGE)                         │
├──────────────────────────────────────────────┤
│ • 核心框架包 (packages/)                      │
│ • 开发工具 (tools/)                           │
│ • 文档 (SAGE-Pub 或 .sage/docs/)             │
│ • CI/CD (.github/)                            │
└──────────────────────────────────────────────┘
                     ↓
              PyPI 发布
         (isage-* packages)
                     ↓
┌──────────────────────────────────────────────┐
│ sage-examples Repository                     │
│ (intellistream/sage-examples)                │
├──────────────────────────────────────────────┤
│ • 应用示例入口 (examples/)                    │
│ • 独立 sage-apps 包 (sage-apps/)             │
│ • 依赖 PyPI 上的 isage-* 包                   │
└──────────────────────────────────────────────┘
```

## Installation

### Minimal (Examples only)

```bash
# 克隆仓库
git clone https://github.com/intellistream/sage-examples.git
cd sage-examples

# 安装核心依赖
python -m pip install -r requirements.txt

# 或只安装示例所需
python -m pip install isage-common isagellm isage-libs
```

### Full (All examples including apps)

```bash
# 安装所有依赖
python -m pip install -r requirements.txt

# 或使用 pip extras
python -m pip install -e ".[full]"
```

### Development (sage-apps package)

```bash
# 安装 sage-apps 包用于开发
cd sage-apps
python -m pip install -e ".[dev]"
```

## Environment Setup

### Environment Variables

创建 `.env` 文件（从 `.env.template` 复制）：

```bash
# === LLM API Keys ===
OPENAI_API_KEY=sk-xxx
HF_TOKEN=hf_xxx

# === SAGE Services (可选，使用本地服务时) ===
# SAGE_CHAT_BASE_URL=http://localhost:8889/v1  # Gateway URL
# SAGE_CHAT_MODEL=Qwen/Qwen2.5-7B-Instruct

# === DashScope (可选，使用阿里云时) ===
# SAGE_CHAT_API_KEY=sk-xxx
# SAGE_CHAT_MODEL=qwen-turbo-2025-02-11
# SAGE_CHAT_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

**注意**:
- 本地开发优先使用 SAGE Gateway (`localhost:8889`)
- DashScope 等云端 API 仅用于无本地服务时
- HuggingFace Token 用于下载模型（会自动检测网络并配置镜像）

## Running Examples

### Quick Start

```bash
# 视频智能分析
python examples/run_video_intelligence.py --video path/to/video.mp4

# 医疗诊断
python examples/run_medical_diagnosis.py

# 智能家居
python examples/run_smart_home.py

# 文章监控
python examples/run_article_monitoring.py

# 自动扩展聊天
python examples/run_auto_scaling_chat.py
```

> **学习教程**: 前往 [SAGE/tutorials](https://github.com/intellistream/SAGE/tree/main/tutorials) 查看完整教程。

### Applications

```bash
# 视频智能分析
python examples/run_video_intelligence.py --video path/to/video.mp4

# 医疗诊断
python examples/run_medical_diagnosis.py

# 智能家居
python examples/run_smart_home.py

# 文章监控
python examples/run_article_monitoring.py

# 自动扩展聊天
python examples/run_auto_scaling_chat.py
```

## Common Issues

### Import Errors

**问题**: `ModuleNotFoundError: No module named 'sage'`

**解决**:
```bash
# 确保安装了 SAGE 核心包
python -m pip install isage-common isagellm isage-libs

# 或安装完整依赖
python -m pip install -r requirements.txt
```

### API Key Errors

**问题**: `ValueError: OPENAI_API_KEY not found`

**解决**:
```bash
# 1. 创建 .env 文件
cp .env.template .env

# 2. 编辑 .env 添加 API key
echo "OPENAI_API_KEY=sk-xxx" >> .env

# 3. 或使用环境变量
export OPENAI_API_KEY=sk-xxx
```

### Service Connection Errors

**问题**: `Connection refused to http://localhost:8889`

**解决**:
```bash
# 确保 SAGE Gateway 正在运行（在 SAGE 主仓库）
cd /path/to/SAGE
sage gateway start

# 或使用云端 API（设置 .env）
SAGE_CHAT_BASE_URL=https://dashscope.aliyuncs.com/compatible-mode/v1
```

### Model Download Issues

**问题**: HuggingFace 模型下载慢或失败

**解决**:
```bash
# 中国大陆自动使用镜像，无需手动配置
# 如需强制使用镜像：
export HF_ENDPOINT=https://hf-mirror.com

# 或预下载模型（在 SAGE 主仓库）
sage llm model download Qwen/Qwen2.5-7B-Instruct
```

## Testing

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_tutorials.py
pytest tests/test_apps.py

# 运行 sage-apps 包测试
cd sage-apps
pytest tests/
```

## Code Style

### Formatting & Linting

```bash
# 使用 ruff 格式化
ruff format .

# 检查代码质量
ruff check .

# 自动修复
ruff check --fix .
```

### Pre-commit Hooks

```bash
# 安装 pre-commit
pip install pre-commit

# 安装 hooks
pre-commit install

# 手动运行
pre-commit run --all-files
```

## Contributing

### Adding New Examples

1. **选择正确的位置**:
   - 教程 → `SAGE/tutorials/L{1-6}-*/` (在 SAGE 主仓库)
   - 应用示例 → `examples/`
   - 配置 → `examples/*/config/` 或应用内部

2. **遵循命名规范**:
   - 使用描述性名称：`run_video_intelligence.py`, `run_medical_diagnosis.py`
   - 添加 README：每个目录应有 README.md
   - 示例数据：放在应用包内 `sage-apps/src/sage/apps/*/data/`

3. **文档要求**:
   - 代码注释：解释关键步骤
   - README：说明示例目的和使用方法
   - Docstrings：函数和类的文档字符串

4. **依赖管理**:
   - 更新 `requirements.txt` 或 `pyproject.toml`
   - 不要手动 `pip install`
   - 声明版本约束

### Example Template

```python
"""
Brief description of what this example demonstrates.

Requirements:
    - isage-libs>=0.2.0
    - transformers>=4.52.0

Usage:
    python example_name.py
"""

from sage.llm import UnifiedInferenceClient
from sage.libs.rag import SimpleRAG


def main():
    """Main function with clear steps."""
    # Step 1: Setup
    client = UnifiedInferenceClient.create()
    
    # Step 2: Execute
    response = client.chat([
        {"role": "user", "content": "Hello!"}
    ])
    
    # Step 3: Display results
    print(f"Response: {response}")


if __name__ == "__main__":
    main()
```

## Resources

- **SAGE 主仓库**: https://github.com/intellistream/SAGE
- **SAGE 文档**: https://sage.intellistream.com
- **PyPI 包**: https://pypi.org/search/?q=isage
- **sage-benchmark**: https://github.com/intellistream/sage-benchmark
- **Issue Tracker**: https://github.com/intellistream/sage-examples/issues

## Final Reminder for Copilot

**Trust these instructions** - search only if incomplete, errors occur, or deep architecture needed.

**🔍 When encountering difficulties or uncertainties:**

1. **First**, check if there's relevant documentation in `tutorials/docs/` or layer READMEs
2. **Use tools** like `grep_search` or `semantic_search` to find documentation before making assumptions
3. **Read before acting** - documentation exists to guide you, not as optional reference
4. **Common documentation locations:**
   - Root: `README.md`
   - Tutorials: `tutorials/README.md`, `tutorials/QUICK_START.md`
   - Layer guides: `tutorials/L{1-6}-*/README.md`
   - Examples: `examples/README.md`

**Remember**: Don't guess. Read the docs. They exist for this reason.
