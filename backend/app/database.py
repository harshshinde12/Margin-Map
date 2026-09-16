"""Margin Map read-only database layer (Phase 8).

All access goes through this module. Connections are opened in
read-only mode (``mode=ro`` + ``PRAGMA query_only=ON``) against the
frozen Phase 6 database ``data/processed/marginmap.db``. Only
parameterized ``SELECT`` statements are executed here; there is no
INSERT/UPDATE/DELETE/DDL anywhere in the backend.
"""

from __future__ import annotations

import os
import sqlite3
from pathlib import Path

# backend/app/database.py -> parents[2] == repository root.
REPO_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_DB_PATH = REPO_ROOT / "data" / "processed" / "marginmap.db"


def resolve_db_path() -> Path:
    """Return the SQLite file to read.

    ``MARGINMAP_DB`` env var overrides the default (useful for tests).
    The path is resolved relative to the repository root so the API works
    regardless of the process working directory.
    """
    override = os.environ.get("MARGINMAP_DB")
    if override:
        return Path(override)
    return DEFAULT_DB_PATH


def get_connection() -> sqlite3.Connection:
    """Open a read-only connection to the frozen database."""
    db_path = resolve_db_path()
    if not db_path.is_file():
        raise FileNotFoundError(f"SQLite database not found: {db_path}")
    con = sqlite3.connect(f"file:{db_path}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    # Belt-and-braces: even if a write were attempted, SQLite refuses it.
    con.execute("PRAGMA query_only=ON;")
    return con


def fetch_all(sql: str, params: tuple = ()) -> list[dict]:
    """Execute a parameterized SELECT and return rows as dicts.

    The connection is always closed, even on error.
    """
    con = get_connection()
    try:
        cur = con.execute(sql, params)
        return [dict(row) for row in cur.fetchall()]
    finally:
        con.close()


def fetch_count(sql: str, params: tuple = ()) -> int:
    """Execute a parameterized SELECT COUNT(*) query."""
    con = get_connection()
    try:
        row = con.execute(sql, params).fetchone()
        return int(row[0])
    finally:
        con.close()


def build_where(filters: dict[str, str | None], allowed: set[str]) -> tuple[str, tuple]:
    """Build a safe ``WHERE`` clause from exact-match filters.

    Only columns in ``allowed`` are accepted (callers pass literals, never
    raw user input as identifiers). ``None`` values are skipped. Unknown
    filter *values* are passed through as parameters and simply match zero
    rows -- they are never reinterpreted and never interpolated into SQL.
    """
    clauses: list[str] = []
    params: list[str] = []
    for column, value in filters.items():
        if value is None:
            continue
        if column not in allowed:
            raise ValueError(f"Filter column not allowed: {column}")
        clauses.append(f'"{column}" = ?')
        params.append(value)
    if not clauses:
        return "", ()
    return " WHERE " + " AND ".join(clauses), tuple(params)
