import importlib.util
import sys
import types
import unittest
from pathlib import Path
from unittest.mock import patch


class FakeEmbedding:
    def tolist(self):
        return [[0.4, 0.6]]


class FakeModel:
    def encode(self, values):
        return FakeEmbedding()


class FakeCollection:
    last_params = None

    def count(self):
        return 1

    def query(self, **kwargs):
        self.last_params = kwargs
        return {"ids": [["lecture.pdf_p1_c0"]], "documents": [["Content"]],
                "metadatas": [[{"file_name": "lecture.pdf"}]], "distances": [[0.1]]}


class RetrievalScopeTests(unittest.TestCase):
    def test_retrieval_restricts_selected_lecture(self):
        module_stub = types.ModuleType("app.ingestion.embedder")
        module_stub.collection = FakeCollection()
        module_stub._model = FakeModel()
        filename = Path(__file__).resolve().parents[1] / "app" / "retrieval" / "retriever.py"
        with patch.dict(sys.modules, {"app.ingestion.embedder": module_stub}):
            spec = importlib.util.spec_from_file_location("isolated_retriever", filename)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            hits = module.retrieve("Transformers", file_name="lecture.pdf")
        self.assertEqual(hits[0]["chunk_id"], "lecture.pdf_p1_c0")
        self.assertEqual(module_stub.collection.last_params["where"], {"file_name": "lecture.pdf"})


if __name__ == "__main__":
    unittest.main()
