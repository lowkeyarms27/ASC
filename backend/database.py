import sqlite3
import os
import json

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data", "asc.db")


def get_connection():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db():
    with get_connection() as conn:
        conn.execute('''
            CREATE TABLE IF NOT EXISTS sessions (
                id                   INTEGER PRIMARY KEY AUTOINCREMENT,
                clip_filename        TEXT,
                game                 TEXT,
                attacking_team       TEXT,
                defending_team       TEXT,
                winner               TEXT,
                round_number         INTEGER,
                notes                TEXT,
                status               TEXT,
                error_message        TEXT,
                full_result          TEXT,
                pegasus_analysis     TEXT,
                agent_log_live       TEXT,
                webhook_url          TEXT,
                confidence_threshold REAL DEFAULT 0.75,
                rating               INTEGER,
                feedback_notes       TEXT,
                created_at           DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        for col in [
            "rating INTEGER",
            "feedback_notes TEXT",
            "pegasus_analysis TEXT",
            "agent_log_live TEXT",
            "webhook_url TEXT",
            "confidence_threshold REAL DEFAULT 0.75",
        ]:
            try:
                conn.execute(f"ALTER TABLE sessions ADD COLUMN {col}")
            except Exception:
                pass

        conn.execute('''
            CREATE TABLE IF NOT EXISTS mistakes (
                id                 INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id         INTEGER,
                team               TEXT,
                category           TEXT,
                severity           TEXT,
                description        TEXT,
                timestamp          REAL,
                better_alternative TEXT,
                clip_path          TEXT,
                confidence         INTEGER DEFAULT 2,
                FOREIGN KEY (session_id) REFERENCES sessions(id)
            )
        ''')
        for col in ["confidence INTEGER DEFAULT 2", "embedding TEXT"]:
            try:
                conn.execute(f"ALTER TABLE mistakes ADD COLUMN {col}")
            except Exception:
                pass
        conn.commit()


def create_session(clip_filename: str, game: str, attacking_team: str,
                   defending_team: str, winner: str, round_number: int, notes: str,
                   webhook_url: str = "", confidence_threshold: float = 0.75) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            '''INSERT INTO sessions
               (clip_filename, game, attacking_team, defending_team, winner,
                round_number, notes, status, webhook_url, confidence_threshold)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (clip_filename, game, attacking_team, defending_team, winner,
             round_number, notes, "uploading", webhook_url, confidence_threshold)
        )
        conn.commit()
        return cur.lastrowid


def update_session(session_id: int, **kwargs):
    if not kwargs:
        return
    with get_connection() as conn:
        set_clause = ", ".join(f"{k} = ?" for k in kwargs)
        conn.execute(
            f"UPDATE sessions SET {set_clause} WHERE id = ?",
            (*kwargs.values(), session_id)
        )
        conn.commit()


def append_agent_log_event(session_id: int, event: dict):
    """Append a single agent log event to agent_log_live (JSON array in DB)."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT agent_log_live FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if not row:
            return
        existing = []
        try:
            existing = json.loads(row["agent_log_live"] or "[]")
        except Exception:
            pass
        existing.append(event)
        conn.execute(
            "UPDATE sessions SET agent_log_live = ? WHERE id = ?",
            (json.dumps(existing), session_id)
        )
        conn.commit()


def get_agent_log_live(session_id: int) -> list:
    """Return the live agent log as a list of events."""
    with get_connection() as conn:
        row = conn.execute(
            "SELECT agent_log_live FROM sessions WHERE id = ?", (session_id,)
        ).fetchone()
        if not row or not row["agent_log_live"]:
            return []
        try:
            return json.loads(row["agent_log_live"])
        except Exception:
            return []


def get_session(session_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        return dict(row) if row else None


def save_mistake(session_id: int, m: dict):
    # Compute embedding in background (non-blocking on failure)
    embedding_json = None
    try:
        from backend.ml.embedder import embed_mistake
        vec = embed_mistake(m)
        if vec:
            embedding_json = json.dumps(vec)
    except Exception:
        pass

    with get_connection() as conn:
        conn.execute(
            '''INSERT INTO mistakes
               (session_id, team, category, severity, description, timestamp,
                better_alternative, clip_path, confidence, embedding)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)''',
            (session_id, m.get("team"), m.get("category"), m.get("severity"),
             m.get("description"), m.get("timestamp"), m.get("better_alternative"),
             m.get("clip_path"), m.get("confidence", 2), embedding_json)
        )
        conn.commit()


def semantic_search_mistakes(query: str, game: str = None,
                              limit: int = 10) -> list[dict]:
    """Find mistakes semantically similar to query using stored embeddings."""
    with get_connection() as conn:
        sql = """
            SELECT m.*, s.game, s.attacking_team, s.defending_team, s.round_number, s.created_at
            FROM mistakes m JOIN sessions s ON m.session_id = s.id
            WHERE m.embedding IS NOT NULL AND s.status = 'complete'
        """
        params = []
        if game:
            sql += " AND s.game = ?"
            params.append(game)
        rows = conn.execute(sql, params).fetchall()

    candidates = [dict(r) for r in rows]
    if not candidates:
        return []

    try:
        from backend.ml.embedder import find_similar_mistakes
        return find_similar_mistakes(query, candidates, top_k=limit)
    except Exception:
        return []


def get_embedded_mistakes(game: str = None, limit: int = 500) -> list:
    """Fetch all mistakes that have stored embeddings, optionally filtered by game."""
    with get_connection() as conn:
        sql = """
            SELECT m.*, s.game, s.attacking_team, s.defending_team, s.round_number, s.created_at
            FROM mistakes m JOIN sessions s ON m.session_id = s.id
            WHERE m.embedding IS NOT NULL AND s.status = 'complete'
        """
        params = []
        if game:
            sql += " AND s.game = ?"
            params.append(game)
        sql += " ORDER BY m.id DESC LIMIT ?"
        params.append(limit)
        rows = conn.execute(sql, params).fetchall()
    return [dict(r) for r in rows]


def get_results(session_id: int) -> dict | None:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM sessions WHERE id = ?", (session_id,)).fetchone()
        if not row:
            return None
        data = dict(row)
        full_result = data.get("full_result")
        data["full_result"] = json.loads(full_result) if full_result else {}
        rows = conn.execute(
            "SELECT * FROM mistakes WHERE session_id = ? ORDER BY timestamp ASC", (session_id,)
        ).fetchall()
        data["mistakes"] = [dict(r) for r in rows]
        return data


def save_feedback(session_id: int, rating: int, notes: str):
    with get_connection() as conn:
        conn.execute(
            "UPDATE sessions SET rating = ?, feedback_notes = ? WHERE id = ?",
            (rating, notes, session_id)
        )
        conn.commit()


def get_top_examples(game: str, limit: int = 2) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT full_result, attacking_team, defending_team, winner, round_number
               FROM sessions
               WHERE game = ? AND status = 'complete' AND rating >= 4 AND full_result IS NOT NULL
               ORDER BY rating DESC, id DESC
               LIMIT 6""",
            (game,)
        ).fetchall()

    candidates = [dict(r) for r in rows]
    if len(candidates) <= limit:
        return candidates

    def get_categories(ex):
        try:
            result = json.loads(ex.get("full_result", "{}"))
            return set(m.get("category", "") for m in result.get("mistakes", []))
        except Exception:
            return set()

    selected, covered = [], set()
    for _ in range(limit):
        best, best_new = None, -1
        for c in candidates:
            if c in selected:
                continue
            new_cats = len(get_categories(c) - covered)
            if new_cats > best_new:
                best_new, best = new_cats, c
        if best:
            selected.append(best)
            covered |= get_categories(best)

    return selected


def get_opponent_profile(game: str, team: str, limit: int = 20) -> dict:
    """
    Build a profile of a team's historical mistakes across all sessions.
    Used by Planner to exploit opponent weaknesses.
    """
    with get_connection() as conn:
        sessions = conn.execute(
            """SELECT id FROM sessions
               WHERE game = ? AND status = 'complete'
               AND (attacking_team = ? OR defending_team = ?)
               ORDER BY id DESC LIMIT ?""",
            (game, team, team, limit)
        ).fetchall()

        if not sessions:
            return {}

        session_ids = [s["id"] for s in sessions]
        placeholders = ",".join("?" * len(session_ids))
        mistakes = conn.execute(
            f"""SELECT category, severity
                FROM mistakes
                WHERE session_id IN ({placeholders})""",
            session_ids
        ).fetchall()

    cats: dict = {}
    for m in mistakes:
        c = m["category"] or "unknown"
        cats[c] = cats.get(c, 0) + 1

    top = sorted(cats.items(), key=lambda x: x[1], reverse=True)[:5]
    return {
        "team":                 team,
        "sessions_seen":        len(session_ids),
        "exploitable_patterns": [{"category": c, "occurrences": n} for c, n in top],
    }


def list_sessions(limit: int = 100) -> list[dict]:
    with get_connection() as conn:
        rows = conn.execute(
            """SELECT id, clip_filename, game, attacking_team, defending_team, winner,
               round_number, status, error_message, rating, created_at
               FROM sessions ORDER BY id DESC LIMIT ?""",
            (limit,)
        ).fetchall()
        return [dict(r) for r in rows]
