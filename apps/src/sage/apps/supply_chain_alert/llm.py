"""Optional SAGE serving gateway integration for natural-language risk explanations."""

from __future__ import annotations

import json
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

from sage.foundation import SagePorts
from sage.serving import SageServeConfig, probe_gateway

from .models import (
    AlertExplanation,
    DashboardSnapshot,
    GatewayExplanationStatus,
    OpenAlert,
    RiskExplanationResult,
    SupplierRiskSummary,
)

try:
    import httpx
    from openai import OpenAI
except ImportError:  # pragma: no cover - dependency availability is environment-specific
    httpx = None
    OpenAI = None

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover - dependency availability is environment-specific
    load_dotenv = None


DEFAULT_USER_AGENT = "sage-supply-chain-alert/0.1.0"


def _load_local_env_file(env_file: str | os.PathLike[str] | None = None) -> None:
    if load_dotenv is None:
        return

    candidate_paths: list[Path] = []
    if env_file is not None:
        candidate_paths.append(Path(env_file).expanduser())
    else:
        candidate_paths.append(Path.cwd() / ".env")
        for parent in Path(__file__).resolve().parents:
            candidate_paths.append(parent / ".env")

    seen_paths: set[Path] = set()
    for candidate_path in candidate_paths:
        resolved_path = candidate_path.resolve()
        if resolved_path in seen_paths:
            continue
        seen_paths.add(resolved_path)
        if resolved_path.is_file():
            load_dotenv(dotenv_path=resolved_path, override=False)
            return


@dataclass(frozen=True)
class SupplyChainGatewaySettings:
    base_url_override: str | None = None
    health_url_override: str | None = None
    host: str = "127.0.0.1"
    port: int = SagePorts.SAGELLM_GATEWAY
    model: str | None = None
    api_key: str = "EMPTY"
    health_timeout: float = 3.0
    request_timeout: float = 30.0

    @classmethod
    def from_env(
        cls,
        env_file: str | os.PathLike[str] | None = None,
    ) -> SupplyChainGatewaySettings:
        _load_local_env_file(env_file)
        port_value = os.getenv("SAGE_SUPPLY_CHAIN_GATEWAY_PORT")
        base_url = os.getenv("SAGE_SUPPLY_CHAIN_BASE_URL") or os.getenv("SAGE_OPENAI_BASE_URL")
        api_key = (
            os.getenv("SAGE_SUPPLY_CHAIN_API_KEY")
            or os.getenv("SAGE_OPENAI_API_KEY")
            or os.getenv("OPENAI_API_KEY")
            or "EMPTY"
        )
        model = os.getenv("SAGE_SUPPLY_CHAIN_MODEL") or os.getenv("SAGE_OPENAI_MODEL")
        return cls(
            base_url_override=base_url.rstrip("/") if base_url else None,
            health_url_override=os.getenv("SAGE_SUPPLY_CHAIN_HEALTH_URL"),
            host=os.getenv("SAGE_SUPPLY_CHAIN_GATEWAY_HOST", "127.0.0.1"),
            port=int(port_value) if port_value else SagePorts.SAGELLM_GATEWAY,
            model=model,
            api_key=api_key,
            health_timeout=float(os.getenv("SAGE_SUPPLY_CHAIN_HEALTH_TIMEOUT", "3.0")),
            request_timeout=float(os.getenv("SAGE_SUPPLY_CHAIN_REQUEST_TIMEOUT", "30.0")),
        )

    @property
    def gateway_config(self) -> SageServeConfig:
        return SageServeConfig(host=self.host, port=self.port, model=self.model)

    @property
    def base_url(self) -> str:
        if self.base_url_override is not None:
            return self.base_url_override
        return self.gateway_config.base_url

    @property
    def health_url(self) -> str:
        if self.health_url_override is not None:
            return self.health_url_override
        if self.base_url_override is not None:
            parsed = urlparse(self.base_url_override)
            return f"{parsed.scheme}://{parsed.netloc}/health"
        return self.gateway_config.health_url


class SupplyChainRiskExplainer:
    """Generate natural-language supply-chain risk explanations via SAGE serving."""

    def __init__(self, settings: SupplyChainGatewaySettings | None = None) -> None:
        self.settings = settings or SupplyChainGatewaySettings.from_env()

    def explain_current_risks(
        self,
        *,
        dashboard: DashboardSnapshot,
        alerts: list[OpenAlert],
        supplier_risk_summaries: list[SupplierRiskSummary],
        max_alerts: int = 5,
    ) -> RiskExplanationResult:
        probe = self._probe_gateway()
        if not probe.ok and self.settings.base_url_override is None:
            gateway_status = GatewayExplanationStatus(
                reachable=False,
                base_url=self.settings.base_url,
                health_url=self.settings.health_url,
                model=self.settings.model,
                status_code=probe.status_code,
                error=probe.error,
            )
            return RiskExplanationResult(
                generated_at=dashboard.generated_at,
                gateway_status=gateway_status,
            )

        try:
            client = self._build_client()
            model_name = self._resolve_model(client)
            dashboard_summary = self.generate_dashboard_summary(
                client=client,
                model_name=model_name,
                dashboard=dashboard,
                supplier_risk_summaries=supplier_risk_summaries,
            )
            alert_explanations = [
                AlertExplanation(
                    alert_id=alert.alert_id,
                    rule_id=alert.rule_id,
                    title=alert.title,
                    risk_level=alert.risk_level,
                    explanation=self.generate_alert_explanation(
                        client=client,
                        model_name=model_name,
                        alert=alert,
                        dashboard=dashboard,
                    ),
                )
                for alert in alerts[:max_alerts]
            ]
            return RiskExplanationResult(
                generated_at=dashboard.generated_at,
                gateway_status=GatewayExplanationStatus(
                    reachable=True,
                    base_url=self.settings.base_url,
                    health_url=self.settings.health_url,
                    model=model_name,
                    status_code=probe.status_code if probe.ok else None,
                    error=None,
                ),
                dashboard_summary=dashboard_summary,
                alert_explanations=alert_explanations,
            )
        except RuntimeError as exc:
            if not probe.ok:
                error_message = str(exc)
                return RiskExplanationResult(
                    generated_at=dashboard.generated_at,
                    gateway_status=GatewayExplanationStatus(
                        reachable=False,
                        base_url=self.settings.base_url,
                        health_url=self.settings.health_url,
                        model=self.settings.model,
                        status_code=probe.status_code,
                        error=error_message,
                    ),
                )
            return RiskExplanationResult(
                generated_at=dashboard.generated_at,
                gateway_status=GatewayExplanationStatus(
                    reachable=True,
                    base_url=self.settings.base_url,
                    health_url=self.settings.health_url,
                    model=self.settings.model,
                    status_code=probe.status_code,
                    error=str(exc),
                ),
            )

    def _probe_gateway(self):
        if self.settings.base_url_override is None:
            return probe_gateway(self.settings.gateway_config, timeout=self.settings.health_timeout)

        try:
            if httpx is None:
                raise RuntimeError("Missing httpx dependency for remote gateway probing.")
            with httpx.Client(timeout=self.settings.health_timeout) as client:
                response = client.get(self.settings.health_url)
                payload = None
                try:
                    payload = response.json()
                except ValueError:
                    payload = None
                return type("RemoteProbeResult", (), {
                    "ok": 200 <= response.status_code < 300,
                    "url": self.settings.health_url,
                    "status_code": response.status_code,
                    "payload": payload,
                    "error": None if 200 <= response.status_code < 300 else response.text,
                })()
        except Exception as exc:  # noqa: BLE001
            return type("RemoteProbeResult", (), {
                "ok": False,
                "url": self.settings.health_url,
                "status_code": None,
                "payload": None,
                "error": str(exc),
            })()

    def _build_client(self):
        if httpx is None:
            raise RuntimeError(
                "Missing gateway client dependencies. Ensure httpx is installed.",
            )
        if self.settings.base_url_override is not None:
            return httpx.Client(
                headers={
                    "User-Agent": DEFAULT_USER_AGENT,
                    "Authorization": f"Bearer {self.settings.api_key}",
                    "Content-Type": "application/json",
                },
                timeout=self.settings.request_timeout,
                follow_redirects=True,
            )
        if OpenAI is None:
            raise RuntimeError(
                "Missing OpenAI SDK dependency for local gateway mode. Ensure openai is installed.",
            )
        http_client = httpx.Client(
            headers={"User-Agent": DEFAULT_USER_AGENT},
            timeout=self.settings.request_timeout,
        )
        return OpenAI(
            base_url=self.settings.base_url,
            api_key=self.settings.api_key,
            http_client=http_client,
        )

    def _resolve_model(self, client) -> str:
        if self.settings.model:
            return self.settings.model
        if self.settings.base_url_override is not None:
            try:
                response = client.get(f"{self.settings.base_url}/models")
                response.raise_for_status()
            except Exception as exc:  # noqa: BLE001
                raise RuntimeError(f"Failed to list remote gateway models: {exc}") from exc
            payload = response.json()
            model_ids = [
                item.get("id")
                for item in payload.get("data", [])
                if isinstance(item, dict) and item.get("id")
            ]
            if not model_ids:
                raise RuntimeError("The configured SAGE gateway returned no models.")
            return model_ids[0]
        response = client.models.list()
        model_ids = [item.id for item in getattr(response, "data", [])]
        if not model_ids:
            raise RuntimeError("The configured SAGE gateway returned no models.")
        return model_ids[0]

    def generate_dashboard_summary(
        self,
        *,
        client,
        model_name: str,
        dashboard: DashboardSnapshot,
        supplier_risk_summaries: list[SupplierRiskSummary],
    ) -> str:
        payload = self._build_dashboard_prompt_payload(dashboard, supplier_risk_summaries)
        return self._complete_text(
            client=client,
            model_name=model_name,
            system_prompt=(
                "你是供应链风险运营助手。请基于结构化输入，输出一段简洁中文管理摘要。"
                "要求：1) 先说当前总风险 2) 点出最需要关注的两个问题 3) 最后给出一条总动作建议。"
                "不要编造输入中不存在的数据。"
            ),
            user_payload=payload,
        )

    def generate_alert_explanation(
        self,
        *,
        client,
        model_name: str,
        alert: OpenAlert,
        dashboard: DashboardSnapshot,
    ) -> str:
        payload = self._build_alert_prompt_payload(alert, dashboard)
        return self._complete_text(
            client=client,
            model_name=model_name,
            system_prompt=(
                "你是供应链异常解释助手。请针对单条预警输出简洁、可执行、可解释的中文说明。"
                "格式要求：先解释为什么触发，再说明可能业务影响，最后说明建议动作。"
                "不要使用项目符号，不要虚构额外事实。"
            ),
            user_payload=payload,
        )

    def _complete_text(
        self,
        *,
        client,
        model_name: str,
        system_prompt: str,
        user_payload: dict[str, object],
    ) -> str:
        if self.settings.base_url_override is not None:
            return self._complete_text_httpx(
                client=client,
                model_name=model_name,
                system_prompt=system_prompt,
                user_payload=user_payload,
            )
        response = client.chat.completions.create(
            model=model_name,
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": json.dumps(user_payload, ensure_ascii=False, indent=2),
                },
            ],
        )
        choices = getattr(response, "choices", None) or []
        if not choices:
            raise RuntimeError("SAGE gateway returned no completion choices.")

        message = getattr(choices[0], "message", None)
        content = getattr(message, "content", None)
        if isinstance(content, str) and content.strip():
            return content.strip()

        if isinstance(content, list):
            text_chunks = [
                item.get("text", "")
                for item in content
                if isinstance(item, dict) and item.get("type") in {"text", "output_text"}
            ]
            merged = "\n".join(chunk for chunk in text_chunks if chunk).strip()
            if merged:
                return merged

        raise RuntimeError("SAGE gateway returned an empty explanation response.")

    def _complete_text_httpx(
        self,
        *,
        client,
        model_name: str,
        system_prompt: str,
        user_payload: dict[str, object],
    ) -> str:
        request_payload = {
            "model": model_name,
            "temperature": 0.2,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": self._render_user_payload(user_payload)},
            ],
        }
        try:
            response = client.post(
                f"{self.settings.base_url}/chat/completions",
                json=request_payload,
            )
            response.raise_for_status()
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(f"Remote gateway completion failed: {exc}") from exc

        payload = response.json()
        choices = payload.get("choices", [])
        if not choices:
            raise RuntimeError("SAGE gateway returned no completion choices.")

        message = choices[0].get("message", {})
        content = message.get("content")
        if isinstance(content, str) and content.strip():
            return content.strip()

        if isinstance(content, list):
            text_chunks = [
                item.get("text", "")
                for item in content
                if isinstance(item, dict) and item.get("type") in {"text", "output_text"}
            ]
            merged = "\n".join(chunk for chunk in text_chunks if chunk).strip()
            if merged:
                return merged

        raise RuntimeError("SAGE gateway returned an empty explanation response.")

    def _build_dashboard_prompt_payload(
        self,
        dashboard: DashboardSnapshot,
        supplier_risk_summaries: list[SupplierRiskSummary],
    ) -> dict[str, Any]:
        return {
            "generated_at": dashboard.generated_at,
            "open_alert_count": dashboard.open_alert_count,
            "high_risk_alert_count": dashboard.high_risk_alert_count,
            "low_stock_sku_count": dashboard.low_stock_sku_count,
            "delayed_shipment_count": dashboard.delayed_shipment_count,
            "overdue_order_count": dashboard.overdue_order_count,
            "high_risk_supplier_count": dashboard.high_risk_supplier_count,
            "average_delay_hours": dashboard.average_delay_hours,
            "top_shortage_skus": dashboard.top_shortage_skus[:3],
            "top_risk_suppliers": [
                {
                    "supplier_id": item.supplier_id,
                    "risk_score": item.risk_score,
                    "open_alert_count": item.open_alert_count,
                }
                for item in supplier_risk_summaries[:3]
            ],
        }

    def _build_alert_prompt_payload(
        self,
        alert: OpenAlert,
        dashboard: DashboardSnapshot,
    ) -> dict[str, Any]:
        return {
            "alert": {
                "alert_id": alert.alert_id,
                "rule_id": alert.rule_id,
                "title": alert.title,
                "risk_level": alert.risk_level,
                "summary": alert.summary,
                "sku": alert.sku,
                "warehouse": alert.warehouse,
                "supplier_id": alert.supplier_id,
                "recommended_actions": alert.recommended_actions[:3],
                "alternative_suppliers": alert.alternative_suppliers[:2],
            },
            "dashboard_context": {
                "open_alert_count": dashboard.open_alert_count,
                "high_risk_alert_count": dashboard.high_risk_alert_count,
                "low_stock_sku_count": dashboard.low_stock_sku_count,
                "delayed_shipment_count": dashboard.delayed_shipment_count,
                "overdue_order_count": dashboard.overdue_order_count,
            },
        }

    def _render_user_payload(self, user_payload: dict[str, object]) -> str:
        return json.dumps(user_payload, ensure_ascii=False, separators=(",", ":"))