from sage.apps.sageflow_service_demo import (
    available_demo_datasets,
    build_demo_raw_events,
    build_security_demo_raw_events,
    build_snapshot_demo_sources,
    describe_demo_dataset,
)


def test_medium_dataset_profile_is_repo_visible_and_larger() -> None:
    assert "baseline" in available_demo_datasets()
    assert "medium" in available_demo_datasets()

    baseline_events = build_demo_raw_events("baseline")
    medium_events = build_demo_raw_events("medium")
    medium_security_events = build_security_demo_raw_events("medium")
    medium_primary, medium_context = build_snapshot_demo_sources("medium")
    dataset_info = describe_demo_dataset("medium")

    assert len(medium_events) > len(baseline_events)
    assert len(medium_events) >= 24
    assert len(medium_security_events) > len(medium_events)
    assert len(medium_primary) == 6
    assert len(medium_context) == len(medium_events) - len(medium_primary)
    assert dataset_info["dataset_file"].endswith("demo_datasets.json")
    assert dataset_info["recommended_window_size"] >= len(medium_security_events)