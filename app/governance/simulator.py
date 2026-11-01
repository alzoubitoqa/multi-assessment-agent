"""Incremental incident simulation with independent institutional assessments.

All scenarios use synthetic facts. Decisions are advisory and always require a
human reviewer. The audit is a *decision trace*, not hidden LLM chain-of-thought.
"""

import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from config import BASE_DIR, DB_PATH, LLM_MODEL
from app.policy.kb import load_catalog, search_global_examples, search_policies

SCENARIO_DIR = BASE_DIR / "data" / "scenarios"

HUMAN_ACTIONS = {
    "dismiss_false_flag": "Dismiss unsubstantiated integrity flag",
    "correct_assessment": "Approve assessment correction and remediation",
    "request_more_evidence": "Request further evidence and keep case open",
    "escalate_review": "Escalate to qualified institutional or legal review",
    "close_no_sanction": "Close case without misconduct sanction",
}

GAP_CHECKS = {
    "fast_answer": "Verify whether the institution has defined evidentiary thresholds and an appeal procedure for speed-based integrity alerts.",
    "fairness": "Verify whether institutional policy requires validation of response-time heuristics against legitimate performance variations.",
    "invalid_question": "Verify whether a documented question-validation and quarantine policy covers unsupported AI-generated content.",
    "student_impact": "Verify whether documented remediation rules cover affected grades, analytics and student notification.",
    "privacy": "Verify whether documented privacy, retention, access and correction procedures govern the data involved in this scenario.",
    "review": "Verify whether a documented human review, incident closure and correction procedure applies to this case.",
}

EDUCATION_EVIDENCE = {
    "UNESCO-ETHICS-2021-P43", "UNESCO-ETHICS-2021-P53",
    "UNESCO-ETHICS-2021-P104",
}
PRIVACY_EVIDENCE = {
    "UAE-PDPL-2021-ART1", "UAE-PDPL-2021-ART2",
    "UAE-PDPL-2021-ART4", "UAE-PDPL-2021-ART5",
    "UAE-PDPL-2021-ART13", "UAE-PDPL-2021-ART15",
    "UAE-PDPL-2021-ART18", "UAE-PDPL-2021-ART22",
    "UAE-PDPL-2021-ART23",
}

ROLES = {
    "academic_integrity": {
        "label": "Academic Integrity Officer",
        "mandate": "Protect fair process and avoid automatic punishment based on weak behavioural signals.",
        "query": "academic integrity student monitoring fairness human oversight",
    },
    "privacy_officer": {
        "label": "Data Protection Officer",
        "mandate": "Examine personal-data collection, processing basis, retention and access.",
        "query": "personal data privacy consent student records oversight",
    },
    "academic_quality": {
        "label": "Academic Quality Reviewer",
        "mandate": "Protect assessment validity, correct errors and ensure human review.",
        "query": "education AI evaluation student fairness quality auditability",
    },
}

RECOMMENDATIONS = {
    "fast_answer": {
        "academic_integrity": "Keep the flag advisory; seek corroborating evidence before any allegation or sanction.",
        "academic_quality": "Check the timing heuristic against legitimate high-speed answers and question difficulty.",
    },
    "fairness": {
        "academic_integrity": "Reassess the alert using the learner's context; provide a fair opportunity to respond.",
        "academic_quality": "Evaluate false-positive impact and avoid treating response speed as proof of misconduct.",
    },
    "invalid_question": {
        "academic_quality": "Stop presenting the unsupported question and preserve its retrieved source evidence for review.",
    },
    "student_impact": {
        "academic_quality": "Identify affected attempts, invalidate the faulty question and correct aggregate analytics.",
        "academic_integrity": "Do not disadvantage students for a model-generated assessment error.",
    },
    "privacy": {
        "privacy_officer": "Map actual data flows, check lawful basis and institutional scope, restrict unnecessary access, and review retention.",
        "academic_integrity": "Document the student's concern and provide a route to human review and correction.",
    },
    "review": {
        "academic_quality": "Record the correction, verify assessment validity and approve remediation before closing the incident.",
        "academic_integrity": "Resolve the flag or grading concern with documented human review and no automatic punishment.",
        "privacy_officer": "Confirm data handling and update the incident record with access and retention decisions.",
    },
}


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


@contextmanager
def _connect(db_path: Path | str = DB_PATH):
    """Transactional connection which closes before temp-file cleanup on Windows."""
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init_incident_db(db_path: Path | str = DB_PATH) -> None:
    with _connect(db_path) as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS incident_runs (
            run_id TEXT PRIMARY KEY, scenario_id TEXT NOT NULL,
            position INTEGER NOT NULL DEFAULT 0, started_at TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS incident_events (
            run_id TEXT NOT NULL, event_number INTEGER NOT NULL,
            event_json TEXT NOT NULL, released_at TEXT NOT NULL,
            PRIMARY KEY (run_id, event_number)
        );
        CREATE TABLE IF NOT EXISTS agent_assessments (
            run_id TEXT NOT NULL, event_number INTEGER NOT NULL,
            role TEXT NOT NULL, assessment_json TEXT NOT NULL,
            created_at TEXT NOT NULL,
            PRIMARY KEY (run_id, event_number, role)
        );
        CREATE TABLE IF NOT EXISTS incident_coordination (
            run_id TEXT NOT NULL, event_number INTEGER NOT NULL,
            coordination_json TEXT NOT NULL, created_at TEXT NOT NULL,
            PRIMARY KEY (run_id, event_number)
        );
        CREATE TABLE IF NOT EXISTS incident_human_decisions (
            decision_id INTEGER PRIMARY KEY AUTOINCREMENT,
            run_id TEXT NOT NULL, action TEXT NOT NULL,
            reviewer TEXT NOT NULL, rationale TEXT NOT NULL,
            recorded_at TEXT NOT NULL
        );
        """)


def list_scenarios() -> list[dict]:
    return [{k: s[k] for k in ("id", "title", "description", "jurisdiction")}
            for s in (_read_scenario(p) for p in sorted(SCENARIO_DIR.glob("*.json")))]


def _read_scenario(path: Path) -> dict:
    scenario = json.loads(path.read_text(encoding="utf-8"))
    if len({e["id"] for e in scenario["events"]}) != len(scenario["events"]):
        raise ValueError("Scenario event IDs must be unique")
    for event in scenario["events"]:
        if set(event["visible_to"]) - set(ROLES):
            raise ValueError(f"Unknown role in event {event['id']}")
    return scenario


def get_scenario(scenario_id: str) -> dict:
    for path in SCENARIO_DIR.glob("*.json"):
        scenario = _read_scenario(path)
        if scenario["id"] == scenario_id:
            return scenario
    raise ValueError(f"Unknown scenario: {scenario_id}")


def start_scenario(scenario_id: str, db_path: Path | str = DB_PATH) -> str:
    get_scenario(scenario_id)
    init_incident_db(db_path)
    run_id = uuid.uuid4().hex[:12]
    with _connect(db_path) as conn:
        conn.execute("INSERT INTO incident_runs VALUES (?, ?, ?, ?)",
                     (run_id, scenario_id, 0, _now()))
    return run_id


def _evaluate_role(role: str, events: list[dict], jurisdiction: str,
                   policy_search=search_policies, use_llm: bool = False) -> dict:
    started = time.monotonic()
    latest = events[-1]
    advice = RECOMMENDATIONS.get(latest["issue"], {}).get(
        role, "Review relevant documents and refer the incident to the responsible human authority.")
    issue_terms = {
        "privacy": "retention correction access personal data automated decisions external processing possible cross-border transfer applicability",
        "invalid_question": "question assessment evidence validation human oversight",
        "student_impact": "assessment correction student fairness audit remediation",
    }
    query = " ".join((ROLES[role]["query"], latest["title"],
                      issue_terms.get(latest["issue"], latest["issue"])))
    retrieved = policy_search(query, jurisdiction=jurisdiction, limit=16)
    observed_privacy = any(event["issue"] == "privacy" for event in events)
    if role == "privacy_officer":
        allowed = PRIVACY_EVIDENCE
    elif observed_privacy:
        allowed = EDUCATION_EVIDENCE | PRIVACY_EVIDENCE
    else:
        allowed = EDUCATION_EVIDENCE
    policies = [p for p in retrieved if p["id"] in allowed or
                (p["source_kind"] == "official_pdf" and role == "privacy_officer")]
    if role == "privacy_officer":
        # The legal scope/source check must never be dropped by top-k truncation.
        # Include only the articles relevant to this event; unrelated articles
        # risk giving the model a false impression of legal support.
        # External-provider use warrants checking transfer provisions, but does
        # not prove that personal data was sent or that it crossed a border.
        external_provider_seen = any(e["id"] == "external_processing" for e in events)
        relevant = (["ART2", "ART1", "ART4", "ART22", "ART23"]
                    if external_provider_seen else
                    ["ART2", "ART5", "ART13", "ART15", "ART18"])
        curated = {p["id"]: p for p in load_catalog()}
        ranked = {p["id"]: p for p in policies}
        selected = []
        for article in relevant:
            source_id = f"UAE-PDPL-2021-{article}"
            selected.append(ranked.get(source_id) or {
                **curated[source_id], "retrieval_mode": "legal_scope_and_rights_guardrail"
            })
        official_chunks = [p for p in policies if p["source_kind"] == "official_pdf"]
        if official_chunks:
            selected.append(official_chunks[0])
        else:
            supplementary_id = ("UAE-PDPL-2021-ART5" if external_provider_seen
                                else "UAE-PDPL-2021-ART1")
            selected.append(ranked.get(supplementary_id) or {
                **curated[supplementary_id],
                "retrieval_mode": "legal_scope_and_rights_guardrail"
            })
        policies = selected
    else:
        policies = policies[:6]
    citations = [{"id": p["id"], "reference": p["reference"],
                  "url": p["url"], "binding_level": p["binding_level"],
                  "source_kind": p["source_kind"], "jurisdiction": p["jurisdiction"],
                  "page_number": p.get("page_number"),
                  "record_id": p.get("record_id")} for p in policies]
    model_result = None
    if use_llm:
        from app.agents.policy_adviser import grounded_advice
        model_result = grounded_advice(role, events, policies)
    if model_result:
        advice = model_result["recommendation"]
        citations = [source for source in citations if source["id"] in model_result["citation_ids"]]
        if role == "academic_quality" and latest["issue"] == "invalid_question":
            # A forward-looking validation plan alone cannot contain a bad
            # question already delivered to students. Keep the mitigation
            # advisory: never change any student record automatically.
            if not any(word in advice.lower() for word in
                       ("quarantine", "withdraw", "stop presenting", "pause the question",
                        "block the question", "remove the question", "suspend the question")):
                advice = ("Quarantine the unsupported question pending human review, "
                          "preserve its source evidence, and do not change grades automatically. "
                          + advice)
    assessment = {
        "role": role, "role_label": ROLES[role]["label"], "mandate": ROLES[role]["mandate"],
        "observed_event_ids": [event["id"] for event in events],
        "latest_observation": latest["detail"],
        "recommendation": advice, "citations": citations,
        "assessment_mode": "source_grounded_llm" if model_result else "rules_fallback",
        "public_rationale": model_result["public_rationale"] if model_result else ROLES[role]["mandate"],
        "confidence_note": "Advisory assessment; evidence is incomplete until human verification.",
        "policy_gap": model_result["policy_gap"] if model_result else GAP_CHECKS.get(
            latest["issue"], "Verify whether an institution-specific procedure addresses this incident."
        ),
        "gap_evidence_status": "unverified_in_available_corpus",
        "legal_applicability": "unverified; determine institutional status, jurisdiction and exceptions before legal conclusions",
        "citation_validation": "retrieved_source_ids_only; semantic support requires human/source-text review",
        "review_required": True,
        "trace": {"rule": latest["issue"], "retrieval_query": query,
                  "source_ids": [citation["id"] for citation in citations],
                  "model": LLM_MODEL if model_result else None,
                  "temperature": 0 if model_result else None},
    }
    assessment["evaluated_at"] = _now()
    assessment["latency_ms"] = round((time.monotonic() - started) * 1000, 2)
    return assessment


def _coordinate(assessments: list[dict], event_id: str) -> dict:
    """Explicit protocol: gather independent views, then request a human decision."""
    subject = "education AI assessment and academic integrity monitoring"
    comparisons = search_global_examples(subject, limit=3)
    needed = [f"{a['role_label']}: confirm evidence and authority for the proposed action"
              for a in assessments]
    return {"event_id": event_id, "protocol": "independent_roles_then_human_review_v1",
            "contributors": [item["role"] for item in assessments],
            "combined_recommendations": [item["recommendation"] for item in assessments],
            "policy_sources": sorted({c["id"] for a in assessments for c in a["citations"]}),
            "unresolved_gaps": sorted({a["policy_gap"] for a in assessments}),
            "open_review_questions": needed,
            "global_examples": [{"id": p["id"], "reference": p["reference"],
                                 "jurisdiction": p["jurisdiction"], "url": p["url"],
                                 "applicability": "comparative_only_not_UAE_law"}
                                for p in comparisons],
            "coordination_limit": "Independent role assessments are synthesized; no agent negotiation or conflict resolution is claimed.",
            "final_action": "Pending authorized human decision; no automatic sanction or grade change."}


def get_run_history(run_id: str, db_path: Path | str = DB_PATH) -> dict:
    init_incident_db(db_path)
    with _connect(db_path) as conn:
        row = conn.execute("SELECT * FROM incident_runs WHERE run_id = ?", (run_id,)).fetchone()
        if row is None:
            raise ValueError("Unknown run ID")
        event_rows = conn.execute(
            "SELECT * FROM incident_events WHERE run_id = ? ORDER BY event_number", (run_id,)).fetchall()
        assessments = conn.execute(
            "SELECT * FROM agent_assessments WHERE run_id = ? ORDER BY event_number, role", (run_id,)).fetchall()
        coordination = conn.execute(
            "SELECT * FROM incident_coordination WHERE run_id = ? ORDER BY event_number", (run_id,)).fetchall()
        decisions = conn.execute(
            "SELECT * FROM incident_human_decisions WHERE run_id = ? ORDER BY decision_id", (run_id,)).fetchall()
    scenario = get_scenario(row["scenario_id"])
    decision_items = [{"action": r["action"], "action_label": HUMAN_ACTIONS[r["action"]],
                       "reviewer": r["reviewer"], "rationale": r["rationale"],
                       "recorded_at": r["recorded_at"], "identity_verified": False}
                      for r in decisions]
    return {"run_id": run_id, "scenario_id": row["scenario_id"],
            "title": scenario["title"], "started_at": row["started_at"],
            "released_count": row["position"],
            "total_events": len(scenario["events"]),
            "events": [{**json.loads(r["event_json"]), "number": r["event_number"],
                        "released_at": r["released_at"]} for r in event_rows],
            "assessments": [{**json.loads(r["assessment_json"]),
                             "logged_at": r["created_at"]} for r in assessments],
            "coordination": [{**json.loads(r["coordination_json"]),
                              "logged_at": r["created_at"]} for r in coordination],
            "human_decisions": decision_items,
            "human_decision": (decision_items[-1]["action_label"] +
                               " (self-reported reviewer; identity not verified)"
                               if decision_items else "Pending human review"),
            "trace_type": "structured decision trace, not private model reasoning"}


def record_human_decision(run_id: str, reviewer: str, action: str, rationale: str,
                          db_path: Path | str = DB_PATH) -> dict:
    """Append an explicit, self-reported human review entry (no authentication).

    This action records governance recommendations only. It never changes a grade
    or student record, and does not certify that the reviewer is authorized.
    """
    if action not in HUMAN_ACTIONS:
        raise ValueError("Unknown or prohibited human decision action")
    reviewer, rationale = reviewer.strip(), rationale.strip()
    if not reviewer or not rationale:
        raise ValueError("Human reviewer and documented rationale are required")
    if len(reviewer) > 120 or len(rationale) > 4000:
        raise ValueError("Human decision fields exceed the permitted length")
    history = get_run_history(run_id, db_path)
    if history["released_count"] != history["total_events"]:
        raise ValueError("Release all events before recording a final human review")
    recorded_at = _now()
    with _connect(db_path) as conn:
        conn.execute("INSERT INTO incident_human_decisions "
                     "(run_id, action, reviewer, rationale, recorded_at) VALUES (?, ?, ?, ?, ?)",
                     (run_id, action, reviewer, rationale, recorded_at))
    return {"run_id": run_id, "action": action, "reviewer": reviewer,
            "rationale": rationale, "recorded_at": recorded_at,
            "identity_verified": False}


def release_next_event(run_id: str, db_path: Path | str = DB_PATH,
                       policy_search=search_policies, use_llm: bool = False) -> dict:
    """Release exactly one event. Each role sees only events disclosed to it."""
    history = get_run_history(run_id, db_path)
    scenario = get_scenario(history["scenario_id"])
    position = history["released_count"]
    if position >= len(scenario["events"]):
        raise ValueError("The scenario has no remaining events")
    event = scenario["events"][position]
    visible_history = history["events"] + [event]
    assessments = []
    for role in event["visible_to"]:
        visible_to_role = [item for item in visible_history if role in item["visible_to"]]
        assessments.append(_evaluate_role(role, visible_to_role,
                                          scenario["jurisdiction"], policy_search,
                                          use_llm=use_llm))
    coordination = _coordinate(assessments, event["id"])
    with _connect(db_path) as conn:
        conn.execute("BEGIN IMMEDIATE")
        actual_position = conn.execute("SELECT position FROM incident_runs WHERE run_id = ?",
                                       (run_id,)).fetchone()[0]
        if actual_position != position:
            raise RuntimeError("This event was already released in another session")
        conn.execute("INSERT INTO incident_events VALUES (?, ?, ?, ?)",
                     (run_id, position + 1, json.dumps(event), _now()))
        for assessment in assessments:
            conn.execute("INSERT INTO agent_assessments VALUES (?, ?, ?, ?, ?)",
                         (run_id, position + 1, assessment["role"], json.dumps(assessment), _now()))
        conn.execute("INSERT INTO incident_coordination VALUES (?, ?, ?, ?)",
                     (run_id, position + 1, json.dumps(coordination), _now()))
        conn.execute("UPDATE incident_runs SET position = position + 1 WHERE run_id = ?", (run_id,))
    return {"event_number": position + 1, "event": event,
            "assessments": assessments, "coordination": coordination,
            "next_step": "Human review required; do not auto-sanction.",
            "completed": position + 1 == len(scenario["events"])}
