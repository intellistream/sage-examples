# SAGE Examples

[![CI Status](https://github.com/intellistream/sage-examples/workflows/Tests/badge.svg)](https://github.com/intellistream/sage-examples/actions)
[![Code Quality](https://github.com/intellistream/sage-examples/workflows/Quality/badge.svg)](https://github.com/intellistream/sage-examples/actions)
[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

Production-ready application examples for the SAGE framework.

## 🎯 What is This?

**sage-examples** showcases production application examples for [SAGE](https://github.com/intellistream/SAGE):

- **🎯 Examples**: Complete, runnable application demonstrations
- **📦 apps Package**: Installable application library (published to PyPI as `iapps`)

> **� Looking for tutorials?** Visit [SAGE/tutorials](https://github.com/intellistream/SAGE/tree/main/tutorials) for learning materials.

## 🚀 Quick Start

```bash
# Clone this repository
git clone https://github.com/intellistream/sage-examples.git
cd sage-examples

# Install (all dependencies included)
pip install -e .

# Run an application example
python examples/run_video_intelligence.py
```

> **New to SAGE?** Start with [SAGE/tutorials](https://github.com/intellistream/SAGE/tree/main/tutorials) first.

## 📁 Repository Structure

```
sage-examples/
├── examples/                  # 🎯 Production application examples
│   ├── run_video_intelligence.py
│   ├── run_medical_diagnosis.py
│   ├── run_smart_home.py
│   └── ...
│
├── apps/                 # 📦 Installable application package
│   ├── src/sage/apps/         # Application implementations
│   └── tests/                 # Package tests
│
├── docs/                      # 📖 Project documentation
└── pyproject.toml             # Project configuration
```

## 📚 Learning vs Examples

| Your Goal | Repository |
|-----------|------------|
| **Learn SAGE basics** | [SAGE/tutorials](https://github.com/intellistream/SAGE/tree/main/tutorials) |
| **See production examples** | [sage-examples](https://github.com/intellistream/sage-examples) (this repo) |
| **Install applications** | `pip install iapps` |

## 🎯 Application Examples

Complete, runnable applications demonstrating real-world use cases:

| Application | Description | Script |
|-------------|-------------|--------|
| 🎬 **Video Intelligence** | Multi-model video analysis | `examples/run_video_intelligence.py` |
| 🏥 **Medical Diagnosis** | AI medical image analysis | `examples/run_medical_diagnosis.py` |
| 🏠 **Smart Home** | IoT automation system | `examples/run_smart_home.py` |
| 📰 **Article Monitoring** | News monitoring pipeline | `examples/run_article_monitoring.py` |
| 💬 **Auto-scaling Chat** | Dynamic scaling chat | `examples/run_auto_scaling_chat.py` |
| ⚙️ **Runtime API Layering** | Facade vs Local/FlownetEnvironment contract demo | `examples/run_runtime_api_layering.py` |

See `examples/README.md` for details.

## 📦 Installation

```bash
# Clone repository
git clone https://github.com/intellistream/sage-examples.git
cd sage-examples

# Install (all dependencies included by default)
pip install -e .

# Or install from PyPI
pip install isage-examples

# Development mode (includes pytest, ruff, mypy)
pip install -e .[dev]
```

> **Note**: Following SAGE principles, all application dependencies are installed by default. No need for extra flags like `[video]` or `[medical]`.

## 🏗️ SAGE Architecture Overview

SAGE uses a strict 6-layer architecture with unidirectional dependencies:

```
┌─────────────────────────────────────────────┐
│ L6: Interface                                │  CLI, Web UI, Tools
├─────────────────────────────────────────────┤
│ L5: Applications                             │  Production Apps
├─────────────────────────────────────────────┤
│ L4: Middleware                               │  Domain Operators
├─────────────────────────────────────────────┤
│ L3: Core                                     │  Execution + Algorithms
│     ├─ Kernel (Batch/Stream Engine)         │
│     └─ Libs (RAG/Agents/Algorithms)         │
├─────────────────────────────────────────────┤
│ L2: Platform                                 │  Scheduler, Storage
├─────────────────────────────────────────────┤
│ L1: Foundation                               │  Config, Logging, LLM
└─────────────────────────────────────────────┘
```

**Dependency Rule**: Upper layers can depend on lower layers (L6→L5→...→L1), but never the reverse.

## 🛠️ Development

### Setup

```bash
# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Run all checks
pre-commit run --all-files
```

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Auto-fix issues
ruff check --fix .

# Type checking
mypy .
```

### Testing

```bash
# Run all tests
pytest

# Run specific tests
pytest examples/test_apps.py
pytest apps/tests/

# With coverage
pytest --cov=. --cov-report=html
```

See `docs/DEVELOPMENT.md` for complete development guide.

## 📖 Documentation

- **Examples Guide**: `examples/README.md` - Application examples
- **Development Guide**: `docs/DEVELOPMENT.md` - Contributing
- **SAGE Tutorials**: [SAGE/tutorials](https://github.com/intellistream/SAGE/tree/main/tutorials) - Learn SAGE
- **SAGE Docs**: https://intellistream.github.io/SAGE

## 🤝 Contributing

We welcome contributions! Please see:

1. **Development Guide**: `docs/DEVELOPMENT.md`
2. **Code of Conduct**: Follow respectful collaboration
3. **Issue Tracker**: https://github.com/intellistream/sage-examples/issues

### Adding Examples

1. **Tutorials**: Add to [SAGE/tutorials](https://github.com/intellistream/SAGE/tree/main/tutorials)
2. **Applications**: 
   - Implementation → `apps/src/sage/apps/your_app/`
   - Entry script → `examples/run_your_app.py`
3. **Tests**: Add tests and ensure they pass
4. **Dependencies**: Update `pyproject.toml`

## 🔗 Related Repositories

- **SAGE Main**: https://github.com/intellistream/SAGE
- **SAGE Benchmark**: https://github.com/intellistream/sage-benchmark
- **PyPI Packages**: https://pypi.org/search/?q=isage

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

## 🙋 Getting Help

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: Questions and community support
- **GitHub Copilot**: Use "SAGE Examples Assistant" chat mode

## 🌟 Star History

If you find this project helpful, please consider giving it a ⭐️!

---

**Made with ❤️ by the IntelliStream Team**
