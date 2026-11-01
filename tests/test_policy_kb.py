import unittest

from app.policy.kb import load_catalog, search_global_examples, search_policies


class PolicyCatalogTests(unittest.TestCase):
    def test_catalog_provenance(self):
        docs = load_catalog()
        self.assertGreaterEqual(len(docs), 6)
        self.assertEqual(len({d["id"] for d in docs}), len(docs))
        self.assertTrue(all(d["url"].startswith("https://") for d in docs))
        self.assertTrue(all(d["source_kind"] in {"curated_summary", "catalog_metadata"} for d in docs))
        self.assertTrue(any(d.get("local_pdf") for d in docs))

    def test_search_finds_unesco_student_monitoring(self):
        hits = search_policies("student monitoring academic integrity fairness",
                               use_vector=False)
        self.assertIn("UNESCO-ETHICS-2021-P104", {h["id"] for h in hits})

    def test_national_and_global_records_are_distinguished(self):
        hits = search_policies("personal data privacy", jurisdiction="UAE", use_vector=False)
        self.assertTrue(all(h["jurisdiction"] in {"UAE", "GLOBAL"} for h in hits))
        self.assertTrue(any(h["binding_level"] == "binding_where_applicable" for h in hits))

    def test_privacy_rights_have_specific_original_article_references(self):
        ids = {source["id"] for source in load_catalog()}
        for article in ("ART2", "ART5", "ART13", "ART15", "ART18", "ART22", "ART23"):
            self.assertIn(f"UAE-PDPL-2021-{article}", ids)
        self.assertIn("cross-border", next(
            item["text"].lower() for item in load_catalog()
            if item["id"] == "UAE-PDPL-2021-ART22"))

    def test_eu_law_is_comparative_not_local_legal_evidence(self):
        local = search_policies("education AI monitoring tests assessment",
                                jurisdiction="UAE", use_vector=False, limit=20)
        self.assertNotIn("EU-AI-ACT-ANNEX3-EDUCATION", {hit["id"] for hit in local})
        global_examples = search_global_examples("education assessment")
        self.assertIn("EU-AI-ACT-ANNEX3-EDUCATION", {hit["id"] for hit in global_examples})
        self.assertTrue(all(hit["comparison_only"] for hit in global_examples))


if __name__ == "__main__":
    unittest.main()
