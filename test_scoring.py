#!/usr/bin/env python3
"""
Tests for the combining rule (`scoring.py::combine_signals`).

    python test_scoring.py          # run everything
    python test_scoring.py -v       # show each test's name

─────────────────────────────────────────────────────────────────────────────
WHAT THIS FILE DOES, IN SHORT

`combine_signals` is where the false-positive decision from Milestone 1 gets
made, so a quiet mistake here undoes everything built on it. It is also pure
arithmetic with no model, so it can be tested exhaustively and cheaply. These
tests check four kinds of thing:

  - the rule gives the hand-worked answer (agreeing, disagreeing, and the
    funeral example from the README);
  - the edges of the rule: exactly at the point where it switches on, and at
    the point where it stops growing;
  - properties that must hold for ANY pair of scores: the result stays in 0-1,
    swapping the two signals changes nothing when the weights are equal, and
    the rule never pushes a score AWAY from 0.5 (disagreement can only make the
    answer less confident, never more);
  - a higher input never makes the result lower (monotonic), swept across a
    grid, so no pair of scores quietly misbehaves.
─────────────────────────────────────────────────────────────────────────────
"""

import itertools
import unittest
from unittest import mock

import config
import scoring


class Agreeing(unittest.TestCase):
    def test_equal_scores_come_back_unchanged(self):
        for x in (0.0, 0.2, 0.5, 0.9, 1.0):
            self.assertAlmostEqual(scoring.combine_signals(x, x), x, places=4)

    def test_close_scores_are_a_plain_average(self):
        self.assertAlmostEqual(scoring.combine_signals(0.6, 0.8), 0.7, places=4)

    def test_a_gap_of_exactly_the_start_value_is_still_a_plain_average(self):
        # 0.30 apart: the rule has not switched on yet.
        self.assertAlmostEqual(scoring.combine_signals(0.35, 0.65), 0.5, places=4)
        self.assertAlmostEqual(scoring.combine_signals(0.5, 0.8), 0.65, places=4)


class Disagreeing(unittest.TestCase):
    def test_readme_funeral_example(self):
        # model 0.127, style 0.632 -> average 0.3795, gap 0.505, pull 0.25625,
        # result 0.3795 + 0.25625 * (0.5 - 0.3795) = 0.4104.
        self.assertAlmostEqual(scoring.combine_signals(0.127, 0.632), 0.4104, places=3)

    def test_just_past_the_start_pulls_only_a_little(self):
        plain_average = (0.2 + 0.52) / 2          # gap 0.32
        result = scoring.combine_signals(0.2, 0.52)
        self.assertGreater(result, plain_average)  # moved up toward 0.5
        self.assertLess(result - plain_average, 0.01)

    def test_full_gap_pulls_halfway_to_one_half(self):
        # gap 0.8 (past FULL) -> pull is capped at 0.5.
        # average 0.5 here, so use an asymmetric pair: 0.1 and 0.9 averages 0.5;
        # use 0.0 and 0.8 instead: average 0.4, result 0.4 + 0.5 * 0.1 = 0.45.
        self.assertAlmostEqual(scoring.combine_signals(0.0, 0.8), 0.45, places=4)

    def test_pull_stops_growing_beyond_the_full_gap(self):
        # Gaps of 0.70 and 0.90 are both at the cap, so each is pulled exactly
        # MAX_PULL (half) of the way from its average toward 0.5.
        for m, s in ((0.0, 0.7), (0.0, 0.9)):
            average = (m + s) / 2
            expected = average + config.DISAGREEMENT_MAX_PULL * (0.5 - average)
            self.assertAlmostEqual(scoring.combine_signals(m, s), expected, places=4)

    def test_a_pair_that_averages_one_half_stays_there(self):
        self.assertAlmostEqual(scoring.combine_signals(0.0, 1.0), 0.5, places=4)

    def test_high_average_pair_is_pulled_down_toward_unsure(self):
        # One signal certain it's AI, the other unsure-ish: not confident AI.
        result = scoring.combine_signals(0.95, 0.3)    # average 0.625, gap 0.65
        self.assertLess(result, 0.625)
        self.assertGreater(result, 0.5)

    def test_low_average_pair_is_pulled_up_toward_unsure(self):
        result = scoring.combine_signals(0.05, 0.6)    # average 0.325, gap 0.55
        self.assertGreater(result, 0.325)
        self.assertLess(result, 0.5)

    def test_the_rule_cannot_turn_a_disagreement_into_a_confident_ai_score(self):
        # Whatever the pair, if the signals are far apart the result stays
        # clear of both extremes: they cannot produce a confident answer.
        self.assertLess(scoring.combine_signals(1.0, 0.2), 0.7)


class Properties(unittest.TestCase):
    GRID = [i / 20 for i in range(21)]     # 0.00, 0.05, ... 1.00

    def test_always_between_zero_and_one(self):
        for m, s in itertools.product(self.GRID, self.GRID):
            r = scoring.combine_signals(m, s)
            self.assertTrue(0.0 <= r <= 1.0, (m, s, r))

    def test_out_of_range_inputs_are_squeezed_not_trusted(self):
        self.assertTrue(0.0 <= scoring.combine_signals(5.0, -3.0) <= 1.0)
        self.assertEqual(scoring.combine_signals(5.0, 5.0), 1.0)
        self.assertEqual(scoring.combine_signals(-1.0, -1.0), 0.0)

    def test_swapping_the_signals_changes_nothing_when_weights_are_equal(self):
        for m, s in itertools.product(self.GRID, self.GRID):
            self.assertAlmostEqual(scoring.combine_signals(m, s),
                                   scoring.combine_signals(s, m), places=9, msg=(m, s))

    def test_the_rule_never_moves_a_score_away_from_one_half(self):
        for m, s in itertools.product(self.GRID, self.GRID):
            average = (m + s) / 2
            result = scoring.combine_signals(m, s)
            self.assertLessEqual(abs(result - 0.5), abs(average - 0.5) + 1e-4, (m, s))

    def test_raising_either_signal_never_lowers_the_result(self):
        for fixed in self.GRID:
            previous_a = previous_b = -1.0
            for moving in self.GRID:
                a = scoring.combine_signals(moving, fixed)
                b = scoring.combine_signals(fixed, moving)
                self.assertGreaterEqual(a, previous_a - 1e-4, (moving, fixed))
                self.assertGreaterEqual(b, previous_b - 1e-4, (fixed, moving))
                previous_a, previous_b = a, b


class Configuration(unittest.TestCase):
    def test_weights_are_proportions_not_required_to_sum_to_one(self):
        with mock.patch.object(config, "WEIGHT_MODEL_SIGNAL", 3.0), \
                mock.patch.object(config, "WEIGHT_STYLE_SIGNAL", 1.0):
            # 3:1 weighting of 0.7 and 0.5 (only 0.2 apart, so no pull):
            # (3 * 0.7 + 0.5) / 4 = 0.65
            self.assertAlmostEqual(scoring.combine_signals(0.7, 0.5), 0.65, places=4)

    def test_turning_the_disagreement_rule_off_gives_a_plain_average(self):
        with mock.patch.object(config, "DISAGREEMENT_MAX_PULL", 0.0):
            self.assertAlmostEqual(scoring.combine_signals(0.127, 0.632), 0.3795, places=4)

    def test_weights_in_config_are_valid(self):
        self.assertGreater(config.WEIGHT_MODEL_SIGNAL + config.WEIGHT_STYLE_SIGNAL, 0)
        self.assertLess(config.DISAGREEMENT_START, config.DISAGREEMENT_FULL)
        self.assertTrue(0.0 <= config.DISAGREEMENT_MAX_PULL <= 1.0)


if __name__ == "__main__":
    unittest.main()
