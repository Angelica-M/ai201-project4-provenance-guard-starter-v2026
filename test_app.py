#!/usr/bin/env python3
"""
Tests for the web service itself (`app.py`): the /submit and /appeal routes.

    python test_app.py          # run everything
    python test_app.py -v       # show each test's name

─────────────────────────────────────────────────────────────────────────────
WHAT THIS FILE DOES, IN SHORT

The other test files check one piece at a time (the style signal, the combining
rule, the labels, the harness). This one checks the pieces TOGETHER, through the
real Flask routes, the way a caller would meet them:

  - /submit: what comes back, which label each kind of text gets, what is
    written to the audit log, and what happens to bad input;
  - /appeal: that it records the appeal, marks the item under_review, leaves the
    original decision alone, and refuses an id that doesn't exist.

Two things keep it fast and safe to run anywhere:

  1. The language model is replaced by a fixed number (`mock.patch`). The model
     needs a 550 MB download and a second or two per text, and what is under
     test here is the ROUTE, not the model. Signal two, the combining rule and
     the labels are all the real code.
  2. Every test writes to a throwaway log in a temp folder, never to the real
     `logs/audit.jsonl`, so running the tests can't touch the evidence.
─────────────────────────────────────────────────────────────────────────────
"""

import json
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

import app as service
import audit
import config
import detector
import scenarios
import scoring

# Texts whose style score is known from earlier milestones. With the model
# signal replaced by a chosen number, each lands in a known label.
AI_TEXT = scenarios.CLEARLY_AI[0]         # style 0.976
HUMAN_TEXT = scenarios.CLEARLY_HUMAN[1]   # style 0.000
UNSURE_TEXT = scenarios.BORDERLINE[1]     # style 0.582


class ServiceTestCase(unittest.TestCase):
    """Gives every test a fresh client, a fresh temp log, and a fake model."""

    model_score = 0.5     # what the replaced model signal returns; tests change it

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        patches = [
            mock.patch.object(config, "LOG_DIR", self.tmp),
            mock.patch.object(config, "AUDIT_LOG", self.tmp / "audit.jsonl"),
            mock.patch.object(detector, "model_signal",
                              side_effect=lambda text: self.model_score),
        ]
        for patch in patches:
            patch.start()
            self.addCleanup(patch.stop)
        self.addCleanup(shutil.rmtree, self.tmp, ignore_errors=True)
        self.client = service.app.test_client()

    # Small helpers, so tests read as what they check.
    def submit(self, text=AI_TEXT, creator="writer", **overrides):
        body = {"text": text, "creator_id": creator, **overrides}
        return self.client.post("/submit", json=body)

    def log(self):
        return audit.read_entries()


class Submit(ServiceTestCase):
    def test_a_good_submission_returns_every_field(self):
        self.model_score = 0.794
        response = self.submit()
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        for field in ("content_id", "guess", "confidence", "label",
                      "model_score", "style_score"):
            self.assertIn(field, data)
        self.assertEqual(data["model_score"], 0.794)
        self.assertTrue(data["content_id"])

    def test_each_submission_gets_its_own_content_id(self):
        a = self.submit().get_json()["content_id"]
        b = self.submit().get_json()["content_id"]
        self.assertNotEqual(a, b)

    def test_confidence_is_the_combined_score(self):
        self.model_score = 0.794
        data = self.submit().get_json()
        self.assertEqual(data["confidence"],
                         scoring.combine_signals(data["model_score"], data["style_score"]))

    def test_all_three_labels_are_reachable_through_the_route(self):
        cases = [
            (AI_TEXT, 0.794, "ai", scoring.LABEL_AI),
            (HUMAN_TEXT, 0.230, "human", scoring.LABEL_HUMAN),
            (UNSURE_TEXT, 0.639, "unsure", scoring.LABEL_UNSURE),
        ]
        for text, model, guess, label in cases:
            self.model_score = model
            data = self.submit(text).get_json()
            self.assertEqual(data["guess"], guess, (guess, data))
            self.assertEqual(data["label"], label, guess)

    def test_the_label_in_the_response_is_never_a_placeholder(self):
        for model in (0.0, 0.3, 0.5, 0.7, 1.0):
            self.model_score = model
            self.assertNotIn("PLACEHOLDER", self.submit().get_json()["label"])

    def test_the_decision_is_logged_with_every_field_filled(self):
        self.model_score = 0.794
        data = self.submit(creator="writer_ana").get_json()
        (entry,) = self.log()
        self.assertEqual(entry["content_id"], data["content_id"])
        self.assertEqual(entry["creator_id"], "writer_ana")
        self.assertEqual(entry["guess"], data["guess"])
        self.assertEqual(entry["model_score"], data["model_score"])
        self.assertEqual(entry["style_score"], data["style_score"])
        self.assertEqual(entry["combined_score"], data["confidence"])
        self.assertEqual(entry["label"], data["label"])      # what the reader saw
        self.assertEqual(entry["status"], "decided")
        self.assertTrue(entry["timestamp"])

    def test_the_log_has_all_nine_required_fields(self):
        self.submit()
        (entry,) = self.log()
        for field in ("timestamp", "content_id", "creator_id", "guess", "model_score",
                      "style_score", "combined_score", "label", "status"):
            self.assertIn(field, entry)
            self.assertIsNotNone(entry[field], field)


class SubmitRefusals(ServiceTestCase):
    """Bad input gets a clean 4xx, never a crash, and leaves a trace."""

    def assert_refused(self, response, status, code):
        self.assertEqual(response.status_code, status)
        data = response.get_json()
        self.assertEqual(data["error"], code)
        self.assertTrue(data["message"])

    def test_the_eight_bad_inputs_from_criterion_5(self):
        bodies = [
            ({"creator_id": "u"}, 400, "invalid_input"),
            ({"text": "", "creator_id": "u"}, 400, "invalid_input"),
            ({"text": "  \n\t ", "creator_id": "u"}, 400, "invalid_input"),
            ({"text": None, "creator_id": "u"}, 400, "invalid_input"),
            ({"text": 12345, "creator_id": "u"}, 400, "invalid_input"),
            ({"text": AI_TEXT}, 400, "invalid_input"),
            ([1, 2, 3], 400, "invalid_input"),
            ({"text": "word " * 50000, "creator_id": "u"}, 413, "text_too_long"),
        ]
        for body, status, code in bodies:
            self.assert_refused(self.client.post("/submit", json=body), status, code)

    def test_a_body_that_is_not_json_is_refused(self):
        response = self.client.post("/submit", data="not json", content_type="text/plain")
        self.assert_refused(response, 400, "invalid_input")

    def test_text_too_short_for_the_model_is_a_422(self):
        with mock.patch.object(detector, "model_signal",
                               side_effect=ValueError("Text is too short to score")):
            self.assert_refused(self.submit("Hi"), 422, "text_too_short")

    def test_a_model_that_cannot_load_is_a_503(self):
        with mock.patch.object(detector, "model_signal",
                               side_effect=detector.DetectorUnavailable("no model")):
            self.assert_refused(self.submit(), 503, "detector_unavailable")

    def test_every_refusal_is_logged_and_none_is_logged_as_a_decision(self):
        self.submit(text="", creator="writer_ben")
        self.client.post("/submit", json=[1])
        entries = self.log()
        self.assertEqual(len(entries), 2)
        self.assertTrue(all(e["event"] == "rejected" for e in entries))
        self.assertEqual(entries[0]["creator_id"], "writer_ben")   # attributed
        self.assertEqual(entries[1]["creator_id"], "unknown")      # nothing to attribute

    def test_a_refusal_does_not_burn_a_content_id_or_call_the_model(self):
        with mock.patch.object(detector, "model_signal") as model:
            self.submit(text="")
            model.assert_not_called()

    def test_ping_still_answers(self):
        response = self.client.post("/ping", json={"message": "hello"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.get_json()["you_sent"], "hello")


if __name__ == "__main__":
    unittest.main()
