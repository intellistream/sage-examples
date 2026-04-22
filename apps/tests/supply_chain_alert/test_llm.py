import json

from sage.apps.supply_chain_alert import SupplyChainAlertApplicationService
from sage.apps.supply_chain_alert.llm import (
    SupplyChainGatewaySettings,
    SupplyChainRiskExplainer,
)
from sage.serving import GatewayProbeResult


def test_gateway_settings_from_env(monkeypatch) -> None:
    monkeypatch.setenv("SAGE_SUPPLY_CHAIN_GATEWAY_HOST", "10.0.0.8")
    monkeypatch.setenv("SAGE_SUPPLY_CHAIN_GATEWAY_PORT", "18080")
    monkeypatch.setenv("SAGE_SUPPLY_CHAIN_MODEL", "demo-model")
    monkeypatch.setenv("SAGE_SUPPLY_CHAIN_API_KEY", "gateway-key")  # pragma: allowlist secret

    settings = SupplyChainGatewaySettings.from_env()

    assert settings.host == "10.0.0.8"
    assert settings.port == 18080
    assert settings.model == "demo-model"
    assert settings.api_key == "gateway-key"  # pragma: allowlist secret


def test_gateway_settings_support_remote_base_url(monkeypatch) -> None:
    monkeypatch.setenv("SAGE_SUPPLY_CHAIN_BASE_URL", "https://api.sage.org.ai/v1")
    monkeypatch.setenv("SAGE_SUPPLY_CHAIN_HEALTH_URL", "https://api.sage.org.ai/health")

    settings = SupplyChainGatewaySettings.from_env()

    assert settings.base_url == "https://api.sage.org.ai/v1"
    assert settings.health_url == "https://api.sage.org.ai/health"


def test_explainer_reports_unavailable_gateway(tmp_path, monkeypatch) -> None:
    service = SupplyChainAlertApplicationService(storage_path=tmp_path / "supply-chain-state.json")
    service.run_demo(reset=True)
    explainer = SupplyChainRiskExplainer(
        settings=SupplyChainGatewaySettings(host="127.0.0.1", port=19000),
    )

    monkeypatch.setattr(
        "sage.apps.supply_chain_alert.llm.probe_gateway",
        lambda config, timeout=3.0: GatewayProbeResult(
            ok=False,
            url=config.health_url,
            error="connection refused",
        ),
    )

    result = explainer.explain_current_risks(
        dashboard=service.get_dashboard(),
        alerts=service.list_open_alerts(),
        supplier_risk_summaries=service.get_supplier_risk_summary(),
    )

    assert result.gateway_status.reachable is False
    assert result.gateway_status.error == "connection refused"
    assert result.alert_explanations == []
    assert result.dashboard_summary is None


def test_explainer_generates_dashboard_and_alert_explanations(tmp_path, monkeypatch) -> None:
    service = SupplyChainAlertApplicationService(storage_path=tmp_path / "supply-chain-state.json")
    service.run_demo(reset=True)
    explainer = SupplyChainRiskExplainer(
        settings=SupplyChainGatewaySettings(host="127.0.0.1", port=19000),
    )

    monkeypatch.setattr(
        "sage.apps.supply_chain_alert.llm.probe_gateway",
        lambda config, timeout=3.0: GatewayProbeResult(
            ok=True,
            url=config.health_url,
            status_code=200,
        ),
    )
    monkeypatch.setattr(explainer, "_build_client", lambda: object())
    monkeypatch.setattr(explainer, "_resolve_model", lambda client: "demo-model")
    monkeypatch.setattr(
        explainer,
        "generate_dashboard_summary",
        lambda **kwargs: "当前整体风险集中在低库存和订单积压。",
    )
    monkeypatch.setattr(
        explainer,
        "generate_alert_explanation",
        lambda **kwargs: "这条预警说明当前订单履约存在明显延迟风险，需要优先处理。",
    )

    result = explainer.explain_current_risks(
        dashboard=service.get_dashboard(),
        alerts=service.list_open_alerts(),
        supplier_risk_summaries=service.get_supplier_risk_summary(),
        max_alerts=2,
    )

    assert result.gateway_status.reachable is True
    assert result.gateway_status.model == "demo-model"
    assert result.dashboard_summary == "当前整体风险集中在低库存和订单积压。"
    assert len(result.alert_explanations) == 2


def test_explainer_probes_remote_base_url(tmp_path, monkeypatch) -> None:
    service = SupplyChainAlertApplicationService(storage_path=tmp_path / "supply-chain-state.json")
    service.run_demo(reset=True)
    explainer = SupplyChainRiskExplainer(
        settings=SupplyChainGatewaySettings(
            base_url_override="https://api.sage.org.ai/v1",
            health_url_override="https://api.sage.org.ai/health",
            api_key="remote-key",  # pragma: allowlist secret
        ),
    )

    class FakeResponse:
        status_code = 200

        @staticmethod
        def json():
            return {"status": "ok"}

    class FakeClient:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, url):
            assert url == "https://api.sage.org.ai/health"
            return FakeResponse()

    monkeypatch.setattr("sage.apps.supply_chain_alert.llm.httpx.Client", FakeClient)
    monkeypatch.setattr(explainer, "_build_client", lambda: object())
    monkeypatch.setattr(explainer, "_resolve_model", lambda client: "demo-model")
    monkeypatch.setattr(
        explainer,
        "generate_dashboard_summary",
        lambda **kwargs: "远程网关已正常生成摘要。",
    )
    monkeypatch.setattr(
        explainer,
        "generate_alert_explanation",
        lambda **kwargs: "远程网关已正常生成预警解释。",
    )

    result = explainer.explain_current_risks(
        dashboard=service.get_dashboard(),
        alerts=service.list_open_alerts(),
        supplier_risk_summaries=service.get_supplier_risk_summary(),
        max_alerts=1,
    )

    assert result.gateway_status.reachable is True
    assert result.gateway_status.base_url == "https://api.sage.org.ai/v1"
    assert result.dashboard_summary == "远程网关已正常生成摘要。"
    assert len(result.alert_explanations) == 1


def test_explainer_remote_base_url_can_bypass_failed_health_probe(tmp_path, monkeypatch) -> None:
    service = SupplyChainAlertApplicationService(storage_path=tmp_path / "supply-chain-state.json")
    service.run_demo(reset=True)
    explainer = SupplyChainRiskExplainer(
        settings=SupplyChainGatewaySettings(
            base_url_override="https://api.sage.org.ai/v1",
            health_url_override="https://api.sage.org.ai/health",
            api_key="remote-key",  # pragma: allowlist secret
        ),
    )

    class FakeResponse:
        status_code = 504
        text = "upstream timeout"

        @staticmethod
        def json():
            raise ValueError("not json")

    class FakeClient:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, url):
            assert url == "https://api.sage.org.ai/health"
            return FakeResponse()

    monkeypatch.setattr("sage.apps.supply_chain_alert.llm.httpx.Client", FakeClient)
    monkeypatch.setattr(explainer, "_build_client", lambda: object())
    monkeypatch.setattr(explainer, "_resolve_model", lambda client: "qwen7b-a100")
    monkeypatch.setattr(
        explainer,
        "generate_dashboard_summary",
        lambda **kwargs: "虽然 health 探测失败，但远程模型接口可用，已生成摘要。",
    )
    monkeypatch.setattr(
        explainer,
        "generate_alert_explanation",
        lambda **kwargs: "远程模型接口可用，已生成预警解释。",
    )

    result = explainer.explain_current_risks(
        dashboard=service.get_dashboard(),
        alerts=service.list_open_alerts(),
        supplier_risk_summaries=service.get_supplier_risk_summary(),
        max_alerts=1,
    )

    assert result.gateway_status.reachable is True
    assert result.gateway_status.model == "qwen7b-a100"
    assert result.gateway_status.status_code is None
    assert result.gateway_status.error is None
    assert result.dashboard_summary == "虽然 health 探测失败，但远程模型接口可用，已生成摘要。"
    assert len(result.alert_explanations) == 1


def test_explainer_remote_base_url_uses_direct_httpx_calls(tmp_path, monkeypatch) -> None:
    service = SupplyChainAlertApplicationService(storage_path=tmp_path / "supply-chain-state.json")
    service.run_demo(reset=True)
    explainer = SupplyChainRiskExplainer(
        settings=SupplyChainGatewaySettings(
            base_url_override="https://api.sage.org.ai/v1",
            health_url_override="https://api.sage.org.ai/health",
            api_key="remote-key",  # pragma: allowlist secret
            model="Qwen/Qwen2.5-7B-Instruct",
        ),
    )

    class FakeResponse:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload
            self.text = json.dumps(payload, ensure_ascii=False)

        def json(self):
            return self._payload

        def raise_for_status(self):
            if self.status_code >= 400:
                raise RuntimeError(self.text)

    class FakeClient:
        def __init__(self, **kwargs):
            self.kwargs = kwargs
            self.posts = []

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, url):
            if url.endswith("/health"):
                return FakeResponse(504, {"error": "upstream timeout"})
            if url.endswith("/models"):
                return FakeResponse(200, {"data": [{"id": "Qwen/Qwen2.5-7B-Instruct"}]})
            raise AssertionError(url)

        def post(self, url, json):
            self.posts.append((url, json))
            return FakeResponse(
                200,
                {
                    "choices": [
                        {
                            "message": {
                                "content": "这是远程网关返回的解释。先说明触发原因，再说明影响。"
                            }
                        }
                    ]
                },
            )

    monkeypatch.setattr("sage.apps.supply_chain_alert.llm.httpx.Client", FakeClient)

    result = explainer.explain_current_risks(
        dashboard=service.get_dashboard(),
        alerts=service.list_open_alerts(),
        supplier_risk_summaries=service.get_supplier_risk_summary(),
        max_alerts=1,
    )

    assert result.gateway_status.reachable is True
    assert result.gateway_status.error is None
    assert result.gateway_status.status_code is None
    assert result.dashboard_summary
    assert len(result.alert_explanations) == 1
    assert "远程网关返回的解释" in result.alert_explanations[0].explanation


def test_explainer_remote_base_url_reports_actual_generation_error(tmp_path, monkeypatch) -> None:
    service = SupplyChainAlertApplicationService(storage_path=tmp_path / "supply-chain-state.json")
    service.run_demo(reset=True)
    explainer = SupplyChainRiskExplainer(
        settings=SupplyChainGatewaySettings(
            base_url_override="https://api.sage.org.ai/v1",
            health_url_override="https://api.sage.org.ai/health",
            api_key="remote-key",  # pragma: allowlist secret
            model="Qwen/Qwen2.5-7B-Instruct",
        ),
    )

    class FakeResponse:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload
            self.text = json.dumps(payload, ensure_ascii=False)

        def json(self):
            return self._payload

        def raise_for_status(self):
            if self.status_code >= 400:
                raise RuntimeError(self.text)

    class FakeClient:
        def __init__(self, **kwargs):
            self.kwargs = kwargs

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def get(self, url):
            if url.endswith("/health"):
                return FakeResponse(504, {"error": "upstream timeout"})
            raise AssertionError(url)

        def post(self, url, json):
            return FakeResponse(403, {"error": {"message": "request blocked"}})

    monkeypatch.setattr("sage.apps.supply_chain_alert.llm.httpx.Client", FakeClient)

    result = explainer.explain_current_risks(
        dashboard=service.get_dashboard(),
        alerts=service.list_open_alerts(),
        supplier_risk_summaries=service.get_supplier_risk_summary(),
        max_alerts=1,
    )

    assert result.gateway_status.reachable is False
    assert result.gateway_status.status_code == 504
    assert "request blocked" in (result.gateway_status.error or "")
    assert result.dashboard_summary is None
    assert result.alert_explanations == []
