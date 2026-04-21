"""检验样本周转异常预警系统 application."""

from .pipeline import run_lab_turnaround_alert_pipeline

__all__ = ["run_lab_turnaround_alert_pipeline"]
