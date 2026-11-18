#!/usr/bin/env python3
"""Run the five capstone acceptance checks against local service instances."""

import argparse
import json
import sqlite3
import time
from pathlib import Path

import requests

import config


ROOT = Path(__file__).parent
SHORT_CASES = [
    "Neat. Black. Smug.",
    "A.",
    "Hi.",
    "Plain words without punctuation",
    "One sentence only.",
    "Two words.",
    "The quiet room.",
    "A writer.",
    "Short sample text.",
    "A brief final example.",
]
NORMAL_TEXT = (
    "A careful writer revises a sentence several times while preserving "
    "the original meaning and tone. The process takes patience and attention."
)
LONG_TEXT = "word. " * 500
REQUIRED_TELEMETRY_FIELDS = {
    "content_id", "model_ms", "style_ms", "disagreement_triggered", "guess",
}


def post_json(base_url: str, path: str, body: dict, timeout: float = 30.0):
    started = time.perf_counter()
    try:
        response = requests.post(
            base_url.rstrip("/") + path,
            json=body,
            timeout=timeout,
        )
        elapsed_ms = (time.perf_counter() - started) * 1000
        try:
            data = response.json()
        except ValueError:
            data = {}
        return response.status_code, data, elapsed_ms
    except requests.RequestException as exc:
        return None, {"error": str(exc)}, (time.perf_counter() - started) * 1000


def load_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def audit_sqlite_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        with sqlite3.connect(path) as connection:
            rows = connection.execute(
                "SELECT payload FROM audit_entries ORDER BY id"
            ).fetchall()
        return [json.loads(payload) for (payload,) in rows]
    except (sqlite3.Error, json.JSONDecodeError):
        return []


def telemetry_by_id(path: Path, content_ids: set[str]) -> dict[str, list[dict]]:
    found = {content_id: [] for content_id in content_ids}
    for row in load_jsonl(path):
        content_id = row.get("content_id")
        if content_id in found:
            found[content_id].append(row)
    return found


def run_evaluation(args) -> dict:
    run_id = args.run_number
    results = {"run": run_id, "checks": {}}

    # Criterion 1: the service must refuse to score insufficient evidence,
    # rather than returning a score or throwing an unhandled server exception.
    c1_successes = 0
    c1_details = []
    for index, text in enumerate(SHORT_CASES):
        status, data, elapsed_ms = post_json(
            args.base_url, "/submit",
            {"text": text, "creator_id": f"cap-c1-{run_id}-{index}"},
        )
        passed = (
            status == 200
            and data.get("guess") == "unsure"
            and data.get("reason_code") == "insufficient_text_length"
        )
        c1_successes += int(passed)
        c1_details.append({
            "text": text, "http_status": status, "response": data,
            "latency_ms": round(elapsed_ms, 3), "passed": passed,
        })
    results["checks"]["1_short_text_gate"] = {
        "successes": c1_successes, "total": len(SHORT_CASES),
        "target_met": c1_successes == len(SHORT_CASES),
        "details": c1_details,
    }

    # Criterion 2: requests are directed to an isolated local server whose
    # detector has an injected >3s delay (capstone_timeout_server.py).
    c2_successes = 0
    c2_details = []
    for index in range(5):
        status, data, elapsed_ms = post_json(
            args.timeout_url, "/submit",
            {
                "text": NORMAL_TEXT * 3,
                "creator_id": f"cap-c2-{run_id}-{index}",
            },
            timeout=5.0,
        )
        audit_rows = requests.get(
            args.timeout_url.rstrip("/") + "/log",
            params={"limit": 2000},
            timeout=5.0,
        ).json().get("entries", [])
        decision = next(
            (row for row in reversed(audit_rows)
             if row.get("content_id") == data.get("content_id")),
            {},
        )
        passed = (
            status == 200
            and elapsed_ms < 3500
            and data.get("model_score") is None
            and data.get("guess") == "unsure"
            and decision.get("status") == "degraded"
        )
        c2_successes += int(passed)
        c2_details.append({
            "http_status": status, "response": data,
            "latency_ms": round(elapsed_ms, 3), "audit_row": decision,
            "passed": passed,
        })
    results["checks"]["2_timeout_degradation"] = {
        "successes": c2_successes, "total": 5,
        "target_met": c2_successes == 5,
        "details": c2_details,
    }

    # Criterion 3: each case submits once and retries its appeal. Verify one
    # appeal in both backing SQLite and the JSONL compatibility export.
    c3_successes = 0
    c3_details = []
    for index in range(5):
        status, decision, _ = post_json(
            args.base_url, "/submit",
            {"text": NORMAL_TEXT * 3, "creator_id": f"cap-c3-{run_id}-{index}"},
        )
        content_id = decision.get("content_id")
        appeal_statuses = []
        for retry in range(2):
            appeal_status, _, _ = post_json(
                args.base_url, "/appeal",
                {"content_id": content_id, "reasoning": f"retry {retry}"},
            )
            appeal_statuses.append(appeal_status)

        db_rows = audit_sqlite_rows(args.db_path)
        jsonl_rows = load_jsonl(args.audit_jsonl)
        db_appeals = [
            row for row in db_rows
            if row.get("content_id") == content_id
            and row.get("event") == "appeal"
            and row.get("status") == "under_review"
        ]
        jsonl_appeals = [
            row for row in jsonl_rows
            if row.get("content_id") == content_id
            and row.get("event") == "appeal"
            and row.get("status") == "under_review"
        ]
        db_decision = next(
            (row for row in db_rows if row.get("content_id") == content_id
             and "event" not in row),
            {},
        )
        passed = (
            status == 200
            and appeal_statuses == [200, 200]
            and len(db_appeals) == 1
            and len(jsonl_appeals) == 1
            and bool(db_decision.get("config_hash"))
            and bool(db_decision.get("raw_sha256"))
        )
        c3_successes += int(passed)
        c3_details.append({
            "content_id": content_id, "submit_status": status,
            "appeal_statuses": appeal_statuses,
            "sqlite_appeal_count": len(db_appeals),
            "jsonl_appeal_count": len(jsonl_appeals),
            "config_hash_present": bool(db_decision.get("config_hash")),
            "raw_sha256_present": bool(db_decision.get("raw_sha256")),
            "passed": passed,
        })
    results["checks"]["3_appeal_and_audit_integrity"] = {
        "successes": c3_successes, "total": 5,
        "target_met": c3_successes == 5,
        "details": c3_details,
    }

    # Criterion 4: reject over-limit text, and report exact 400-token truncation
    # for valid long text, cross-checking each response against telemetry.
    c4_oversize = []
    for index in range(5):
        status, data, _ = post_json(
            args.base_url, "/submit",
            {"text": "x" * 25001, "creator_id": f"cap-c4-large-{run_id}-{index}"},
        )
        c4_oversize.append({
            "http_status": status, "response": data,
            "passed": status in (400, 413),
        })

    long_results = []
    long_ids = set()
    for index in range(5):
        status, data, elapsed_ms = post_json(
            args.base_url, "/submit",
            {"text": LONG_TEXT, "creator_id": f"cap-c4-long-{run_id}-{index}"},
            timeout=35.0,
        )
        content_id = data.get("content_id")
        if content_id:
            long_ids.add(content_id)
        long_results.append({
            "http_status": status, "response": data,
            "latency_ms": round(elapsed_ms, 3),
        })
    telemetry = telemetry_by_id(args.telemetry, long_ids)
    c4_long_successes = 0
    for row in long_results:
        data = row["response"]
        events = telemetry.get(data.get("content_id"), [])
        passed = (
            row["http_status"] == 200
            and data.get("text_truncated") is True
            and data.get("tokens_evaluated") == 400
            and len(events) == 1
            and events[0].get("truncated") is True
        )
        row["telemetry"] = events
        row["passed"] = passed
        c4_long_successes += int(passed)
    c4_large_successes = sum(row["passed"] for row in c4_oversize)
    results["checks"]["4_payload_and_truncation"] = {
        "oversize_successes": c4_large_successes, "oversize_total": 5,
        "long_successes": c4_long_successes, "long_total": 5,
        "target_met": c4_large_successes == 5 and c4_long_successes == 5,
        "oversize_details": c4_oversize, "long_details": long_results,
    }

    # Criterion 5: ten warm requests; one and only one complete telemetry record
    # is required for each response content_id.
    c5_details = []
    c5_ids = set()
    for index in range(10):
        status, data, elapsed_ms = post_json(
            args.base_url, "/submit",
            {"text": NORMAL_TEXT * 2, "creator_id": f"cap-c5-{run_id}-{index}"},
            timeout=35.0,
        )
        content_id = data.get("content_id")
        if content_id:
            c5_ids.add(content_id)
        c5_details.append({
            "http_status": status, "content_id": content_id,
            "latency_ms": round(elapsed_ms, 3),
            "guess": data.get("guess"), "response": data,
        })
    c5_telemetry = telemetry_by_id(args.telemetry, c5_ids)
    latency_successes = 0
    telemetry_successes = 0
    for row in c5_details:
        events = c5_telemetry.get(row["content_id"], [])
        valid = (
            len(events) == 1
            and REQUIRED_TELEMETRY_FIELDS.issubset(events[0])
        )
        row["telemetry"] = events
        row["telemetry_valid"] = valid
        row["latency_passed"] = (
            row["http_status"] == 200 and row["latency_ms"] < 1500
        )
        latency_successes += int(row["latency_passed"])
        telemetry_successes += int(valid)
    results["checks"]["5_latency_and_telemetry"] = {
        "latency_successes": latency_successes, "latency_total": 10,
        "telemetry_successes": telemetry_successes, "telemetry_total": 10,
        "target_met": latency_successes >= 9 and telemetry_successes == 10,
        "details": c5_details,
    }

    results["verdict"] = all(
        check["target_met"] for check in results["checks"].values()
    )
    return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://127.0.0.1:8000")
    parser.add_argument("--timeout-url", default="http://127.0.0.1:8001")
    parser.add_argument("--run-number", type=int, required=True, choices=(1, 2, 3))
    parser.add_argument("--db-path", type=Path, default=config.AUDIT_DB)
    parser.add_argument("--audit-jsonl", type=Path, default=config.AUDIT_LOG)
    parser.add_argument("--telemetry", type=Path, default=config.TELEMETRY_LOG)
    args = parser.parse_args()

    results = run_evaluation(args)
    output = ROOT / "results" / f"capstone_run_{args.run_number}.json"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n",
                      encoding="utf-8")
    summary = {
        "run": results["run"],
        "checks": {
            name: {
                key: value for key, value in check.items()
                if key not in ("details", "oversize_details", "long_details")
            }
            for name, check in results["checks"].items()
        },
        "verdict": results["verdict"],
        "result_file": str(output),
    }
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
