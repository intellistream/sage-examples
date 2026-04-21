# SAGE Examples: 100 Meaningful Application Roadmap

This document is the planning baseline for expanding `sage-examples` into a portfolio of 100
meaningful SAGE applications.

The goal here is not to create 100 empty scripts. The goal is to define 100 application targets
that are worth building, prioritize them in rational batches, and keep future implementation
consistent with the current repository structure.

## Portfolio Rules

- Keep runnable entry points in `examples/` only when an app is actually maintained.
- Keep implementation code in `apps/src/sage/apps/<slug>/`.
- Keep each runnable script named `examples/run_<slug>.py`.
- Prefer apps that demonstrate one or more SAGE strengths: stateful workflows, streaming,
  multimodal processing, retrieval, agentic coordination, or service orchestration.
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

1. `literature_report_assistant` | `existing` | Personalized paper discovery, clustering, and reading report generation.
2. `article_monitoring` | `existing` | Continuous article monitoring with topic extraction and alerting.
3. `patent_landscape_mapper` | `B1` | Map patent trends, assignees, claim overlap, and white-space opportunities.
4. `grant_call_matcher` | `B1` | Match research groups or startups to grant calls and generate opportunity briefs.
5. `experiment_log_summarizer` | `B1` | Convert lab logs into structured daily summaries, anomalies, and next actions.
6. `scientific_claim_verifier` | `B2` | Check whether a scientific claim is supported, mixed, or contradicted by sources.
7. `conference_trend_monitor` | `B2` | Track conference sessions, speakers, themes, and emerging topic shifts.
8. `peer_review_copilot` | `B2` | Produce structured review rubrics, evidence notes, and revision requests.
9. `reproducibility_auditor` | `B2` | Audit datasets, configs, scripts, and environment metadata for reproducibility.
10. `benchmark_change_tracker` | `B1` | Track benchmark leaderboards, evaluation changes, and model movement over time.

### Education And Training

1. `student_improvement` | `existing` | Stateful score-improvement workflow with wrong-question tracking.
1. `course_qa_tutor` | `B1` | Retrieval-based course tutor over notes, slides, and assignments.
1. `lesson_plan_designer` | `B1` | Generate lesson plans, weekly pacing, and differentiated exercises.
1. `classroom_attention_monitor` | `B2` | Analyze classroom video for engagement, confusion, and pacing signals.
1. `assignment_feedback_assistant` | `B1` | Provide rubric-based draft feedback before teacher review.
1. `oral_exam_coach` | `B2` | Evaluate spoken answers and generate targeted follow-up drills.
1. `skill_gap_mapper` | `B1` | Map learner performance to a competency graph and recommend practice paths.
1. `training_compliance_tracker` | `B1` | Monitor enterprise training completion and highlight compliance risks.
1. `interview_practice_coach` | `B1` | Simulate interviews, score responses, and suggest role-specific improvements.
1. `campus_service_desk` | `B2` | Route student requests for finance, housing, advising, and administration.

### Healthcare And Life Sciences

1. `medical_diagnosis` | `existing` | AI-assisted medical image analysis workflow.
1. `triage_intake_assistant` | `B2` | Structure patient intake information and prioritize triage queues.
1. `radiology_followup_tracker` | `B2` | Detect follow-up recommendations in reports and track unresolved cases.
1. `clinical_guideline_copilot` | `B2` | Link patient context to guideline sections and action checklists.
1. `adverse_event_monitor` | `B2` | Monitor notes, reports, and signals for potential adverse events.
1. `medical_claim_auditor` | `B3` | Review claim packets for coding gaps, missing evidence, and denial risk.
1. `eldercare_home_monitor` | `B3` | Combine home-device signals and notes to flag decline or safety issues.
1. `hospital_bed_flow_coordinator` | `B3` | Summarize bed status, discharge blockers, and escalation priorities.
1. `drug_label_extractor` | `B1` | Extract dosage, contraindications, and warnings from drug labels.
1. `telehealth_visit_summarizer` | `B1` | Turn telehealth transcripts into structured visit notes and action items.

### Enterprise Productivity And Operations

1. `work_report_generator` | `existing` | Generate work reports from activity history and project context.
1. `meeting_action_tracker` | `B1` | Extract decisions, owners, deadlines, and unresolved blockers from meetings.
1. `contract_review_assistant` | `B2` | Highlight risky clauses, obligations, and missing terms in contracts.
1. `sales_call_insights` | `B1` | Summarize objections, buying signals, and follow-up priorities from calls.
1. `customer_support_copilot` | `B1` | Draft grounded responses and route tickets by issue type and urgency.
1. `procurement_analyzer` | `B2` | Compare supplier quotes, delivery risk, and negotiation leverage.
1. `org_policy_search` | `B1` | Answer internal policy questions with source-grounded citations.
1. `internal_ticket_router` | `B1` | Route IT, HR, and finance requests to the right queue with context.
1. `knowledge_base_curator` | `B1` | Deduplicate, summarize, and age-rank internal knowledge articles.
1. `multi_team_status_board` | `B2` | Aggregate project updates into a leadership-level cross-team digest.

### Media And Creative Operations

1. `video_intelligence` | `existing` | Multimodal video understanding and event summarization.
1. `podcast_clip_generator` | `B1` | Find high-value podcast segments and generate clips with titles and notes.
1. `brand_asset_reviewer` | `B2` | Check copy, visuals, and metadata for brand consistency.
1. `livestream_incident_monitor` | `B3` | Detect incidents, dead air, and moderation risks in livestreams.
1. `ad_creative_tester` | `B2` | Compare ad variants, messaging hooks, and likely audience resonance.
1. `subtitle_qc_assistant` | `B1` | Detect subtitle timing, terminology, and translation quality issues.
1. `content_calendar_planner` | `B1` | Plan multi-channel content schedules based on themes and launches.
1. `social_trend_storyboard` | `B2` | Turn social trend signals into short-form content concepts.
1. `news_bias_analyzer` | `B2` | Compare framing and bias patterns across outlets on the same event.
1. `media_archive_indexer` | `B1` | Build searchable indexes over large media collections with summaries.

### IoT, Edge, And Physical World

1. `smart_home` | `existing` | Stateful IoT automation and home-event orchestration.
1. `building_energy_manager` | `B2` | Optimize occupancy, HVAC schedules, and energy anomalies.
1. `factory_sensor_watchdog` | `B2` | Detect abnormal sensor patterns and summarize likely causes.
1. `cold_chain_monitor` | `B2` | Track storage temperature excursions and delivery quality risk.
1. `retail_queue_monitor` | `B3` | Analyze camera and POS signals to predict queue pressure.
1. `parking_lot_coordinator` | `B2` | Combine camera, gate, and event data to manage parking flow.
1. `edge_safety_alerting` | `B3` | Detect unsafe zones, restricted access, and PPE violations at the edge.
1. `greenhouse_copilot` | `B2` | Orchestrate irrigation, climate signals, and crop alerting.
1. `fleet_dashcam_reviewer` | `B3` | Summarize risky driving events and coaching recommendations.
1. `warehouse_robot_supervisor` | `B3` | Detect stalled tasks, congestion, and robot-assist escalation needs.

### Public Sector And Smart City

1. `emergency_signal_fusion` | `B3` | Fuse call-center, camera, and field-report signals into incident views.
1. `citizen_feedback_router` | `B1` | Classify citizen complaints and route them to departments with summaries.
1. `traffic_incident_briefing` | `B2` | Summarize traffic disruptions, likely impact, and response priorities.
1. `urban_maintenance_scheduler` | `B2` | Cluster repair requests and recommend efficient maintenance routing.
1. `environmental_complaint_analyzer` | `B1` | Detect recurring pollution complaints and hotspot trends.
1. `permit_review_assistant` | `B2` | Check permit submissions for missing materials and policy mismatches.
1. `utility_outage_triage` | `B3` | Correlate outage reports, asset telemetry, and restoration priorities.
1. `public_health_signal_watch` | `B3` | Monitor weak signals from clinics, news, and reports for outbreaks.
1. `disaster_resource_matcher` | `B3` | Match shelters, supplies, volunteers, and requests during emergencies.
1. `municipal_doc_search` | `B1` | Search city policies, council decisions, and service procedures.

### Finance And Risk

1. `invoice_exception_detector` | `B1` | Flag unusual invoice amounts, duplicate risk, and missing fields.
1. `expense_audit_assistant` | `B1` | Review reimbursements for policy violations and evidence gaps.
1. `loan_application_screening` | `B2` | Structure applicant packets and surface review priorities.
1. `aml_case_prioritizer` | `B3` | Rank anti-money-laundering cases by signal strength and analyst value.
1. `insurance_claim_triage` | `B2` | Classify claim complexity, fraud indicators, and next-review steps.
1. `portfolio_news_risk_monitor` | `B2` | Connect news events to holdings and summarize exposure impact.
1. `vendor_risk_scanner` | `B2` | Combine public signals, contracts, and incidents into vendor risk views.
1. `cashflow_forecaster` | `B2` | Blend invoicing, pipeline, and payment signals into short-term forecasts.
1. `pricing_anomaly_monitor` | `B2` | Detect suspicious price changes across products or accounts.
1. `billing_dispute_resolver` | `B1` | Organize billing evidence and draft dispute-resolution responses.

### Commerce And Supply Chain

1. `demand_sensing_assistant` | `B2` | Merge sales, promotions, weather, and events to improve demand sensing.
1. `dynamic_catalog_enricher` | `B1` | Normalize product listings and generate richer catalog attributes.
1. `return_reason_analyzer` | `B1` | Cluster return causes and identify avoidable quality or expectation gaps.
1. `supplier_delay_predictor` | `B2` | Forecast likely supplier delays from signals across orders and incidents.
1. `warehouse_pick_path_optimizer` | `B3` | Combine order waves and layout constraints for better pick routing.
1. `aftersales_ticket_triage` | `B1` | Prioritize installation, warranty, and repair tickets.
1. `menu_margin_copilot` | `B1` | Help restaurant operators balance menu pricing, margin, and demand.
1. `store_ops_digest` | `B1` | Summarize shift issues, stockouts, shrinkage, and action items.
1. `franchise_quality_monitor` | `B2` | Compare quality drift, service complaints, and compliance across stores.
1. `marketplace_listing_guard` | `B2` | Detect duplicate listings, policy risk, and misleading claims.

### Sustainability And Infrastructure

1. `carbon_data_collector` | `B1` | Gather emissions data from documents, meters, and operational systems.
1. `solar_farm_alerting` | `B2` | Summarize inverter anomalies, weather effects, and maintenance needs.
1. `water_leak_monitor` | `B2` | Detect persistent leak signatures and prioritize field inspection.
1. `campus_emissions_reporter` | `B1` | Build periodic campus sustainability reports from distributed data.
1. `hvac_fault_diagnosis` | `B2` | Diagnose HVAC performance issues from building telemetry.
1. `grid_event_summarizer` | `B3` | Turn grid alarms and operator logs into concise incident timelines.
1. `recycling_sorting_analytics` | `B3` | Analyze contamination patterns in recycling streams using vision inputs.
1. `construction_site_safety_monitor` | `B3` | Detect unsafe behavior, zone conflicts, and repeated risk patterns.
1. `data_center_capacity_watch` | `B2` | Track capacity, cooling pressure, and incident risk in data centers.
1. `pipeline_anomaly_review` | `B3` | Review inspection imagery, sensor events, and maintenance history.

## First 15 New Apps To Build

If the goal is to move from planning to implementation with the highest signal and lowest wasted
effort, these are the strongest next candidates after the already existing apps:

1. `meeting_action_tracker`
2. `course_qa_tutor`
3. `assignment_feedback_assistant`
4. `patent_landscape_mapper`
5. `grant_call_matcher`
6. `customer_support_copilot`
7. `org_policy_search`
8. `podcast_clip_generator`
9. `dynamic_catalog_enricher`
10. `return_reason_analyzer`
11. `carbon_data_collector`
12. `campus_emissions_reporter`
13. `drug_label_extractor`
14. `telehealth_visit_summarizer`
15. `citizen_feedback_router`

## Recommended Implementation Order

1. Finish stabilizing and testing the existing apps as reusable reference implementations.
2. Build the first 5 `B1` apps that mostly reuse current dependencies and packaging.
3. Extract shared retrieval, state, and operator utilities from those apps before starting `B2`.
4. Only start `B3` apps after the repo has enough stable multimodal and integration primitives.
