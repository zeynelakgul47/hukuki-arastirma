"""SQLite cache: içtihat full text + daire/künye + konu etiketleri. Mevzuat metni kaynak değil."""
from __future__ import annotations

import json
import sqlite3
import threading
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Optional

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
                    fetched_at TEXT NOT NULL,
                    birim_adi TEXT,
                    esas_no TEXT,
                    karar_no TEXT,
                    karar_tarihi TEXT,
                    court_type TEXT
                )
                """
            )
            cols = {r[1] for r in conn.execute("PRAGMA table_info(ictihat)")}
            for name, decl in [
                ("birim_adi", "TEXT"),
                ("esas_no", "TEXT"),
                ("karar_no", "TEXT"),
                ("karar_tarihi", "TEXT"),
                ("court_type", "TEXT"),
            ]:
                if name not in cols:
                    conn.execute(f"ALTER TABLE ictihat ADD COLUMN {name} {decl}")
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_ictihat_daire ON ictihat(birim_adi)"
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS ictihat_tag (
                    document_id TEXT NOT NULL,
                    tag TEXT NOT NULL,
                    PRIMARY KEY (document_id, tag)
                )
                """
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_ictihat_tag ON ictihat_tag(tag)"
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
                """
                SELECT document_id, markdown, metadata_json, fetched_at,
                       birim_adi, esas_no, karar_no, karar_tarihi, court_type
                FROM ictihat WHERE document_id = ?
                """,
                (document_id,),
            ).fetchone()
            tags = []
            if row:
                tags = [
                    r[0]
                    for r in conn.execute(
                        "SELECT tag FROM ictihat_tag WHERE document_id = ? ORDER BY tag",
                        (document_id,),
                    )
                ]
        if not row:
            return None
        meta = json.loads(row["metadata_json"] or "{}")
        return {
            "document_id": row["document_id"],
            "markdown": row["markdown"],
            "metadata": meta,
            "fetched_at": row["fetched_at"],
            "birim_adi": row["birim_adi"],
            "esas_no": row["esas_no"],
            "karar_no": row["karar_no"],
            "karar_tarihi": row["karar_tarihi"],
            "court_type": row["court_type"],
            "tags": tags,
            "cache_hit": True,
        }

    def put_ictihat(
        self,
        document_id: str,
        markdown: str,
        metadata: Optional[dict] = None,
        *,
        birim_adi: Optional[str] = None,
        esas_no: Optional[str] = None,
        karar_no: Optional[str] = None,
        karar_tarihi: Optional[str] = None,
        court_type: Optional[str] = None,
        tags: Optional[Iterable[str]] = None,
    ) -> None:
        now = _utc_now()
        meta = dict(metadata or {})
        birim_adi = birim_adi or meta.get("birimAdi") or meta.get("birim_adi")
        esas_no = esas_no or meta.get("esasNo") or meta.get("esas_no")
        karar_no = karar_no or meta.get("kararNo") or meta.get("karar_no")
        karar_tarihi = (
            karar_tarihi
            or meta.get("kararTarihiStr")
            or meta.get("karar_tarihi")
        )
        item = meta.get("itemType") or {}
        if isinstance(item, dict):
            court_type = court_type or item.get("name") or item.get("description")
        court_type = court_type or meta.get("court_type")
        payload = json.dumps(meta, ensure_ascii=False)
        with _lock, self._connect() as conn:
            conn.execute(
                """
                INSERT INTO ictihat(
                    document_id, markdown, metadata_json, fetched_at,
                    birim_adi, esas_no, karar_no, karar_tarihi, court_type
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(document_id) DO UPDATE SET
                    markdown=COALESCE(excluded.markdown, ictihat.markdown),
                    metadata_json=excluded.metadata_json,
                    fetched_at=excluded.fetched_at,
                    birim_adi=COALESCE(excluded.birim_adi, ictihat.birim_adi),
                    esas_no=COALESCE(excluded.esas_no, ictihat.esas_no),
                    karar_no=COALESCE(excluded.karar_no, ictihat.karar_no),
                    karar_tarihi=COALESCE(excluded.karar_tarihi, ictihat.karar_tarihi),
                    court_type=COALESCE(excluded.court_type, ictihat.court_type)
                """,
                (
                    document_id,
                    markdown,
                    payload,
                    now,
                    birim_adi,
                    esas_no,
                    karar_no,
                    karar_tarihi,
                    court_type,
                ),
            )
            if markdown:
                conn.execute("DELETE FROM ictihat_fts WHERE document_id = ?", (document_id,))
                conn.execute(
                    "INSERT INTO ictihat_fts(document_id, markdown) VALUES (?, ?)",
                    (document_id, markdown),
                )
            if tags:
                for tag in tags:
                    t = (tag or "").strip()
                    if not t:
                        continue
                    conn.execute(
                        "INSERT OR IGNORE INTO ictihat_tag(document_id, tag) VALUES (?, ?)",
                        (document_id, t),
                    )
            conn.commit()

    def add_tags(self, document_id: str, tags: Iterable[str]) -> None:
        with _lock, self._connect() as conn:
            for tag in tags:
                t = (tag or "").strip()
                if not t:
                    continue
                conn.execute(
                    "INSERT OR IGNORE INTO ictihat_tag(document_id, tag) VALUES (?, ?)",
                    (document_id, t),
                )
            conn.commit()

    def list_by_daire(self, birim_adi: str) -> list[dict[str, Any]]:
        with _lock, self._connect() as conn:
            rows = conn.execute(
                """
                SELECT document_id, birim_adi, esas_no, karar_no, karar_tarihi, court_type,
                       (markdown IS NOT NULL AND length(markdown) > 0) AS has_text
                FROM ictihat
                WHERE birim_adi = ?
                ORDER BY karar_tarihi DESC, karar_no DESC
                """,
                (birim_adi,),
            ).fetchall()
        return [dict(r) for r in rows]

    def daire_ozet(self) -> list[dict[str, Any]]:
        with _lock, self._connect() as conn:
            rows = conn.execute(
                """
                SELECT COALESCE(birim_adi, '(daire yok)') AS birim_adi,
                       COUNT(*) AS n,
                       SUM(CASE WHEN markdown IS NOT NULL AND length(markdown) > 0 THEN 1 ELSE 0 END) AS with_text
                FROM ictihat
                GROUP BY COALESCE(birim_adi, '(daire yok)')
                ORDER BY n DESC, birim_adi
                """
            ).fetchall()
        return [dict(r) for r in rows]

    def list_by_tag(self, tag: str) -> list[dict[str, Any]]:
        with _lock, self._connect() as conn:
            rows = conn.execute(
                """
                SELECT i.document_id, i.birim_adi, i.esas_no, i.karar_no, i.karar_tarihi
                FROM ictihat i
                JOIN ictihat_tag t ON t.document_id = i.document_id
                WHERE t.tag = ?
                ORDER BY i.karar_tarihi DESC
                """,
                (tag,),
            ).fetchall()
        return [dict(r) for r in rows]

    def search_fts(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        if not query.strip():
            return []
        with _lock, self._connect() as conn:
            rows = conn.execute(
                """
                SELECT f.document_id, snippet(ictihat_fts, 1, '[', ']', '…', 24) AS snip,
                       i.birim_adi, i.esas_no, i.karar_no
                FROM ictihat_fts f
                LEFT JOIN ictihat i ON i.document_id = f.document_id
                WHERE ictihat_fts MATCH ?
                LIMIT ?
                """,
                (query, limit),
            ).fetchall()
        return [dict(r) for r in rows]

    def remember_mevzuat(self, mevzuat_id: str, mevzuat_no: Optional[str], title: Optional[str], content_hash: Optional[str]) -> Optional[str]:
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
