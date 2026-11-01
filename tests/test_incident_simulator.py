import tempfile
import unittest
import sqlite3
from pathlib import Path
from unittest.mock import patch

from app.governance.simulator import (
    HUMAN_ACTIONS, _connect, _evaluate_role, get_run_history, get_scenario, list_scenarios,
    record_human_decision, release_next_event, start_scenario,
)
from app.policy.kb import search_policies


def policy_lookup(query, jurisdiction="UAE", limit=3):
    return search_policies(query, jurisdiction=jurisdiction, limit=limit, use_vector=False)


class IncidentSimulationTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.db = Path(self.temp.name) / "incidents.sqlite"

    def tearDown(self):
        self.temp.cleanup()

    def test_incident_connection_closes_after_context(self):
        with _connect(self.db) as connection:
            self.assertEqual(connection.execute("SELECT 1").fetchone()[0], 1)
        with self.assertRaises(sqlite3.ProgrammingError):
            connection.execute("SELECT 1")

    def test_two_scenarios_are_available(self):
        self.assertEqual({s["id"] for s in list_scenarios()},
                         {"integrity_false_positive", "assessment_error"})

    def test_sequential_release_and_no_future_leak(self):
        scenario = get_scenario("integrity_false_positive")
        run = start_scenario(scenario["id"], self.db)
        history = get_run_history(run, self.db)
        self.assertEqual(history["events"], [])
        self.assertEqual(history["released_count"], 0)

        first = release_next_event(run, self.db, policy_lookup)
        self.assertEqual(first["event"]["id"], "speed_flag")
        self.assertEqual(first["coordination"]["contributors"],
                         ["academic_integrity", "academic_quality"])
        history = get_run_history(run, self.db)
        self.assertEqual(len(history["events"]), 1)
        self.assertNotIn("student_appeal", str(history))

        for index in range(1, len(scenario["events"])):
            result = release_next_event(run, self.db, policy_lookup)
            self.assertEqual(result["event"]["id"], scenario["events"][index]["id"])
        history = get_run_history(run, self.db)
        self.assertEqual(history["released_count"], 4)
        self.assertEqual(len(history["coordination"]), 4)
        self.assertTrue(all(c["final_action"].startswith("Pending") for c in history["coordination"]))
        with self.assertRaises(ValueError):
            release_next_event(run, self.db, policy_lookup)

    def test_role_visibility_and_audit_citations(self):
        run = start_scenario("assessment_error", self.db)
        one = release_next_event(run, self.db, policy_lookup)
        self.assertEqual({a["role"] for a in one["assessments"]}, {"academic_quality"})
        two = release_next_event(run, self.db, policy_lookup)
        self.assertNotIn("privacy_officer", {a["role"] for a in two["assessments"]})
        three = release_next_event(run, self.db, policy_lookup)
        self.assertEqual({a["role"] for a in three["assessments"]}, {"privacy_officer"})
        self.assertEqual(three["assessments"][0]["observed_event_ids"], ["external_processing"])
        self.assertIn("UAE-PDPL-2021-ART2",
                      {c["id"] for c in three["assessments"][0]["citations"]})
        self.assertTrue({"UAE-PDPL-2021-ART22", "UAE-PDPL-2021-ART23"}.issubset(
            {c["id"] for c in three["assessments"][0]["citations"]}))
        for assessment in three["assessments"]:
            for citation in assessment["citations"]:
                self.assertTrue(citation["url"].startswith("https://"))
                self.assertIn("source_kind", citation)

    def test_model_cannot_skip_immediate_containment_of_invalid_question(self):
        first = get_scenario("assessment_error")["events"][0]
        response = {
            "recommendation": "Introduce stricter validation before future quizzes.",
            "public_rationale": "Human oversight helps assess unsupported output.",
            "policy_gap": "Verify whether question approval is documented.",
            "citation_ids": ["UNESCO-ETHICS-2021-P43"],
        }
        with patch("app.agents.policy_adviser.grounded_advice", return_value=response):
            assessment = _evaluate_role("academic_quality", [first], "UAE",
                                        policy_search=policy_lookup, use_llm=True)
        self.assertEqual(assessment["assessment_mode"], "source_grounded_llm")
        self.assertIn("Quarantine the unsupported question", assessment["recommendation"])
        self.assertIn("do not change grades automatically", assessment["recommendation"])

    def test_human_decision_is_explicit_append_only_and_requires_complete_run(self):
        run = start_scenario("integrity_false_positive", self.db)
        with self.assertRaisesRegex(ValueError, "Release all events"):
            record_human_decision(run, "Reviewer", "close_no_sanction", "No evidence", self.db)
        for _ in range(4):
            release_next_event(run, self.db, policy_lookup)
        with self.assertRaisesRegex(ValueError, "prohibited"):
            record_human_decision(run, "Reviewer", "auto_penalize_student", "Bad", self.db)
        with self.assertRaisesRegex(ValueError, "required"):
            record_human_decision(run, "Reviewer", "close_no_sanction", "", self.db)
        record_human_decision(run, "Academic chair (demo)", "close_no_sanction",
                              "No independent misconduct evidence was established", self.db)
        history = get_run_history(run, self.db)
        self.assertEqual(len(history["human_decisions"]), 1)
        self.assertEqual(history["human_decisions"][0]["action"], "close_no_sanction")
        self.assertFalse(history["human_decisions"][0]["identity_verified"])
        self.assertIn(HUMAN_ACTIONS["close_no_sanction"], history["human_decision"])
        record_human_decision(run, "Academic chair (demo)", "escalate_review",
                              "A separate legal review is needed", self.db)
        self.assertEqual(len(get_run_history(run, self.db)["human_decisions"]), 2)

    def test_audit_metadata_and_global_comparisons_are_separate(self):
        run = start_scenario("integrity_false_positive", self.db)
        result = release_next_event(run, self.db, policy_lookup)
        assessment = result["assessments"][0]
        self.assertIsInstance(assessment["latency_ms"], float)
        self.assertEqual(assessment["gap_evidence_status"], "unverified_in_available_corpus")
        self.assertTrue(assessment["policy_gap"].startswith("Verify whether"))
        self.assertEqual(assessment["assessment_mode"], "rules_fallback")
        self.assertTrue(result["coordination"]["global_examples"])
        self.assertTrue(all(
            item["applicability"] == "comparative_only_not_UAE_law"
            for item in result["coordination"]["global_examples"]
        ))


if __name__ == "__main__":
    unittest.main()
