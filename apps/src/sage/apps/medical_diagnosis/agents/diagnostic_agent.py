"""
医疗诊断Agent - 主Agent
负责协调影像分析、知识检索和报告生成
"""

from pathlib import Path
from typing import Any

import yaml

# 导入 DiagnosisReport，DiagnosisResult 作为别名以保持向后兼容
from .report_generator import DiagnosisReport

# 向后兼容别名
DiagnosisResult = DiagnosisReport


class DiagnosticAgent:
    """
    腰椎MRI诊断Agent

    功能:
    1. 接收MRI影像和患者信息
    2. 调用影像分析Agent提取特征
    3. 检索相关医学知识和相似病例
    4. 生成诊断报告
    """

    def __init__(self, config_path: str | None = None):
        """
        初始化诊断Agent

        Args:
            config_path: 配置文件路径
        """
        self.config = self._load_config(config_path)
        self.image_analyzer = None
        self.knowledge_base = None
        self.report_generator = None
        self._setup_components()

    def _load_config(self, config_path: str | None) -> dict:
        """加载配置"""
        if config_path and Path(config_path).exists():
            with open(config_path, encoding="utf-8") as f:
                return yaml.safe_load(f)

        # 默认配置
        return {
            "agent": {
                "name": "LumbarSpineDiagnosticAgent",
                "version": "1.0.0",
                "max_iterations": 5,
            },
            "models": {
                "vision_model": "Qwen/Qwen2-VL-7B-Instruct",
                "llm_model": "Qwen/Qwen2.5-7B-Instruct",
                "embedding_model": "BAAI/bge-large-zh-v1.5",
            },
            "services": {
                "sagellm": {"enabled": True, "gpu_memory_utilization": 0.9},
                "embedding": {"method": "hf", "cache_enabled": True},
                "vector_db": {"collection_name": "lumbar_spine_cases", "top_k": 5},
            },
        }

    def _setup_components(self):
        """设置组件"""
        from sage.apps.medical_diagnosis.agents.image_analyzer import ImageAnalyzer
        from sage.apps.medical_diagnosis.agents.report_generator import ReportGenerator
        from sage.apps.medical_diagnosis.tools.knowledge_base import MedicalKnowledgeBase

        # 初始化各个组件
        self.image_analyzer = ImageAnalyzer(self.config)
        self.knowledge_base = MedicalKnowledgeBase(self.config)
        self.report_generator = ReportGenerator(self.config)

        print("✅ DiagnosticAgent 初始化完成")
        print(f"   Vision Model: {self.config['models']['vision_model']}")
        print(f"   LLM Model: {self.config['models']['llm_model']}")

    def diagnose(
        self,
        image_path: str,
        patient_info: dict[str, Any] | None = None,
        verbose: bool = True,
    ) -> DiagnosisResult:
        """
        执行诊断

        Args:
            image_path: MRI影像路径
            patient_info: 患者信息（年龄、性别、症状等）
            verbose: 是否打印详细信息

        Returns:
            DiagnosisResult: 诊断结果
        """
        if verbose:
            print(f"\n{'=' * 60}")
            print("🏥 开始诊断分析")
            print(f"{'=' * 60}")
            print(f"📄 影像路径: {image_path}")
            if patient_info:
                print(f"👤 患者信息: {patient_info}")

        # Step 1: 影像分析
        if verbose:
            print("\n📊 Step 1: 影像特征提取...")

        if not self.image_analyzer:
            raise RuntimeError("Image analyzer not initialized")
        image_features = self.image_analyzer.analyze(image_path)

        if verbose:
            print(f"   ✓ 检测到 {len(image_features.get('vertebrae', []))} 个椎体")
            print(f"   ✓ 检测到 {len(image_features.get('discs', []))} 个椎间盘")
            if image_features.get("abnormalities"):
                print(f"   ⚠ 发现 {len(image_features['abnormalities'])} 处异常")

        # Step 2: 知识库检索
        if verbose:
            print("\n🔍 Step 2: 检索相关知识和病例...")

        # 构建查询
        query = self._build_query(image_features, patient_info)

        # 检索相似病例
        if not self.knowledge_base:
            raise RuntimeError("Knowledge base not initialized")
        similar_cases = self.knowledge_base.retrieve_similar_cases(
            query=query,
            image_features=image_features,
            top_k=self.config["services"]["vector_db"]["top_k"],
        )

        if verbose:
            print(f"   ✓ 检索到 {len(similar_cases)} 个相似病例")

        # 检索医学知识
        medical_knowledge = self.knowledge_base.retrieve_knowledge(query=query, top_k=3)

        # Step 3: 生成诊断报告
        if verbose:
            print("\n📝 Step 3: 生成诊断报告...")

        if not self.report_generator:
            raise RuntimeError("Report generator not initialized")
        diagnosis_result = self.report_generator.generate(
            image_features=image_features,
            patient_info=patient_info,
            similar_cases=similar_cases,
            medical_knowledge=medical_knowledge,
        )

        if verbose:
            print("   ✓ 报告生成完成")
            print(f"\n{'=' * 60}")
            print("📋 诊断结果")
            print(f"{'=' * 60}")
            print(f"\n{diagnosis_result.report}")

        return diagnosis_result

    def _build_query(self, image_features: dict, patient_info: dict | None) -> str:
        """构建检索查询"""
        query_parts = []

        # 添加影像发现
        if image_features.get("abnormalities"):
            findings = [a["description"] for a in image_features["abnormalities"]]
            query_parts.append(f"影像发现: {', '.join(findings)}")

        # 添加患者症状
        if patient_info and "symptoms" in patient_info:
            query_parts.append(f"症状: {patient_info['symptoms']}")

        # 添加年龄信息
        if patient_info and "age" in patient_info:
            age = patient_info["age"]
            if age > 60:
                query_parts.append("老年患者退行性变化")
            elif age > 40:
                query_parts.append("中年腰椎病变")

        return " ".join(query_parts)

    def batch_diagnose(
        self, cases: list[dict[str, Any]], output_dir: str | None = None
    ) -> list[DiagnosisResult]:
        """
        批量诊断

        Args:
            cases: 病例列表，每个包含 image_path 和 patient_info
            output_dir: 输出目录

        Returns:
            诊断结果列表
        """
        results = []

        print(f"\n🏥 批量诊断开始 - 共 {len(cases)} 个病例")

        for i, case in enumerate(cases, 1):
            print(f"\n处理病例 {i}/{len(cases)}")

            result = self.diagnose(
                image_path=case["image_path"],
                patient_info=case.get("patient_info"),
                verbose=False,
            )

            results.append(result)

            # 保存结果
            if output_dir:
                output_path = Path(output_dir) / f"case_{i:03d}_report.txt"
                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, "w", encoding="utf-8") as f:
                    f.write(result.report)

        print("\n✅ 批量诊断完成！")
        return results


if __name__ == "__main__":
    # 测试代码
    agent = DiagnosticAgent()

    # 示例诊断
    result = agent.diagnose(
        image_path="data/medical/test/sample_mri.jpg",
        patient_info={"age": 45, "gender": "male", "symptoms": "下背部疼痛，左腿麻木"},
    )
