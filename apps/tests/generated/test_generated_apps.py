"""Smoke tests for generated SAGE example apps."""

from __future__ import annotations

import importlib
import json
from pathlib import Path

APP_PIPELINES = {
    "log_parser": "run_log_parser_pipeline",
    "data_cleaner": "run_data_cleaner_pipeline",
    "resume_parser": "run_resume_parser_pipeline",
    "feedback_analyzer": "run_feedback_analyzer_pipeline",
    "web_scraper": "run_web_scraper_pipeline",
    "academic_metadata": "run_academic_metadata_pipeline",
    "customer_deduplication": "run_customer_deduplication_pipeline",
    "voucher_classifier": "run_voucher_classifier_pipeline",
    "product_sync": "run_product_sync_pipeline",
    "doc_classifier": "run_doc_classifier_pipeline",
    "contract_matcher": "run_contract_matcher_pipeline",
    "news_aggregator": "run_news_aggregator_pipeline",
    "ticket_router": "run_ticket_router_pipeline",
    "content_moderation": "run_content_moderation_pipeline",
    "contract_risk": "run_contract_risk_pipeline",
    "user_behavior_analytics": "run_user_behavior_analytics_pipeline",
    "inventory_alert": "run_inventory_alert_pipeline",
    "quality_defect_filter": "run_quality_defect_filter_pipeline",
    "permission_audit": "run_permission_audit_pipeline",
    "order_anomaly_detector": "run_order_anomaly_detector_pipeline",
    "attendance_alert": "run_attendance_alert_pipeline",
    "lead_scoring": "run_lead_scoring_pipeline",
    "arbitrage_detector": "run_arbitrage_detector_pipeline",
    "weather_sales_forecast": "run_weather_sales_forecast_pipeline",
    "geo_recommendation": "run_geo_recommendation_pipeline",
    "company_credit": "run_company_credit_pipeline",
    "movie_scheduling_optimizer": "run_movie_scheduling_optimizer_pipeline",
    "real_estate_valuation": "run_real_estate_valuation_pipeline",
    "multi_factor_credit_score": "run_multi_factor_credit_score_pipeline",
    "logistics_cost_optimizer": "run_logistics_cost_optimizer_pipeline",
    "medical_registration_optimizer": "run_medical_registration_optimizer_pipeline",
    "exhibition_heatmap": "run_exhibition_heatmap_pipeline",
    "dorm_energy_optimizer": "run_dorm_energy_optimizer_pipeline",
    "restaurant_sales_analysis": "run_restaurant_sales_analysis_pipeline",
    "warehouse_slot_optimizer": "run_warehouse_slot_optimizer_pipeline",
    "paper_classifier": "run_paper_classifier_pipeline",
    "vendor_evaluation_standardizer": "run_vendor_evaluation_standardizer_pipeline",
    "content_tagger": "run_content_tagger_pipeline",
    "partner_profile_hub": "run_partner_profile_hub_pipeline",
    "subscription_dispatch": "run_subscription_dispatch_pipeline",
    "contract_versioning": "run_contract_versioning_pipeline",
    "invoice_reconciliation": "run_invoice_reconciliation_pipeline",
    "project_risk_monitor": "run_project_risk_monitor_pipeline",
    "learning_record_hub": "run_learning_record_hub_pipeline",
    "supply_chain_tracker": "run_supply_chain_tracker_pipeline",
    "compliance_doc_manager": "run_compliance_doc_manager_pipeline",
    "mail_classifier": "run_mail_classifier_pipeline",
    "meeting_minutes": "run_meeting_minutes_pipeline",
    "policy_update_notifier": "run_policy_update_notifier_pipeline",
    "export_transformer": "run_export_transformer_pipeline",
    "api_log_analytics": "run_api_log_analytics_pipeline",
    "backup_sync": "run_backup_sync_pipeline",
    "patent_competition_monitor": "run_patent_competition_monitor_pipeline",
    "grant_subscription": "run_grant_subscription_pipeline",
    "experiment_review": "run_experiment_review_pipeline",
    "repro_audit": "run_repro_audit_pipeline",
    "benchmark_watch": "run_benchmark_watch_pipeline",
    "course_qa_helper": "run_course_qa_helper_pipeline",
    "lesson_scheduler": "run_lesson_scheduler_pipeline",
    "assignment_feedback": "run_assignment_feedback_pipeline",
    "skill_gap_diagnosis": "run_skill_gap_diagnosis_pipeline",
    "interview_coach": "run_interview_coach_pipeline",
    "campus_aid_gap_alert": "run_campus_aid_gap_alert_pipeline",
    "triage_structurer": "run_triage_structurer_pipeline",
    "radiology_followup_loop": "run_radiology_followup_loop_pipeline",
    "drug_leaflet_extractor": "run_drug_leaflet_extractor_pipeline",
    "lab_turnaround_alert": "run_lab_turnaround_alert_pipeline",
    "quote_compare": "run_quote_compare_pipeline",
    "policy_search_helper": "run_policy_search_helper_pipeline",
    "knowledge_cleanup": "run_knowledge_cleanup_pipeline",
    "podcast_highlight": "run_podcast_highlight_pipeline",
    "brand_compliance_review": "run_brand_compliance_review_pipeline",
    "subtitle_qc": "run_subtitle_qc_pipeline",
    "content_scheduler": "run_content_scheduler_pipeline",
    "media_archive_search": "run_media_archive_search_pipeline",
    "factory_watch": "run_factory_watch_pipeline",
    "cold_chain_watch": "run_cold_chain_watch_pipeline",
    "greenhouse_assistant": "run_greenhouse_assistant_pipeline",
    "community_hotspot_drift": "run_community_hotspot_drift_pipeline",
    "traffic_briefing": "run_traffic_briefing_pipeline",
    "urban_repair_scheduler": "run_urban_repair_scheduler_pipeline",
    "permit_material_review": "run_permit_material_review_pipeline",
    "municipal_search": "run_municipal_search_pipeline",
    "budget_variance_alert": "run_budget_variance_alert_pipeline",
    "cashflow_watch": "run_cashflow_watch_pipeline",
    "return_reason_mining": "run_return_reason_mining_pipeline",
    "store_daily_digest": "run_store_daily_digest_pipeline",
    "carbon_collection": "run_carbon_collection_pipeline",
    "solar_alerting": "run_solar_alerting_pipeline",
    "campus_emission_report": "run_campus_emission_report_pipeline",
    "data_center_watch": "run_data_center_watch_pipeline",
}


def test_generated_pipeline_exports():
    for app_name, symbol in APP_PIPELINES.items():
        module = importlib.import_module(f"sage.apps.{app_name}")
        assert hasattr(module, symbol)


def test_operator_smoke_behaviors(tmp_path: Path):
    from sage.apps.academic_metadata.operators import AuthorNormalizer, MetadataExtractor
    from sage.apps.contract_matcher.operators import KeywordExtractor, TemplateMatcher
    from sage.apps.customer_deduplication.operators import DuplicateDetector, SimilarityCalculator
    from sage.apps.doc_classifier.operators import Classifier as DocClassifier
    from sage.apps.doc_classifier.operators import FeatureExtractor
    from sage.apps.doc_classifier.operators import TextExtractor as DocTextExtractor
    from sage.apps.doc_classifier.operators import Tokenizer as DocTokenizer
    from sage.apps.feedback_analyzer.operators import KeywordExtractor as FeedbackKeywordExtractor
    from sage.apps.feedback_analyzer.operators import KeywordScorer, TextCleaner
    from sage.apps.inventory_alert.operators import AlertGenerator, InventoryComparator
    from sage.apps.log_parser.operators import ErrorFilter, LogEnricher, LogParser
    from sage.apps.order_anomaly_detector.operators import FeatureCalculator, RuleScorer
    from sage.apps.product_sync.operators import DataValidator, FieldMapper
    from sage.apps.quality_defect_filter.operators import (
        DefectSeverityScorer,
        DefectSplitter,
        DefectStandardizer,
        DefectTextExtractor,
    )
    from sage.apps.restaurant_sales_analysis.operators import (
        DishSplitter,
        InventoryJoiner,
        MenuProfitScorer,
    )
    from sage.apps.voucher_classifier.operators import FieldExtractor as VoucherFieldExtractor
    from sage.apps.voucher_classifier.operators import RuleClassifier as VoucherRuleClassifier

    requirement = KeywordExtractor().execute(
        {"text": "Need a confidentiality and disclosure contract"}
    )
    matched = TemplateMatcher(top_k=2).execute(requirement)
    assert matched["matches"]

    parsed_log = LogParser().execute("2026-04-21T10:00:00 ERROR [API] Request failed ERR500")
    filtered_log = ErrorFilter(error_levels=["ERROR"]).execute(parsed_log)
    enriched_log = LogEnricher().execute(filtered_log)
    assert enriched_log["has_error_code"] is True

    metadata = MetadataExtractor().execute(
        {
            "text": "A Practical Medical Study\nAlice Smith, Bob Lee\nAbstract: This paper studies biomarkers.\nKeywords: medicine\nDOI 10.1234/ABC123"
        }
    )
    normalized_metadata = AuthorNormalizer().execute(metadata)
    assert normalized_metadata["title"] == "A Practical Medical Study"
    assert normalized_metadata["authors"]

    duplicate_detector = DuplicateDetector(threshold=0.8)
    first = duplicate_detector.execute(
        SimilarityCalculator().execute(
            {"customer_id": "1", "name": "Alice", "email": "a@example.com", "phone": "13800000000"}
        )
    )
    second = duplicate_detector.execute(
        SimilarityCalculator().execute(
            {"customer_id": "2", "name": "Alice", "email": "a@example.com", "phone": "13800000000"}
        )
    )
    assert first["is_duplicate"] is False
    assert second["is_duplicate"] is True

    cleaned_feedback = TextCleaner().execute(
        {"text": "Great support, but refund is slow", "id": "1"}
    )
    scored_feedback = FeedbackKeywordExtractor(top_n=5).execute(
        KeywordScorer().execute(
            {"feedback_id": "1", "token": cleaned_feedback["cleaned_text"].split()[0], "length": 5}
        )
    )
    assert scored_feedback is not None

    voucher = VoucherRuleClassifier().execute(
        VoucherFieldExtractor().execute(
            {"ocr_text": "Amount: 200 Date: 2026-04-01 taxi reimbursement"}
        )
    )
    assert voucher["voucher_type"] == "travel_expense"

    mapped_product = DataValidator().execute(
        FieldMapper().execute(
            {"sku": "S-1", "name": "Widget", "price": "8.5", "inventory": "12", "category": "tool"}
        )
    )
    assert mapped_product["is_valid"] is True

    tokenized_doc = DocTokenizer().execute(
        DocTextExtractor().execute(
            {"text": "This contract includes agreement clauses and liability terms."}
        )
    )
    classified_doc = DocClassifier().execute(FeatureExtractor().execute(tokenized_doc[0]))
    assert classified_doc["label"] == "contract"

    inventory = AlertGenerator().execute(
        InventoryComparator().execute(
            {"sku": "A-1", "current_stock": 2, "reorder_point": 5, "max_stock": 20}
        )
    )
    assert inventory["status"] == "low"

    defect_items = DefectSplitter().execute(
        DefectTextExtractor().execute(
            {"report_id": "R1", "description": "scratch; crack", "severity": "high"}
        )
    )
    scored_defect = DefectSeverityScorer().execute(DefectStandardizer().execute(defect_items[1]))
    assert scored_defect["severity_level"] in {"medium", "high"}

    dish_items = DishSplitter().execute(
        {
            "order_id": "O1",
            "dishes": "noodles:2:48:20|tea:1:12:3",
            "inventory_qty": 3,
            "waste_rate": 0.1,
        }
    )
    advised_dish = MenuProfitScorer().execute(InventoryJoiner().execute(dish_items[0]))
    assert advised_dish["recommendation"] in {"restock", "keep", "promote", "remove_or_reprice"}

    scored_order = RuleScorer().execute(
        FeatureCalculator().execute({"amount": 12000, "quantity": 2})
    )
    assert scored_order["is_anomaly"] is True

    snapshot = tmp_path / "snapshot.json"
    snapshot.write_text(json.dumps({"ok": True}), encoding="utf-8")
    assert json.loads(snapshot.read_text(encoding="utf-8"))["ok"] is True
