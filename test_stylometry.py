#!/usr/bin/env python3
"""
Tests for the style signal (`stylometry.py`).

    python test_stylometry.py          # run everything
    python test_stylometry.py -v       # show each test's name

─────────────────────────────────────────────────────────────────────────────
WHAT THIS FILE DOES, IN SHORT

The style signal is pure arithmetic on text: no model, no network, the same
answer every time. That makes it cheap to test thoroughly, so these tests pin
down each measure on inputs where the right answer can be worked out by hand,
and then check the properties the rest of the service relies on:

  - each measure returns the number it should (hand-worked cases);
  - the awkward inputs (empty, one sentence, no punctuation) don't crash and
    don't accuse anyone;
  - the combined score always stays between 0 and 1;
  - the direction is right: even, machine-like sentences score HIGHER (more
    AI-like) than lumpy, human ones. If that flipped, everything built above
    this signal would be wrong in a way that is hard to see.
─────────────────────────────────────────────────────────────────────────────
"""

import unittest

import scenarios
import stylometry as sty


class SentenceLengthSpread(unittest.TestCase):
    def test_identical_sentence_lengths_have_zero_spread(self):
        self.assertEqual(sty.sentence_length_spread("One two three. Four five six. Seven eight nine."), 0.0)

    def test_hand_worked_value(self):
        # Lengths 2 and 6: mean 4, sample stdev sqrt(8) = 2.828, so 2.828 / 4.
        value = sty.sentence_length_spread("Go now. Please come back to me soon.")
        self.assertAlmostEqual(value, 2.8284271 / 4, places=4)

    def test_lumpier_text_has_more_spread(self):
        even = "I like tea. You like coffee. We like both. They like neither."
        lumpy = ("No. I walked home through the park that evening, past the "
                 "fountain and the closed kiosk, thinking about nothing at all. Ok.")
        self.assertGreater(sty.sentence_length_spread(lumpy), sty.sentence_length_spread(even))

    def test_one_sentence_and_empty_do_not_crash(self):
        self.assertEqual(sty.sentence_length_spread("Just the one sentence here."), 0.0)
        self.assertEqual(sty.sentence_length_spread(""), 0.0)


class TypeTokenRatio(unittest.TestCase):
    def test_hand_worked_values(self):
        self.assertEqual(sty.type_token_ratio("a a b b"), 0.5)
        self.assertEqual(sty.type_token_ratio("every word here differs"), 1.0)

    def test_case_and_punctuation_are_ignored(self):
        self.assertEqual(sty.type_token_ratio("Go, GO! go."), 1 / 3)

    def test_empty_is_zero(self):
        self.assertEqual(sty.type_token_ratio(""), 0.0)

    def test_only_the_first_window_of_words_counts(self):
        # 100 distinct words, then 400 repeats of one word. If the whole text
        # counted the ratio would collapse; with the window it stays 1.0.
        text = " ".join(f"w{i}" for i in range(sty.TTR_WINDOW)) + " same" * 400
        self.assertEqual(sty.type_token_ratio(text), 1.0)


class PunctuationDensity(unittest.TestCase):
    def test_hand_worked_value(self):
        # "Well, yes; no." has 2 counted marks (comma, semicolon) over 3 words.
        # The closing full stop is deliberately not counted.
        self.assertAlmostEqual(sty.punctuation_density("Well, yes; no."), 2 / 3)

    def test_no_punctuation_is_zero(self):
        self.assertEqual(sty.punctuation_density("just plain words with nothing else"), 0.0)

    def test_single_full_stops_do_not_count_but_ellipses_do(self):
        self.assertEqual(sty.punctuation_density("One. Two. Three."), 0.0)
        self.assertGreater(sty.punctuation_density("Well... maybe"), 0.0)

    def test_apostrophes_do_not_count(self):
        self.assertEqual(sty.punctuation_density("don't can't won't"), 0.0)

    def test_dashes_and_quotes_count(self):
        self.assertGreater(sty.punctuation_density('He said — "no" — and left'), 0)

    def test_empty_is_zero(self):
        self.assertEqual(sty.punctuation_density(""), 0.0)


class StyleSignal(unittest.TestCase):
    EVEN = ("The system is useful. It works in most cases. Users find it easy. "
            "Results are generally good. It saves time overall.")
    LUMPY = ("No. Honestly, after eleven years of stepping over the same crack in "
             "the pavement outside the chemist, I stood there like an idiot "
             "mourning it. Fine. Just paying respects, I told the woman with "
             "the pushchair, who walked faster.")

    def test_direction_even_text_scores_more_ai_than_lumpy_text(self):
        self.assertGreater(sty.style_signal(self.EVEN), sty.style_signal(self.LUMPY))

    def test_even_text_scores_high_and_lumpy_text_scores_low(self):
        self.assertGreater(sty.style_signal(self.EVEN), 0.8)
        self.assertLess(sty.style_signal(self.LUMPY), 0.2)

    def test_always_between_zero_and_one(self):
        samples = [self.EVEN, self.LUMPY, "", "x", "...", "A. B. C. D.",
                   "word " * 500, "No. " * 50]
        samples += scenarios.OWN_WRITING + scenarios.CLEARLY_AI
        samples += scenarios.CLEARLY_HUMAN + scenarios.BORDERLINE
        for text in samples:
            score = sty.style_signal(text)
            self.assertGreaterEqual(score, 0.0, repr(text[:30]))
            self.assertLessEqual(score, 1.0, repr(text[:30]))

    def test_one_sentence_is_neutral_not_accused(self):
        # One sentence has no spread. That is "unknown", not "perfectly even",
        # so it must land at 0.5 and not at 1.0.
        self.assertEqual(sty.style_signal("A single sentence with no companions at all."), 0.5)

    def test_empty_text_is_neutral(self):
        self.assertEqual(sty.style_signal(""), 0.5)

    def test_same_input_same_answer(self):
        self.assertEqual(sty.style_signal(self.LUMPY), sty.style_signal(self.LUMPY))

    def test_weights_are_usable(self):
        self.assertGreater(sum(sty.WEIGHTS.values()), 0)
        self.assertTrue(all(w >= 0 for w in sty.WEIGHTS.values()))

    def test_parts_report_every_measure(self):
        parts = sty.style_parts(self.EVEN)
        for key in ("sentences", "spread", "spread_ai", "ttr", "ttr_ai", "punct", "punct_ai"):
            self.assertIn(key, parts)
        for key in ("spread_ai", "ttr_ai", "punct_ai"):
            self.assertTrue(0.0 <= parts[key] <= 1.0, key)

    def test_clearly_ai_set_scores_apart_from_clearly_human_set(self):
        ai = [sty.style_signal(t) for t in scenarios.CLEARLY_AI]
        human = [sty.style_signal(t) for t in scenarios.CLEARLY_HUMAN]
        self.assertGreater(sum(ai) / len(ai) - sum(human) / len(human), 0.4)


if __name__ == "__main__":
    unittest.main()
