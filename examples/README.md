# SAGE Application Examples# SAGE Applications Examples



Production-ready application examples demonstrating SAGE's capabilities in real-world scenarios.This directory contains example scripts for running applications from the `apps` package.



## 🎯 Overview## Overview



This directory contains **runnable application examples** that showcase complete end-to-end AI solutions built with SAGE.The `apps` package provides production-ready AI applications built on the SAGE framework. These

example scripts demonstrate how to use them.

**Architecture Note**: 

- **This directory (`examples/`)**: Entry point scripts that demonstrate how to use applications## Available Applications

- **`apps/` package**: The actual application code (published to PyPI as `iapps`)

### 1. Video Intelligence Pipeline

Think of it as:

- `examples/` = "How to run applications" (demonstrations)Multi-model video analysis combining CLIP and MobileNetV3 for comprehensive video understanding.

- `apps/` = "Application implementation" (library code)

**Run:**

## 📁 Available Applications

```bash

### 1. 🎬 Video Intelligencepython examples/apps/run_video_intelligence.py --video path/to/video.mp4

```

Multi-model video analysis combining CLIP and MobileNetV3 for comprehensive video understanding.

**Features:**

**Script**: `run_video_intelligence.py`

- Scene understanding with CLIP

```bash- Action recognition with MobileNetV3

python examples/run_video_intelligence.py --video path/to/video.mp4- Frame-by-frame analysis

```- Comprehensive video insights



**Features**:### 2. Medical Diagnosis System

- Scene understanding with CLIP

- Action recognition with MobileNetV3AI-assisted medical imaging analysis using multi-agent systems.

- Frame-by-frame analysis

- Comprehensive video insights**Run:**



**Dependencies**: `pip install isage-examples[examples]` or `pip install iapps[video]````bash

python examples/apps/run_medical_diagnosis.py

---```



### 2. 🏥 Medical Diagnosis**Features:**



AI-assisted medical imaging analysis using multi-agent systems.- Multi-agent diagnostic workflow

- Medical image analysis

**Script**: `run_medical_diagnosis.py`- Knowledge base integration

- Diagnostic report generation

```bash

python examples/run_medical_diagnosis.py### 3. Article Monitoring

```

Automated article/news monitoring and analysis pipeline.

**Features**:

- Multi-agent diagnostic workflow**Run:**

- Medical image analysis

- Knowledge base integration```bash

- Diagnostic report generationpython examples/apps/run_article_monitoring.py

```

**Dependencies**: `pip install isage-examples[examples]` or `pip install iapps[medical]`

**Features:**

---

- Article content extraction

### 3. 🏠 Smart Home- Sentiment analysis

- Topic classification

IoT automation and intelligent home control system.- Automated summarization



**Script**: `run_smart_home.py`### 4. Auto Scaling Chat



```bashScalable chat application with automatic resource scaling.

python examples/run_smart_home.py

```**Run:**



**Features**:```bash

- Device control and automationpython examples/apps/run_auto_scaling_chat.py

- Scene recognition```

- Energy optimization

- Voice command integration**Features:**



---- Dynamic scaling based on load

- Multi-turn conversation support

### 4. 📰 Article Monitoring- LLM integration

- Resource-aware execution

Automated article/news monitoring and analysis pipeline.

### 5. Smart Home

**Script**: `run_article_monitoring.py`

IoT-enabled smart home automation using SAGE pipelines.

```bash

python examples/run_article_monitoring.py**Run:**

```

```bash

**Features**:python examples/apps/run_smart_home.py

- Real-time article tracking```

- Content analysis and summarization

- Trend detection**Features:**

- Alert generation

- Sensor data processing

---- Device control automation

- Event-driven workflows

### 5. 💬 Auto-scaling Chat- Real-time monitoring



Dynamic scaling chat service with load balancing.## Installation



**Script**: `run_auto_scaling_chat.py`### Install All Applications



```bash```bash

python examples/run_auto_scaling_chat.pypip install -e packages/apps[all]

``````



**Features**:### Install Specific Applications

- Automatic scaling based on load

- Multi-model support```bash

- Queue management# Video Intelligence only

- Performance monitoringpip install -e packages/apps[video]



---# Medical Diagnosis only

pip install -e packages/apps[medical]

### 6. 📝 Work Report Generator```



Automated work report generation from task data.## Configuration



**Script**: `run_work_report.py`Each application can be configured using YAML files located in `examples/config/`:



```bash- Video Intelligence: `config_video_intelligence.yaml`

python examples/run_work_report.py- Medical Diagnosis: Custom configurations in the medical diagnosis data directory

```

## Development

**Features**:

- Task data analysisFor developing new applications or modifying existing ones, see:

- Report template generation

- Multi-format export- `packages/apps/README.md` - Package overview

- Customizable templates- `packages/apps/MIGRATION.md` - Migration guide

- `packages/apps/PACKAGE_CREATION_SUMMARY.md` - Implementation details

---

## Support

### 7. 🔍 Feature Extraction Demo

For questions or issues:

Feature extraction demonstration for various data types.

1. Check the application-specific documentation in `packages/apps/src/sage/apps/<app_name>/`

**Script**: `demo_feature_extraction.py`1. Review the main SAGE documentation

1. Open an issue on GitHub

```bash
python examples/demo_feature_extraction.py
```

**Features**:
- Text feature extraction
- Image feature extraction
- Embedding generation
- Similarity search

## 🚀 Quick Start

### Installation

```bash
# Install all example dependencies
pip install -e ".[examples]"

# Or install specific applications from apps
pip install iapps[video]      # Video intelligence
pip install iapps[medical]    # Medical diagnosis
pip install iapps[all]        # All applications
```

### Running Examples

```bash
# From project root
cd /path/to/sage-examples

# Run video intelligence
python examples/run_video_intelligence.py --video data/sample.mp4

# Run medical diagnosis
python examples/run_medical_diagnosis.py

# Run smart home
python examples/run_smart_home.py
```

## 📦 Relationship with apps

```
sage-examples/
├── examples/                          # This directory - Entry points
│   ├── run_video_intelligence.py     # Calls sage.apps.video
│   └── run_medical_diagnosis.py      # Calls sage.apps.medical_diagnosis
│
└── apps/                         # Application library
    └── src/sage/apps/                 # Actual implementation
        ├── video/                     # Video app code
        │   └── video_intelligence_pipeline.py
        └── medical_diagnosis/         # Medical app code
            └── diagnosis_pipeline.py
```

**Why this structure?**
- ✅ **Clean separation**: Demos vs. library code
- ✅ **PyPI distribution**: `apps` can be installed independently
- ✅ **Easy to use**: Users can `pip install iapps` without cloning examples
- ✅ **Maintainable**: Library code is properly packaged and versioned

## 🧪 Testing

```bash
# Run all example tests
pytest examples/test_apps.py -v

# Test specific application
pytest examples/test_apps.py::test_video_intelligence -v
```

## 📚 Learn More

- **Tutorials**: See `tutorials/` for learning SAGE basics
- **apps Documentation**: See `apps/README.md` for library details
- **SAGE Main Repository**: https://github.com/intellistream/SAGE

## 🤝 Contributing

When adding new application examples:

1. **Add implementation** to `apps/src/sage/apps/your_app/`
2. **Add entry script** to `examples/run_your_app.py`
3. **Update this README** with your application description
4. **Add tests** to `examples/test_apps.py`
5. **Update dependencies** in `pyproject.toml`

## 📝 Notes

- All examples use environment variables from `.env` (copy from `.env.template`)
- Some examples require API keys (OpenAI, HuggingFace, etc.)
- For production use, consider installing `iapps` package directly
- These scripts are optimized for demonstration, not production deployment

---

**Need help?** Check `docs/DEVELOPMENT.md` or open an issue on GitHub.
