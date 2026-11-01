# 🎓 Micro-Assessment AI Agent (CodeMentor AI)

An intelligent, proactive formative assessment system that transforms academic evaluation from stressful, spaced-out exams into continuous, adaptive, and interactive learning.

## 🚀 The Pitch
Instructors often discover students' lack of understanding only after midterms or finals. This system uses a **Multi-Agent AI Architecture** to analyze lecture content instantly, generate personalized micro-quizzes, adapt to student performance in real-time, and provide instructors with a live "Knowledge Gap Heatmap" before it's too late.

---

## 📚 Knowledge Base & Data Architecture
Our Knowledge Base aligns with ITU-T Y.3172 standards to ensure strict curriculum alignment, data privacy, and zero-hallucination assessment:
- **Raw Material Ingestion:** Instructors upload official lecture PDFs (`app.py`), establishing the core institutional context.
- **Chunking & Local Embeddings:** Text is segmented into context-aware chunks (`splitter.py`) and embedded locally using `Sentence-Transformers` (`embedder.py`). No PII or proprietary content is sent to external APIs during database creation.
- **Vector Database (ChromaDB):** High-performance vector storage (`ChromaDB`) enables precision semantic retrieval (`retriever.py`) that feeds verified context directly into the LLM.

---

## ✨ Key Features
- **📄 Dynamic RAG Generation:** Ingests lecture PDFs, extracts core concepts, and generates context-aware questions with source chunk attribution.
- **🧠 Adaptive Feedback Loop (LangGraph):** Provides tailored hints upon wrong answers and simplifies questions if students continue to struggle.
- **🚨 Integrity & Forensics Agent:** Analyzes response latency (< 3s thresholds) to detect suspicious patterns without auto-penalizing (Human-in-the-loop advisory).
- **📊 Instructor Analytics Dashboard:** Real-time visual Heatmap, timeline analytics, session tracking, and CSV reporting.
- **🔎 Auditability & Source Attribution:** Complete transparency with logged time traces, attempt counters, and source chunk IDs for every generated question.

---

## 🛠️ Tech Stack
- **Frontend/UI:** Streamlit (Instructor Dashboard & Student Portal)
- **Agent Orchestration:** LangGraph (State Machine for adaptive routing)
- **LLM Engine:** Groq API (`llama-3.3-70b-versatile`)
- **Embeddings:** Sentence-Transformers (`all-MiniLM-L6-v2`)
- **Vector Database:** ChromaDB (Local persistent store)
- **Relational Database:** SQLite (Auditable session & answer history)

---

## ⚙️ Quick Start Guide

### 1. Installation
```bash
git clone https://github.com/alzoubitoqa/micro-assessment-agent.git
cd micro-assessment-agent
```

### 2 · Create a virtual environment

**Windows PowerShell**

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

**macOS / Linux**

```bash
python3.12 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3 · Configure environment variables

Create a `.env` file in the project root:

```dotenv
GROQ_API_KEY=your_groq_api_key_here
LLM_MODEL=llama-3.3-70b-versatile
EMBEDDING_MODEL=all-MiniLM-L6-v2

CHUNK_SIZE=400
CHUNK_OVERLAP=60
TOP_K_RETRIEVAL=5
VALIDATE_QUESTIONS=true
```

Use a model available to your Groq account if the configured model changes.

> [!CAUTION]
> Never commit your real `GROQ_API_KEY`, `.env`, student records, or private lecture materials to GitHub.

### 4 · Start both interfaces

Open **two terminals**, activate the same virtual environment in each, and run:

**Terminal 1 — Instructor dashboard**

```bash
streamlit run dashboard/app.py
```

Default local URL: **http://localhost:8501**

**Terminal 2 — Student portal**

```bash
streamlit run dashboard/student_ui.py --server.port 8502
