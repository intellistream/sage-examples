from sage.apps.sageflow_service_demo import SageFlowServiceDemoApplication
from sage.apps.sageflow_service_demo.contracts import build_snapshot_prompt, contract_allowed_evidence_ids


def test_run_demo_emits_correlated_and_emerging_insights() -> None:
    service = SageFlowServiceDemoApplication()

    result = service.run_demo(reset=True)
    insight_types = {item.insight_type for item in result.insights}

    assert result.processed_event_count == 7
    assert result.insight_count >= 3
    assert "correlated_incident" in insight_types
    assert "emerging_pattern" in insight_types
    assert result.final_snapshot is not None
    assert result.final_snapshot.cluster_count >= 3
    assert result.final_snapshot.hot_clusters[0].size == 3


def test_latest_snapshot_exposes_source_breakdown() -> None:
    service = SageFlowServiceDemoApplication()

    service.run_demo(reset=True)
    snapshot = service.get_latest_snapshot()

    assert snapshot is not None
    assert snapshot.window_size == 7
    assert snapshot.source_breakdown["nvd"] == 3
    assert snapshot.source_breakdown["vendor_advisory"] == 2


def test_pipeline_can_materialize_contracts_and_explicit_llm_fallback() -> None:
    service = SageFlowServiceDemoApplication()

    result = service.run_demo(reset=True, generate_llm=True, allow_template_fallback=True)

    assert len(result.contracts) == result.processed_event_count
    assert len(result.llm_answers) == result.processed_event_count
    assert result.llm_answers[-1].status == "template_fallback"
    assert result.llm_answers[-1].evidence_ids
    assert result.llm_answers[-1].contract_id == result.contracts[-1].contract_id


def test_snapshot_contract_prompt_carries_bounded_evidence_metadata() -> None:
    service = SageFlowServiceDemoApplication()

    result = service.run_demo(reset=True)
    contract = result.contracts[-1]
    prompt = build_snapshot_prompt(contract)

    assert contract_allowed_evidence_ids(contract)
    assert "allowed_evidence_ids" in prompt
    assert "runtime_trace" in prompt
    assert "source_consensus" in prompt
    assert contract.query_event.event_id in prompt
    assert all(item.metadata for item in contract.neighbors)
