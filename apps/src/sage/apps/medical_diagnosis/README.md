# Medical Diagnosis Application

SAGE 医疗诊断应用示例 - 展示如何使用 SAGE 构建多智能体医疗诊断系统。

## 📋 概述

这个应用展示了如何使用 SAGE 框架构建一个协作式医疗诊断系统，其中多个专业医生智能体协同工作，分析患者症状并提供诊断建议。

## 🏗️ 架构

```
medical_diagnosis/
├── agents/          # 智能体定义
│   ├── doctor.py    # 主治医生智能体
│   └── specialist.py # 专科医生智能体
├── config/          # 配置文件
│   └── agents.yaml  # 智能体配置
├── tools/           # 工具函数
│   ├── medical_knowledge.py  # 医学知识库
│   └── symptom_analyzer.py   # 症状分析工具
├── data/            # 数据文件
│   └── patient_cases/  # 患者案例
├── scripts/         # 脚本文件
└── run_diagnosis.py # 主运行脚本
```

## 🚀 快速开始

### 安装依赖

```bash
# 安装 SAGE
pip install isage-apps

# 或从源码安装
cd packages/sage-apps
pip install -e .
```

### 准备数据

```bash
# 运行数据准备脚本
cd src/sage/apps/medical_diagnosis
./setup_data.sh
```

### 运行诊断

```bash
# 单个案例诊断
python run_diagnosis.py --case patient_001

# 批量诊断
python run_diagnosis.py --batch --input-dir data/patient_cases/

# 交互式诊断
python run_diagnosis.py --interactive
```

## 📊 示例

### 单个患者诊断

```python
from sage.apps.medical_diagnosis import MedicalDiagnosisSystem

# 创建诊断系统
system = MedicalDiagnosisSystem()

# 患者症状
patient_data = {
    "age": 45,
    "gender": "male",
    "symptoms": ["头痛", "发烧", "咳嗽"],
    "duration": "3天",
    "medical_history": ["高血压"],
}

# 执行诊断
result = system.diagnose(patient_data)

# 查看结果
print(f"初步诊断: {result['diagnosis']}")
print(f"建议检查: {result['recommended_tests']}")
print(f"治疗方案: {result['treatment_plan']}")
```

### 批量处理

```python
from sage.apps.medical_diagnosis import run_batch_diagnosis

# 批量诊断
results = run_batch_diagnosis(input_dir="data/patient_cases/", output_dir="results/")

# 生成报告
for patient_id, diagnosis in results.items():
    print(f"患者 {patient_id}: {diagnosis['summary']}")
```

## 🎯 功能特性

- **多智能体协作**: 主治医生和专科医生协同诊断
- **知识库集成**: 整合医学知识库和诊断指南
- **症状分析**: 自动分析患者症状并生成诊断假设
- **治疗建议**: 基于诊断结果提供治疗方案
- **批量处理**: 支持批量处理多个患者案例
- **可视化结果**: 生成诊断报告和可视化图表

## 🔧 配置

编辑 `config/agents.yaml` 来配置智能体行为：

```yaml
agents:
  - name: primary_doctor
    role: 主治医生
    llm_config:
      model: gpt-4
      temperature: 0.7

  - name: cardiologist
    role: 心脏科专家
    llm_config:
      model: gpt-4
      temperature: 0.5
```

## 📝 数据格式

### 输入格式

患者案例应使用 JSON 格式：

```json
{
  "patient_id": "P001",
  "age": 45,
  "gender": "male",
  "chief_complaint": "胸痛",
  "symptoms": [
    {"name": "胸痛", "severity": "severe", "duration": "2小时"},
    {"name": "呼吸困难", "severity": "moderate", "duration": "30分钟"}
  ],
  "vital_signs": {
    "blood_pressure": "140/90",
    "heart_rate": 95,
    "temperature": 37.2
  },
  "medical_history": ["高血压", "糖尿病"]
}
```

### 输出格式

诊断结果：

```json
{
  "diagnosis": {
    "primary": "急性心肌梗死可能性高",
    "differential": ["不稳定型心绞痛", "主动脉夹层"],
    "confidence": 0.85
  },
  "recommended_tests": [
    "心电图",
    "心肌酶谱",
    "冠状动脉造影"
  ],
  "treatment_plan": {
    "immediate": ["氧疗", "硝酸甘油", "阿司匹林"],
    "follow_up": ["心脏超声", "冠脉介入"]
  },
  "reasoning": "基于患者症状、体征和病史，考虑急性冠脉综合征..."
}
```

## 🧪 测试

```bash
# 运行所有测试
pytest tests/medical_diagnosis/

# 运行单个测试
pytest tests/medical_diagnosis/test_diagnosis.py -v

# 运行带覆盖率的测试
pytest tests/medical_diagnosis/ --cov=sage.apps.medical_diagnosis
```

## 📚 相关文档

- [SAGE 框架文档](../../docs/)
- [多智能体系统指南](../../docs/guides/multi-agent.md)
- [医疗 AI 应用最佳实践](../../docs/tutorials/medical-ai.md)

## ⚠️ 免责声明

**重要**: 这是一个演示应用，仅用于教学和研究目的。**不应**用于实际医疗诊断。任何医疗决策都应由专业医疗人员做出。

## 📄 许可证

本应用遵循 SAGE 项目的 MIT 许可证。

## 🤝 贡献

欢迎贡献！请参阅 [CONTRIBUTING.md](../../../../CONTRIBUTING.md) 了解如何参与项目。

## 📧 联系方式

- 问题反馈: [GitHub Issues](https://github.com/intellistream/SAGE/issues)
- 讨论: [GitHub Discussions](https://github.com/intellistream/SAGE/discussions)

______________________________________________________________________

**构建于** [SAGE](https://github.com/intellistream/SAGE) - 下一代智能体框架
