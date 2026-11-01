# ITQAN - Windows update and final demo guide

This is a **research prototype**, not a university production deployment or
an automated legal-compliance decision system.

## 1. Update safely

1. Stop both Streamlit terminals by pressing **Ctrl+C**.
2. Keep a backup copy of the previous `micro-assessment-agent` folder. Unzip
   the new release into **another folder** before deciding whether to replace it.
3. If you need previous local student statistics or uploaded lectures, carefully
   copy `data/sessions.db` and your own PDFs from `data/lectures/` into the new
   project while all apps are **stopped**. Do not overwrite an existing database.
4. Copy your private `.env` locally, if you had one. The ZIP intentionally does
   **not** include API credentials. Never upload `.env` to GitHub or chat.
5. Re-create the virtual environment; do not copy `.venv` between locations.

## 2. Install and verify in PowerShell

Open PowerShell in the **new extracted project directory** and run:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python -B -m unittest discover -s tests -v
```

Expected result: **19 tests passed** in the updated release from 1 November 2026.
If activation is restricted by PowerShell, use
`.\.venv\Scripts\python.exe` instead of `python` in subsequent commands.

**Windows SQLite fix:** If an older copy failed tests with `PermissionError:
[WinError 32]` when deleting `sessions.db` or `incidents.sqlite` from a temporary
folder, replace the old code with this release. SQLite context managers now
explicitly close file handles before temporary files are deleted. Stop any old
Streamlit terminals before rerunning the tests.

## 3. Optional Groq policy AI

Inside a local `.env` file (not committed to Git), configure:

```dotenv
GROQ_API_KEY=replace_with_your_private_api_key
LLM_MODEL=llama-3.3-70b-versatile
```

The app still works without an API key using deterministic `rules_fallback`.
Enabling AI sends retrieved policy text to the chosen hosted model; see the
project README for privacy considerations.

## 4. Open instructor and student apps in two terminals

Instructor:

```powershell
streamlit run dashboard/app.py --server.port 8501
```

Student (second activated PowerShell):

```powershell
streamlit run dashboard/student_ui.py --server.port 8502
```

- Instructor: http://localhost:8501
- Student: http://localhost:8502

## 5. Demonstrate the ITU Policy and Incident Lab

1. Open the instructor **Policy & Incident Lab** tab.
2. Open **Policy Knowledge Base** and optionally **Build / refresh policy
   vector index**; if a source PDF is available it will be indexed as page
   chunks. Lexical fallback works without this step.
3. Choose **Fast Answer, False Misconduct Flag** and click **Start new
   simulation**.
4. Keep AI **off** for a reproducible baseline; release each of the 4 events,
   inspect each role and download the JSON trace.
5. Start another new simulation; turn AI **on** if a valid Groq API key exists;
   again release all 4 events and compare recommendations.
6. Complete **Record human review (demo only)** after the 4th event. This logs
   a self-reported decision and rationale; reviewer authority is **not** checked.
7. Download the updated trace. It now includes `human_decisions`, model / latency
   metadata when available, source IDs, and comparative policy examples.
8. Repeat with **Hallucinated Question and Assessment Failure**. Selecting a
   different scenario clears the active run display; it does not delete its
   SQLite history. Download a desired trace **before** switching.

## 6. Verify the off-line simulation without Streamlit

```powershell
python -m scripts.demo_incident --scenario assessment_error --record-demo-review
```

## Important boundaries

- The curated policy catalog is **not** a complete national legal corpus.
- UAE law applicability must be determined from institution status and relevant
  exceptions; it is not presumed by the demo.
- EU AI Act and OECD examples are for international comparison only.
- Source IDs are checked, but legal accuracy / citation entailment still need
  qualified human verification.
- The coordination log synthesizes independent role assessments and questions;
  it does not represent a live multi-agent negotiation.
- The dashboard has no production-grade access control or identity verification.
