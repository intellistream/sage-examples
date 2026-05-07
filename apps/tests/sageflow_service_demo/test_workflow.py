from sage.apps.sageflow_service_demo import SageFlowServiceDemoApplication


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
