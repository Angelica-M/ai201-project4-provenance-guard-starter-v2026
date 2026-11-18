"""
The audit log.

Every decision your service makes gets written here as one JSON object per
line. Not `print()` — a file you can read back.

The reason is next unit: you run an attack against this service, and **an
attack you can't see in a log is an attack you can't diagnose.** An input that
slipped past your detector leaves no other trace.

All nine fields the unit 8 rubric requires are in the entry shape from the
start, even though unit 7 only fills some of them. That's deliberate — adding
fields later means your early entries and your late ones have different shapes,
and the one you most want to compare is the one from before the change.

    from audit import log_decision, read_entries

    log_decision(content_id=..., creator_id=..., guess="ai", ...)
    entries = read_entries(limit=50)
"""

import json
import threading
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

import config

_lock = threading.RLock()


def _db_path():
    # A deployment can mount a durable volume and point the DB at it.
    # Test patches of AUDIT_LOG keep the JSONL and SQLite artifacts isolated.
    if getattr(config, "AUDIT_DB", None) is not None:
        return Path(config.AUDIT_DB)
    return config.AUDIT_LOG.with_name("audit.sqlite3")


def _now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def log_decision(
    content_id: str,
    creator_id: str,
    guess: str | None = None,
    model_score: float | None = None,
    style_score: float | None = None,
    combined_score: float | None = None,
    label: str | None = None,
    status: str = "decided",
    **extra,
) -> dict:
    """
    Write one decision to the audit log.

    The nine required fields, all present from unit 7 whether or not you can
    fill them yet:

        timestamp, content_id, creator_id, guess,
        model_score, style_score, combined_score, label, status

    `status` moves over an item's life: `decided` when first judged,
    `under_review` once the writer appeals.

    Anything extra you pass gets written too — useful for `rejected` entries in
    unit 8, where there's no decision but you still want the trace.
    """
    entry = {
        "timestamp": _now(),
        "content_id": content_id,
        "creator_id": creator_id,
        "guess": guess,
        "model_score": model_score,
        "style_score": style_score,
        "combined_score": combined_score,
        "label": label,
        "status": status,
        "config_hash": config.generate_config_hash(),
    }
    entry.update(extra)
    return _append(entry)


def log_appeal(content_id: str, creator_id: str, reasoning: str) -> dict:
    """
    Record an appeal beside the original decision.

    This doesn't overwrite anything. The log is append-only, so the original
    decision stays exactly where it was and the appeal sits after it — which is
    the whole point of an audit log. Someone reading it later can see what was
    decided, that it was challenged, and in what order.
    """
    with _lock:
        existing = next((e for e in entries_for(content_id)
                         if e.get("event") == "appeal"
                         and e.get("status") == "under_review"), None)
        if existing is not None:
            return existing

        return _append({
            "timestamp": _now(),
            "content_id": content_id,
            "creator_id": creator_id,
            "event": "appeal",
            "status": "under_review",
            "reasoning": reasoning,
            "config_hash": config.generate_config_hash(),
        })


def log_rejection(creator_id: str, reason: str, **extra) -> dict:
    """
    Record a request that never became a decision — a rate-limit rejection or
    an input your route refused.

    ⚠️ Unit 8 asks for this explicitly, and the reason is worth holding onto:
    **an attack that shows up only as an absence is one you'll never find.** A
    thousand requests that got a 429 and left no trace look exactly like a
    quiet afternoon.
    """
    return _append({
        "timestamp": _now(),
        "creator_id": creator_id,
        "event": "rejected",
        "status": "rejected",
        "reason": reason,
        **extra,
    })


def _append(entry: dict) -> dict:
    config.LOG_DIR.mkdir(parents=True, exist_ok=True)
    with _lock:
        db = _db_path()
        db.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(db)
        try:
            connection.execute("PRAGMA journal_mode=WAL;")
            connection.execute(
                "CREATE TABLE IF NOT EXISTS audit_entries "
                "(id INTEGER PRIMARY KEY AUTOINCREMENT, payload TEXT NOT NULL)"
            )
            connection.execute(
                "INSERT INTO audit_entries(payload) VALUES (?)",
                (json.dumps(entry, ensure_ascii=False, sort_keys=True),),
            )
            connection.commit()
        finally:
            connection.close()
        # Preserve the human-readable JSONL artifact as a compatibility/export
        # mirror of the SQLite source of truth.
        config.AUDIT_LOG.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(entry, ensure_ascii=False, sort_keys=True)
        with config.AUDIT_LOG.open("a", encoding="utf-8", newline="\n") as handle:
            handle.write(line + "\n")
    return entry


def read_entries(limit: int | None = None) -> list[dict]:
    """
    Read the log back, oldest first. `limit` keeps the most recent N.

    A malformed line is skipped rather than raising — a log that can't be read
    because of one bad row is worse than a log with a gap.
    """
    db = _db_path()
    entries = []
    if db.exists():
        try:
            connection = sqlite3.connect(db)
            try:
                connection.execute("PRAGMA journal_mode=WAL;")
                rows = connection.execute(
                    "SELECT payload FROM audit_entries ORDER BY id ASC"
                ).fetchall()
            finally:
                connection.close()
            for (payload,) in rows:
                try:
                    entries.append(json.loads(payload))
                except json.JSONDecodeError:
                    continue
        except sqlite3.Error:
            entries = []

    if not entries and config.AUDIT_LOG.exists():
        for line in config.AUDIT_LOG.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    return entries[-limit:] if limit else entries


def clear() -> int:
    """Wipe the log. Handy between attack runs; returns how many went."""
    count = len(read_entries())
    db = _db_path()
    if db.exists():
        db.unlink()
    for suffix in ("-wal", "-shm"):
        sidecar = db.with_name(db.name + suffix)
        if sidecar.exists():
            sidecar.unlink()
    if config.AUDIT_LOG.exists():
        config.AUDIT_LOG.unlink()
    return count


def export_audit_jsonl(path: str | Path | None = None) -> Path:
    """Export SQLite entries to a deterministic canonical JSON Lines file."""
    destination = Path(path) if path is not None else config.AUDIT_LOG
    destination.parent.mkdir(parents=True, exist_ok=True)
    entries = read_entries()
    with destination.open("w", encoding="utf-8", newline="\n") as handle:
        for entry in entries:
            handle.write(json.dumps(
                entry,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            ) + "\n")
    return destination


def entries_for(content_id: str) -> list[dict]:
    """Every entry touching one content id, in order."""
    return [e for e in read_entries() if e.get("content_id") == content_id]
