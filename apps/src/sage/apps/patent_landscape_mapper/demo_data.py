"""Demo patent corpus for the patent landscape mapper."""

from __future__ import annotations

from .models import PatentRecord


def build_demo_focus_keywords() -> list[str]:
    return [
        "industrial safety copilots",
        "predictive maintenance",
        "warehouse robotics",
        "cold chain monitoring",
    ]


def build_demo_patent_corpus() -> list[PatentRecord]:
    return [
        PatentRecord(
            patent_id="PAT-001",
            title="Edge Vision Hazard Detection for Forklift Crossings",
            abstract=(
                "An edge inference system uses ceiling cameras and low-latency scene graphs to "
                "detect forklift and pedestrian conflict zones inside industrial warehouses."
            ),
            assignee="SafeSight Robotics",
            year=2024,
            jurisdictions=["US", "EP"],
            tags=["industrial safety", "edge vision", "forklift monitoring"],
        ),
        PatentRecord(
            patent_id="PAT-002",
            title="Wearable and Camera Fusion for PPE Compliance",
            abstract=(
                "A multimodal worker safety system combines smart helmets, proximity beacons, and "
                "camera analytics to identify missing protective equipment on factory floors."
            ),
            assignee="Titan Works AI",
            year=2025,
            jurisdictions=["US"],
            tags=["worker safety", "ppe compliance", "multimodal sensing"],
        ),
        PatentRecord(
            patent_id="PAT-003",
            title="Low-Power Vision Accelerator for Industrial Cameras",
            abstract=(
                "A compact accelerator chip performs defect detection and safety inference on edge "
                "cameras with thermal constraints suitable for factory deployment."
            ),
            assignee="SilicaEdge Systems",
            year=2023,
            jurisdictions=["US", "JP"],
            tags=["edge ai", "vision accelerator", "industrial cameras"],
        ),
        PatentRecord(
            patent_id="PAT-004",
            title="Digital Twin Maintenance Planner for CNC Spindles",
            abstract=(
                "A digital twin updates spindle degradation models from vibration and temperature "
                "streams, predicting intervention windows before tool failure."
            ),
            assignee="MechaTwin Labs",
            year=2024,
            jurisdictions=["US", "CN"],
            tags=["predictive maintenance", "digital twin", "cnc monitoring"],
        ),
        PatentRecord(
            patent_id="PAT-005",
            title="Acoustic Anomaly Detection for Pump Fleets",
            abstract=(
                "An unsupervised maintenance engine identifies early acoustic deviations across pump "
                "fleets and routes explanations to plant reliability teams."
            ),
            assignee="GridPulse Analytics",
            year=2025,
            jurisdictions=["US", "EP"],
            tags=["predictive maintenance", "acoustic anomalies", "asset reliability"],
        ),
        PatentRecord(
            patent_id="PAT-006",
            title="Maintenance Copilot for Turbine Sensor Drift",
            abstract=(
                "A maintenance copilot correlates sensor drift, work orders, and turbine operating "
                "state to recommend corrective inspections for field teams."
            ),
            assignee="FluxWorks Industrial",
            year=2022,
            jurisdictions=["US"],
            tags=["maintenance copilot", "sensor drift", "turbine health"],
        ),
        PatentRecord(
            patent_id="PAT-007",
            title="Robot Swarm Coordination for Dynamic Picking Waves",
            abstract=(
                "Warehouse orchestration software assigns autonomous mobile robots to picking waves "
                "based on aisle congestion, order urgency, and battery state."
            ),
            assignee="RouteHive Robotics",
            year=2025,
            jurisdictions=["US", "KR"],
            tags=["warehouse robotics", "robot swarms", "picking optimization"],
        ),
        PatentRecord(
            patent_id="PAT-008",
            title="Adaptive Slotting Engine for Fulfillment Centers",
            abstract=(
                "A fulfillment engine updates storage slotting using robot path density, product turn, "
                "and replenishment latency to reduce pick path overhead."
            ),
            assignee="FulfillOS",
            year=2024,
            jurisdictions=["US", "EP"],
            tags=["warehouse robotics", "slotting optimization", "fulfillment control"],
        ),
        PatentRecord(
            patent_id="PAT-009",
            title="Dock Traffic Graph for Forklift and AMR Coordination",
            abstract=(
                "A traffic graph predicts congestion between forklifts and mobile robots across dock "
                "zones, enabling safer handoffs and faster trailer turns."
            ),
            assignee="DockPilot Systems",
            year=2023,
            jurisdictions=["US", "CN"],
            tags=["dock orchestration", "warehouse robotics", "traffic graph"],
        ),
        PatentRecord(
            patent_id="PAT-010",
            title="Spoilage Prediction for Biologic Shipments",
            abstract=(
                "Cold chain shipment containers track thermal excursions, route delays, and handling "
                "events to estimate spoilage risk for biologic therapies."
            ),
            assignee="CryoPulse",
            year=2025,
            jurisdictions=["US", "EP"],
            tags=["cold chain", "biologics logistics", "spoilage prediction"],
        ),
        PatentRecord(
            patent_id="PAT-011",
            title="Adaptive Alerting for Pharma Delivery Sensors",
            abstract=(
                "A pharmaceutical logistics platform prioritizes route alerts by combining package "
                "telemetry, thermal stability profiles, and delivery handoff confidence."
            ),
            assignee="MediChain Logistics",
            year=2024,
            jurisdictions=["US", "IN"],
            tags=["cold chain", "pharma logistics", "sensor alerting"],
        ),
        PatentRecord(
            patent_id="PAT-012",
            title="Edge Inspection for Sterile Storage Rooms",
            abstract=(
                "A clean-room monitoring system runs local vision checks on storage room door states, "
                "temperature seals, and manual handling anomalies for sensitive medical goods."
            ),
            assignee="SteriVision Labs",
            year=2023,
            jurisdictions=["US", "EP"],
            tags=["cold chain", "edge inspection", "sterile storage"],
        ),
    ]