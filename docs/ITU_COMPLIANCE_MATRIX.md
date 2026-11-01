# ITU AI for Good UAE — implementation and evidence matrix

This document describes the **implemented research prototype**, not formal legal compliance,
certification or approval by ITU. All incident data in the demo is fictional.

| Hackathon requirement | Implementation | Evidence / current limit |
| --- | --- | --- |
| Innovative education application | Lecture-PDF RAG, generation, hints and instructor analytics | `app/agents`, `app/graph`, `dashboard/` |
| Country-specific policy KB | 18 seed records; UAE PDPL Arts 1, 2, 4, 5, 13, 15, 18, 22 and 23; AI Strategy; optional official-PDF page indexing | `data/policies/catalog.json`, `app/policy/kb.py`. Curated summaries ship in git; official source text can be indexed separately. This is a seed corpus, not national coverage. Arts 22/23 inform conditional cross-border-transfer checks; using an external API alone proves neither personal-data exposure nor a cross-border transfer |
| Relevant global policy examples | UNESCO ethics paragraphs 43, 53, 104; OECD Principle 1.3; EU AI Act Annex III education comparator | Separate `search_global_examples()` output and explicit comparative-only lab panel. EU law is **not** presumed applicable in UAE |
| Policy/legal adviser | Role-specific advice, optional Groq-generated grounded assessment, verified citation IDs | `app/agents/policy_adviser.py`; output is advisory, with mandatory human review |
| Institutional multi-agent roles | Academic Integrity, Data Protection, Academic Quality | `app/governance/simulator.py`; each event has `visible_to` and independent, role-scoped histories |
| Progressive error scenarios | 4 staged events per scenario, hidden until release | `data/scenarios/*.json`, `release_next_event()` |
| Inter-agent coordination | Independent assessments aggregated, review checks and global comparators surfaced before human review | `incident_coordination` records in SQLite. This is transparent synthesis, **not** multi-turn negotiation |
| Auditable decisions | Event log, role-specific facts, rationale, citations, candidate corpus gap notices, inference timestamp/latency/model, self-reported human decision entries, JSON export | SQLite `incident_*` and `agent_assessments` tables. No private LLM chain-of-thought is stored; reviewer identity remains unverified |
| Y.3172 ML pipeline | Teaching PDFs → text prep → local embeddings / retrieval → generation / validation → interfaces | Analogical pipeline mapping only; Y.3172 formally addresses ML in telecom networks, **not** educational certification |
| ITU AI Readiness | Data governance, digital infrastructure, human oversight, inclusion, national strategy | See below; not a full country readiness assessment |
| ITU distributed Lab KB | Exportable source metadata, local Chroma policy collection | Integration into ITU Lab requires sandbox access and the organizer's reference schema; not yet verified |

## Readiness mapping

- **Data governance:** local lecture embeddings, explicit source metadata, source-scoped retrieval, policy provenance.
- **AI integration and GenAI:** Groq question generation, grounded validation, optional policy LLM.
- **Human supervision:** integrity flags, incident recommendations and policy applicability stay advisory; optional human-review records contain a reviewer-entered rationale but are not identity-authenticated.
- **Inclusivity:** educational hints; accessibility and disparate-impact testing remain required.
- **Digital infrastructure and energy:** hosted Groq inference plus local embedding; latency, cost and carbon measurements are not yet available.
- **Policy innovation:** contrasts UAE national documents with UNESCO/OECD guidance and an EU regulatory comparator; candidate policy gaps are explicitly unverified until local institutional documents are checked.

## Scenarios and expected response

1. **Fast-answer false positive:** flag → legitimate performance context → student appeal/privacy → institutional decision. Expected: no automatic accusation, human review, traceable evidence.
2. **Invalid generated question:** malformed source → student grading impact → external model data flow → quality committee review. Expected: stop faulty question, correct analytics, review data handling, retain audit references.

The simulator does not see future events and does not determine whether a law applies
automatically. Policy source summaries are **curated paraphrases**; use page-level official
PDF evidence before treating a conclusion as legally supported. The application lacks
production login, access control, data retention enforcement and full adversarial testing.
The policy LLM validates cited IDs against retrieved IDs, **not** legal entailment or
correct statutory interpretation. Current outputs are decision support, not legal advice.
The coordinator lists independent roles' questions but does not perform active negotiations.

The user-supplied, four-event JSON runs provide additional empirical evidence for both
deterministic and optional-LLM modes; see [final evaluation](FINAL_EVALUATION.md).

## Reproduction

```bash
python -B -m unittest discover -s tests -v
python -m scripts.demo_incident --scenario integrity_false_positive
python -m scripts.fetch_policy_sources --source all
python -m scripts.ingest_policies
streamlit run dashboard/app.py
```

**Sources:**

- ITU hackathon: https://aiforgood.itu.int/event/ai-for-good-sandbox-hackathon-united-arab-emirates/
- UAE personal data law: https://www.uaelegislation.gov.ae/en/legislations/1972/download
- UAE AI Strategy 2031: https://ai.gov.ae/wp-content/uploads/2021/07/UAE-National-Strategy-for-Artificial-Intelligence-2031.pdf
- UNESCO Ethics of AI: https://www.unesco.org/en/legal-affairs/recommendation-ethics-artificial-intelligence
- OECD transparency: https://oecd.ai/en/dashboards/ai-principles/P7
- EU AI Act: https://eur-lex.europa.eu/eli/reg/2024/1689
- ITU-T Y.3172: https://www.itu.int/rec/T-REC-Y.3172/en
- ITU Readiness: https://www.itu.int/epublications/publication/ai-ready-analysis-towards-a-standardized-readiness-framework
