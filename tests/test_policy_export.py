"""Check that the submit-ready policy KB preserves citations and source boundaries."""

import csv
import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path

from app.policy.kb import CATALOG_PATH, load_catalog
from scripts.export_policy_kb import export_knowledge_base


class PolicyExportTests(unittest.TestCase):
    def test_metadata_only_export_preserves_comparative_policy_labels(self):
        with tempfile.TemporaryDirectory() as workspace:
            output = Path(workspace) / "portable_kb"
            manifest = export_knowledge_base(output, include_pdfs=False)
            rows = [json.loads(line) for line in
                    (output / "data/policies/exports/records.jsonl").read_text(
                        encoding="utf-8").splitlines()]
            self.assertEqual(manifest["catalog_records"], len(load_catalog()))
            self.assertEqual(manifest["indexable_text_records"], len(rows))
            self.assertEqual(manifest["official_pdf_text_records"], 0)
            self.assertEqual(len(rows), 16)
            self.assertEqual(len({row["record_id"] for row in rows}), len(rows))
            self.assertTrue(all(row["source_kind"] == "curated_summary" for row in rows))
            with (output / "data/policies/exports/provenance.csv").open(
                    encoding="utf-8", newline="") as handle:
                provenance = list(csv.DictReader(handle))
            self.assertEqual(len(provenance), len(load_catalog()))
            comparative = next(row for row in rows
                               if row["policy_id"] == "EU-AI-ACT-ANNEX3-EDUCATION")
            self.assertTrue(comparative["comparison_only"])
            self.assertEqual(comparative["binding_level"], "comparative_foreign_law")
            self.assertFalse(manifest["itu_distributed_kb_uploaded"])

    def test_pdf_export_tracks_pages_checksums_and_zip_integrity(self):
        with tempfile.TemporaryDirectory() as workspace:
            output = Path(workspace) / "portable_kb"
            archive = Path(workspace) / "policy_kb.zip"
            manifest = export_knowledge_base(output, archive=archive)
            ids = set()
            with (output / "data/policies/exports/records.jsonl").open(
                    encoding="utf-8") as handle:
                for line in handle:
                    record = json.loads(line)
                    self.assertNotIn(record["record_id"], ids)
                    ids.add(record["record_id"])
            self.assertEqual(len(ids), manifest["indexable_text_records"])
            for info in manifest["official_sources_included"]:
                source = CATALOG_PATH.parent / "sources" / info["filename"]
                copied = output / "data/policies/sources" / info["filename"]
                self.assertEqual(copied.read_bytes(), source.read_bytes())
                self.assertEqual(hashlib.sha256(copied.read_bytes()).hexdigest(), info["sha256"])
                self.assertGreater(info["text_chunks"], 0)
            with zipfile.ZipFile(archive) as z:
                self.assertIsNone(z.testzip())
                self.assertIn("ITQAN_Policy_Knowledge_Base/README_KNOWLEDGE_BASE.md",
                              z.namelist())
                self.assertIn("ITQAN_Policy_Knowledge_Base/data/policies/catalog.json",
                              z.namelist())


if __name__ == "__main__":
    unittest.main()
