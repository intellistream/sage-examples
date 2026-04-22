# SAGE Examples: 100 Meaningful Application Roadmap

This document is the planning baseline for expanding `sage-examples` into a portfolio of 100
meaningful SAGE applications.

The goal here is not to create 100 empty scripts. The goal is to define 100 application targets that
are worth building, prioritize them in rational batches, and keep future implementation consistent
with the current repository structure.

## Portfolio Rules

- Keep runnable entry points in `examples/` only when an app is actually maintained.
- Keep implementation code in `apps/src/sage/apps/<slug>/`.
- Keep each runnable script named `examples/run_<slug>.py`.
- Prefer apps that demonstrate one or more SAGE strengths: stateful workflows, streaming, multimodal
  processing, retrieval, agentic coordination, or service orchestration.
- Prefer fail-fast application flows over hidden fallback logic.
- Do not add new `ray` dependencies or imports.

## Batch Legend

- `existing`: already present in the repository.
- `B1`: best near-term build candidates with relatively low implementation friction.
- `B2`: useful mid-term apps that need more domain modeling or integration work.
- `B3`: valuable long-tail apps that likely need heavier multimodal, device, or regulated-domain
  integration.

## Suggested Delivery Strategy

- First make the portfolio explicit.
- Then build `B1` apps in small groups of 5 to 10, with each group sharing reusable operators,
  models, or service abstractions.
- Only add a new `examples/run_<slug>.py` when the corresponding app is runnable and tested.

## Application Portfolio

### Research And Knowledge Systems

1. `literature_report_assistant` | `existing` | Personalized paper discovery, clustering, and
   reading report generation.
1. `article_monitoring` | `existing` | Continuous article monitoring with topic extraction and
   alerting.
1. `patent_landscape_mapper` | `B1` | Map patent trends, assignees, claim overlap, and white-space
   opportunities.
1. `grant_call_matcher` | `B1` | Match research groups or startups to grant calls and generate
   opportunity briefs.
1. `experiment_log_summarizer` | `B1` | Convert lab logs into structured daily summaries, anomalies,
   and next actions.
1. `scientific_claim_verifier` | `B2` | Check whether a scientific claim is supported, mixed, or
   contradicted by sources.
1. `conference_trend_monitor` | `B2` | Track conference sessions, speakers, themes, and emerging
   topic shifts.
1. `peer_review_copilot` | `B2` | Produce structured review rubrics, evidence notes, and revision
   requests.
1. `reproducibility_auditor` | `B2` | Audit datasets, configs, scripts, and environment metadata for
   reproducibility.
1. `benchmark_change_tracker` | `B1` | Track benchmark leaderboards, evaluation changes, and model
   movement over time.

### Education And Training

11. `student_improvement` | `existing` | Stateful score-improvement workflow with wrong-question
    tracking.
01. `course_qa_tutor` | `B1` | Retrieval-based course tutor over notes, slides, and assignments.
01. `lesson_plan_designer` | `B1` | Generate lesson plans, weekly pacing, and differentiated
    exercises.
01. `classroom_attention_monitor` | `B2` | Analyze classroom video for engagement, confusion, and
    pacing signals.
01. `assignment_feedback_assistant` | `B1` | Provide rubric-based draft feedback before teacher
    review.
01. `oral_exam_coach` | `B2` | Evaluate spoken answers and generate targeted follow-up drills.
01. `skill_gap_mapper` | `B1` | Map learner performance to a competency graph and recommend practice
    paths.
01. `training_compliance_tracker` | `B1` | Monitor enterprise training completion and highlight
    compliance risks.
01. `interview_practice_coach` | `B1` | Simulate interviews, score responses, and suggest
    role-specific improvements.
01. `campus_service_desk` | `B2` | Route student requests for finance, housing, advising, and
    administration.

### Healthcare And Life Sciences

21. `medical_diagnosis` | `existing` | AI-assisted medical image analysis workflow.
01. `triage_intake_assistant` | `B2` | Structure patient intake information and prioritize triage
    queues.
01. `radiology_followup_tracker` | `B2` | Detect follow-up recommendations in reports and track
    unresolved cases.
01. `clinical_guideline_copilot` | `B2` | Link patient context to guideline sections and action
    checklists.
01. `adverse_event_monitor` | `B2` | Monitor notes, reports, and signals for potential adverse
    events.
01. `medical_claim_auditor` | `B3` | Review claim packets for coding gaps, missing evidence, and
    denial risk.
01. `eldercare_home_monitor` | `B3` | Combine home-device signals and notes to flag decline or
    safety issues.
01. `hospital_bed_flow_coordinator` | `B3` | Summarize bed status, discharge blockers, and
    escalation priorities.
01. `drug_label_extractor` | `B1` | Extract dosage, contraindications, and warnings from drug
    labels.
01. `telehealth_visit_summarizer` | `B1` | Turn telehealth transcripts into structured visit notes
    and action items.

### Enterprise Productivity And Operations

31. `work_report_generator` | `existing` | Generate work reports from activity history and project
    context.
01. `meeting_action_tracker` | `B1` | Extract decisions, owners, deadlines, and unresolved blockers
    from meetings.
01. `contract_review_assistant` | `B2` | Highlight risky clauses, obligations, and missing terms in
    contracts.
01. `sales_call_insights` | `B1` | Summarize objections, buying signals, and follow-up priorities
    from calls.
01. `customer_support_copilot` | `B1` | Draft grounded responses and route tickets by issue type and
    urgency.
01. `procurement_analyzer` | `B2` | Compare supplier quotes, delivery risk, and negotiation
    leverage.
01. `org_policy_search` | `B1` | Answer internal policy questions with source-grounded citations.
01. `internal_ticket_router` | `B1` | Route IT, HR, and finance requests to the right queue with
    context.
01. `knowledge_base_curator` | `B1` | Deduplicate, summarize, and age-rank internal knowledge
    articles.
01. `multi_team_status_board` | `B2` | Aggregate project updates into a leadership-level cross-team
    digest.

### Media And Creative Operations

41. `video_intelligence` | `existing` | Multimodal video understanding and event summarization.
01. `podcast_clip_generator` | `B1` | Find high-value podcast segments and generate clips with
    titles and notes.
01. `brand_asset_reviewer` | `B2` | Check copy, visuals, and metadata for brand consistency.
01. `livestream_incident_monitor` | `B3` | Detect incidents, dead air, and moderation risks in
    livestreams.
01. `ad_creative_tester` | `B2` | Compare ad variants, messaging hooks, and likely audience
    resonance.
01. `subtitle_qc_assistant` | `B1` | Detect subtitle timing, terminology, and translation quality
    issues.
01. `content_calendar_planner` | `B1` | Plan multi-channel content schedules based on themes and
    launches.
01. `social_trend_storyboard` | `B2` | Turn social trend signals into short-form content concepts.
01. `news_bias_analyzer` | `B2` | Compare framing and bias patterns across outlets on the same
    event.
01. `media_archive_indexer` | `B1` | Build searchable indexes over large media collections with
    summaries.

### IoT, Edge, And Physical World

51. `smart_home` | `existing` | Stateful IoT automation and home-event orchestration.
01. `building_energy_manager` | `B2` | Optimize occupancy, HVAC schedules, and energy anomalies.
01. `factory_sensor_watchdog` | `B2` | Detect abnormal sensor patterns and summarize likely causes.
01. `cold_chain_monitor` | `B2` | Track storage temperature excursions and delivery quality risk.
01. `retail_queue_monitor` | `B3` | Analyze camera and POS signals to predict queue pressure.
01. `parking_lot_coordinator` | `B2` | Combine camera, gate, and event data to manage parking flow.
01. `edge_safety_alerting` | `B3` | Detect unsafe zones, restricted access, and PPE violations at
    the edge.
01. `greenhouse_copilot` | `B2` | Orchestrate irrigation, climate signals, and crop alerting.
01. `fleet_dashcam_reviewer` | `B3` | Summarize risky driving events and coaching recommendations.
01. `warehouse_robot_supervisor` | `B3` | Detect stalled tasks, congestion, and robot-assist
    escalation needs.

### Public Sector And Smart City

61. `emergency_signal_fusion` | `B3` | Fuse call-center, camera, and field-report signals into
    incident views.
01. `citizen_feedback_router` | `B1` | Classify citizen complaints and route them to departments
    with summaries.
01. `traffic_incident_briefing` | `B2` | Summarize traffic disruptions, likely impact, and response
    priorities.
01. `urban_maintenance_scheduler` | `B2` | Cluster repair requests and recommend efficient
    maintenance routing.
01. `environmental_complaint_analyzer` | `B1` | Detect recurring pollution complaints and hotspot
    trends.
01. `permit_review_assistant` | `B2` | Check permit submissions for missing materials and policy
    mismatches.
01. `utility_outage_triage` | `B3` | Correlate outage reports, asset telemetry, and restoration
    priorities.
01. `public_health_signal_watch` | `B3` | Monitor weak signals from clinics, news, and reports for
    outbreaks.
01. `disaster_resource_matcher` | `B3` | Match shelters, supplies, volunteers, and requests during
    emergencies.
01. `municipal_doc_search` | `B1` | Search city policies, council decisions, and service procedures.

### Finance And Risk

71. `invoice_exception_detector` | `B1` | Flag unusual invoice amounts, duplicate risk, and missing
    fields.
01. `expense_audit_assistant` | `B1` | Review reimbursements for policy violations and evidence
    gaps.
01. `loan_application_screening` | `B2` | Structure applicant packets and surface review priorities.
01. `aml_case_prioritizer` | `B3` | Rank anti-money-laundering cases by signal strength and analyst
    value.
01. `insurance_claim_triage` | `B2` | Classify claim complexity, fraud indicators, and next-review
    steps.
01. `portfolio_news_risk_monitor` | `B2` | Connect news events to holdings and summarize exposure
    impact.
01. `vendor_risk_scanner` | `B2` | Combine public signals, contracts, and incidents into vendor risk
    views.
01. `cashflow_forecaster` | `B2` | Blend invoicing, pipeline, and payment signals into short-term
    forecasts.
01. `pricing_anomaly_monitor` | `B2` | Detect suspicious price changes across products or accounts.
01. `billing_dispute_resolver` | `B1` | Organize billing evidence and draft dispute-resolution
    responses.

### Commerce And Supply Chain

81. `demand_sensing_assistant` | `B2` | Merge sales, promotions, weather, and events to improve
    demand sensing.
01. `dynamic_catalog_enricher` | `B1` | Normalize product listings and generate richer catalog
    attributes.
01. `return_reason_analyzer` | `B1` | Cluster return causes and identify avoidable quality or
    expectation gaps.
01. `supplier_delay_predictor` | `B2` | Forecast likely supplier delays from signals across orders
    and incidents.
01. `warehouse_pick_path_optimizer` | `B3` | Combine order waves and layout constraints for better
    pick routing.
01. `aftersales_ticket_triage` | `B1` | Prioritize installation, warranty, and repair tickets.
01. `menu_margin_copilot` | `B1` | Help restaurant operators balance menu pricing, margin, and
    demand.
01. `store_ops_digest` | `B1` | Summarize shift issues, stockouts, shrinkage, and action items.
01. `franchise_quality_monitor` | `B2` | Compare quality drift, service complaints, and compliance
    across stores.
01. `marketplace_listing_guard` | `B2` | Detect duplicate listings, policy risk, and misleading
    claims.

### Sustainability And Infrastructure

91. `carbon_data_collector` | `B1` | Gather emissions data from documents, meters, and operational
    systems.
01. `solar_farm_alerting` | `B2` | Summarize inverter anomalies, weather effects, and maintenance
    needs.
01. `water_leak_monitor` | `B2` | Detect persistent leak signatures and prioritize field inspection.
01. `campus_emissions_reporter` | `B1` | Build periodic campus sustainability reports from
    distributed data.
01. `hvac_fault_diagnosis` | `B2` | Diagnose HVAC performance issues from building telemetry.
01. `grid_event_summarizer` | `B3` | Turn grid alarms and operator logs into concise incident
    timelines.
01. `recycling_sorting_analytics` | `B3` | Analyze contamination patterns in recycling streams using
    vision inputs.
01. `construction_site_safety_monitor` | `B3` | Detect unsafe behavior, zone conflicts, and repeated
    risk patterns.
01. `data_center_capacity_watch` | `B2` | Track capacity, cooling pressure, and incident risk in
    data centers.
01. `pipeline_anomaly_review` | `B3` | Review inspection imagery, sensor events, and maintenance
    history.

## First 15 New Apps To Build

If the goal is to move from planning to implementation with the highest signal and lowest wasted
effort, these are the strongest next candidates after the already existing apps:

1. `meeting_action_tracker`
1. `course_qa_tutor`
1. `assignment_feedback_assistant`
1. `patent_landscape_mapper`
1. `grant_call_matcher`
1. `customer_support_copilot`
1. `org_policy_search`
1. `podcast_clip_generator`
1. `dynamic_catalog_enricher`
1. `return_reason_analyzer`
1. `carbon_data_collector`
1. `campus_emissions_reporter`
1. `drug_label_extractor`
1. `telehealth_visit_summarizer`
1. `citizen_feedback_router`

## Recommended Implementation Order

1. Finish stabilizing and testing the existing apps as reusable reference implementations.
1. Build the first 5 `B1` apps that mostly reuse current dependencies and packaging.
1. Extract shared retrieval, state, and operator utilities from those apps before starting `B2`.
1. Only start `B3` apps after the repo has enough stable multimodal and integration primitives.
