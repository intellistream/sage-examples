"""SAGE applications built on the consolidated main-repo runtime.

This package contains production-ready applications demonstrating SAGE's
capabilities across various domains:

- video: Video intelligence and analysis
- medical_diagnosis: AI-assisted medical imaging diagnosis
- patent_landscape_mapper: Patent clustering, whitespace analysis, and assignee mapping
- sageflow_service_demo: Treat sageFlow as a vector snapshot service inside a SAGE workflow
- student_improvement: Personalized score improvement with stateful learning workflows
- ticket_triage: Customer support ticket triage with explicit stateful routing
- work_report_generator: Weekly/daily work report generator with GitHub integration
- literature_report_assistant: Literature search and reading report generation assistant

Architecture:
- 直接依赖主仓 `sage` 提供的流、运行时与服务能力
- 保持应用层最小封装，提供端到端示例
"""

from ._version import __version__

__all__ = [
    "__version__",
]
