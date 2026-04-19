#!/usr/bin/env python3
"""
数据预处理脚本
将下载的数据集转换为训练/测试集，并生成模拟的诊断报告
"""

import json
import random
from pathlib import Path

from datasets import load_from_disk
from PIL import Image
from sklearn.model_selection import train_test_split

# Note: This script assumes sage-apps package is installed
# Install with: cd sage-apps && pip install -e .

# 当前 medical_diagnosis 应用目录
APP_DIR = Path(__file__).resolve().parent.parent


# 疾病类别映射 (模拟)
DISEASE_MAPPING = {
    0: {"name": "正常", "severity": "无", "description": "未见明显异常"},
    1: {
        "name": "轻度退行性变",
        "severity": "轻度",
        "description": "L4/L5椎间盘轻度退行性变",
    },
    2: {
        "name": "椎间盘突出",
        "severity": "中度",
        "description": "L4/L5椎间盘向后突出,压迫硬膜囊",
    },
    3: {
        "name": "多节段退行性变",
        "severity": "中度",
        "description": "L3/L4, L4/L5, L5/S1多节段退行性变",
    },
    4: {
        "name": "椎管狭窄",
        "severity": "重度",
        "description": "L4/L5椎管狭窄,硬膜囊受压",
    },
    5: {
        "name": "椎间盘脱出",
        "severity": "重度",
        "description": "L5/S1椎间盘脱出,游离到椎管内",
    },
    6: {"name": "骨质增生", "severity": "轻度", "description": "L3-L5椎体缘骨质增生"},
    7: {"name": "椎体滑脱", "severity": "中度", "description": "L4椎体前移,I度滑脱"},
    8: {"name": "韧带钙化", "severity": "轻度", "description": "后纵韧带钙化"},
}


def generate_mock_report(label: int, patient_info: dict) -> str:
    """生成模拟诊断报告"""

    disease_info = DISEASE_MAPPING.get(label, DISEASE_MAPPING[0])

    age = patient_info.get("age", 45)
    gender = patient_info.get("gender", "男")

    # 根据疾病生成症状
    if label == 0:
        symptoms = "无明显不适"
        findings = "腰椎MRI T2加权矢状位: 未见明显异常。各椎间盘信号正常，椎体排列整齐，椎管通畅。"
        conclusion = "影像学未见明显异常。"
        recommendations = "定期体检，保持良好的生活习惯。"
    elif label in [1, 6, 8]:
        symptoms = "偶尔腰部酸痛"
        findings = (
            f"腰椎MRI T2加权矢状位: {disease_info['description']}。椎管尚通畅，未见明显神经根受压。"
        )
        conclusion = f"{disease_info['name']}，程度{disease_info['severity']}。"
        recommendations = (
            "适当休息，避免久坐久站。可进行腰背肌锻炼，如游泳、普拉提等。必要时物理治疗。"
        )
    elif label in [2, 3]:
        symptoms = "腰痛伴右下肢放射痛3周"
        findings = f"腰椎MRI T2加权矢状位: {disease_info['description']}。相应节段椎管变窄，神经根可能受压。"
        conclusion = f"{disease_info['name']}，程度{disease_info['severity']}。"
        recommendations = "建议卧床休息2-3周，牵引治疗。口服非甾体抗炎药及神经营养药物。保守治疗无效时考虑手术治疗。"
    elif label == 7:
        symptoms = "腰部疼痛，活动受限"
        findings = f"腰椎MRI T2加权矢状位: {disease_info['description']}。相应节段不稳定。"
        conclusion = f"{disease_info['name']}，程度{disease_info['severity']}。"
        recommendations = "避免重体力劳动，佩戴腰围保护。核心肌群训练。症状明显时考虑手术固定。"
    else:  # 重度 (4, 5)
        symptoms = "腰痛伴双下肢麻木、无力2月"
        findings = f"腰椎MRI T2加权矢状位: {disease_info['description']}。马尾神经受压。"
        conclusion = f"{disease_info['name']}，程度{disease_info['severity']}。"
        recommendations = (
            "建议尽早手术治疗(椎间盘摘除术或椎管减压术)，以解除神经压迫。术后康复训练。"
        )

    report = f"""患者信息:
  年龄: {age}岁
  性别: {gender}
  主诉: {symptoms}

影像描述:
  {findings}

主要发现:
  - 病变节段: {"多节段" if label == 3 else "L4/L5或L5/S1"}
  - 病变类型: {disease_info["name"]}
  - 严重程度: {disease_info["severity"]}

诊断结论:
  {conclusion}

治疗建议:
  {recommendations}

注: 本报告仅供参考，请结合临床症状和其他检查结果综合判断。
"""

    return report


def prepare_dataset():
    """准备数据集"""

    dataset_path = APP_DIR / "data" / "medical" / "lumbar-spine-mri" / "cache"
    output_dir = APP_DIR / "data" / "processed"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 80)
    print("📊 数据预处理")
    print("=" * 80)

    # 加载数据集
    print("\n📂 加载数据集...")
    dataset = load_from_disk(str(dataset_path))
    print(f"   ✓ 已加载 {len(dataset)} 个样本")

    # 准备数据
    print("\n🔄 准备数据...")

    samples = []
    for i, sample in enumerate(dataset):  # type: ignore[arg-type]
        if not isinstance(sample, dict):
            continue
        label = sample["label"]
        image = sample["image"]

        # 生成患者信息
        age = random.randint(25, 75)
        gender = random.choice(["男", "女"])

        patient_info = {
            "age": age,
            "gender": gender,
            "patient_id": f"P{i + 1:04d}",
        }

        # 生成诊断报告
        report = generate_mock_report(label, patient_info)

        # 保存图像
        image_filename = f"case_{i + 1:04d}_label{label}.jpg"
        image_path = output_dir / "images" / image_filename
        image_path.parent.mkdir(exist_ok=True)

        if isinstance(image, Image.Image):
            # 统一resize到512x512
            image_resized = image.resize((512, 512), Image.Resampling.LANCZOS)
            image_resized.save(image_path, quality=95)

        # 保存报告
        report_filename = f"case_{i + 1:04d}_report.txt"
        report_path = output_dir / "reports" / report_filename
        report_path.parent.mkdir(exist_ok=True)

        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)

        # 记录样本信息
        disease_info = DISEASE_MAPPING.get(label, DISEASE_MAPPING[0])
        samples.append(
            {
                "case_id": f"case_{i + 1:04d}",
                "patient_id": patient_info["patient_id"],
                "age": age,
                "gender": gender,
                "label": label,
                "disease": disease_info["name"],
                "severity": disease_info["severity"],
                "image_path": str(image_path.relative_to(output_dir)),
                "report_path": str(report_path.relative_to(output_dir)),
            }
        )

        if (i + 1) % 20 == 0:
            print(f"   处理进度: {i + 1}/{len(dataset)}")

    print(f"   ✓ 已处理 {len(samples)} 个病例")

    # 划分训练/测试集 (80/20)
    print("\n✂️  划分训练/测试集...")

    train_samples, test_samples = train_test_split(
        samples, test_size=0.2, random_state=42, stratify=[s["label"] for s in samples]
    )

    print(f"   ✓ 训练集: {len(train_samples)} 样本")
    print(f"   ✓ 测试集: {len(test_samples)} 样本")

    # 保存索引文件
    print("\n💾 保存索引文件...")

    # 保存JSON格式
    with open(output_dir / "train_index.json", "w", encoding="utf-8") as f:
        json.dump(train_samples, f, ensure_ascii=False, indent=2)

    with open(output_dir / "test_index.json", "w", encoding="utf-8") as f:
        json.dump(test_samples, f, ensure_ascii=False, indent=2)

    with open(output_dir / "all_cases.json", "w", encoding="utf-8") as f:
        json.dump(samples, f, ensure_ascii=False, indent=2)

    print("   ✓ train_index.json")
    print("   ✓ test_index.json")
    print("   ✓ all_cases.json")

    # 生成统计报告
    print("\n📊 生成统计报告...")

    stats = {
        "total_samples": len(samples),
        "train_samples": len(train_samples),
        "test_samples": len(test_samples),
        "label_distribution": {},
        "disease_distribution": {},
        "severity_distribution": {},
        "age_range": [min(s["age"] for s in samples), max(s["age"] for s in samples)],
        "gender_distribution": {
            "男": sum(1 for s in samples if s["gender"] == "男"),
            "女": sum(1 for s in samples if s["gender"] == "女"),
        },
    }

    for sample in samples:
        label = sample["label"]
        disease = sample["disease"]
        severity = sample["severity"]

        stats["label_distribution"][label] = stats["label_distribution"].get(label, 0) + 1
        stats["disease_distribution"][disease] = stats["disease_distribution"].get(disease, 0) + 1
        stats["severity_distribution"][severity] = (
            stats["severity_distribution"].get(severity, 0) + 1
        )

    with open(output_dir / "stats.json", "w", encoding="utf-8") as f:
        json.dump(stats, f, ensure_ascii=False, indent=2)

    # 生成可读的统计报告
    with open(output_dir / "README.txt", "w", encoding="utf-8") as f:
        f.write("腰椎MRI数据集 - 处理后\n")
        f.write("=" * 80 + "\n\n")
        f.write(f"总样本数: {stats['total_samples']}\n")
        f.write(f"训练集: {stats['train_samples']}\n")
        f.write(f"测试集: {stats['test_samples']}\n\n")

        f.write("疾病分布:\n")
        for disease, count in sorted(stats["disease_distribution"].items(), key=lambda x: -x[1]):
            percentage = count / stats["total_samples"] * 100
            f.write(f"  - {disease}: {count} ({percentage:.1f}%)\n")

        f.write("\n严重程度分布:\n")
        for severity, count in stats["severity_distribution"].items():
            percentage = count / stats["total_samples"] * 100
            f.write(f"  - {severity}: {count} ({percentage:.1f}%)\n")

        f.write(f"\n年龄范围: {stats['age_range'][0]} - {stats['age_range'][1]} 岁\n")
        f.write("\n性别分布:\n")
        for gender, count in stats["gender_distribution"].items():
            percentage = count / stats["total_samples"] * 100
            f.write(f"  - {gender}: {count} ({percentage:.1f}%)\n")

        f.write("\n目录结构:\n")
        f.write("  - images/: MRI影像文件 (512x512 JPG)\n")
        f.write("  - reports/: 诊断报告文件 (TXT)\n")
        f.write("  - train_index.json: 训练集索引\n")
        f.write("  - test_index.json: 测试集索引\n")
        f.write("  - all_cases.json: 所有病例索引\n")
        f.write("  - stats.json: 统计信息 (JSON)\n")
        f.write("  - README.txt: 本文件\n")

    print("   ✓ stats.json")
    print("   ✓ README.txt")

    print("\n" + "=" * 80)
    print("✅ 数据预处理完成!")
    print(f"📁 输出目录: {output_dir}")
    print("=" * 80)

    # 显示一些统计信息
    print("\n📊 数据集统计:")
    print(f"   - 总样本: {stats['total_samples']}")
    print(f"   - 训练集: {stats['train_samples']}")
    print(f"   - 测试集: {stats['test_samples']}")
    print(f"\n🏥 疾病类型: {len(stats['disease_distribution'])} 种")
    for disease, count in sorted(stats["disease_distribution"].items(), key=lambda x: -x[1])[:5]:
        print(f"   - {disease}: {count}")


if __name__ == "__main__":
    prepare_dataset()
