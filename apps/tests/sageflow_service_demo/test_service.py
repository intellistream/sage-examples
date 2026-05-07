from sage.apps.sageflow_service_demo import SageFlowServiceDemoApplication, build_demo_vector_events


def test_reset_clears_previous_window_state() -> None:
    service = SageFlowServiceDemoApplication(window_size=8)

    first_result = service.run_demo(reset=True)
    service.reset()
    second_result = service.ingest_events(build_demo_vector_events()[:3])

    assert first_result.final_snapshot is not None
    assert second_result.final_snapshot is not None
    assert first_result.final_snapshot.window_size == 7
    assert second_result.final_snapshot.window_size == 3
    assert second_result.final_snapshot.cluster_count == 1


def test_ingest_events_accepts_plain_dict_payloads() -> None:
    service = SageFlowServiceDemoApplication()
    payload = [item.to_dict() for item in build_demo_vector_events()[:2]]

    result = service.ingest_events(payload)

    assert result.processed_event_count == 2
    assert result.final_snapshot is not None
    assert result.final_snapshot.hot_clusters[0].member_ids == [
        "cve-2024-3400-nvd",
        "pan-2024-3400-vendor",
    ]
