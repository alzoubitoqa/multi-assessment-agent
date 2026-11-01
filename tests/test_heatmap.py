import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from app.db import session_store


class HeatmapTests(unittest.TestCase):
    def test_final_mastery_is_distinct_from_attempts(self):
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(session_store, "DB_PATH", Path(temp) / "sessions.db"):
                session_store.init_db()
                question = SimpleNamespace(question_id="q1", concept="Transformers", difficulty="medium",
                                           question_text="Question?", correct_answer="A",
                                           source_chunk_ids=["lecture.pdf_p1_c0"])
                s1 = session_store.create_session("learner1", "lecture.pdf")
                session_store.log_answer(s1, question, "B", False, 9.0, attempt_number=1)
                session_store.log_answer(s1, question, "A", True, 11.0, attempt_number=2, is_final_attempt=True)
                s2 = session_store.create_session("learner2", "lecture.pdf")
                session_store.log_answer(s2, question, "B", False, 8.0, attempt_number=1, is_final_attempt=True)
                row = session_store.get_concept_heatmap("lecture.pdf")[0]
                self.assertEqual(row["total_attempts"], 3)
                self.assertEqual(row["question_sessions"], 2)
                self.assertEqual(row["failure_rate"], 0.5)
                self.assertEqual(row["first_try_success_rate"], 0.0)


if __name__ == "__main__":
    unittest.main()
