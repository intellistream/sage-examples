from sage.apps.sageflow_service_demo import (
    SageFlowSecurityEscalationApplication,
    SageFlowTriageRoutingApplication,
)


def test_triage_pipeline_routes_payment_logistics_and_security_events() -> None:
    app = SageFlowTriageRoutingApplication()

    decisions = app.run_demo(reset=True)
    decision_by_id = {item.event_id: item for item in decisions}

    assert decision_by_id["cve-2024-3400-nvd"].route == "edge-firewall-response"
    assert decision_by_id["cve-2024-3094-nvd"].route == "linux-supply-chain-response"
    assert decision_by_id["cve-2024-6387-nvd"].route == "identity-access-response"
    assert decision_by_id["cve-2024-3400-nvd"].supporting_neighbor_ids


def test_security_pipeline_pages_oncall_when_security_pattern_is_correlated() -> None:
    app = SageFlowSecurityEscalationApplication()

    signals = app.run_demo(reset=True)
    signal_by_id = {item.event_id: item for item in signals}

    assert signal_by_id["ubuntu-2024-6387-notice"].action == "page-vulnerability-oncall"
    assert signal_by_id["ubuntu-2024-6387-notice"].severity == "critical"
    assert len(signal_by_id["ubuntu-2024-6387-notice"].supporting_neighbor_ids) >= 2