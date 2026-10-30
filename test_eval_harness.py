#!/usr/bin/env python3
"""
Tests for the evaluation harness (`run_eval.py` and the checks in `scenarios.py`).

    python test_eval_harness.py          # run everything
    python test_eval_harness.py -v       # show each test's name

─────────────────────────────────────────────────────────────────────────────
WHAT THIS FILE DOES, IN SHORT

The harness measures my service against my five criteria. But a measuring tool
that is itself wrong is worse than none: it can report "target met" when it
wasn't, or crash halfway through a run. This file tests the tool, not the
service. It needs no model, no download and no running `app.py`.

It does that in two layers:

  1. Check functions, directly. Each criterion's `check` gets hand-made results
     right on the line (exactly at the limit, one past it) to prove it says yes
     and no in the right places. This is boundary testing: bugs live at edges.

  2. The whole harness against a STAND-IN SERVICE. A tiny fake of Provenance
     Guard (below) obeys the endpoint contract from Milestone 1 and scores text
     from a lookup table. The real harness runs three trials against it over
     real HTTP. With the fake behaving, every criterion must read "met". Then
     the fake is made to misbehave one way at a time (accuse a writer, rewrite
     the log, skip logging rejections, crash on input) and the matching
     criterion must read "missed". A harness that can't fail proves nothing.

The fake is not the real service and says nothing about how the real one will
score. It exists only so the harness can be proven correct today, before
/submit and /appeal are built.
─────────────────────────────────────────────────────────────────────────────
"""

import contextlib
import io
import logging
import sys
import tempfile
import threading
import unittest
from pathlib import Path
from unittest import mock

from flask import Flask, jsonify, request
from werkzeug.serving import make_server

import config
import run_eval
import scenarios


# ── The stand-in service ─────────────────────────────────────────────────────

# Fixed scores for the known test texts. In the real service these come from
# the two signals; here they are a lookup so the outcome is predictable.
_SCORE_FOR = {}
for _t in scenarios.CLEARLY_AI:
    _SCORE_FOR[_t] = 0.90
for _t in scenarios.CLEARLY_HUMAN:
    _SCORE_FOR[_t] = 0.10
for _t in scenarios.BORDERLINE:
    _SCORE_FOR[_t] = 0.50
for _t in scenarios.OWN_WRITING:
    _SCORE_FOR[_t] = 0.10

LABEL_TEXT = {
    "human": "We think this was probably written by a person.",
    "unsure": "We can't tell whether a person or an AI wrote this.",
    "ai": "This looks like it may have been written by an AI. You can appeal.",
}


def make_fake_service(accuse_own_writing=0, rewrite_log_on_appeal=False,
                      log_rejections=True, crash_on_empty=False,
                      appeal_unknown_ok=False):
    """
    Build a fake Provenance Guard that follows the Milestone 1 contract.

    The keyword arguments switch on one specific misbehaviour each, so a test
    can prove the harness notices it:

      accuse_own_writing     label this many of my own pieces as AI
      rewrite_log_on_appeal  edit the original log entry instead of appending
      log_rejections         write refused requests to the log (contract says yes)
      crash_on_empty         return a 500 HTML page on empty text
      appeal_unknown_ok      accept an appeal on an id that doesn't exist
    """
    app = Flask(__name__)
    log = []
    accused = set(scenarios.OWN_WRITING[:accuse_own_writing])

    def refuse(status, code, message, creator="unknown"):
        if log_rejections:
            log.append({"creator_id": creator, "event": "rejected",
                        "status": "rejected", "reason": code})
        return jsonify({"error": code, "message": message}), status

    @app.post("/ping")
    def ping():
        return jsonify({"ok": True, "service": "provenance-guard-fake"})

    @app.get("/health")
    def health():
        return jsonify({"ok": True})

    @app.get("/log")
    def get_log():
        return jsonify({"count": len(log), "entries": log})

    @app.post("/submit")
    def submit():
        body = request.get_json(silent=True)
        if not isinstance(body, dict):
            return refuse(400, "invalid_input", "Send a JSON object.")
        text, creator = body.get("text"), body.get("creator_id")
        if crash_on_empty and text == "":
            return "<html>Internal Server Error</html>", 500
        if not isinstance(text, str) or not text.strip():
            return refuse(400, "invalid_input", "text must be a non-empty string.")
        if not isinstance(creator, str) or not creator.strip():
            return refuse(400, "invalid_input", "creator_id is required.")
        if len(text) > 20000:
            return refuse(413, "text_too_long", "That text is too long.", creator)

        confidence = 0.90 if text in accused else _SCORE_FOR.get(text, 0.50)
        guess = "ai" if confidence > 0.65 else "human" if confidence < 0.35 else "unsure"
        entry = {"timestamp": "t", "content_id": f"c{len(log) + 1}",
                 "creator_id": creator, "guess": guess,
                 "model_score": confidence, "style_score": confidence,
                 "combined_score": confidence, "label": LABEL_TEXT[guess],
                 "status": "decided"}
        log.append(entry)
        return jsonify({"content_id": entry["content_id"], "guess": guess,
                        "confidence": confidence, "label": LABEL_TEXT[guess],
                        "model_score": confidence, "style_score": confidence})

    @app.post("/appeal")
    def appeal():
        body = request.get_json(silent=True)
        if not isinstance(body, dict) or not body.get("content_id") \
                or not body.get("reasoning"):
            return refuse(400, "invalid_input", "content_id and reasoning are required.")
        cid = body["content_id"]
        decision = next((e for e in log if e.get("content_id") == cid), None)
        if decision is None and not appeal_unknown_ok:
            return refuse(404, "unknown_content_id", "No submission has that id.")
        if rewrite_log_on_appeal and decision is not None:
            decision["status"] = "under_review"      # the forbidden shortcut
        else:
            log.append({"content_id": cid, "event": "appeal",
                        "status": "under_review", "reasoning": body["reasoning"]})
        return jsonify({"content_id": cid, "status": "under_review",
                        "message": "Your appeal has been recorded."})

    return app


@contextlib.contextmanager
def running(app):
    """Serve `app` on a free local port for the duration of a `with` block."""
    # Werkzeug prints one line per request, which would bury the test results.
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    server = make_server("127.0.0.1", 0, app)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield f"http://127.0.0.1:{server.server_port}"
    finally:
        server.shutdown()
        thread.join(timeout=5)


def run_harness(url, trials=3):
    """
    Run the real `run_eval.main()` against `url` and return (stdout, report).

    The report is written to a throwaway folder so tests never leave files in
    the repo's own results/ directory.
    """
    out = io.StringIO()
    with tempfile.TemporaryDirectory() as tmp, \
            mock.patch.object(config, "RESULTS_DIR", Path(tmp)), \
            mock.patch.object(sys, "argv", ["run_eval.py", "--url", url,
                                            "--trials", str(trials), "--label", "t"]), \
            contextlib.redirect_stdout(out):
        run_eval.main()
        report = next(Path(tmp).glob("run_*.md")).read_text(encoding="utf-8")
    return out.getvalue(), report


def scenario_lines(output, name):
    """The 'target met' lines printed for one scenario."""
    lines, inside = [], False
    for line in output.splitlines():
        if line and not line.startswith(" "):
            inside = line.startswith(name)
        elif inside and "target met" in line:
            lines.append(line)
    return lines


# ── Layer 1: the check functions, at their edges ─────────────────────────────

def rows(*guesses, confidence=None, status=200):
    """Make results rows from a list of guesses."""
    return [{"status": status, "guess": g,
             "confidence": confidence if confidence is not None else 0.5,
             "label": run_label(g)} for g in guesses]


def run_label(guess):
    return LABEL_TEXT.get(guess, "")


class FalsePositiveCheck(unittest.TestCase):
    """Criterion 1: at most 1 of 10 labelled AI."""

    def test_zero_and_one_pass_two_fails(self):
        for n_ai, expected in ((0, True), (1, True), (2, False)):
            guesses = ["ai"] * n_ai + ["human"] * (10 - n_ai)
            met, _ = scenarios.check_false_positives(rows(*guesses), {})
            self.assertEqual(met, expected, f"{n_ai} AI labels")

    def test_unsure_is_not_an_accusation(self):
        met, _ = scenarios.check_false_positives(rows(*["unsure"] * 10), {})
        self.assertTrue(met)

    def test_pieces_that_failed_to_score_are_a_miss_not_a_pass(self):
        # 10 rows of status 500 contain zero "ai" guesses; that must not pass.
        met, note = scenarios.check_false_positives(rows(*["human"] * 10, status=500), {})
        self.assertFalse(met)
        self.assertIn("did not score", note)

    def test_wrong_number_of_pieces_is_a_miss(self):
        met, _ = scenarios.check_false_positives(rows(*["human"] * 9), {})
        self.assertFalse(met)


class ScoreSpreadCheck(unittest.TestCase):
    """Criterion 2: gap of at least 0.30, and 4 of 5 per group on their side."""

    @staticmethod
    def results(ai, human):
        return [{"status": 200, "confidence": c} for c in ai + human]

    def test_exactly_on_the_limit_passes(self):
        met, _ = scenarios.check_score_spread(
            self.results([0.65] * 5, [0.35] * 5), {})
        self.assertTrue(met)

    def test_just_under_the_gap_fails(self):
        met, _ = scenarios.check_score_spread(
            self.results([0.649] * 5, [0.35] * 5), {})
        self.assertFalse(met)

    def test_one_stray_per_group_still_passes(self):
        met, _ = scenarios.check_score_spread(
            self.results([0.9, 0.9, 0.9, 0.9, 0.4], [0.1, 0.1, 0.1, 0.1, 0.6]), {})
        self.assertTrue(met)

    def test_two_strays_in_a_group_fails_even_with_a_big_gap(self):
        met, _ = scenarios.check_score_spread(
            self.results([0.99, 0.99, 0.99, 0.4, 0.4], [0.01] * 5), {})
        self.assertFalse(met)

    def test_missing_confidence_is_a_miss(self):
        res = self.results([0.9] * 5, [0.1] * 5)
        res[0]["confidence"] = None
        met, _ = scenarios.check_score_spread(res, {})
        self.assertFalse(met)


class LabelCoverageCheck(unittest.TestCase):
    """Criterion 3: all labels appear, 3 of 4 borderline unsure, real text."""

    @staticmethod
    def results(ai=("ai",) * 4, human=("human",) * 4,
                border=("unsure",) * 4):
        return rows(*ai, *human, *border)

    def test_all_three_present_passes(self):
        met, _ = scenarios.check_label_coverage(self.results(), {})
        self.assertTrue(met)

    def test_one_borderline_miss_still_passes_two_fails(self):
        ok, _ = scenarios.check_label_coverage(
            self.results(border=("unsure", "unsure", "unsure", "ai")), {})
        bad, _ = scenarios.check_label_coverage(
            self.results(border=("unsure", "unsure", "ai", "human")), {})
        self.assertTrue(ok)
        self.assertFalse(bad)

    def test_a_label_that_is_never_produced_fails(self):
        # No clearly-AI input reaches "ai": that label is unreachable.
        met, note = scenarios.check_label_coverage(
            self.results(ai=("unsure",) * 4), {})
        self.assertFalse(met)
        self.assertIn("ai", note)

    def test_placeholder_and_empty_labels_fail(self):
        for bad_text in ("PLACEHOLDER - write the label.", "", None):
            res = self.results()
            res[0]["label"] = bad_text
            met, _ = scenarios.check_label_coverage(res, {})
            self.assertFalse(met, repr(bad_text))

    def test_two_different_texts_for_one_guess_fails(self):
        res = self.results()
        res[1]["label"] = "Something else entirely."
        met, _ = scenarios.check_label_coverage(res, {})
        self.assertFalse(met)

    def test_two_guesses_sharing_one_text_fails(self):
        res = self.results()
        for r in res:
            r["label"] = "Same words for everyone."
        met, _ = scenarios.check_label_coverage(res, {})
        self.assertFalse(met)


class AppealPathCheck(unittest.TestCase):
    """Criterion 4: 10/10 appeals recorded, 5/5 unknown ids refused."""

    @staticmethod
    def good_real():
        return {"kind": "appeal", "appeal_status": 200, "state": "under_review",
                "appeal_logged": True, "decision_unchanged": True}

    @staticmethod
    def good_fake():
        return {"kind": "unknown", "appeal_status": 404, "appeal_logged": False}

    def results(self):
        return [self.good_real() for _ in range(10)] + [self.good_fake() for _ in range(5)]

    def test_perfect_run_passes(self):
        met, _ = scenarios.check_appeal_path(self.results(), {})
        self.assertTrue(met)

    def test_every_failure_mode_is_caught_separately(self):
        broken = {
            "appeal wrong status": (0, "appeal_status", 500),
            "status not under_review": (0, "state", "decided"),
            "appeal not logged": (0, "appeal_logged", False),
            "decision was rewritten": (0, "decision_unchanged", False),
            "unknown id accepted": (10, "appeal_status", 200),
            "unknown id left a log entry": (10, "appeal_logged", True),
        }
        for name, (index, key, value) in broken.items():
            res = self.results()
            res[index][key] = value
            met, _ = scenarios.check_appeal_path(res, {})
            self.assertFalse(met, name)

    def test_too_few_requests_is_a_miss(self):
        met, _ = scenarios.check_appeal_path(self.results()[:-1], {})
        self.assertFalse(met)


class BadInputCheck(unittest.TestCase):
    """Criterion 5: 8/8 clean JSON 4xx, no 500, alive, 8 rejections logged."""

    @staticmethod
    def results(status=400):
        return [{"status": status, "json_ok": True, "error": "invalid_input",
                 "message": "Nope."} for _ in range(8)]

    GOOD = {"alive_after": True, "new_rejections": 8}

    def test_perfect_run_passes(self):
        met, _ = scenarios.check_bad_input(self.results(), self.GOOD)
        self.assertTrue(met)

    def test_413_and_422_count_as_clean(self):
        res = self.results()
        res[0]["status"], res[1]["status"] = 413, 422
        met, _ = scenarios.check_bad_input(res, self.GOOD)
        self.assertTrue(met)

    def test_each_failure_mode_is_caught(self):
        cases = {}
        res = self.results(); res[0]["status"] = 500
        cases["a 500"] = (res, self.GOOD)
        res = self.results(); res[0]["status"] = None
        cases["no response at all"] = (res, self.GOOD)
        res = self.results(); res[0]["status"] = 200
        cases["accepted bad input"] = (res, self.GOOD)
        res = self.results(); res[0]["json_ok"] = False
        cases["HTML error page"] = (res, self.GOOD)
        res = self.results(); res[0].pop("error")
        cases["no error code"] = (res, self.GOOD)
        res = self.results(); res[0].pop("message")
        cases["no message"] = (res, self.GOOD)
        cases["service died"] = (self.results(), {**self.GOOD, "alive_after": False})
        cases["rejections not logged"] = (self.results(), {**self.GOOD, "new_rejections": 0})
        cases["log unreadable"] = (self.results(), {**self.GOOD, "new_rejections": None})
        cases["only 7 requests"] = (self.results()[:7], self.GOOD)
        for name, (res, extras) in cases.items():
            met, _ = scenarios.check_bad_input(res, extras)
            self.assertFalse(met, name)


class ScenarioFile(unittest.TestCase):
    """scenarios.py itself must be well-formed and match criteria.md."""

    def test_validates_clean(self):
        self.assertEqual(scenarios.validate(), [])

    def test_one_scenario_per_criterion_each_with_a_check_and_target(self):
        self.assertEqual(sorted(s["criterion"] for s in scenarios.SCENARIOS), [1, 2, 3, 4, 5])
        for s in scenarios.SCENARIOS:
            self.assertTrue(callable(s.get("check")), s["name"])
            self.assertTrue(s.get("target"), s["name"])

    def test_set_sizes_match_the_criteria(self):
        by_name = {s["name"]: s for s in scenarios.SCENARIOS}
        self.assertEqual(len(scenarios.OWN_WRITING), 10)
        self.assertEqual(len(by_name["score spread"]["texts"]), 10)
        self.assertEqual(len(by_name["label coverage"]["texts"]), 12)
        self.assertEqual(len(by_name["appeal path"]["texts"]), 10)
        self.assertEqual(by_name["appeal path"]["unknown_ids"], 5)
        self.assertEqual(len(by_name["bad input"]["bodies"]), 8)

    def test_validate_catches_real_mistakes(self):
        bad = [
            {"name": "x", "texts": []},
            {"name": "x", "texts": ["a"], "bodies": [{}]},
            {"name": "x", "texts": ["REPLACE ME please"]},
            {"name": "x", "bodies": ["a string is not a body"]},
            {"name": "x", "kind": "mystery", "texts": ["a"]},
            {"name": "x", "kind": "appeal", "bodies": [{}]},
        ]
        for scenario in bad:
            with mock.patch.object(scenarios, "SCENARIOS", [scenario]):
                self.assertTrue(scenarios.validate(), scenario)

    def test_a_bare_list_is_an_allowed_body(self):
        with mock.patch.object(scenarios, "SCENARIOS", [{"name": "x", "bodies": [[1, 2]]}]):
            self.assertEqual(scenarios.validate(), [])


# ── Layer 2: the whole harness against the stand-in service ──────────────────

class WholeHarness(unittest.TestCase):
    """Real run_eval.main(), real HTTP, three trials, fake service."""

    def assert_all_met(self, output, name):
        lines = scenario_lines(output, name)
        self.assertEqual(len(lines), 3, f"{name}: expected 3 trial lines\n{output}")
        for line in lines:
            self.assertIn("target met: yes", line, f"{name}\n{output}")

    def assert_missed(self, output, name):
        lines = scenario_lines(output, name)
        self.assertEqual(len(lines), 3, f"{name}: expected 3 trial lines\n{output}")
        for line in lines:
            self.assertIn("target met: NO", line, f"{name}\n{output}")

    def test_a_service_that_follows_the_contract_meets_every_criterion(self):
        with running(make_fake_service()) as url:
            output, report = run_harness(url)
        for name in ("my own writing", "score spread", "label coverage",
                     "appeal path", "bad input"):
            self.assert_all_met(output, name)
        self.assertEqual(output.count("held in all 3 trials: yes"), 5)
        # The report fills Target and Run in but leaves Verdict for the human.
        self.assertIn("| 1. my own writing | At most 1 of 10", report)
        self.assertIn("| met | met | met |  |", report)
        self.assertNotIn("| missed", report)  # a table cell, not the prose

    def test_report_keeps_the_raw_responses(self):
        with running(make_fake_service()) as url:
            _, report = run_harness(url)
        self.assertIn("## What actually came back", report)
        self.assertIn('"content_id"', report)
        self.assertIn('"new_rejections": 8', report)

    def test_two_wrongly_accused_writers_miss_criterion_1_only(self):
        with running(make_fake_service(accuse_own_writing=2)) as url:
            output, _ = run_harness(url)
        self.assert_missed(output, "my own writing")
        self.assert_all_met(output, "score spread")

    def test_one_wrongly_accused_writer_is_still_within_target(self):
        with running(make_fake_service(accuse_own_writing=1)) as url:
            output, _ = run_harness(url)
        self.assert_all_met(output, "my own writing")

    def test_rewriting_the_log_instead_of_appending_misses_criterion_4(self):
        with running(make_fake_service(rewrite_log_on_appeal=True)) as url:
            output, _ = run_harness(url)
        self.assert_missed(output, "appeal path")
        self.assert_all_met(output, "bad input")

    def test_accepting_an_appeal_on_an_unknown_id_misses_criterion_4(self):
        with running(make_fake_service(appeal_unknown_ok=True)) as url:
            output, _ = run_harness(url)
        self.assert_missed(output, "appeal path")

    def test_not_logging_rejections_misses_criterion_5(self):
        with running(make_fake_service(log_rejections=False)) as url:
            output, _ = run_harness(url)
        self.assert_missed(output, "bad input")

    def test_a_500_on_bad_input_misses_criterion_5(self):
        with running(make_fake_service(crash_on_empty=True)) as url:
            output, _ = run_harness(url)
        self.assert_missed(output, "bad input")

    def test_the_unbuilt_starter_service_misses_without_crashing(self):
        """
        The starter's routes return 501 and nothing else. The harness must
        finish the whole run and report misses, not die on the first oddity.
        """
        starter = Flask(__name__)

        @starter.post("/submit")
        def submit():
            return jsonify({"error": "not_implemented", "message": "Not built."}), 501

        @starter.post("/appeal")
        def appeal():
            return jsonify({"error": "not_implemented", "message": "Not built."}), 501

        @starter.get("/health")
        def health():
            return jsonify({"ok": True})

        @starter.get("/log")
        def log():
            return jsonify({"count": 0, "entries": []})

        @starter.post("/ping")
        def ping():
            return jsonify({"ok": True})

        with running(starter) as url:
            output, report = run_harness(url)
        for name in ("my own writing", "score spread", "label coverage",
                     "appeal path", "bad input"):
            self.assert_missed(output, name)
        self.assertNotIn("met | met", report)

    def test_no_service_running_exits_with_a_clear_message(self):
        err = io.StringIO()
        with mock.patch.object(sys, "argv", ["run_eval.py", "--url", "http://127.0.0.1:9"]), \
                contextlib.redirect_stderr(err), self.assertRaises(SystemExit) as caught:
            run_eval.main()
        self.assertEqual(caught.exception.code, 1)
        self.assertIn("Nothing answering", err.getvalue())


if __name__ == "__main__":
    unittest.main()
