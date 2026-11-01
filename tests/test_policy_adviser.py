"""Offline contract checks for the optional policy LLM adapter."""

import json
import sys
import types
import unittest
from unittest.mock import patch

from app.agents import policy_adviser


class PolicyAdviserTests(unittest.TestCase):
    def _run_response(self, payload):
        response = types.SimpleNamespace(
            choices=[types.SimpleNamespace(message=types.SimpleNamespace(
                content=json.dumps(payload)))])
        fake = types.ModuleType("groq")
        fake.Groq = lambda **kwargs: types.SimpleNamespace(
            chat=types.SimpleNamespace(completions=types.SimpleNamespace(
                create=lambda **kwargs: response)))
        policies = [{"id": "UNESCO-ETHICS-2021-P43", "reference": "Paragraph 43",
                     "text": "Auditability and human oversight are encouraged.",
                     "binding_level": "non_binding_guidance",
                     "source_kind": "curated_summary"}]
        events = [{"id": "speed_flag", "detail": "Fast correct answer was flagged."}]
        with patch.object(policy_adviser, "GROQ_API_KEY", "test-key"), \
                patch.dict(sys.modules, {"groq": fake}):
            return policy_adviser.grounded_advice("academic_integrity", events, policies)

    def test_rejects_invented_citation(self):
        result = self._run_response({"recommendation": "Investigate fairly",
                                     "public_rationale": "Oversight is important",
                                     "policy_gap": "Verify whether an appeal policy exists",
                                     "citation_ids": ["INVENTED-SOURCE"]})
        self.assertIsNone(result)

    def test_rewrites_unverified_policy_absence_claim(self):
        result = self._run_response({"recommendation": "Review the alert",
                                     "public_rationale": "Human oversight is required",
                                     "policy_gap": "The institution lacks any such policy.",
                                     "citation_ids": ["UNESCO-ETHICS-2021-P43"]})
        self.assertIsNotNone(result)
        self.assertTrue(result["policy_gap"].startswith("Verify whether"))
        self.assertNotIn("lacks any", result["policy_gap"])


if __name__ == "__main__":
    unittest.main()
