"""Reproducibly build a five-page technical-report draft from verified prototype claims.

Usage: python -m scripts.build_itu_report
The generated PDF is a draft; verify any new results before formal submission.
"""

from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.units import inch
from reportlab.platypus import (
    HRFlowable, KeepTogether, PageBreak, Paragraph, SimpleDocTemplate,
    Spacer, Table, TableStyle,
)

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "Itqan_ITU_Submission_Draft.pdf"
FONT_DIR = Path("/usr/share/fonts/truetype/dejavu")
if (FONT_DIR / "DejaVuSans.ttf").is_file() and (FONT_DIR / "DejaVuSans-Bold.ttf").is_file():
    pdfmetrics.registerFont(TTFont("DejaVu", str(FONT_DIR / "DejaVuSans.ttf")))
    pdfmetrics.registerFont(TTFont("DejaVu-Bold", str(FONT_DIR / "DejaVuSans-Bold.ttf")))
    NORMAL_FONT, BOLD_FONT = "DejaVu", "DejaVu-Bold"
else:
    # Report generation also works on Windows without system DejaVu fonts.
    NORMAL_FONT, BOLD_FONT = "Helvetica", "Helvetica-Bold"
PURPLE = colors.HexColor("#4239A4")
INK = colors.HexColor("#19233A")
MUTED = colors.HexColor("#536176")
PALE = colors.HexColor("#F3F1FC")

TITLE = ParagraphStyle("title", fontName=BOLD_FONT, fontSize=17, leading=23,
                       textColor=PURPLE, alignment=TA_CENTER, spaceAfter=9)
SUBTITLE = ParagraphStyle("sub", fontName=NORMAL_FONT, fontSize=10, leading=14,
                          alignment=TA_CENTER, textColor=MUTED, spaceAfter=11)
H1 = ParagraphStyle("h1", fontName=BOLD_FONT, fontSize=12.1, leading=16,
                    textColor=PURPLE, spaceBefore=11, spaceAfter=6)
H2 = ParagraphStyle("h2", fontName=BOLD_FONT, fontSize=10.2, leading=14,
                    textColor=INK, spaceBefore=8, spaceAfter=4)
BODY = ParagraphStyle("body", fontName=NORMAL_FONT, fontSize=8.7, leading=12.3,
                      textColor=INK, spaceAfter=5)
SMALL = ParagraphStyle("small", parent=BODY, fontSize=7.7, leading=10.6, spaceAfter=2)
TABLE_HEAD = ParagraphStyle("thead", parent=SMALL, fontName=BOLD_FONT, textColor=colors.white)
TABLE_CELL = ParagraphStyle("tcell", parent=SMALL)


def p(text, style=BODY):
    return Paragraph(text, style)


def bullet(text):
    return p("&#8226; " + text)


def table(columns, rows, widths):
    data = [[p(str(item), TABLE_HEAD) for item in columns]]
    data += [[p(str(item), TABLE_CELL) for item in row] for row in rows]
    result = Table(data, colWidths=widths, repeatRows=1, hAlign="LEFT")
    result.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), PURPLE),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, PALE]),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("GRID", (0, 0), (-1, -1), .35, colors.HexColor("#D9DCE9")),
        ("LEFTPADDING", (0, 0), (-1, -1), 7),
        ("RIGHTPADDING", (0, 0), (-1, -1), 7),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    return result


def page_decoration(canvas, doc):
    canvas.saveState()
    width, height = letter
    canvas.setFillColor(PURPLE)
    canvas.rect(0, height - 9, width, 9, fill=1, stroke=0)
    canvas.setStrokeColor(colors.HexColor("#DDDBE8"))
    canvas.line(42, 37, width - 42, 37)
    canvas.setFont(NORMAL_FONT, 7.3)
    canvas.setFillColor(MUTED)
    canvas.drawString(42, 24, "Team ITQAN  |  AI for Good Lab UAE  |  Research prototype")
    canvas.drawRightString(width - 42, 24, f"Page {doc.page} of 5")
    canvas.restoreState()


def build():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(str(OUTPUT), pagesize=letter, rightMargin=42,
                            leftMargin=42, topMargin=39, bottomMargin=49)
    flow = []

    # Page 1 — use case and implemented innovation
    flow += [Spacer(1, 12), p("ITQAN - MICRO-ASSESSMENT AI AGENT", TITLE),
             p("Policy-aware formative assessment and staged educational incident simulation", SUBTITLE),
             HRFlowable(width="100%", color=PURPLE, thickness=1), Spacer(1, 9),
             p("<b>Team leader:</b> Toqa Mahmoud Tawfiq Al-zoubi", BODY),
             p("<b>Team members:</b> Afnan Bassem Mohammad Sami Sawalha; Natalia Samer Mohammad Abu Durei", BODY),
             p("<b>GitHub:</b> github.com/alzoubitoqa/micro-assessment-agent  |  <b>Domain:</b> Education", BODY),
             p("1. Introduction and problem", H1),
             p("Traditional high-stakes examinations can reveal comprehension gaps too late for effective intervention. "
               "ITQAN transforms uploaded lecture PDFs into source-grounded micro-assessments, provides "
               "contextual hints and simpler retries, and shows instructors topic-level performance signals. "
               "In the ITU UAE extension, the same system becomes a laboratory for investigating "
               "AI-generated assessment errors, privacy questions and academic integrity false positives."),
             p("2. Solution and distinctive contribution", H1),
             bullet("<b>Assessment:</b> local PDF text extraction, semantic retrieval, Groq LLM question generation and source-chunk validation."),
             bullet("<b>Adaptation:</b> LangGraph state transitions route wrong answers to hints and validated simplified questions."),
             bullet("<b>Instructional analytics:</b> SQLite records attempts, feedback and response times; dashboards show final mastery separately from first-attempt performance."),
             bullet("<b>Governance:</b> a UAE/global policy catalog, three institutional roles, staged incident events and transparent human-review recommendations."),
             p("The tool supports Sustainable Development Goal 4 by enabling early feedback while highlighting "
               "how human oversight, fair treatment, accountability and privacy matter in education."),
             p("Status: working prototype and reproducible offline simulation; not a certified or production-grade institutional system.", SMALL),
             p("Prototype evidence available for review", H1),
             table(["Artifact", "Independent verification possible"], [
                 ("Source code", "Reproducible local project branch and submission ZIP with separated lecture RAG, policy retrieval and governance modules; GitHub publication to be confirmed."),
                 ("Functional tests", "19 automated regression checks for staged events, source provenance, human review, citations, immediate error containment, Windows SQLite cleanup and analytics."),
                 ("Runnable exercise", "Two fictional four-event scenarios, with role-specific evidence, comparative sources, human-review form and downloadable JSON audit."),
             ], [143, 385]),
             PageBreak()]

    # Page 2 — technical pipeline and Y.3172 analogy
    flow += [p("3. Technical architecture and AI pipeline", H1),
             table(["Layer", "Implemented pipeline / implementation"], [
                 ("SRC / ingestion", "Instructor lecture PDF, student answer events; <b>pypdf</b> extraction and page-aware chunks."),
                 ("Preprocessing", "Recursive split (default 400 characters, 60 overlap), local Sentence-Transformers embeddings."),
                 ("Model / retrieval", "ChromaDB lecture collection; top-k scoped by selected lecture; Groq Llama 3.3 70B question generation."),
                 ("Policies / validation", "Source ID verification, semantic Validator Agent, revisited validation after simplification, policy evidence in separate collection."),
                 ("Orchestration", "LangGraph question/hint/simplify workflow; independent incident-role assessments and explicit coordination protocol."),
                 ("SINK / audit", "Streamlit student and instructor portals; SQLite attempt and incident records; downloadable JSON decision traces."),
             ], [113, 415]),
             p("This is a <b>conceptual pipeline mapping</b> to ITU-T Y.3172 components. "
               "The recommendation formally concerns machine learning in future telecommunications networks; "
               "this educational prototype does not claim Y.3172 certification or network implementation."),
             p("4. Multi-agent responsibilities", H1),
             table(["Agent or role", "Specific mandate and interaction"], [
                 ("Generator / Validator", "Generate source-grounded questions; reject unsupported answers or unverified source IDs."),
                 ("Adaptive Tutor", "Deliver contextual hints, then a simpler question when necessary."),
                 ("Integrity Officer", "Treat fast responses as weak advisory indicators, not proof of misconduct."),
                 ("Data Protection Officer", "Inspect data flow, processing basis, access and retention questions."),
                 ("Academic Quality Reviewer", "Assess question validity, learner impact and correction of faulty records."),
                 ("Coordinator", "Synthesize independent role assessments and review questions; no automated sanction or grade change."),
             ], [150, 378]),
             p("Institutional agents see only events addressed to their roles. The optional policy LLM is constrained "
               "to retrieved source IDs, while a deterministic fallback enables offline reproduction.", SMALL),
             PageBreak()]

    # Page 3 — policies and readiness
    flow += [p("5. Country-specific knowledge base and policy mapping", H1),
             p("The shareable seed catalog contains 18 provenance records: UAE legal and strategy references, "
               "UNESCO, OECD, EU-comparator and ITU guidance. Its initial text consists of labelled summaries and source "
               "metadata; official UAE PDF page indexing is supported after local download. These summaries "
               "must <b>not</b> be misrepresented as the complete national policy corpus."),
             table(["Source", "Relevant issue / legal status"], [
                 ("UAE Personal Data Decree-Law 45/2021", "Arts 1/2/4: definitions, scope, consent exceptions. Arts 5/13/15/18: retention, rights, automated processing. Arts 22/23: conditional cross-border transfers. Confirm actual data transfer and legal applicability."),
                 ("UAE National AI Strategy 2031", "AI integration, governance and infrastructure priorities. National strategy; not a statutory compliance certificate."),
                 ("UNESCO, OECD and EU comparison", "UNESCO paras 43/53/104, OECD transparency principle, EU AI Act Annex III education example. EU law is a foreign comparator, NOT an automatic UAE obligation."),
                 ("ITU AI Readiness", "Data governance, AI policy, infrastructure and innovation metrics. Assessment framework, not binding legislation."),
             ], [205, 323]),
             p("Each catalog item retains an official URL, authority, jurisdiction, type, citation reference "
               "and a binding-level label. Policies are stored separately from course lectures to avoid accidental "
               "cross-domain retrieval. A vector index can include original PDF page chunks."),
             p("6. ITU AI Readiness perspective", H1),
             table(["Readiness dimension", "Implemented evidence / limitation"], [
                 ("Data and governance", "Local embeddings, scoped retrieval, policy provenance; student retention and access controls remain incomplete."),
                 ("GenAI and integration", "RAG question generation, validation, optional policy assistant and multi-role simulation."),
                 ("Human oversight and inclusion", "No automatic punishment; human decision pending; learner accessibility and fairness studies required."),
                 ("Infrastructure and sustainability", "Local embedding and hosted inference; latency, energy and deployment cost require measurement."),
             ], [165, 363]),
             PageBreak()]

    # Page 4 — scenarios and audit
    flow += [p("7. Interactive progressive error scenarios", H1),
             p("Scenario A - <b>False Academic Misconduct Flag</b>", H2),
             table(["Stage", "New information / expected institutional response"], [
                 ("Event 1", "Correct first-attempt answer in 2.4 seconds triggers a heuristic flag. Integrity and quality reviewers advise against automatic accusations."),
                 ("Event 2", "Prior legitimate fast responses are disclosed to two roles. They reassess the false-positive risk."),
                 ("Event 3", "Student seeks explanation and correction of stored behavioural data. Privacy officer receives the event and inspects data-handling obligations."),
                 ("Event 4", "Instructor finds no corroborating evidence. All roles contribute to a documented, human-reviewed resolution."),
             ], [75, 453]),
             p("Scenario B - <b>Hallucinated Question and Assessment Failure</b>", H2),
             table(["Stage", "New information / expected institutional response"], [
                 ("Event 1", "Malformed PDF causes an unsupported generated answer. Academic Quality Reviewer recommends blocking the question."),
                 ("Event 2", "Affected student attempts appear. Quality and Integrity Officers recommend correction without penalizing students."),
                 ("Event 3", "External LLM processing of retrieved lecture text is revealed to the Data Protection Officer."),
                 ("Event 4", "Academic committee requests traceability, corrected analytics and revised validation controls."),
             ], [75, 453]),
             p("8. Transparent decision traces", H1),
             p("A SQLite audit stores run/event timestamps, role-scoped facts, citations and source URLs, public "
               "rationales, candidate corpus gaps, model/latency metadata and inter-agent synthesis. After all "
               "stages, a reviewer may append a named, reasoned decision (identity is not authenticated). JSON "
               "export reveals decisions without disclosing private model chain-of-thought or auto-sanctioning."),
             p("The original incident sequence is intentionally hidden from roles until each event is released. "
               "This allows reproducible tests of incremental information, uneven institutional knowledge, "
               "and reviewable coordination.", SMALL),
             p("Scenario A - information distribution", H2),
             table(["Institutional role", "Events received as the simulation unfolds"], [
                 ("Academic Integrity Officer", "Events 1, 2, 3 and 4"),
                 ("Academic Quality Reviewer", "Events 1, 2 and 4; does not initially receive the student's data-access inquiry."),
                 ("Data Protection Officer", "Events 3 and 4; receives no initial cheating allegation before disclosure."),
             ], [186, 342]),
             p("Every log entry includes evidence identifiers and an explicit rule or public rationale. "
               "Incomplete policy coverage is identified as an uncertainty requiring human verification.", SMALL),
             PageBreak()]

    # Page 5 — evaluation, gaps, references
    flow += [p("9. Evaluation and reproducibility", H1),
             p("Static code review and the pure-Python regression suite were run on 1 November 2026. "
               "<b>19 of 19 tests passed</b>: provenance, foreign-comparator separation, safe policy-gap wording, "
               "rejection of invented citations, event order, role visibility, human decision recording, "
               "invalid-question containment, scoped retrieval, Windows SQLite cleanup and analytics."),
             p("These are functional checks, <b>not</b> a measured question-quality benchmark or evidence "
               "of real-world legal compliance. Five user-exported four-event JSON runs cover both scenarios "
               "and both modes: rules-mode 9/9 and 7/7 role assessments; LLM-mode 9/9 and 7/7; "
               "all assessments had citations. One demo human review was recorded in rules mode. "
               "LLM-mode exports had no human decision; the API was not re-run in this build environment."),
             p("10. Policy, strategy and standards gaps", H1),
             bullet("<b>Academic integrity governance:</b> the current catalog does not establish an institution-specific rule on response-time surveillance, escalation or appeals. This is a corpus gap, not proof that no such rule exists."),
             bullet("<b>Assessment fairness:</b> a source-grounded Validator does not automatically demonstrate cultural, linguistic or disability fairness; independent audits are necessary."),
             bullet("<b>Data processing:</b> hosted LLM calls can include retrieved lecture excerpts; check actual personal-data and cross-border flows against applicable Arts 22/23, not Article 4 alone."),
             bullet("<b>Institutional coordination:</b> formal mandates, access rights and incident response playbooks require validation with real organizations."),
             p("11. Limitations and next steps", H1),
             p("The prototype has no production authentication, retention enforcement, deployed distributed ITU "
               "Lab knowledge base or measured energy impact. Next steps: integrate official full-text documents, "
               "benchmark policy retrieval/citation quality, secure institutional access, perform accessibility "
               "tests and connect to the ITU Lab infrastructure when authorized."),
             p("Primary sources", H1),
             p("[1] ITU AI for Good Lab UAE Hackathon: aiforgood.itu.int/event/ai-for-good-sandbox-hackathon-united-arab-emirates/", SMALL),
             p("[2] ITU-T Y.3172 (2019): itu.int/rec/T-REC-Y.3172/en", SMALL),
             p("[3] ITU AI Ready Framework: itu.int/epublications/publication/ai-ready-analysis-towards-a-standardized-readiness-framework", SMALL),
             p("[4] UAE Federal Decree-Law 45/2021: uaelegislation.gov.ae/en/legislations/1972/download", SMALL),
             p("[5] UAE National AI Strategy 2031: ai.gov.ae/strategy", SMALL),
             p("[6] UNESCO Recommendation on the Ethics of AI (2021): unesco.org/en/legal-affairs/recommendation-ethics-artificial-intelligence", SMALL),
             p("[7] OECD AI Principles (Transparency): oecd.ai/en/dashboards/ai-principles/P7", SMALL),
             p("[8] EU AI Act (comparative only): eur-lex.europa.eu/eli/reg/2024/1689", SMALL)]

    doc.build(flow, onFirstPage=page_decoration, onLaterPages=page_decoration)
    print(OUTPUT)


if __name__ == "__main__":
    build()
