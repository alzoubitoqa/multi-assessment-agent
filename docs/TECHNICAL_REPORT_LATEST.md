# ITQAN Micro Assessment AI Agent

**Submission report content — current revision, 1 November 2026**

**Team leader:** Toqa Mahmoud Tawfiq Al-zoubi  
**Members:** Afnan Bassem Mohammad Sami Sawalha; Natalia Samer Mohammad Abu Durei  
**Repository:** https://github.com/alzoubitoqa/micro-assessment-agent  
**Application domain:** Education

## 1 Introduction and innovation

ITQAN is a retrieval-augmented, adaptive formative-assessment prototype. An
instructor uploads lecture PDFs; a source-scoped retrieval and validation
workflow generates micro-quizzes and gives learners contextual hints or simpler
retries. The instructor dashboard presents concept mastery, answer history and
timing signals separately. In the ITU AI for Good UAE extension, ITQAN also
explores what happens if AI-generated educational content or automated
academic-integrity flags are wrong.

Its innovation is the practical link between *an operating educational AI
application* and a *policy-aware, auditable institutional incident exercise*.
The policy lab is a synthetic decision-support environment, not an actual
university disciplinary system or a certified legal-advice service.

## 2 Architecture and ITU alignment

Lecture PDFs are extracted and divided into page-aware chunks. Local
Sentence-Transformers embeddings and ChromaDB retrieval constrain the context
sent to a hosted Groq model for question generation and validation. A LangGraph
flow manages feedback, hints and simplified-question retries. Student answer
events are stored in SQLite, and Streamlit exposes separate learner and
instructor experiences. Source chunk identifiers are checked against retrieved
records; automated proof that every semantic claim is correct remains a
limitation.

The governance layer uses a **separate** policy collection rather than lecture
documents, then conducts two staged educational incidents. Three independent
role advisers are modeled: Academic Quality, Academic Integrity and Data
Protection. An orchestrator releases only the facts visible to each role at
each stage and aggregates recommendations into a coordination record. It
cannot impose sanctions, update grades or verify an institutional reviewer’s
real identity. The exercise supports either deterministic rules or optional
source-grounded Groq assessments.

**ITU-T Y.3172 mapping:** PDF/event input and evidence sourcing; extraction
and chunk preprocessing; local retrieval and model inference; model/decision
validation; educational interface and audit output. This is an **analogy** to
the Y.3172 machine-learning pipeline, which was defined for future networks,
not an assertion of sector-specific certification.

## 3 Policy knowledge base and governance

The shareable seed knowledge base contains **18 provenance-bearing catalog
records**, including UAE Federal Decree-Law 45/2021 on personal data, UAE AI
Strategy 2031, UNESCO guidance, OECD principles, the EU AI Act as a comparison,
and ITU material. Each item identifies its authority, original URL,
jurisdiction, reference, type and legal-strength label. Original official UAE
PDF page chunks can also be indexed, but summaries in the Git repository are
not a comprehensive national legal corpus.

Relevant UAE personal-data articles include 1 (definitions), 2 (applicability
and exceptions), 4 (processing without consent), 5 (processing principles),
13 (information rights), 15 (correction/erasure), 18 (automated-processing
issues), and **22–23 (different conditions for cross-border transfers)**.
An external model provider does not, by itself, establish that personal data
was sent or crossed a border. The institution's legal identity, data categories,
provider location, processing basis and exemptions must first be determined.
UNESCO, OECD and EU policy examples are comparators, not substitutes for
applicable UAE law.

**ITU AI Readiness:** the design addresses data provenance and openness,
domain-specific GenAI integration, a national policy context, cross-domain
privacy issues, human supervision, inclusion through formative feedback, and
infrastructure considerations. Accessibility/fairness evaluation, deployed
access controls, retention enforcement, system energy accounting and formal
national readiness assessment remain future work.

## 4 Progressive incidents and auditable review

**Scenario A — Fast Answer, False Misconduct Flag** releases four facts:
a correct answer submitted in 2.4 seconds triggers a weak heuristic; previous
legitimate quick work emerges; the student requests explanation and access;
and the instructor finds no independent misconduct evidence. Different
institutional advisers see different events. Appropriate recommendations are
to avoid automatic punishment, gather corroborating evidence, verify the
alert’s fairness and allow a documented human process.

**Scenario B — Hallucinated Question and Assessment Failure** begins with
an unsupported generated question following malformed PDF extraction;
continues with affected student attempts and heatmap data; discloses an
external LLM data flow; and ends with an institutional request for remedy.
The updated model advisory flow includes immediate question quarantine and
source-evidence preservation, followed by impact review, validation repairs,
conditional data-flow checks and human-approved remediation.

SQLite preserves event timestamps, role-scoped disclosures, public decision
rationales, citation identifiers and URLs, candidate corpus gaps, model and
latency metadata, coordination records, and append-only reviewer-entered
decisions. JSON is downloadable. Logs show a **reviewable decision trace**;
they do not expose a model’s hidden chain-of-thought or authenticate the
identity stated by a demo reviewer.

## 5 Evaluation, gap analysis and limitations

On 1 November 2026 the updated local build passed **19/19 unit tests**,
including lecture retrieval isolation, candidate-source validation,
sequential event disclosure, role visibility, policy source distinctions,
model citation-ID rejection, quarantine fallback, reviewer recording,
Windows SQLite handling and analytics.

Five user-exported, full-length four-event JSON traces demonstrate both
scenario types and both execution modes. The false-flag case produced **9/9
role assessments** in each mode; the unsupported-question case produced
**7/7 assessments** in each mode. Every role assessment contained citations
to retrieved source IDs. One **demo human review** was recorded in the
rules-mode unsupported-question run; the LLM-mode exported run had **no
reviewer entry**. The optional Groq endpoint was not rerun in the report
environment. These observations are not a claim of legal or semantic
correctness; see `docs/FINAL_EVALUATION.md` for trace-level evidence.

**Domain-specific policy gaps to validate:** institution-specific thresholds
for behavioural integrity flags and student appeals; documented protocols for
invalid AI assessment questions and correction of analytics; governance of
retention, human access and correction rights; review of hosted-model data
flows; precise inter-departmental mandates and authentic approval authority.
These are **unverified gaps in the available corpus**, not proof that any
real institution has no such policy. Comparative global approaches inform
options for human oversight, transparency, contestability and risk management.

**Limits and next steps:** existing policy indexing is a seed; cited IDs are
checked for existence but not semantic entailment. The coordinator synthesizes
independent views rather than performing negotiation. There is no production
authentication, deployed distributed ITU Lab knowledge base, legal
certification, accessibility audit or measured energy impact. Future work
requires expert review, official institutional source documents, quantitative
retrieval/fairness evaluation and authorized Lab ingestion.

### Primary sources

1. ITU-T Y.3172, https://www.itu.int/rec/T-REC-Y.3172/en
2. ITU AI Readiness Framework, https://www.itu.int/dms_pub/itu-t/opb/ai4g/T-AI4G-AI4GOOD-2025-6-PDF-E.pdf
3. UAE Federal Decree-Law 45/2021, https://www.uaelegislation.gov.ae/en/legislations/1972/download
4. UAE National AI Strategy 2031, https://ai.gov.ae/strategy
5. UNESCO Recommendation on the Ethics of AI, https://www.unesco.org/en/legal-affairs/recommendation-ethics-artificial-intelligence
6. OECD AI Principles, https://oecd.ai/en/dashboards/ai-principles/P7
7. EU AI Act (comparison only), https://eur-lex.europa.eu/eli/reg/2024/1689

*This is current report content, for insertion into the organizer's official
template and verification against the five-page maximum. The previously built
PDF in the repo may represent the preceding code revision; do not submit it
as evidence of the 19-test / 18-record release without regenerating it.*
