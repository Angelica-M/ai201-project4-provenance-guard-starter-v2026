#!/usr/bin/env python3
"""
Run your five criteria three times each.  <- UNIT 8, MILESTONE 3

    python app.py                              # in one terminal
    python run_eval.py --label before          # in another
    python run_eval.py --label after

─────────────────────────────────────────────────────────────────────────────
WHAT THIS FILE DOES, IN SHORT

`criteria.md` says what "working" means. `scenarios.py` says what to run
against each criterion (the inputs) and how to tell whether a trial met its
target (a small `check` function). This file is the runner in the middle:

  1. Reads `scenarios.py` and refuses to start if it is malformed.
  2. For each scenario, runs it three times against the live service:
       - a normal scenario POSTs each text to /submit;
       - a "bad_input" scenario also pings the service afterwards and counts
         the rejections written to the audit log;
       - an "appeal" scenario submits, appeals, then reads /log to check the
         appeal was recorded and the original decision was left alone.
  3. Asks the scenario's `check` whether the trial met its target, and prints
     "target met: yes/no" with the numbers behind it.
  4. Writes everything, including the raw responses, to results/run_*.md.

The Verdict column in that report stays BLANK on purpose. A trial meeting its
target is a measurement; the verdict is your judgement after diagnosing why.

!! Three trials, and **your first signal runs a model, so identical input can
score differently twice.** That's exactly why repeats matter here: a target has
to hold in every trial, not on average.

Changes from the starter version, so you can see what was extended:
  - bodies can be any JSON value (a bare list is a legitimate bad input)
  - API error codes and non-JSON responses are recorded, not just crashes
  - "appeal" and "bad_input" scenario kinds (criteria 4 and 5)
  - a per-trial "target met" line, using each scenario's `check`
  - the report's Target and Run columns are filled in automatically
─────────────────────────────────────────────────────────────────────────────
"""

import argparse
import datetime as dt
import json
import sys
import uuid

import config

# Windows consoles often run a codepage that can't print every character in
# this file's help text. Without this, `--help` ends in a UnicodeEncodeError
# traceback instead of the help — which is a miserable first thing to hit.
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(errors="replace")
    except (AttributeError, ValueError):  # not a normal text stream
        pass


DEFAULT_URL = f"http://{config.HOST}:{config.PORT}"


# ── Small helpers ────────────────────────────────────────────────────────────

def bodies_for(scenario):
    """
    The request bodies one scenario sends.

    A "texts" scenario gets a creator_id made up for it. A "bodies" scenario is
    sent exactly as written, which is how a bad-input criterion says things a
    string can't — no `text` field, a null, something enormous, a bare list.
    """
    if scenario.get("bodies"):
        return list(scenario["bodies"])
    return [
        {"text": text, "creator_id": f"eval_{scenario['name'][:12]}_{i}"}
        for i, text in enumerate(scenario["texts"], 1)
    ]


def describe(body):
    """A short, readable note of what was sent — for the report."""
    if isinstance(body, dict) and set(body) == {"text", "creator_id"} \
            and isinstance(body.get("text"), str):
        text = body["text"]
        return text[:70] if text else "(empty text)"
    return json.dumps(body)[:120]


def send(requests, url, path, body, timeout):
    """
    POST one body and return (status, payload, json_ok). Never raises.

    - status:  the HTTP status code, or None if the request itself failed.
    - payload: the response as a dict ({} if it wasn't a JSON object).
    - json_ok: True only if the response WAS a JSON object. A 500 that comes
               back as an HTML error page is a failure of its own, so it has
               to be distinguishable from a clean JSON error.
    A failed request is returned as status None with the reason in payload, so
    one dead request can't abort a long run halfway through.
    """
    try:
        response = requests.post(f"{url}{path}", json=body, timeout=timeout)
    except Exception as exc:  # noqa: BLE001
        return None, {"exception": f"{type(exc).__name__}: {exc}"}, False
    try:
        payload = response.json() if response.content else {}
    except ValueError:
        return response.status_code, {}, False
    if not isinstance(payload, dict):
        return response.status_code, {}, False
    return response.status_code, payload, True


def read_log(requests, url, timeout):
    """Every audit log entry, oldest first, or None if /log can't be read."""
    try:
        response = requests.get(f"{url}/log", timeout=timeout)
        return response.json()["entries"]
    except Exception:  # noqa: BLE001
        return None


def ping_ok(requests, url, timeout):
    """
    Does the control route still answer? Criterion 5 asks this after a batch
    of malformed requests, because a request that kills the process wouldn't
    show up as a failure on its own response.
    """
    try:
        response = requests.post(f"{url}/ping", json={"message": "alive?"},
                                 timeout=timeout)
        return response.status_code == 200 and response.json().get("ok") is True
    except Exception:  # noqa: BLE001
        return False


# ── Running one trial of one scenario ────────────────────────────────────────

def run_submit_trial(scenario, args, requests):
    """
    One trial of a normal or "bad_input" scenario: POST every body to /submit.

    Returns (results, extras). `results` has one row per request. `extras`
    holds anything measured around the batch rather than on a single request;
    for "bad_input" that is whether /ping still answered and how many
    rejection entries the audit log gained.
    """
    is_bad_input = scenario.get("kind") == "bad_input"

    rejections_before = None
    if is_bad_input:
        entries = read_log(requests, args.url, args.timeout)
        rejections_before = (None if entries is None else
                             sum(1 for e in entries if e.get("event") == "rejected"))

    results = []
    for body in bodies_for(scenario):
        status, payload, json_ok = send(requests, args.url, "/submit", body,
                                        args.timeout)
        row = {
            "status": status,
            "json_ok": json_ok,
            "guess": payload.get("guess"),
            "confidence": payload.get("confidence"),
            "model_score": payload.get("model_score"),
            "style_score": payload.get("style_score"),
            "label": payload.get("label"),
            "sent": describe(body),
        }
        # An error response carries `error` (a code) and `message` (a
        # sentence); keep both, since criterion 5 asks for them.
        if payload.get("error") is not None:
            row["error"] = payload.get("error")
            row["message"] = payload.get("message")
        if "exception" in payload:
            row["exception"] = payload["exception"]
        results.append(row)

    extras = {}
    if is_bad_input:
        entries = read_log(requests, args.url, args.timeout)
        rejections_after = (None if entries is None else
                            sum(1 for e in entries if e.get("event") == "rejected"))
        extras["alive_after"] = ping_ok(requests, args.url, args.timeout)
        extras["new_rejections"] = (
            None if rejections_before is None or rejections_after is None
            else rejections_after - rejections_before
        )
    return results, extras


def run_appeal_trial(scenario, args, requests):
    """
    One trial of the appeal-path scenario (criterion 4).

    An appeal can't be tested with text alone: it needs a real submission
    first, then an appeal that quotes the content_id that came back. So for
    each text this does, in order:

        submit  ->  read the log  ->  appeal  ->  read the log again

    and compares the two reads. That is how "the original decision stays
    exactly where it was" and "the appeal sits after it" become checkable
    facts instead of hopes. Then it appeals against ids that don't exist, which
    must be refused and must leave no appeal entry behind.
    """
    results = []

    for i, text in enumerate(scenario["texts"], 1):
        body = {"text": text, "creator_id": f"eval_{scenario['name'][:12]}_{i}"}
        status, payload, _ = send(requests, args.url, "/submit", body, args.timeout)
        content_id = payload.get("content_id")
        row = {"kind": "appeal", "sent": describe(body),
               "submit_status": status, "content_id": content_id}

        if not content_id:
            # Nothing to appeal against. Record that and move on rather than
            # crashing, so the report shows exactly which submission failed.
            row["note"] = "submit returned no content_id, so nothing to appeal"
            results.append(row)
            continue

        before = [e for e in (read_log(requests, args.url, args.timeout) or [])
                  if e.get("content_id") == content_id]

        reasoning = f"eval appeal {i}: I wrote this myself."
        appeal_status, appeal_payload, _ = send(
            requests, args.url, "/appeal",
            {"content_id": content_id, "reasoning": reasoning}, args.timeout)

        after = [e for e in (read_log(requests, args.url, args.timeout) or [])
                 if e.get("content_id") == content_id]
        new_entries = after[len(before):]

        row.update({
            "appeal_status": appeal_status,
            # What the service says the item's status now is.
            "state": appeal_payload.get("status"),
            # The entries that existed before must be untouched and still
            # first: the log is append-only, so a rewritten decision fails
            # this even if the appeal itself was recorded.
            "decision_unchanged": bool(before) and after[:len(before)] == before,
            # Exactly the appeal we sent must have been appended after them.
            "appeal_logged": any(
                e.get("event") == "appeal"
                and e.get("reasoning") == reasoning
                and e.get("status") == "under_review"
                for e in new_entries),
        })
        results.append(row)

    # Appeals against ids that were never issued. A unique prefix per trial
    # means a previous trial's rows can't be mistaken for this trial's.
    run_id = uuid.uuid4().hex[:8]
    for k in range(1, scenario.get("unknown_ids", 0) + 1):
        fake_id = f"eval_unknown_{run_id}_{k}"
        appeal_status, _, _ = send(
            requests, args.url, "/appeal",
            {"content_id": fake_id, "reasoning": "eval: this id does not exist."},
            args.timeout)
        entries = read_log(requests, args.url, args.timeout) or []
        results.append({
            "kind": "unknown",
            "content_id": fake_id,
            "appeal_status": appeal_status,
            # A refused appeal must not leave an appeal entry behind.
            "appeal_logged": any(e.get("content_id") == fake_id for e in entries),
        })

    return results, {}


def run_trial(scenario, args, requests):
    """Pick the right runner for this kind of scenario."""
    if scenario.get("kind") == "appeal":
        return run_appeal_trial(scenario, args, requests)
    return run_submit_trial(scenario, args, requests)


def evaluate(scenario, results, extras):
    """
    Ask the scenario's `check` whether this trial met its target.

    Returns (met, note): met is True, False, or None if the scenario defines
    no check. A check that raises counts as a miss with the reason attached,
    because a crashed check must never read as a pass.
    """
    check = scenario.get("check")
    if check is None:
        return None, "no check defined for this scenario"
    try:
        met, note = check(results, extras)
        return bool(met), note
    except Exception as exc:  # noqa: BLE001
        return False, f"check crashed: {type(exc).__name__}: {exc}"


def trial_line(scenario, results):
    """The one-line summary of what came back, shown while the run goes."""
    if scenario.get("kind") == "appeal":
        return f"{len(results)} requests"
    return ", ".join(r.get("guess") or str(r.get("status") or "-") for r in results)


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--trials", type=int, default=3)
    parser.add_argument("--label", default="")
    parser.add_argument("--url", default=DEFAULT_URL)
    parser.add_argument("--timeout", type=float, default=90.0)
    args = parser.parse_args()

    try:
        import requests
    except ImportError:
        print("The `requests` package isn't installed.\n"
              "Run: pip install -r requirements.txt", file=sys.stderr)
        sys.exit(1)

    try:
        import scenarios
    except ImportError:
        print("No scenarios.py found. Milestone 3 starts by filling it in.",
              file=sys.stderr)
        sys.exit(1)

    # Fail before a long run, not during one.
    problems = scenarios.validate()
    if problems:
        print("scenarios.py has problems:\n", file=sys.stderr)
        for problem in problems:
            print(f"  - {problem}", file=sys.stderr)
        sys.exit(1)

    try:
        requests.get(f"{args.url}/health", timeout=5)
    except Exception:  # noqa: BLE001
        print(f"Nothing answering at {args.url}. Start it:  python app.py",
              file=sys.stderr)
        sys.exit(1)

    if args.trials < 3:
        print(f"!! {args.trials} trial(s). The submission asks for three.\n")

    rows = []
    for scenario in scenarios.SCENARIOS:
        print(f"\n{scenario['name']}  (criterion {scenario.get('criterion') or '-'})")

        trials, outcomes = [], []
        for trial in range(1, args.trials + 1):
            results, extras = run_trial(scenario, args, requests)
            met, note = evaluate(scenario, results, extras)

            trials.append({"results": results, "extras": extras})
            outcomes.append((met, note))

            verdict = {True: "yes", False: "NO", None: "n/a"}[met]
            print(f"  trial {trial}: {trial_line(scenario, results)}")
            print(f"           target met: {verdict} - {note}")

        rows.append({"scenario": scenario, "trials": trials, "outcomes": outcomes})

        held = all(met for met, _ in outcomes) if all(
            met is not None for met, _ in outcomes) else None
        if held is not None:
            print(f"  held in all {args.trials} trials: {'yes' if held else 'NO'}")

    write_report(rows, args)


def write_report(rows, args):
    config.RESULTS_DIR.mkdir(exist_ok=True)
    stamp = dt.datetime.now().strftime("%Y-%m-%d_%H%M")
    label = f"_{args.label}" if args.label else ""
    path = config.RESULTS_DIR / f"run_{stamp}{label}.md"

    n = args.trials
    headers = " | ".join(f"Run {i}" for i in range(1, n + 1))
    divider = "|".join(["---"] * n)

    lines = [
        f"# Run log{f' — {args.label}' if args.label else ''}",
        "",
        "- Produced by: `run_eval.py::main`",
        "- Service: `app.py::submit` · scoring: `scoring.py::combine_signals`",
        f"- {n} trials per criterion · {dt.datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "Target and Run are filled in from `scenarios.py`: each Run cell says",
        "whether that trial met the target. Verdict is left blank on purpose,",
        "because it is your judgement after diagnosing why a trial missed.",
        "",
        f"| Criterion | Target | {headers} | Verdict |",
        f"|---|---|{divider}|---|",
    ]

    for row in rows:
        scenario = row["scenario"]
        number = scenario.get("criterion")
        name = f"{number}. {scenario['name']}" if number else scenario["name"]
        target = scenario.get("target", "").replace("|", "/")
        cells = " | ".join({True: "met", False: "missed", None: "-"}[met]
                           for met, _ in row["outcomes"])
        lines.append(f"| {name} | {target} | {cells} |  |")

    lines += ["", "---", "", "## What actually came back", "",
              "Real output. Paste the relevant parts into your README — the rubric",
              "asks for the actual JSON, not a description of it.", ""]

    for row in rows:
        scenario = row["scenario"]
        lines += [f"### {scenario['name']}", ""]
        for trial_number, (trial, (met, note)) in enumerate(
                zip(row["trials"], row["outcomes"]), 1):
            lines += [f"**Trial {trial_number}** - {note}", "", "```json",
                      json.dumps(trial["results"], indent=2), "```", ""]
            if trial["extras"]:
                lines += ["Measured around the batch:", "", "```json",
                          json.dumps(trial["extras"], indent=2), "```", ""]

    path.write_text("\n".join(lines), encoding="utf-8")
    try:
        shown = path.relative_to(config.ROOT)
    except ValueError:  # results dir was pointed somewhere outside the repo
        shown = path
    print(f"\nWrote {shown}")
    print("Commit it. It's the evidence the test actually happened.")


if __name__ == "__main__":
    main()
