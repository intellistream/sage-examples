"""Interactive console app for the student improvement MVP."""

from __future__ import annotations

import io
import json
from contextlib import redirect_stderr, redirect_stdout
from pathlib import Path
from typing import Any

from .llm import SageOpenAIClient, SageOpenAISettings
from .service import create_demo_application_service, load_demo_exam_records


def _to_payload(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    if isinstance(value, list):
        return [_to_payload(item) for item in value]
    if isinstance(value, dict):
        return {key: _to_payload(item) for key, item in value.items()}
    return value


def _print_compact_section(title: str, payload: dict[str, Any]) -> None:
    print("=" * 72)
    print(title)
    print("=" * 72)
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    print()


def _quiet_runtime_call(function, *args, **kwargs):
    sink = io.StringIO()
    with redirect_stdout(sink), redirect_stderr(sink):
        return function(*args, **kwargs)


def _print_section(title: str) -> None:
    print("\n" + "=" * 72)
    print(title)
    print("=" * 72)


def _status_label(status: str) -> str:
    mapping = {
        "mastered": "已掌握",
        "reviewing": "复习中",
        "unmastered": "未掌握",
        "unknown": "未知",
    }
    return mapping.get(status, status)


def _score_bar(current: float, maximum: float, width: int = 24) -> str:
    if maximum <= 0:
        return "-" * width
    ratio = max(0.0, min(1.0, current / maximum))
    filled = round(width * ratio)
    return "#" * filled + "." * (width - filled)


def _mastery_bar(score: float | None, width: int = 16) -> str:
    if score is None:
        return "?" * width
    ratio = max(0.0, min(1.0, score))
    filled = round(width * ratio)
    return "#" * filled + "." * (width - filled)


def _format_knowledge_names(knowledge_point_ids: list[str], graph_payload: dict[str, Any]) -> str:
    knowledge_nodes = {
        node["node_id"]: node["label"]
        for node in graph_payload["nodes"]
        if node["node_type"] == "knowledge_point"
    }
    names = [knowledge_nodes.get(item, item) for item in knowledge_point_ids]
    return "、".join(names)


def _print_exam_snapshot(title: str, payload: dict[str, Any], graph_payload: dict[str, Any]) -> None:
    _print_section(title)
    print(
        f"成绩: {payload['total_score']}/{payload['max_score']}  "
        f"[{_score_bar(payload['total_score'], payload['max_score'])}]"
    )
    print(f"新增错题数: {payload['wrong_question_count']}")
    print(
        "薄弱知识点: "
        + "、".join(item["knowledge_point"] for item in payload["diagnosis"]["weak_knowledge_points"][:3])
    )
    current_exam_time = payload["diagnosis"]["generated_at"]
    new_wrong_questions = [
        item for item in payload["wrong_questions"] if item["last_seen_at"] == current_exam_time
    ]

    print("\n本次新增错题诊断")
    if not new_wrong_questions:
        print("本次没有新增错题。")
    for index, item in enumerate(new_wrong_questions, start=1):
        knowledge_names = _format_knowledge_names(item["knowledge_point_ids"], graph_payload)
        print(f"{index}. {item['question_id']} | {knowledge_names}")
        print(f"   题目: {item['prompt']}")
        print(f"   学生答案: {item['student_answer']} | 标准答案: {item['correct_answer']}")
        print(f"   错因: {'、'.join(item['wrong_cause_tags'])}")
        if item["standard_solution"]:
            print(f"   标准解法: {item['standard_solution'][0]}")

    print("\n学习路径")
    for step in payload["diagnosis"]["study_plan"]:
        print(f"{step['step_index']}. {step['title']}")
        print(f"   理由: {step['rationale']}")
        if step["recommended_actions"]:
            print(f"   动作: {'；'.join(step['recommended_actions'])}")


def _print_mastery_changes(
    first_payload: dict[str, Any],
    second_payload: dict[str, Any],
    graph_payload: dict[str, Any],
) -> None:
    _print_section("掌握度变化")
    knowledge_nodes = [
        node for node in graph_payload["nodes"] if node["node_type"] == "knowledge_point"
    ]
    first_mastery = first_payload["diagnosis"]["mastery_summary"]
    second_mastery = second_payload["diagnosis"]["mastery_summary"]

    for node in knowledge_nodes:
        node_id = node["node_id"]
        first_score = first_mastery.get(node_id)
        second_score = second_mastery.get(node_id)
        if first_score is None and second_score is None:
            continue
        first_value = 0.0 if first_score is None else float(first_score)
        second_value = 0.0 if second_score is None else float(second_score)
        delta = second_value - first_value
        sign = "+" if delta >= 0 else ""
        print(
            f"- {node['label']}: "
            f"{first_value:.2f} [{_mastery_bar(first_value)}] -> "
            f"{second_value:.2f} [{_mastery_bar(second_value)}]  "
            f"({sign}{delta:.2f}, {_status_label(node['mastery_status'])})"
        )


def _print_wrong_bank(final_wrong_bank: list[dict[str, Any]], graph_payload: dict[str, Any]) -> None:
    _print_section("动态错题集")
    for item in final_wrong_bank:
        knowledge_names = _format_knowledge_names(item["knowledge_point_ids"], graph_payload)
        print(
            f"- {item['question_id']} | {knowledge_names} | "
            f"状态={_status_label(item['mastery_status'])} | 次数={item['occurrence_count']} | "
            f"优先级={item['priority']:.1f}"
        )


def _print_knowledge_graph(graph_payload: dict[str, Any]) -> None:
    _print_section("知识图谱视图")
    chapter_nodes = [node for node in graph_payload["nodes"] if node["node_type"] == "chapter"]
    knowledge_nodes = {
        node["node_id"]: node
        for node in graph_payload["nodes"]
        if node["node_type"] == "knowledge_point"
    }
    contains_edges = [edge for edge in graph_payload["edges"] if edge["relation"] == "contains"]
    prerequisite_nodes = {
        edge["target_id"]: []
        for edge in graph_payload["edges"]
        if edge["relation"] == "prerequisite_of"
    }
    for edge in graph_payload["edges"]:
        if edge["relation"] == "prerequisite_of":
            prerequisite_nodes.setdefault(edge["target_id"], []).append(edge["source_id"])

    for chapter in chapter_nodes:
        print(f"[{chapter['label']}]")
        chapter_children = [
            knowledge_nodes[edge["target_id"]]
            for edge in contains_edges
            if edge["source_id"] == chapter["node_id"] and edge["target_id"] in knowledge_nodes
        ]
        for knowledge in chapter_children:
            prerequisites = [
                knowledge_nodes[item]["label"]
                for item in prerequisite_nodes.get(knowledge["node_id"], [])
                if item in knowledge_nodes
            ]
            prerequisite_text = "无" if not prerequisites else "、".join(prerequisites)
            score = knowledge.get("mastery_score")
            score_text = "N/A" if score is None else f"{float(score):.2f}"
            print(
                f"  - {knowledge['label']} | {score_text} [{_mastery_bar(score if score is not None else None)}] "
                f"| {_status_label(knowledge['mastery_status'])} | 前置: {prerequisite_text}"
            )


def run_demo_once(storage_path: str | Path | None = None, *, json_mode: bool = False) -> None:
    service = _quiet_runtime_call(create_demo_application_service, storage_path=storage_path)
    exams = load_demo_exam_records()
    if not exams:
        raise RuntimeError("Demo exam records are empty.")

    student_id = exams[0].student_id
    first_result = _quiet_runtime_call(service.import_exam, exams[0])
    first_graph = _to_payload(_quiet_runtime_call(service.get_student_knowledge_graph, student_id))
    second_result = _quiet_runtime_call(service.import_exam, exams[1])
    second_graph = _to_payload(_quiet_runtime_call(service.get_student_knowledge_graph, student_id))

    if json_mode:
        _print_compact_section("第一次考试导入结果", _to_payload(first_result))
        _print_compact_section("第二次考试导入结果", _to_payload(second_result))
        _print_compact_section("最终学生档案", _to_payload(service.get_student_profile(student_id)))
        _print_compact_section(
            "最终错题集",
            {"wrong_questions": _to_payload(service.get_wrong_question_bank(student_id))},
        )
        _print_compact_section("最终知识图谱", second_graph)
        return

    first_payload = first_result.to_dict()
    second_payload = second_result.to_dict()
    final_profile = _to_payload(service.get_student_profile(student_id))
    final_wrong_bank = _to_payload(service.get_wrong_question_bank(student_id))

    print("\n📘 SAGE Personalized Score Improvement MVP")
    print("展示流程: 初始化课程 -> 导入第一次考试 -> 导入第二次考试 -> 查看状态更新\n")
    print(f"学生: {final_profile['student_id']} | {final_profile['grade']} {final_profile['subject']}")
    print("课程: 八年级数学教材知识图谱 + 两次考试增量导入")
    print(f"诊断概览: {final_profile['diagnosis_overview']}")

    _print_exam_snapshot("第一次考试后", first_payload, first_graph)
    _print_exam_snapshot("第二次考试后", second_payload, second_graph)
    _print_mastery_changes(first_payload, second_payload, second_graph)
    _print_wrong_bank(final_wrong_bank, second_graph)
    _print_knowledge_graph(second_graph)


class StudentImprovementConsoleApp:
    """Interactive console app that keeps running until the user exits."""

    def __init__(self, storage_path: str | Path | None = None) -> None:
        self.storage_path = None if storage_path is None else Path(storage_path)
        self.service = _quiet_runtime_call(
            create_demo_application_service,
            storage_path=self.storage_path,
        )
        self.demo_exams = load_demo_exam_records()
        self.student_id = self.demo_exams[0].student_id if self.demo_exams else ""
        self.session_results: list[dict[str, Any]] = []
        self.session_graphs: list[dict[str, Any]] = []

    def run(self) -> None:
        print("\n📘 SAGE Personalized Score Improvement App")
        print("这个交互式 app 会持续运行，直到你主动选择退出。")

        while True:
            self._print_status()
            choice = input("\n请选择操作 [1-7, 0 退出]: ").strip()
            print()
            if choice == "1":
                self.import_next_demo_exam(render=True)
            elif choice == "2":
                self.show_dashboard()
            elif choice == "3":
                self.show_wrong_bank()
            elif choice == "4":
                self.show_knowledge_graph()
            elif choice == "5":
                self.test_llm_connection()
            elif choice == "6":
                self.show_ai_guidance()
            elif choice == "7":
                self.reset_demo_state()
            elif choice == "0":
                print("已退出 Student Improvement App。")
                return
            else:
                print("无效输入，请输入菜单中的编号。")

    def _print_status(self) -> None:
        imported_exams = self.service.list_student_exams(self.student_id) if self.student_id else []
        imported_ids = {exam.exam_id for exam in imported_exams}
        remaining = [exam for exam in self.demo_exams if exam.exam_id not in imported_ids]
        llm_settings = SageOpenAISettings.from_env()
        print("\n" + "-" * 72)
        print("菜单")
        print("-" * 72)
        print(f"已导入 demo 考试: {len(imported_exams)}/{len(self.demo_exams)}")
        print(f"剩余待导入: {len(remaining)}")
        print(f"LLM 增强: {'已配置' if llm_settings.configured else '未配置'}")
        print("1. 导入下一次 demo 考试")
        print("2. 查看当前学生总览")
        print("3. 查看动态错题集")
        print("4. 查看知识图谱")
        print("5. 测试本地/私有大模型连接")
        print("6. 生成 AI 增强学习建议")
        print("7. 重置 demo 状态")
        print("0. 退出")

    def _next_demo_exam(self):
        imported_ids = {exam.exam_id for exam in self.service.list_student_exams(self.student_id)}
        for exam in self.demo_exams:
            if exam.exam_id not in imported_ids:
                return exam
        return None

    def import_next_demo_exam(self, *, render: bool = False) -> tuple[dict[str, Any], dict[str, Any]] | None:
        next_exam = self._next_demo_exam()
        if next_exam is None:
            print("所有 demo 考试都已经导入完毕。可选择查看总览，或重置 demo 状态。")
            return None

        result = _quiet_runtime_call(self.service.import_exam, next_exam)
        graph = _quiet_runtime_call(self.service.get_student_knowledge_graph, self.student_id)
        result_payload = result.to_dict()
        graph_payload = _to_payload(graph)
        self.session_results.append(result_payload)
        self.session_graphs.append(graph_payload)

        if render:
            _print_exam_snapshot(f"导入 {next_exam.exam_id} 后", result_payload, graph_payload)
        return result_payload, graph_payload

    def show_dashboard(self) -> None:
        try:
            profile = _to_payload(_quiet_runtime_call(self.service.get_student_profile, self.student_id))
            diagnosis = _to_payload(
                _quiet_runtime_call(self.service.get_student_diagnosis, self.student_id)
            )
            graph = _to_payload(
                _quiet_runtime_call(self.service.get_student_knowledge_graph, self.student_id)
            )
        except KeyError:
            print("当前还没有学生诊断数据。请先导入一次考试。")
            return

        _print_section("当前学生总览")
        print(f"学生: {profile['student_id']} | {profile['grade']} {profile['subject']}")
        print(f"诊断概览: {profile['diagnosis_overview']}")
        print(
            "当前薄弱知识点: "
            + "、".join(item["knowledge_point"] for item in diagnosis["weak_knowledge_points"][:3])
        )
        print("下次练习任务: " + "；".join(diagnosis.get("next_practice_tasks", [])[:3]))

        if len(self.session_results) >= 2 and self.session_graphs:
            _print_mastery_changes(
                self.session_results[-2],
                self.session_results[-1],
                self.session_graphs[-1],
            )
        else:
            print("\n掌握度变化将在本次 app 会话中连续导入两次考试后展示。")

        _print_knowledge_graph(graph)

    def show_wrong_bank(self) -> None:
        try:
            wrong_bank = _to_payload(
                _quiet_runtime_call(self.service.get_wrong_question_bank, self.student_id)
            )
            graph = _to_payload(
                _quiet_runtime_call(self.service.get_student_knowledge_graph, self.student_id)
            )
        except KeyError:
            print("当前还没有错题集。请先导入一次考试。")
            return
        if not wrong_bank:
            print("当前错题集为空。")
            return
        _print_wrong_bank(wrong_bank, graph)

    def show_knowledge_graph(self) -> None:
        graph = _to_payload(_quiet_runtime_call(self.service.get_student_knowledge_graph, self.student_id))
        _print_knowledge_graph(graph)

    def test_llm_connection(self) -> None:
        try:
            client = SageOpenAIClient()
            model_ids = client.list_models()
        except Exception as exc:  # noqa: BLE001
            print(f"LLM 连接测试失败: {exc}")
            print(
                "请设置环境变量 SAGE_OPENAI_API_KEY，必要时再设置 SAGE_OPENAI_BASE_URL 和 SAGE_OPENAI_MODEL。",
            )
            return

        _print_section("LLM 连接测试")
        print(f"Base URL: {client.settings.base_url}")
        print(f"可用模型数: {len(model_ids)}")
        for model_id in model_ids[:10]:
            print(f"- {model_id}")

    def show_ai_guidance(self) -> None:
        try:
            profile = _to_payload(_quiet_runtime_call(self.service.get_student_profile, self.student_id))
            diagnosis = _to_payload(
                _quiet_runtime_call(self.service.get_student_diagnosis, self.student_id)
            )
            wrong_bank = _to_payload(
                _quiet_runtime_call(self.service.get_wrong_question_bank, self.student_id)
            )
            graph = _to_payload(
                _quiet_runtime_call(self.service.get_student_knowledge_graph, self.student_id)
            )
            client = SageOpenAIClient()
            guidance = client.generate_learning_guidance(
                student_profile=profile,
                diagnosis=diagnosis,
                wrong_question_bank=wrong_bank,
                knowledge_graph=graph,
            )
        except Exception as exc:  # noqa: BLE001
            print(f"AI 增强建议生成失败: {exc}")
            return

        _print_section("AI 增强学习建议")
        print(guidance)

    def reset_demo_state(self) -> None:
        if self.storage_path is not None and self.storage_path.exists():
            self.storage_path.unlink()
        self.service = _quiet_runtime_call(
            create_demo_application_service,
            storage_path=self.storage_path,
        )
        self.session_results.clear()
        self.session_graphs.clear()
        print("已重置 demo 状态。")
