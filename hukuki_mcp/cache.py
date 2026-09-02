"""SQLite cache for fetched içtihat texts. Mevzuat full text is not stored as source of truth."""
from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

_lock = threading.Lock()


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class IctihatCache:
    def __init__(self, db_path: Path):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init()

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init(self) -> None:
        with _lock, self._connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ictihat (
                    document_id TEXT PRIMARY KEY,
                    markdown TEXT,
                    metadata_json TEXT,
                    fetched_at TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE VIRTUAL TABLE IF NOT EXISTS ictihat_fts
                USING fts5(document_id, markdown, tokenize='unicode61')
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS mevzuat_meta (
                    mevzuat_id TEXT PRIMARY KEY,
                    mevzuat_no TEXT,
                    title TEXT,
                    content_hash TEXT,
                    last_seen_at TEXT NOT NULL
                )
                """
            )
            conn.commit()

    def get_ictihat(self, document_id: str) -> Optional[dict[str, Any]]:
        with _lock, self._connect() as conn:
            row = conn.execute(
                "SELECT document_id, markdown, metadata_json, fetched_at FROM ictihat WHERE document_id = ?",
                (document_id,),
            ).fetchone()
        if not row:
            return None
        meta = json.loads(row["metadata_json"] or "{}")
        return {
            "document_id": row["document_id"],
            "markdown": row["markdown"],
            "metadata": meta,
            "fetched_at": row["fetched_at"],
            "cache_hit": True,
        }

    def put_ictihat(self, document_id: str, markdown: str, metadata: Optional[dict] = None) -> None:
        now = _utc_now()
        payload = json.dumps(metadata or {}, ensure_ascii=False)
        with _lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO ictihat(document_id, markdown, metadata_json, fetched_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(document_id) DO UPDATE SET
                    markdown=excluded.markdown,
                    metadata_json=excluded.metadata_json,
                    fetched_at=excluded.fetched_at
                """,
                (document_id, markdown, payload, now),
            )
            conn.execute("DELETE FROM ictihat_fts WHERE document_id = ?", (document_id,))
            conn.execute(
                "INSERT INTO ictihat_fts(document_id, markdown) VALUES (?, ?)",
                (document_id, markdown or ""),
            )
            conn.commit()

    def search_fts(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        if not query.strip():
            return []
        with _lock, self._connect() as conn:
            rows = conn.execute(
                """
                SELECT document_id, snippet(ictihat_fts, 1, '[', ']', '…', 24) AS snip
                FROM ictihat_fts
                WHERE ictihat_fts MATCH ?
                LIMIT ?
                """,
                (query, limit),
            ).fetchall()
        return [{"document_id": r["document_id"], "snippet": r["snip"]} for r in rows]

    def remember_mevzuat(self, mevzuat_id: str, mevzuat_no: Optional[str], title: Optional[str], content_hash: Optional[str]) -> Optional[str]:
        """Store metadata only. Returns previous hash if it changed."""
        now = _utc_now()
        with _lock, self._connect() as conn:
            prev = conn.execute(
                "SELECT content_hash FROM mevzuat_meta WHERE mevzuat_id = ?",
                (mevzuat_id,),
            ).fetchone()
            conn.execute(
                """
                INSERT INTO mevzuat_meta(mevzuat_id, mevzuat_no, title, content_hash, last_seen_at)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT(mevzuat_id) DO UPDATE SET
                    mevzuat_no=excluded.mevzuat_no,
                    title=excluded.title,
                    content_hash=excluded.content_hash,
                    last_seen_at=excluded.last_seen_at
                """,
                (mevzuat_id, mevzuat_no, title, content_hash, now),
            )
            conn.commit()
        if prev and prev["content_hash"] and content_hash and prev["content_hash"] != content_hash:
            return prev["content_hash"]
        return None
