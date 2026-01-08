# SAGE Examples - 开发指南

本文档说明 sage-examples 项目的开发流程、代码质量标准和 CI/CD 配置。

## 📁 项目结构

```
sage-examples/
├── .github/
│   ├── workflows/          # CI/CD workflows
│   │   ├── quality.yml    # 代码质量检查
│   │   └── tests.yml      # 测试运行
│   ├── chatmodes/          # GitHub Copilot 聊天模式
│   ├── agents/             # GitHub Copilot agents
│   └── copilot-instructions.md  # Copilot 指令
│
├── docs/                   # 📚 项目文档
│   ├── COPILOT_CONFIGURATION.md
│   ├── PYPI_RELEASE_GUIDE.md
│   ├── PYPI_SETUP_SUMMARY.md
│   └── PYPI_TEST_REPORT.md
│
├── tutorials/              # 📚 教程代码（L1-L6 分层）
├── examples/               # 🎯 应用示例（运行入口）
├── sage-apps/              # 独立 sage-apps 包
├── data/                   # 共享数据
│
├── .pre-commit-config.yaml # Pre-commit 配置
├── pyproject.toml          # 项目配置
├── requirements.txt        # Python 依赖
└── README.md               # 项目说明
```

## 🔧 开发环境设置

### 1. 克隆仓库

```bash
git clone https://github.com/intellistream/sage-examples.git
cd sage-examples
```

### 2. 安装依赖

```bash
# 核心依赖（教程）
pip install -r requirements.txt

# 或安装完整依赖（包括应用）
pip install -e ".[full]"

# sage-apps 包开发
cd sage-apps
pip install -e ".[dev]"
cd ..
```

### 3. 安装 Pre-commit Hooks

```bash
# 安装 pre-commit
pip install pre-commit

# 安装 hooks
pre-commit install

# 手动运行所有检查
pre-commit run --all-files
```

## ✅ 代码质量标准

### Pre-commit Hooks

项目使用 pre-commit 自动化代码质量检查，每次提交时自动运行：

#### 检查项目

1. **通用检查**
   - 去除尾随空格
   - 确保文件以换行符结尾
   - 检查 YAML/JSON/TOML 语法
   - 检查大文件（>1MB）
   - 检测合并冲突
   - 统一行尾符（LF）
   - 检测私钥泄露

2. **Python 代码质量**
   - **Ruff**: 快速 lint 和格式化（替代 black, isort, flake8）
   - **mypy**: 类型检查

3. **Shell 脚本**
   - **shellcheck**: Shell 脚本静态分析

4. **文档**
   - **mdformat**: Markdown 格式化
   - **pretty-format-yaml**: YAML 格式化

5. **安全**
   - **detect-secrets**: 敏感信息检测

### 手动运行检查

```bash
# 运行所有 pre-commit 检查
pre-commit run --all-files

# 运行特定检查
pre-commit run ruff --all-files
pre-commit run mypy --all-files
pre-commit run shellcheck --all-files

# 跳过 hooks（不推荐）
git commit --no-verify
```

### 代码格式化

```bash
# 使用 ruff 格式化
ruff format .

# 检查格式（不修改）
ruff format --check .

# 自动修复 lint 问题
ruff check --fix .
```

### 类型检查

```bash
# 运行 mypy
mypy . --config-file=pyproject.toml

# 检查特定目录
mypy tutorials/ examples/
```

## 🧪 测试

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tutorials/
pytest examples/test_apps.py
pytest sage-apps/tests/

# 带覆盖率
pytest --cov=. --cov-report=html

# 并行运行（快速）
pytest -n auto
```

### 测试组织

```
tests/                  # 如果有通用测试
tutorials/              # 教程示例（可作为测试运行）
examples/test_apps.py       # 应用测试
sage-apps/tests/        # sage-apps 包测试
```

## 🚀 CI/CD

### GitHub Actions Workflows

项目包含两个主要 workflow：

#### 1. 代码质量检查 (`.github/workflows/quality.yml`)

**触发条件**:
- Push 到 `main` 或 `main-dev`
- Pull Request
- 手动触发

**检查项**:
- Pre-commit hooks（所有检查）
- Ruff linting
- Ruff formatting
- mypy 类型检查

#### 2. 测试 (`.github/workflows/tests.yml`)

**触发条件**:
- Push 到 `main` 或 `main-dev`
- Pull Request
- 手动触发

**测试矩阵**:
- Python 版本: 3.10, 3.11, 3.12
- 测试套件:
  - 教程测试
  - 应用测试
  - sage-apps 包测试
  - 覆盖率报告

### CI 行为

- ✅ **Pre-commit**: 必须通过所有 hooks
- ⚠️ **mypy**: 类型检查错误不阻塞 CI（continue-on-error）
- ⚠️ **Tests**: 测试失败记录但不阻塞（continue-on-error）

### 本地模拟 CI

```bash
# 运行与 CI 相同的 pre-commit 检查
pre-commit run --all-files

# 运行与 CI 相同的测试
pytest tutorials/ examples/test_apps.py -v --tb=short
```

## 📝 贡献指南

### 提交前检查清单

- [ ] 代码通过 `ruff format .` 格式化
- [ ] 代码通过 `ruff check .` 检查
- [ ] 通过 `pre-commit run --all-files`
- [ ] 新功能有测试覆盖
- [ ] 更新相关文档
- [ ] Commit message 遵循规范（feat/fix/docs/chore）

### Commit Message 规范

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type**:
- `feat`: 新功能
- `fix`: Bug 修复
- `docs`: 文档更新
- `style`: 代码格式（不影响功能）
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

**示例**:
```
feat(tutorials): add L3-libs RAG example

- Add simple RAG tutorial
- Include config examples
- Update L3-libs README

Closes #123
```

### Pull Request 流程

1. Fork 仓库
2. 创建特性分支：`git checkout -b feature/your-feature`
3. 提交变更：`git commit -m "feat: your feature"`
4. 推送分支：`git push origin feature/your-feature`
5. 创建 Pull Request

### 添加新示例

1. **选择正确位置**:
   - 教程 → `tutorials/L{1-6}-*/`
   - 应用示例 → `examples/`
   - 配置 → `tutorials/config/`

2. **遵循命名规范**:
   - 使用描述性名称：`basic_agent.py`, `simple_rag.py`
   - 添加 README：每个目录应有 README.md

3. **文档要求**:
   - 代码注释：解释关键步骤
   - Docstrings：函数和类的文档字符串
   - README：说明示例目的和使用方法

4. **依赖管理**:
   - 更新 `requirements.txt` 或 `pyproject.toml`
   - 不要手动 `pip install`（❌ 禁止）
   - 声明版本约束

### 示例模板

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

## 🛠️ 常见问题

### Pre-commit 很慢？

Pre-commit 第一次运行会下载所有工具，可能需要 5-10 分钟。后续运行会很快。

```bash
# 预安装所有 hooks（可选）
pre-commit install --install-hooks
```

### 如何更新 pre-commit hooks？

```bash
# 更新到最新版本
pre-commit autoupdate

# 清理缓存
pre-commit clean
```

### 如何跳过某个 hook？

```bash
# 跳过特定 hook
SKIP=mypy git commit -m "message"

# 跳过所有 hooks（不推荐）
git commit --no-verify
```

### Ruff 与 Black/isort 的区别？

Ruff 是一个 Rust 编写的超快 linter，替代了：
- Black（代码格式化）
- isort（导入排序）
- flake8（linting）
- 多个 flake8 插件

配置在 `pyproject.toml` 中统一管理。

## 📚 相关资源

- **SAGE 主仓库**: https://github.com/intellistream/SAGE
- **SAGE 文档**: https://sage.intellistream.com
- **PyPI 包**: https://pypi.org/search/?q=isage
- **Issue Tracker**: https://github.com/intellistream/sage-examples/issues

## 🤝 获取帮助

- GitHub Issues: 报告 bug 或请求功能
- GitHub Discussions: 提问和讨论
- GitHub Copilot Chat: 使用 "SAGE Examples Assistant" 模式

---

**记住**: 代码质量不是负担，而是长期可维护性的保证。Pre-commit hooks 帮助我们在提交前捕获问题，避免在 CI 中失败。
