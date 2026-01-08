# SAGE Examples Collection

Complete examples and tutorials demonstrating SAGE's capabilities.

## 🚀 Quick Start

**New to SAGE?** Start with tutorials:

```bash
# Your first SAGE program (30 seconds)
python examples/tutorials/hello_world.py

# Learn embeddings (2 minutes)
python examples/tutorials/embedding_demo.py

# Build an agent (5 minutes)
python examples/tutorials/agents/basic_agent.py
```

## 📁 Directory Structure

```
examples/
├── tutorials/          # 📚 Learning tutorials (START HERE!)
│   ├── hello_world.py
│   ├── agents/        # Agent tutorials
│   │   ├── config/   # Agent configurations
│   │   └── data/     # Agent test data
│   ├── multimodal/    # Text+Image+Video
│   ├── memory/        # Memory systems
│   │   ├── config/   # Memory configurations
│   │   └── data/     # Memory test data
│   ├── service/       # Service integration
│   ├── scheduler/     # Task scheduling
│   ├── sage_db/       # Vector database
│   ├── config/        # General configurations
│   ├── data/          # General data utilities
│   └── ...
│
├── apps/              # 🎯 Production applications
│   ├── run_video_intelligence.py
│   └── run_medical_diagnosis.py
│
└── memory/            # � Advanced memory examples (DEPRECATED - use tutorials/memory)
```

**Note**: RAG examples and benchmarks have been moved to `packages/sage-benchmark/`. See
`packages/sage-benchmark/README.md` for details.

## 📚 Examples by Level

### 🟢 Beginner (< 30 minutes)

Simple, focused tutorials to learn SAGE basics.

**Location**: `examples/tutorials/`

- **Hello World**: Your first pipeline
- **Embeddings**: Text embeddings basics
- **Basic Agent**: Create an AI agent
- **Simple RAG**: Question answering
- **Service Basics**: Embedding service, pipeline service

**Run**: See `examples/tutorials/README.md`

### 🟡 Intermediate (30 min - 2 hours)

Production-ready patterns and integrations.

**Location**: `packages/sage-benchmark/`, `examples/memory/`

- **Advanced RAG**: Dense/sparse retrieval, reranking, multimodal fusion (see `sage-benchmark`)
- **RAG Benchmarking**: Performance evaluation and metrics (see `sage-benchmark/benchmark_rag`)
- **Memory Systems**: RAG with memory, persistence patterns
- **Vector Databases**: Milvus, ChromaDB, FAISS integration (see `sage-benchmark`)
- **Distributed RAG**: Ray-based parallel processing (see `sage-benchmark`)

**See**: `packages/sage-benchmark/README.md` for RAG and benchmark examples

### 🔴 Advanced (2+ hours)

Complete applications and complex workflows.

**Location**: `examples/apps/`

- **Video Intelligence**: Multi-model video analysis
- **Medical Diagnosis**: AI medical imaging
- **Multi-agent Systems**: Coordinated AI agents

## 📦 Installation

### From PyPI (推荐)

```bash
# 最小安装（仅教程）
pip install isage-examples

# 完整安装（教程 + 应用）
pip install isage-examples[all]
pip install isage-apps[all]

# 或安装特定应用
pip install isage-apps[video]        # 视频智能
pip install isage-apps[medical]      # 医疗诊断
```

### 从源码安装（开发）

```bash
# 克隆仓库
git clone https://github.com/intellistream/sage-examples.git
cd sage-examples

# 快速开始（交互式安装）
./quickstart.sh

# 或手动安装
pip install -e .                     # isage-examples（可编辑模式）
pip install -e sage-apps[all]        # isage-apps（可编辑模式）
```

### 依赖说明

- `isage-examples`: 教程和基础示例
- `isage-apps`: 生产级应用示例
- 依赖的 SAGE 核心包会自动从 PyPI 安装

## ⚠️ Examples vs Tests

**This directory contains examples and demos, NOT tests.**

- **Examples** (`examples/`): How to use SAGE features
- **Unit Tests** (`packages/*/tests/`): Verify code correctness
- **Integration Tests** (`tools/tests/`): Test example execution

## 🎯 Learning Paths

### Path 1: RAG Developer

1. `packages/sage-benchmark/src/sage/benchmark/benchmark_rag/implementations/rag_simple.py` - Learn
   basics
1. `packages/sage-benchmark/src/sage/benchmark/benchmark_rag/implementations/qa_dense_retrieval_milvus.py`
   \- Add vector search
1. `packages/sage-benchmark/src/sage/benchmark/benchmark_rag/implementations/qa_rerank.py` - Improve
   results
1. `packages/sage-benchmark/src/sage/benchmark/benchmark_rag/implementations/qa_multimodal_fusion.py`
   \- Add multimodal
1. `tutorials/memory/rag_memory_pipeline.py` - Add memory

See `packages/sage-benchmark/README.md` for complete RAG documentation.

**Note**: All RAG examples have been moved from `examples/rag/` to `packages/sage-benchmark/`.

### Path 2: Agent Builder

1. `tutorials/agents/basic_agent.py` - Agent basics
1. `tutorials/agents/workflow_demo.py` - Workflows
1. `tutorials/agents/arxiv_search_tool.py` - Custom tools
1. `apps/run_medical_diagnosis.py` - Multi-agent app

### Path 3: Service Developer

1. `tutorials/service/embedding_service_demo.py` - Service basics
1. `tutorials/service/pipeline_as_service/` - Pipeline services
1. `tutorials/service/sage_db/` - Vector database service
1. `tutorials/service/sage_flow/` - Stream processing service

## 💡 Tips

**Running examples:**

```bash
# Always run from project root
cd /path/to/SAGE
python examples/tutorials/hello_world.py
```

**API Keys:**

```bash
# Copy and configure
cp .env.example .env
# Edit .env with your keys
```

**Configurations:**

```bash
# Tutorials have their own config directories
ls examples/tutorials/agents/config/*.yaml
ls examples/tutorials/memory/config/*.yaml

# RAG configs are in sage-benchmark
ls packages/sage-benchmark/src/sage/benchmark/benchmark_rag/implementations/config/*.yaml

# See respective README files for details
cat packages/sage-benchmark/src/sage/benchmark/benchmark_rag/implementations/config/README.md
```

**Troubleshooting:**

- Missing dependencies? Check `requirements.txt` in each category
- Import errors? Make sure you installed SAGE: `pip install -e packages/sage-libs`
- Need data? Check the `data/` subdirectory in each example category
- Need config? Check the `config/` subdirectory in each example category
- Need help? See `docs/COMMUNITY.md`

## 📖 Documentation

- **Tutorials README**: `examples/tutorials/README.md`
- **Apps README**: `examples/apps/README.md`
- **RAG & Benchmarks**: `packages/sage-benchmark/README.md`
- **Main Docs**: `docs/` and `docs-public/`
- **API Docs**: Docstrings in `packages/sage-libs/`

## 🔍 Quick Reference

### By Feature

- **Agents**: `tutorials/agents/`
- **RAG**: `packages/sage-benchmark/src/sage/benchmark/benchmark_rag/implementations/`
- **Multimodal**: `tutorials/multimodal/`,
  `sage-benchmark/src/sage/benchmark/benchmark_rag/implementations/qa_multimodal_fusion.py`
- **Memory**: `tutorials/memory/`
- **Services**: `tutorials/service/`
- **Streaming**: `tutorials/stream_mode/`
- **Distributed**:
  `sage-benchmark/src/sage/benchmark/benchmark_rag/implementations/qa_dense_retrieval_ray.py`
- **Benchmarking**: `packages/sage-benchmark/src/sage/benchmark/benchmark_rag/`

### By Technology

- **ChromaDB**:
  `sage-benchmark/src/sage/benchmark/benchmark_rag/implementations/config/config_qa_chroma.yaml`
- **Milvus**:
  `sage-benchmark/src/sage/benchmark/benchmark_rag/implementations/config/config_*_milvus.yaml`
- **Ray**: `sage-benchmark/src/sage/benchmark/benchmark_rag/implementations/config/config_ray.yaml`
- **OpenAI**: Most RAG examples in sage-benchmark
- **Hugging Face**: `sage-benchmark/src/sage/benchmark/benchmark_rag/implementations/qa_hf_model.py`
- **Local LLMs**: Various examples in sage-benchmark

### By Use Case

- **Question Answering**: `sage-benchmark/src/sage/benchmark/benchmark_rag/implementations/qa_*.py`
- **Document Search**:
  `sage-benchmark/src/sage/benchmark/benchmark_rag/implementations/build_*_index.py`
- **Image Search**: `tutorials/multimodal/`
- **Video Analysis**: `apps/run_video_intelligence.py`
- **Medical AI**: `apps/run_medical_diagnosis.py`
- **Web Services**: `tutorials/service/pipeline_as_service/`
- **RAG Benchmarking**: `sage-benchmark/src/sage/benchmark/benchmark_rag/`
