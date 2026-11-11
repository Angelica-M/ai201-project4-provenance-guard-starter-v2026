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
    original decision alone, and refuses an id that doesn't exist;
  - rate limiting on /submit: that the limit bites at the number chosen in
    config.py, that a rejection leaves a trace, and that nothing else is limited.

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

    # Rate limiting is ON in the real service (config.RATE_LIMITING_ENABLED), and
    # the limit is 5 a minute per creator. Most tests submit more than that as
    # one creator and are about something else, so they run with limiting off.
    # Tests that are ABOUT the limiter set `limiting = True`.
    limiting = False

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

        # The limiter keeps its counts in memory for the life of the process, so
        # clear them before AND after each test: otherwise one test's submissions
        # would count against the next test's creator.
        service.limiter.enabled = self.limiting
        service.limiter.reset()
        self.addCleanup(service.limiter.reset)
        self.addCleanup(setattr, service.limiter, "enabled", True)

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

    def test_control_characters_and_punctuation_only_text_are_refused(self):
        self.assert_refused(self.submit("\x00\x01 test"), 400, "invalid_input")
        self.assert_refused(self.submit("!!! ??? ... ,,, ;;; --- ((( )))"),
                            400, "invalid_input")

    def test_non_latin_alphanumeric_text_is_accepted(self):
        response = self.submit("هذا نص عربي صالح لاختبار النظام")
        self.assertEqual(response.status_code, 200)

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


class Appeal(ServiceTestCase):
    """POST /appeal: record it, mark it under_review, never touch the decision."""

    REASON = "I wrote this myself, in one sitting, for a class."

    def submitted(self, creator="writer_ana"):
        """Submit once and hand back the content_id, as a real caller would."""
        return self.submit(creator=creator).get_json()["content_id"]

    def appeal(self, content_id, reasoning=None, **extra):
        body = {"content_id": content_id,
                "reasoning": self.REASON if reasoning is None else reasoning, **extra}
        return self.client.post("/appeal", json=body)

    def test_an_appeal_on_a_real_id_is_confirmed_as_under_review(self):
        cid = self.submitted()
        response = self.appeal(cid)
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["content_id"], cid)
        self.assertEqual(data["status"], "under_review")
        self.assertTrue(data["message"])

    def test_the_appeal_is_written_to_the_log_after_the_decision(self):
        cid = self.submitted()
        self.appeal(cid)
        decision, appeal = self.log()
        self.assertNotIn("event", decision)
        self.assertEqual(appeal["event"], "appeal")
        self.assertEqual(appeal["content_id"], cid)
        self.assertEqual(appeal["status"], "under_review")
        self.assertEqual(appeal["reasoning"], self.REASON)
        self.assertTrue(appeal["timestamp"])

    def test_the_original_decision_is_left_exactly_as_it_was(self):
        cid = self.submitted()
        before = self.log()[0]
        self.appeal(cid)
        self.assertEqual(self.log()[0], before)           # unchanged, still first
        self.assertEqual(self.log()[0]["status"], "decided")

    def test_the_appeal_is_filed_under_the_original_writer_not_the_request(self):
        cid = self.submitted(creator="writer_ana")
        self.appeal(cid, creator_id="someone_else")        # an attempt to spoof
        self.assertEqual(self.log()[1]["creator_id"], "writer_ana")

    def test_appeals_touch_only_their_own_decision(self):
        first, second = self.submitted("a"), self.submitted("b")
        self.appeal(first)
        by_id = {e["content_id"]: [] for e in self.log()}
        for entry in self.log():
            by_id[entry["content_id"]].append(entry)
        self.assertEqual(len(by_id[first]), 2)
        self.assertEqual(len(by_id[second]), 1)

    def test_appealing_twice_records_both_and_stays_under_review(self):
        cid = self.submitted()
        self.assertEqual(self.appeal(cid, "first reason").status_code, 200)
        self.assertEqual(self.appeal(cid, "second reason").status_code, 200)
        appeals = [e for e in self.log() if e.get("event") == "appeal"]
        self.assertEqual([a["reasoning"] for a in appeals], ["first reason", "second reason"])
        self.assertTrue(all(a["status"] == "under_review" for a in appeals))

    def test_an_unknown_id_is_a_404_and_writes_no_appeal(self):
        response = self.appeal("never-issued")
        self.assertEqual(response.status_code, 404)
        self.assertEqual(response.get_json()["error"], "unknown_content_id")
        self.assertFalse([e for e in self.log() if e.get("event") == "appeal"])

    def test_a_typo_in_the_id_is_caught_loudly_not_silently(self):
        # The most common way this endpoint "doesn't work": one wrong character.
        cid = self.submitted()
        typo = cid[:-1] + ("0" if cid[-1] != "0" else "1")
        response = self.appeal(typo)
        self.assertEqual(response.status_code, 404)
        self.assertIn("copied exactly", response.get_json()["message"])
        self.assertFalse([e for e in self.log() if e.get("event") == "appeal"])

    def test_a_refused_appeal_is_still_logged_as_a_rejection(self):
        self.appeal("never-issued")
        (entry,) = self.log()
        self.assertEqual(entry["event"], "rejected")
        self.assertEqual(entry["reason"], "unknown_content_id")

    def test_bad_appeal_bodies_get_a_clean_400(self):
        cid = self.submitted()
        bad = [
            {"reasoning": self.REASON},                       # no content_id
            {"content_id": cid},                              # no reasoning
            {"content_id": "", "reasoning": self.REASON},
            {"content_id": cid, "reasoning": ""},
            {"content_id": cid, "reasoning": "   \n "},
            {"content_id": 123, "reasoning": self.REASON},
            {"content_id": cid, "reasoning": ["a list"]},
            {"content_id": None, "reasoning": None},
            [cid],
        ]
        for body in bad:
            response = self.client.post("/appeal", json=body)
            self.assertEqual(response.status_code, 400, body)
            self.assertEqual(response.get_json()["error"], "invalid_input", body)
        # And none of them recorded an appeal.
        self.assertFalse([e for e in self.log() if e.get("event") == "appeal"])

    def test_a_body_that_is_not_json_is_refused(self):
        response = self.client.post("/appeal", data="nope", content_type="text/plain")
        self.assertEqual(response.status_code, 400)

    def test_an_enormous_reasoning_is_refused_with_a_413(self):
        cid = self.submitted()
        response = self.appeal(cid, "x" * (config.MAX_REASONING_CHARS + 1))
        self.assertEqual(response.status_code, 413)
        self.assertFalse([e for e in self.log() if e.get("event") == "appeal"])

    def test_reasoning_at_exactly_the_limit_is_accepted(self):
        cid = self.submitted()
        self.assertEqual(self.appeal(cid, "x" * config.MAX_REASONING_CHARS).status_code, 200)

    def test_the_log_stays_readable_json_after_unusual_reasoning(self):
        cid = self.submitted()
        odd = 'Quotes "like this", a newline\nand unicode: café — done.'
        self.appeal(cid, odd)
        self.assertEqual(self.log()[1]["reasoning"], odd)
        for line in (self.tmp / "audit.jsonl").read_text(encoding="utf-8").splitlines():
            json.loads(line)                                # every line parses

    def test_a_refusal_does_not_break_the_service(self):
        self.appeal("never-issued")
        self.assertEqual(self.client.post("/ping", json={"message": "x"}).status_code, 200)


class RateLimiting(ServiceTestCase):
    """POST /submit is limited per caller; nothing else is."""

    limiting = True
    PER_MINUTE = config.RATE_LIMIT_PER_MINUTE

    def test_the_limits_are_the_ones_chosen_in_config(self):
        # Pinned here so a change to the numbers is a decision, not an accident.
        self.assertTrue(config.RATE_LIMITING_ENABLED)
        self.assertEqual(config.RATE_LIMIT_PER_MINUTE, 5)
        self.assertEqual(config.RATE_LIMIT_PER_DAY, 50)

    def test_the_limiter_is_really_attached_to_submit(self):
        # Config being "on" is not enough; the decorator has to be on the route.
        # A real limiter (not the do-nothing stand-in) must be what app.py holds.
        self.assertNotEqual(type(service.limiter).__name__, "_LimiterOff")
        self.assertTrue(service.limiter.enabled)

    def test_the_first_submissions_pass_and_the_next_is_refused(self):
        codes = [self.submit(creator="flooder").status_code for _ in range(self.PER_MINUTE + 3)]
        self.assertEqual(codes, [200] * self.PER_MINUTE + [429] * 3)

    def test_a_refusal_has_the_standard_error_shape_and_names_the_limit(self):
        for _ in range(self.PER_MINUTE):
            self.submit(creator="flooder")
        response = self.submit(creator="flooder")
        self.assertEqual(response.status_code, 429)
        data = response.get_json()
        self.assertEqual(data["error"], "rate_limited")
        self.assertTrue(data["message"])
        self.assertIn("minute", data["limit"])

    def test_every_rate_limited_request_is_written_to_the_log(self):
        for _ in range(self.PER_MINUTE + 4):
            self.submit(creator="flooder")
        rejections = [e for e in self.log() if e.get("event") == "rejected"]
        self.assertEqual(len(rejections), 4)
        for entry in rejections:
            self.assertEqual(entry["reason"], "rate_limited")
            self.assertEqual(entry["creator_id"], "flooder")
            self.assertEqual(entry["status"], "rejected")
            self.assertTrue(entry["limit"])
            self.assertTrue(entry["timestamp"])

    def test_limited_requests_never_reach_the_model_or_make_a_decision(self):
        for _ in range(self.PER_MINUTE):
            self.submit(creator="flooder")
        with mock.patch.object(detector, "model_signal") as model:
            self.submit(creator="flooder")
            model.assert_not_called()
        decisions = [e for e in self.log() if "event" not in e]
        self.assertEqual(len(decisions), self.PER_MINUTE)

    def test_one_creator_being_limited_does_not_limit_another(self):
        for _ in range(self.PER_MINUTE + 2):
            self.submit(creator="flooder")
        self.assertEqual(self.submit(creator="a_different_writer").status_code, 200)

    def test_requests_with_no_usable_creator_are_counted_by_address(self):
        # No creator_id to count against, so the caller's address is used; these
        # share one bucket. They are refused (400) until the bucket runs out and
        # then limited (429), and never crash the key function.
        bodies = [{"text": "hello there"}, {"text": "hi", "creator_id": ""},
                  {"text": "hi", "creator_id": 7}, [1, 2], {"text": "x"}]
        codes = [self.client.post("/submit", json=b).status_code for b in bodies]
        codes += [self.client.post("/submit", json={"text": "x"}).status_code]
        self.assertEqual(codes[:self.PER_MINUTE], [400] * self.PER_MINUTE)
        self.assertEqual(codes[self.PER_MINUTE], 429)

    def test_a_body_that_is_not_json_does_not_crash_the_limiter(self):
        response = self.client.post("/submit", data="nope", content_type="text/plain")
        self.assertEqual(response.status_code, 400)

    def test_refused_requests_count_toward_the_limit(self):
        # A script can't dodge the limit by sending junk: every request to
        # /submit is counted, whether or not it was a good one.
        for _ in range(self.PER_MINUTE):
            self.submit(text="", creator="prober")             # each a 400
        self.assertEqual(self.submit(creator="prober").status_code, 429)

    def test_the_other_routes_are_not_limited(self):
        cid = self.submit(creator="writer").get_json()["content_id"]
        for _ in range(self.PER_MINUTE * 3):
            self.assertEqual(self.client.post("/ping", json={"message": "x"}).status_code, 200)
            self.assertEqual(self.client.get("/health").status_code, 200)
            self.assertEqual(self.client.get("/log").status_code, 200)
        for _ in range(self.PER_MINUTE * 3):
            response = self.client.post("/appeal", json={"content_id": cid, "reasoning": "again"})
            self.assertEqual(response.status_code, 200)

    def test_a_limited_writer_can_still_appeal(self):
        # Being rate limited must never lock someone out of challenging a label.
        cid = self.submit(creator="writer").get_json()["content_id"]
        for _ in range(self.PER_MINUTE + 2):
            self.submit(creator="writer")
        self.assertEqual(self.submit(creator="writer").status_code, 429)
        response = self.client.post("/appeal", json={"content_id": cid, "reasoning": "still me"})
        self.assertEqual(response.status_code, 200)

    def test_the_limit_resets_so_a_writer_is_not_locked_out_for_good(self):
        for _ in range(self.PER_MINUTE + 1):
            self.submit(creator="writer")
        self.assertEqual(self.submit(creator="writer").status_code, 429)
        service.limiter.reset()                                  # stands in for time passing
        self.assertEqual(self.submit(creator="writer").status_code, 200)

    def test_health_reports_that_limiting_is_on(self):
        self.assertTrue(self.client.get("/health").get_json()["rate_limiting"])


if __name__ == "__main__":
    unittest.main()
