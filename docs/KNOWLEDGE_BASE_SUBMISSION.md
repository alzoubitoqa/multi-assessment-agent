# ITQAN | ITU AI for Good — Policy Knowledge Base Submission

This package is a **portable, auditable prototype knowledge base** supporting
the ITQAN education assessment incident simulation. It is not a certified legal
database, nor a hosted ITU AI for Good Lab collection.

## 1. What is included

| Item | File | Purpose |
| --- | --- | --- |
| Policy catalog | `data/policies/catalog.json` | 18 source-attributed policy entries with jurisdiction and applicability labels |
| Searchable text | `data/policies/exports/records.jsonl` | Curated summary records and extracted, page-aware chunks from included official PDFs |
| Source register | `data/policies/exports/provenance.csv` | Titles, authorities, source links, legal-status labels and PDF availability |
| Integrity manifest | `data/policies/exports/manifest.json` | Actual counts, PDF SHA-256 checksums, coverage limits and integration status |
| Original sources | `data/policies/sources/` | Available official PDF files, unmodified |
| Extraction code | `app/ingestion/{loader,splitter}.py` | Extract text per PDF page, then split into traceable chunks |
| Index/retrieval code | `app/policy/kb.py`, `app/ingestion/embedder.py` | Local semantic index and evidence retrieval |
| Entry points | `scripts/{fetch_policy_sources,ingest_policies,export_policy_kb}.py` | Official-download allowlist, local indexing and portable export |

The catalog has **16 independently labelled curated summary entries** and
**2 source-document metadata entries**. Curated summaries are *not* official
legal text. They link to original sources and must be independently checked.

Two cataloged official PDF sources are:

1. **UAE Federal Decree by Law No. 45 of 2021 Concerning the Protection of
   Personal Data**, originally linked at
   https://www.uaelegislation.gov.ae/en/legislations/1972/download.
2. **UAE National Strategy for Artificial Intelligence 2031**, originally
   linked at
   https://ai.gov.ae/wp-content/uploads/2021/07/UAE-National-Strategy-for-Artificial-Intelligence-2031.pdf.

An exported manifest identifies which PDFs were actually available at build
time; absent files are listed under `missing_official_pdfs`. Check official
source URLs for updated versions and redistribution permissions before reuse.

## 2. Coverage and legal guardrails

- Focus: **education**, formative assessments, false misconduct flags,
  incomplete source grounding, student data privacy, human review and audit.
- UAE source records are separated from global references (UNESCO, OECD and
  ITU). EU AI Act Annex III is labelled **comparative foreign law only**;
  its requirements must not be presented as UAE law.
- `binding_where_applicable` is a **conditional label**, not a legal finding.
  An institution must verify which UAE rules apply to its status, location,
  data-processing activities and relevant exceptions.
- The content is a **targeted starter corpus**, not comprehensive national
  legislation. Institution-specific assessment, misconduct, appeals, retention
  and technical policies have **not** been verified or fully ingested.
- Absence from this corpus is **not proof** a law, procedure or policy is absent.
- Source-grounded AI outputs carry **reviewable rationales and citations**, not
  hidden model chain-of-thought. Final decisions remain with a human reviewer.

## 3. Rebuild and use locally

From the **repository root**, with Python 3.10+ and a virtual environment:

```powershell
pip install -r requirements-kb.txt
python -B -m scripts.fetch_policy_sources --source all
python -B -m scripts.ingest_policies
```

The second command downloads only two allowlisted UAE government PDF URLs;
if either is unavailable, obtain the file from its official link and save it
under the catalog's `local_pdf` filename. No law is auto-downloaded during
ordinary app use. The third command vectorizes curated summaries and locally
available official PDF page chunks in the **local ChromaDB** collection
`official_policy_sources`. The embedding model defaults to `all-MiniLM-L6-v2`;
first use may download its weights. This step may need a few minutes and RAM.

To regenerate the submission package (offline when PDFs already exist):

```powershell
python -B -m scripts.export_policy_kb --output ../ITQAN_Policy_KB --zip ../ITQAN_ITU_Policy_Knowledge_Base.zip
```

In the ZIP, files keep their repository-relative paths. Extract its
`ITQAN_Policy_Knowledge_Base` directory, then follow the commands above inside
that directory. The export JSONL **does not contain pretrained embeddings**:
it is readable in any JSONL-capable tool and can be re-embedded on another
host. A vector store is local and is regenerated, not shipped with personal
or student data.

## 4. Data structure and audit trail

Each JSONL text record includes:

`record_id`, `policy_id`, `title`, `jurisdiction`, `reference`, `source_url`,
`source_kind`, `binding_level`, `comparison_only`, `page_number`, and `text`.

`curated_summary` records use IDs such as
`UAE-PDPL-2021-ART1-summary`; official chunks use a file, page and chunk
identifier. Provenance is kept with records so agents can cite the source;
retrieval ranking alone does **not** verify that a quoted claim is legally
correct or that the referenced law applies to a specific institution.

## 5. ITU AI for Good Lab integration: **NOT COMPLETED**

This export and the running app use **local ChromaDB**. No data have been
uploaded to the **distributed ITU AI for Good Lab knowledge base**, and no
ITU-specific API endpoint, credentials or distributed ingestion verification
have been supplied. Once access and an ITU ingestion contract are provided,
map the exported JSONL, authority labels, source IDs, jurisdiction fields and
PDF provenance to the official schema; then record ingestion receipt IDs and
verify retrieval from the Lab itself. Do not mark this step complete based on
a successful local vector-index run.

The extraction -> segmentation -> embedding -> storage -> retrieval steps
are a **conceptual mapping** to ITU-T Y.3172 ML pipeline capabilities; the
prototype does **not** claim formal conformance certification.
