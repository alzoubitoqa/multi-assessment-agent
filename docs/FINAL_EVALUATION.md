# ITQAN — evidence-based prototype evaluation (1 November 2026)

**Scope.** These results describe synthetic educational incidents in the instructor
dashboard. The five JSON exports below were supplied by the team after running the
app on Windows. This evaluation was prepared from those exports; the hosted Groq
model was **not** called again in the report-building environment. Do not confuse
functional demonstrations with a benchmark of answer quality or institutional
legal compliance.

## Observed four-event simulations

| Scenario / exported run ID | Assessment mode | Events revealed | Independent role assessments | Coordination records | Assessments with no citations | Human review entries |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| False integrity flag — `ce49aa908c86` | Rules fallback | 4/4 | 9 | 4 | 0 | 0 |
| False integrity flag — `6c5e6dacb80f` | Source-grounded LLM | 4/4 | 9 | 4 | 0 | 0 |
| Unsupported question — `10ee7375024e` | Rules fallback | 4/4 | 7 | 4 | 0 | 0 |
| Unsupported question — `79018d0789f8` | Rules fallback | 4/4 | 7 | 4 | 0 | **1** |
| Unsupported question — `415accfd6146` | Source-grounded LLM | 4/4 | 7 | 4 | 0 | 0 |

**What the observations establish:** both scenario types progressed through all
four staged events under rules and optional LLM assessments. Every exported role
assessment in these five runs contained at least one cited source identifier.
The records show role-specific evidence lists and an inter-agent coordination
record for every event; the user demonstrated a self-reported, documented human
review decision in the unsupported-question scenario. No score or student grade
was modified by the governance lab.

**What they do not establish:** that citations *semantically* support every
sentence, that any particular federal statute applies to the test institution,
that named reviewers hold official authority, or that policy gaps imply a missing
policy in the real world. Both scenarios and their decisions are synthetic.
The LLM-mode unsupported-question export had **no** human decision entry; its
human-review capability was demonstrated on the rules-mode export instead.

## Review findings and corrective work

1. **Immediate containment:** the LLM's original recommendation for an invalid
   question could concentrate on *future* validation and overlook an assessment
   item already shown to learners. The updated simulator supplies an advisory
   quarantine/evidence-preservation instruction when the LLM omits containment;
   it cannot automatically edit grades. An offline regression test verifies this.
2. **Cross-border legal sourcing:** the earlier privacy-agent output could
   describe UAE PDPL Article 4 as the rule for foreign data transfers. Article 4
   addresses circumstances for processing without consent; Articles **22–23**
   address transfers under different protection conditions. The knowledge base
   now includes labeled curated references to Articles 22 and 23, and the
   privacy adviser is directed to check them when a potentially external
   data flow is observed. **External provider != proven cross-border transfer.**
3. **Legal and institutional scope:** all recommendations remain conditional
   on checking the institution's status, actual data flow and sector-specific
   obligations. The catalog is a curated *seed*, not a complete UAE corpus.
4. **Citation reliability:** source IDs must exist in the retrieved evidence.
   Automated support/entailment checks for individual legal claims remain a
   limitation and require human review of primary law texts.
5. **Multi-agent coordination:** independent assessments are combined into a
   shared review record, followed by an explicit human decision opportunity.
   This is aggregation, not autonomous agent negotiation.

## Reproducibility and competition criteria

The updated repository passes **19/19 local unit tests** (1 November 2026),
including sequential release, role visibility, legal-provenance distinctions,
human-review append-only recording, invalid-LLM-citation rejection, immediate
containment, selected-lecture isolation, and Windows-safe SQLite cleanup.

| Evaluation criterion | Evidence | Limitation / proposed follow-up |
| --- | --- | --- |
| Knowledge-base quality | 18 provenance records with UAE and global comparison labels; optional official-PDF page indexing | Broader authoritative institutional/country texts and retrieval benchmarking |
| Agent capability | 4/4 events and 7 or 9 role assessments per run, both modes | Human expert scoring of correctness, hallucination and conflict resolution |
| Domain policy gaps / global examples | Unverified corpus gaps; UNESCO/OECD/EU examples labeled by status | Validate against actual institutional procedures; EU law is comparative only |
| Auditability / oversight | Cited event-level assessments, exported JSON, one demo-only recorded review | Authenticate reviewers; source-text entailment validation; secure audit retention |
| Y.3172 / ITU readiness | Documented pipeline analogy and governance/infrastructure mapping | Not a claim of Y.3172 certification or an ITU Lab deployment |

This file intentionally summarizes exported records instead of committing raw
run JSON containing the self-reported identity of a reviewer. The team can keep
its original exports as private demonstration evidence.
