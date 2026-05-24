from dataclasses import replace

from sage.apps.sageflow_service_demo.llm import LLMClientConfig
from sage.apps.sageflow_service_demo.run_experiment import _answer_faithfulness
from sage.apps.sageflow_service_demo.service import SageFlowServiceDemoApplication


def test_zhipu_provider_disables_thinking_by_default(monkeypatch) -> None:
    monkeypatch.setenv("SAGEFLOW_DEMO_LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
    monkeypatch.setenv("SAGEFLOW_DEMO_LLM_MODEL", "glm-4.5")
    monkeypatch.setenv("SAGEFLOW_DEMO_LLM_PROVIDER", "zhipu")

    config = LLMClientConfig.from_env()

    assert config is not None
    assert config.extra_request_json == {"thinking": {"type": "disabled"}}


def test_llm_extra_json_overrides_provider_profile(monkeypatch) -> None:
    monkeypatch.setenv("SAGEFLOW_DEMO_LLM_BASE_URL", "https://open.bigmodel.cn/api/paas/v4")
    monkeypatch.setenv("SAGEFLOW_DEMO_LLM_MODEL", "glm-4.5")
    monkeypatch.setenv("SAGEFLOW_DEMO_LLM_PROVIDER", "zhipu")
    monkeypatch.setenv("SAGEFLOW_DEMO_LLM_EXTRA_JSON", '{"thinking":{"type":"enabled"}}')

    config = LLMClientConfig.from_env()

    assert config is not None
    assert config.extra_request_json == {"thinking": {"type": "enabled"}}


def test_faithfulness_accepts_standard_cve_aliases_from_contract_metadata() -> None:
    result = SageFlowServiceDemoApplication().run_demo(reset=True)
    original_contract = result.contracts[-1]
    cve_id = "CVE-2099-0001"
    query_event = replace(
        original_contract.query_event,
        event_id="cve-2099-0001-cisa-kev",
        metadata={**original_contract.query_event.metadata, "cve_id": cve_id},
    )
    contract = replace(original_contract, query_event=query_event)
    answer = {
        "answer": (
            f"{cve_id} maps to the runtime evidence id "
            f"{contract.query_event.event_id}."
        )
    }

    faithfulness = _answer_faithfulness(answer, contract)

    assert faithfulness["cited_ids_are_contract_evidence"] == 1.0
    assert faithfulness["cites_at_least_one_contract_id"] is True
    assert faithfulness["unsupported_event_like_ids"] == []
