"""Prepare default input and output paths for example pipelines."""

from __future__ import annotations

from pathlib import Path
import json
import re

from .models import AppDefinition, ArgumentDefinition


def apply_default_argument_values(root_dir: Path, app: AppDefinition) -> AppDefinition:
    notes = list(app.launch_notes)
    touched_arguments = 0

    for argument in app.arguments:
        if argument.kind != "path":
            continue
        if argument.default not in {None, "", "None"}:
            argument.opc_default_value = argument.default
            argument.opc_default_origin = "script-default"
            continue
        default_value, default_origin = _resolve_argument_default(root_dir, app, argument)
        if default_value is None:
            continue
        argument.opc_default_value = default_value
        argument.opc_default_origin = default_origin
        touched_arguments += 1

    if touched_arguments:
        notes.append(f"OPC prepared default path values for {touched_arguments} file or directory arguments.")
    app.launch_notes = notes
    return app


def _resolve_argument_default(root_dir: Path, app: AppDefinition, argument: ArgumentDefinition) -> tuple[str | None, str | None]:
    example_token = _example_token_for_argument(app, argument)
    existing = _existing_repo_path(root_dir, app, argument, example_token)
    if existing is not None:
        return str(existing), "repo-existing"

    if _is_output_argument(argument):
        output_path = _default_output_path(root_dir, app, argument, example_token)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        return str(output_path), "opc-generated-output"

    if _is_directory_argument(argument):
        directory_path = _default_input_directory(root_dir, app, argument, example_token)
        directory_path.mkdir(parents=True, exist_ok=True)
        sample_child = directory_path / _default_child_name(argument, example_token)
        _write_generated_sample(sample_child, app, argument, sample_child.suffix)
        return str(directory_path), "opc-generated-directory"

    input_path = _default_input_path(root_dir, app, argument, example_token)
    input_path.parent.mkdir(parents=True, exist_ok=True)
    _write_generated_sample(input_path, app, argument, input_path.suffix)
    return str(input_path), "opc-generated-file"


def _write_generated_sample(path: Path, app: AppDefinition, argument: ArgumentDefinition, suffix: str) -> None:
    path.write_text(_sample_content_for_argument(app, argument, suffix), encoding="utf-8")


def _example_token_for_argument(app: AppDefinition, argument: ArgumentDefinition) -> str | None:
    for example in app.examples:
        tokens = example.split()
        for index, token in enumerate(tokens):
            cleaned = token.rstrip("\\")
            if any(cleaned == name for name in argument.names):
                if index + 1 < len(tokens):
                    candidate = tokens[index + 1].rstrip("\\")
                    if not candidate.startswith("--"):
                        return candidate
            for name in argument.names:
                prefix = name + "="
                if cleaned.startswith(prefix):
                    return cleaned[len(prefix):]
    return None


def _existing_repo_path(root_dir: Path, app: AppDefinition, argument: ArgumentDefinition, example_token: str | None) -> Path | None:
    candidates: list[Path] = []
    if example_token:
        candidates.append((root_dir / example_token).resolve())
        candidates.append((root_dir / app.working_dir / example_token).resolve())
    lowered = " ".join(part.lower() for part in [argument.primary_name, argument.help or ""])
    if "config" in lowered and "video" in app.id:
        candidates.append((root_dir / "apps/src/sage/apps/video/config/default_config.yaml").resolve())
    if "config" in lowered and "medical" in app.id:
        candidates.append((root_dir / "apps/src/sage/apps/medical_diagnosis/config/agent_config.yaml").resolve())
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def _default_input_directory(root_dir: Path, app: AppDefinition, argument: ArgumentDefinition, example_token: str | None) -> Path:
    path = root_dir / ".sage" / "opc-default-inputs" / app.id / argument.primary_name.lstrip("-").replace("-", "_")
    if example_token:
        token_name = Path(example_token).name
        if token_name and token_name not in {".", ".."} and "." not in token_name:
            path = path.parent / token_name
    return path.resolve()


def _default_input_path(root_dir: Path, app: AppDefinition, argument: ArgumentDefinition, example_token: str | None) -> Path:
    suffix = _preferred_suffix(argument, example_token)
    filename = _default_file_stem(argument, example_token) + suffix
    return (root_dir / ".sage" / "opc-default-inputs" / app.id / filename).resolve()


def _default_output_path(root_dir: Path, app: AppDefinition, argument: ArgumentDefinition, example_token: str | None) -> Path:
    suffix = _preferred_suffix(argument, example_token, output=True)
    filename = _default_file_stem(argument, example_token, output=True) + suffix
    return (root_dir / ".sage" / "opc-default-outputs" / app.id / filename).resolve()


def _default_child_name(argument: ArgumentDefinition, example_token: str | None) -> str:
    suffix = _preferred_suffix(argument, example_token)
    return "sample" + suffix


def _default_file_stem(argument: ArgumentDefinition, example_token: str | None, *, output: bool = False) -> str:
    if example_token:
        example_name = Path(example_token).stem
        if example_name:
            return re.sub(r"[^A-Za-z0-9._-]", "_", example_name)
    stem = argument.primary_name.lstrip("-").replace("-", "_")
    return stem if not output else stem.replace("output", "result")


def _preferred_suffix(argument: ArgumentDefinition, example_token: str | None, *, output: bool = False) -> str:
    if example_token and Path(example_token).suffix:
        return Path(example_token).suffix
    lowered = " ".join(part.lower() for part in [argument.primary_name, argument.help or "", argument.value_name or ""])
    if "csv" in lowered:
        return ".csv"
    if "yaml" in lowered or "yml" in lowered or "config" in lowered:
        return ".yaml"
    if "json" in lowered or "event" in lowered or "record" in lowered or "metric" in lowered or "plan" in lowered or "profile" in lowered:
        return ".json"
    if "log" in lowered:
        return ".log"
    if "html" in lowered:
        return ".html"
    if "md" in lowered or "markdown" in lowered:
        return ".md"
    if "video" in lowered:
        return ".txt"
    if "output" in lowered and output:
        return ".json"
    return ".txt"


def _sample_content_for_argument(app: AppDefinition, argument: ArgumentDefinition, suffix: str) -> str:
    lowered = " ".join(part.lower() for part in [app.id, argument.primary_name, argument.help or ""])
    topic = _sample_topic(lowered)
    if suffix == ".csv":
        return _sample_csv_content(app, argument, topic)
    if suffix == ".json":
        payload = _sample_json_content(app, argument, topic, lowered)
        return json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if suffix == ".yaml":
        return _sample_yaml_content(app, argument, topic)
    if suffix == ".log":
        return _sample_log_content(topic)
    if suffix == ".md":
        return _sample_markdown_content(app, topic)
    if suffix == ".html":
        return _sample_html_content(app, topic)
    return _sample_text_content(app, argument, topic)


def _sample_topic(lowered: str) -> str:
    if any(token in lowered for token in ["ticket", "support", "triage", "router", "helpdesk"]):
        return "support"
    if any(token in lowered for token in ["credit", "invoice", "budget", "cashflow", "quote", "subscription", "sales", "billing", "finance"]):
        return "finance"
    if any(token in lowered for token in ["supply", "shipment", "cold", "inventory", "warehouse", "logistics", "order", "backup", "product"]):
        return "supply_chain"
    if any(token in lowered for token in ["course", "student", "campus", "attendance", "assignment", "lesson", "lab", "learning", "grant"]):
        return "education"
    if any(token in lowered for token in ["medical", "patient", "drug", "radiology", "diagnosis", "registration", "leaflet"]):
        return "medical"
    if any(token in lowered for token in ["contract", "policy", "permit", "audit", "compliance", "permission", "patent"]):
        return "governance"
    if any(token in lowered for token in ["content", "article", "news", "podcast", "subtitle", "brand", "media", "moderation"]):
        return "content"
    if any(token in lowered for token in ["paper", "literature", "academic", "research"]):
        return "research"
    if any(token in lowered for token in ["energy", "carbon", "factory", "data center", "solar", "emission", "hotspot"]):
        return "operations"
    if any(token in lowered for token in ["resume", "interview", "lead", "partner", "profile"]):
        return "people"
    return "generic"


def _sample_csv_content(app: AppDefinition, argument: ArgumentDefinition, topic: str) -> str:
    if topic == "support":
        return (
            "ticket_id,customer,channel,priority,summary\n"
            "T-1001,Acme Foods,email,high,Checkout login failure blocks order confirmation\n"
            "T-1002,Northwind Retail,chat,medium,Refund requested after duplicate payment\n"
            "T-1003,Blue Harbor,portal,low,User asks how to update delivery address\n"
        )
    if topic == "finance":
        return (
            "account_id,period,planned,actual,notes\n"
            "AC-01,2026-01,120000,128500,Cloud spend spiked during launch week\n"
            "AC-02,2026-01,76000,70250,Marketing spend stayed below target\n"
            "AC-03,2026-01,45000,49200,Freight cost increased for urgent orders\n"
        )
    if topic == "supply_chain":
        return (
            "shipment_id,warehouse,status,temperature_c,eta_hours\n"
            "S-9001,W3,delayed,7.2,14\n"
            "S-9002,W1,in_transit,3.8,6\n"
            "S-9003,W3,at_risk,8.1,20\n"
        )
    if topic == "education":
        return (
            "student_id,course,score,attendance,comment\n"
            "ST-01,CS101,84,0.92,Missed one quiz but improving\n"
            "ST-02,CS101,61,0.68,Needs intervention on weekly exercises\n"
            "ST-03,CS101,95,0.98,Strong performance throughout the term\n"
        )
    if topic == "medical":
        return (
            "patient_id,age,complaint,severity,follow_up_days\n"
            "P-01,54,persistent chest tightness,high,1\n"
            "P-02,33,intermittent migraine,medium,7\n"
            "P-03,71,post-op fatigue,medium,3\n"
        )
    if topic == "governance":
        return (
            "doc_id,owner,category,risk_level,summary\n"
            "D-201,Legal,contract,high,Termination clause conflicts with renewal terms\n"
            "D-202,Procurement,policy,medium,New vendor onboarding policy missing audit step\n"
            "D-203,HR,permit,low,Temporary access extension request\n"
        )
    if topic == "content":
        return (
            "content_id,channel,title,status,summary\n"
            "C-11,blog,Cold-chain lessons from Q1,draft,Explains repeated warehouse temperature alerts\n"
            "C-12,newsletter,Campus sustainability weekly,review,Highlights energy reduction milestones\n"
            "C-13,social,Product delivery update,scheduled,Short customer-facing service announcement\n"
        )
    if topic == "research":
        return (
            "paper_id,title,year,topic,abstract\n"
            "R-01,Adaptive Retrieval Pipelines,2025,rag,Studies retrieval routing under mixed workloads\n"
            "R-02,Operator-Aware LLM Systems,2026,systems,Explores runtime-native observability for multi-stage pipelines\n"
        )
    return "id,text,value\n1,alpha,10\n2,beta,20\n3,gamma,30\n"


def _sample_json_content(app: AppDefinition, argument: ArgumentDefinition, topic: str, lowered: str) -> Any:
    if "config" in lowered or "profile" in lowered:
        return {
            "sample": True,
            "app": app.id,
            "model": "gpt-4o-mini",
            "base_url": "https://api.openai.com/v1",
            "api_key_env": "OPENAI_API_KEY",
            "notes": "Generated by OPC as a realistic starter config.",
        }
    if topic == "support":
        return [
            {
                "ticket_id": "T-1001",
                "customer": "Acme Foods",
                "priority": "high",
                "summary": "Checkout login failure blocks order confirmation.",
                "requested_action": "Route to authentication specialist and estimate blast radius.",
            },
            {
                "ticket_id": "T-1002",
                "customer": "Northwind Retail",
                "priority": "medium",
                "summary": "Refund requested after duplicate payment.",
                "requested_action": "Validate payment duplication and draft refund response.",
            },
        ]
    if topic == "finance":
        return [
            {
                "entity": "Acme Foods",
                "monthly_revenue": 182000,
                "monthly_expense": 149500,
                "late_payments": 2,
                "credit_events": ["supplier_delay", "temporary cash pressure"],
            },
            {
                "entity": "Blue Harbor",
                "monthly_revenue": 96000,
                "monthly_expense": 101200,
                "late_payments": 4,
                "credit_events": ["chargeback spike"],
            },
        ]
    if topic == "supply_chain":
        return [
            {
                "shipment_id": "S-9001",
                "warehouse": "W3",
                "severity": "high",
                "summary": "Repeated cold-chain excursion overnight.",
                "temperature_c": 8.1,
                "eta_hours": 20,
            },
            {
                "shipment_id": "S-9002",
                "warehouse": "W1",
                "severity": "medium",
                "summary": "Inbound shipment delayed by weather.",
                "temperature_c": 3.8,
                "eta_hours": 6,
            },
        ]
    if topic == "education":
        return [
            {
                "student_id": "ST-02",
                "course": "CS101",
                "attendance": 0.68,
                "risk": "high",
                "notes": "Missing weekly exercises and office-hour follow-up.",
            },
            {
                "student_id": "ST-05",
                "course": "ENG220",
                "attendance": 0.74,
                "risk": "medium",
                "notes": "Writing quality improving but deadlines are inconsistent.",
            },
        ]
    if topic == "medical":
        return [
            {
                "patient_id": "P-01",
                "age": 54,
                "symptoms": ["chest tightness", "fatigue"],
                "history": ["hypertension"],
                "triage_level": "urgent",
            },
            {
                "patient_id": "P-02",
                "age": 33,
                "symptoms": ["migraine", "light sensitivity"],
                "history": ["seasonal allergies"],
                "triage_level": "routine",
            },
        ]
    if topic == "governance":
        return [
            {
                "document_id": "D-201",
                "type": "contract",
                "owner": "Legal",
                "risk_level": "high",
                "summary": "Termination clause conflicts with the renewal schedule.",
            },
            {
                "document_id": "D-202",
                "type": "policy",
                "owner": "Procurement",
                "risk_level": "medium",
                "summary": "Vendor onboarding draft omits the compliance audit checkpoint.",
            },
        ]
    if topic == "content":
        return [
            {
                "content_id": "C-11",
                "channel": "blog",
                "title": "Cold-chain lessons from Q1",
                "summary": "Explains repeated warehouse temperature alerts and mitigation steps.",
            },
            {
                "content_id": "C-12",
                "channel": "newsletter",
                "title": "Campus sustainability weekly",
                "summary": "Highlights energy reduction milestones and pending actions.",
            },
        ]
    if topic == "research":
        return [
            {
                "paper_id": "R-01",
                "title": "Adaptive Retrieval Pipelines",
                "summary": "Studies retrieval routing under mixed workloads.",
            },
            {
                "paper_id": "R-02",
                "title": "Operator-Aware LLM Systems",
                "summary": "Explores runtime-native observability for multi-stage pipelines.",
            },
        ]
    if "question" in lowered:
        return [{"question": "What changed this week and what should an operator do next?"}]
    return [
        {"id": "S-1001", "text": f"sample input for {app.id}", "category": topic},
        {"id": "S-1002", "text": "follow-up sample input", "category": topic},
    ]


def _sample_yaml_content(app: AppDefinition, argument: ArgumentDefinition, topic: str) -> str:
    if "config" in " ".join([argument.primary_name.lower(), (argument.help or "").lower()]):
        return (
            f"app: {app.id}\n"
            "profile: demo\n"
            "model: gpt-4o-mini\n"
            "api_key_env: OPENAI_API_KEY\n"
            f"topic: {topic}\n"
        )
    return (
        "sample: true\n"
        f"app: {app.id}\n"
        f"topic: {topic}\n"
        "items:\n"
        "  - id: S-1001\n"
        "    text: realistic demo input\n"
    )


def _sample_log_content(topic: str) -> str:
    if topic == "supply_chain":
        return (
            "2026-01-01T10:00:00Z WARN warehouse=W3 cold_chain excursion detected\n"
            "2026-01-01T10:01:15Z INFO shipment=S-9001 operator=reset_sensor\n"
            "2026-01-01T10:04:12Z WARN warehouse=W3 excursion repeated after reset\n"
        )
    return (
        "2026-01-01T10:00:00Z INFO pipeline=demo input_received\n"
        "2026-01-01T10:01:00Z WARN pipeline=demo review_needed\n"
        "2026-01-01T10:02:00Z INFO pipeline=demo export_ready\n"
    )


def _sample_markdown_content(app: AppDefinition, topic: str) -> str:
    return (
        f"# {app.name} Sample Input\n\n"
        f"Topic: {topic}\n\n"
        "This markdown file was generated by OPC as a reusable demo source with enough context to make the output interpretable.\n"
    )


def _sample_html_content(app: AppDefinition, topic: str) -> str:
    return (
        "<html><body>"
        f"<h1>{app.name} Demo Input</h1>"
        f"<p>Topic: {topic}</p>"
        "<p>This HTML artifact is generated by OPC as a richer default input.</p>"
        "</body></html>\n"
    )


def _sample_text_content(app: AppDefinition, argument: ArgumentDefinition, topic: str) -> str:
    if topic == "support":
        return (
            "Customer: Acme Foods\n"
            "Issue: Login failures block checkout for multiple buyers.\n"
            "Priority: High\n"
            "Requested outcome: classify urgency, suggest next owner, and draft a short response.\n"
        )
    if topic == "finance":
        return (
            "Entity: Blue Harbor\n"
            "Observation: expenses exceeded plan for the third week in a row.\n"
            "Risk: short-term cash pressure if freight surcharges continue.\n"
            "Requested outcome: summarize risk drivers and recommend next actions.\n"
        )
    if topic == "supply_chain":
        return (
            "Warehouse W3 triggered a repeated cold-chain alert overnight.\n"
            "Two pallets may require manual inspection before dispatch.\n"
            "Requested outcome: summarize the incident, assign severity, and propose immediate actions.\n"
        )
    if topic == "education":
        return (
            "Student ST-02 has declining attendance and missed two assignments.\n"
            "Requested outcome: explain the risk level and suggest a concise intervention plan.\n"
        )
    if topic == "medical":
        return (
            "Patient P-01 reports chest tightness and fatigue after moderate activity.\n"
            "History includes hypertension.\n"
            "Requested outcome: organize the case context and highlight follow-up urgency.\n"
        )
    if topic == "governance":
        return (
            "The draft contract allows renewal before the termination window closes.\n"
            "Requested outcome: summarize the risk and identify the clause needing revision.\n"
        )
    if topic == "content":
        return (
            "Draft article discusses repeated warehouse temperature alerts in Q1.\n"
            "Requested outcome: produce tags, a concise summary, and one editorial risk note.\n"
        )
    if topic == "research":
        return (
            "Paper draft explores runtime-native observability for multi-stage AI systems.\n"
            "Requested outcome: extract key claims and one open systems question.\n"
        )
    return f"Sample input for {app.name} via {argument.primary_name}.\n"


def _is_output_argument(argument: ArgumentDefinition) -> bool:
    lowered = " ".join(part.lower() for part in [argument.primary_name, argument.help or "", argument.value_name or ""])
    return "output" in lowered or "out-file" in lowered or "outfile" in lowered


def _is_directory_argument(argument: ArgumentDefinition) -> bool:
    lowered = " ".join(part.lower() for part in [argument.primary_name, argument.help or "", argument.value_name or ""])
    return any(token in lowered for token in ["dir", "directory"]) and not _is_output_argument(argument)