import sqlite3
import json
import uuid
import re
from contextlib import contextmanager
from datetime import datetime
from config import DB_PATH


@contextmanager
def _conn():
    """Commit/rollback and always release SQLite's file handle (Windows-safe)."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        with conn:
            yield conn
    finally:
        conn.close()


def init_db():
    with _conn() as conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS sessions (
            session_id TEXT PRIMARY KEY,
            student_id TEXT NOT NULL,
            lecture_file TEXT NOT NULL,
            started_at TEXT NOT NULL,
            ended_at TEXT,
            total_questions INTEGER DEFAULT 0,
            correct_count INTEGER DEFAULT 0
        );

        CREATE TABLE IF NOT EXISTS answers (
            answer_id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT NOT NULL,
            question_id TEXT NOT NULL,
            concept TEXT NOT NULL,
            difficulty TEXT NOT NULL,
            question_text TEXT NOT NULL,
            student_answer TEXT,
            correct_answer TEXT NOT NULL,
            is_correct INTEGER NOT NULL,
            hint_used INTEGER DEFAULT 0,
            hint_text TEXT,
            time_spent_seconds REAL NOT NULL,
            source_chunk_ids TEXT NOT NULL,
            timestamp TEXT NOT NULL,
            attempt_number INTEGER DEFAULT 1,
            FOREIGN KEY (session_id) REFERENCES sessions(session_id)
        );

        CREATE INDEX IF NOT EXISTS idx_answers_session ON answers(session_id);
        CREATE INDEX IF NOT EXISTS idx_answers_concept ON answers(concept);
        """)
        try:
            conn.execute("ALTER TABLE answers ADD COLUMN attempt_number INTEGER DEFAULT 1")
        except sqlite3.OperationalError:
            pass


def create_session(student_id: str, lecture_file: str) -> str:
    session_id = str(uuid.uuid4())[:8]
    now = datetime.now().isoformat()
    with _conn() as conn:
        conn.execute(
            "INSERT INTO sessions (session_id, student_id, lecture_file, started_at) VALUES (?, ?, ?, ?)",
            (session_id, student_id, lecture_file, now),
        )
    return session_id


def log_answer(session_id: str, question, student_answer: str,
               is_correct: bool, time_spent: float,
               hint_used: bool = False, hint_text: str = None,
               attempt_number: int = 1, is_final_attempt: bool = False):
    now = datetime.now().isoformat()
    with _conn() as conn:
        conn.execute("""
            INSERT INTO answers (
                session_id, question_id, concept, difficulty, question_text,
                student_answer, correct_answer, is_correct, hint_used, hint_text,
                time_spent_seconds, source_chunk_ids, timestamp, attempt_number
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            session_id, question.question_id, question.concept, question.difficulty,
            question.question_text, student_answer, question.correct_answer,
            1 if is_correct else 0, 1 if hint_used else 0, hint_text,
            time_spent, json.dumps(question.source_chunk_ids), now, attempt_number,
        ))
        if is_final_attempt:
            conn.execute("""
                UPDATE sessions SET
                    total_questions = total_questions + 1,
                    correct_count = correct_count + ?
                WHERE session_id = ?
            """, (1 if is_correct else 0, session_id))


def end_session(session_id: str):
    now = datetime.now().isoformat()
    with _conn() as conn:
        conn.execute("UPDATE sessions SET ended_at = ? WHERE session_id = ?", (now, session_id))


def get_concept_heatmap(lecture_file: str = None) -> list[dict]:
    where = "WHERE sessions.lecture_file = ?" if lecture_file else ""
    params = (lecture_file,) if lecture_file else ()
    
    query = f"""
        WITH per_question AS (
            SELECT answers.concept, sessions.lecture_file, sessions.session_id,
                   MIN(answers.source_chunk_ids) AS sample_chunks,
                   COUNT(*) AS attempts, SUM(answers.is_correct) AS correct_attempts,
                   MAX(answers.is_correct) AS mastered,
                   MAX(CASE WHEN answers.attempt_number = 1 THEN answers.is_correct ELSE 0 END)
                       AS correct_first_try,
                   SUM(answers.time_spent_seconds) AS total_time
            FROM answers
            JOIN sessions ON answers.session_id = sessions.session_id
            {where}
            GROUP BY answers.concept, sessions.lecture_file, sessions.session_id
        )
        SELECT concept, lecture_file, MIN(sample_chunks) AS sample_chunks,
               SUM(attempts) AS total_attempts,
               SUM(correct_attempts) AS correct_attempts,
               COUNT(*) AS question_sessions, SUM(mastered) AS mastered_sessions,
               SUM(correct_first_try) AS first_try_correct_sessions,
               SUM(total_time) / SUM(attempts) AS avg_time
        FROM per_question
        GROUP BY concept, lecture_file
        ORDER BY question_sessions DESC
    """
    
    with _conn() as conn:
        rows = conn.execute(query, params).fetchall()

    result = []
    for row in rows:
        total = row["total_attempts"]
        correct = row["correct_attempts"] or 0
        questions = row["question_sessions"]
        mastered = row["mastered_sessions"] or 0
        
        page_num = "N/A"
        try:
            chunks = json.loads(row["sample_chunks"])
            if chunks:
                match = re.search(r'_p(\d+)_', chunks[0])
                if match:
                    page_num = int(match.group(1))
        except Exception:
            pass

        result.append({
            "concept": row["concept"],
            "lecture_file": row["lecture_file"],
            "page_number": page_num,
            "total_attempts": total,
            "correct_attempts": correct,
            "question_sessions": questions,
            "mastered_sessions": mastered,
            "failure_rate": round(1.0 - (mastered / questions), 2) if questions else 0.0,
            "first_try_success_rate": round(row["first_try_correct_sessions"] / questions, 2) if questions else 0.0,
            "avg_time_seconds": round(row["avg_time"] or 0, 1),
        })
    return result


def get_session_stats(session_id: str) -> dict | None:
    with _conn() as conn:
        row = conn.execute(
            "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
        ).fetchone()
        return dict(row) if row else None


def list_recent_sessions(limit: int = 10) -> list[dict]:
    with _conn() as conn:
        rows = conn.execute(
            "SELECT * FROM sessions ORDER BY started_at DESC LIMIT ?", (limit,)
        ).fetchall()
        return [dict(r) for r in rows]


def get_student_gaps(student_id: str) -> list[dict]:
    query = """
        SELECT concept, COUNT(*) as failed_attempts
        FROM answers
        JOIN sessions ON answers.session_id = sessions.session_id
        WHERE sessions.student_id = ? AND answers.is_correct = 0
        GROUP BY concept
        HAVING SUM(is_correct) = 0
        ORDER BY failed_attempts DESC
    """
    with _conn() as conn:
        rows = conn.execute(query, (student_id,)).fetchall()
        return [dict(r) for r in rows]
