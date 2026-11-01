"""Isolated unit tests for source-scoped generation and citation rejection."""

import importlib.util
import json
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


class FakeCompletion:
    def create(self, **kwargs):
        payload = {
            "question_text": "Which is correct?", "options": ["A", "B", "C", "D"],
            "correct_answer": "A", "explanation": "Source supports A.",
            "source_chunk_ids": ["lecture.pdf_p1_c0"],
        }
        return types.SimpleNamespace(choices=[types.SimpleNamespace(
            message=types.SimpleNamespace(content=json.dumps(payload)))])


class FakeGroq:
    def __init__(self, **kwargs):
        self.chat = types.SimpleNamespace(completions=FakeCompletion())


class GenerationTests(unittest.TestCase):
    def _load_isolated(self, name, filename, retriever):
        fake_groq = types.ModuleType("groq")
        fake_groq.Groq = FakeGroq
        fake_retriever = types.ModuleType("app.retrieval.retriever")
        fake_retriever.retrieve = retriever
        with patch.dict(sys.modules, {"groq": fake_groq, "app.retrieval.retriever": fake_retriever}):
            spec = importlib.util.spec_from_file_location(name, Path(__file__).resolve().parents[1] / filename)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        return module

    def test_generation_uses_only_selected_lecture(self):
        calls = []

        def retrieve(query, file_name=None):
            calls.append(file_name)
            return [{"chunk_id": "lecture.pdf_p1_c0", "text": "A is supported.", "metadata": {}}]

        generator = self._load_isolated("unit_generator", "app/agents/generator.py", retrieve)
        question = generator._generate_once("Concept", "medium", "lecture.pdf")
        self.assertEqual(calls, ["lecture.pdf"])
        self.assertEqual(question.source_chunk_ids, ["lecture.pdf_p1_c0"])

    def test_validator_rejects_unverifiable_chunk_id(self):
        def retrieve(query, file_name=None):
            return [{"chunk_id": "lecture.pdf_p1_c0", "text": "A is supported."}]

        validator = self._load_isolated("unit_validator", "app/agents/validator.py", retrieve)
        from app.models.schemas import Question
        question = Question(question_id="q1", concept="Concept", difficulty="medium",
                            question_text="Which?", options=["A", "B", "C", "D"],
                            correct_answer="A", explanation="A.",
                            source_chunk_ids=["invented_p99_c0"])
        valid, reason = validator.validate_question(question, "lecture.pdf")
        self.assertFalse(valid)
        self.assertIn("unverified", reason)


if __name__ == "__main__":
    unittest.main()
