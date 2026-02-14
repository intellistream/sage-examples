#!/usr/bin/env python3
"""
测试 sage-examples/apps 目录中所有应用的导入和基本功能
"""

import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_imports():
    """测试应用导入"""
    print("=" * 60)
    print("测试应用导入")
    print("=" * 60)

    tests_passed = 0
    tests_failed = 0

    apps_to_test = [
        ("run_article_monitoring.py", ["yaml", "requests"]),
        ("run_auto_scaling_chat.py", ["yaml"]),
        ("run_medical_diagnosis.py", ["yaml", "PIL", "numpy"]),
        ("run_smart_home.py", ["yaml"]),
        ("run_video_intelligence.py", ["cv2", "torch", "torchvision", "PIL"]),
        ("run_work_report.py", ["yaml"]),
    ]

    for app_file, required_modules in apps_to_test:
        print(f"\n测试: {app_file}")
        print(f"  检查依赖: {', '.join(required_modules)}")

        all_imported = True
        for module in required_modules:
            try:
                __import__(module)
                print(f"    ✓ {module}")
            except ImportError as e:
                print(f"    ✗ {module}: {e}")
                all_imported = False

        if all_imported:
            print(f"  ✅ {app_file} - 所有依赖已安装")
            tests_passed += 1
        else:
            print(f"  ⚠️  {app_file} - 部分依赖缺失")
            tests_failed += 1

    print("\n" + "=" * 60)
    print(f"测试结果: {tests_passed} 通过, {tests_failed} 失败")
    print("=" * 60)

    # Use assert instead of return for pytest
    assert tests_failed == 0, f"{tests_failed} 个应用的依赖缺失"


def test_script_help():
    """测试脚本 --help 参数"""
    print("\n" + "=" * 60)
    print("测试脚本 --help 参数")
    print("=" * 60)

    apps_dir = Path(__file__).parent
    test_scripts = []

    for script in apps_dir.glob("run_*.py"):
        print(f"\n测试: {script.name}")
        # 这里只检查文件存在，不实际运行，因为可能需要配置
        if script.exists():
            print("  ✓ 文件存在")
            test_scripts.append(script.name)
        else:
            print("  ✗ 文件不存在")

    print(f"\n找到 {len(test_scripts)} 个应用脚本")
    # Use assert instead of return for pytest
    assert len(test_scripts) > 0, "没有找到任何应用脚本"


def main():
    """运行所有测试"""
    print("SAGE Examples Apps 测试")
    print("测试环境: Python", sys.version.split()[0])
    print()

    results = []

    # 测试导入
    results.append(("导入测试", test_imports()))

    # 测试脚本
    results.append(("脚本检查", test_script_help()))

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    for name, passed in results:
        status = "✅ 通过" if passed else "❌ 失败"
        print(f"{name}: {status}")

    all_passed = all(r[1] for r in results)
    if all_passed:
        print("\n✅ 所有测试通过！")
        return 0
    else:
        print("\n⚠️  部分测试失败，请检查依赖。")
        return 1


if __name__ == "__main__":
    sys.exit(main())
