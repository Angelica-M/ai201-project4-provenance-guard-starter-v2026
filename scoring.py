"""
Turning two numbers into one, and one number into something a person can read.
← YOU BUILD THIS IN MILESTONES 4 AND 5

Two functions live here, and both are stubs.

`combine_signals` is where your false-positive decision from Milestone 1
actually gets made. Everything above it — the labels, the appeal path — is
downstream of a number this function produced.

`score_to_label` is where you stop writing for a machine and start writing for
a person. A score of 0.62 means nothing to a writer.

⚠️ Your README's **Signals and Scoring** section has to name the file and
function holding your combining rule. The grader checks your code against what
you claim, so that line should read `scoring.py::combine_signals`.
"""

import config


def combine_signals(model_score: float, style_score: float) -> float:
    """
    Combine two 0–1 signals into one 0–1 score. ← TODO (Milestone 4)

    Both inputs point the same way: higher means more likely AI. Your output
    should too.

    Args:
        model_score: from `detector.model_signal` — how predictable the text is.
        style_score: from `stylometry.style_signal` — the shape of the text.

    Returns:
        A float from 0.0 (confidently human) to 1.0 (confidently AI).

    ⚠️ **Write the rule down before you code it, and put the numbers in your
    README.** A weighted average is the obvious choice and it is not the only
    one. Things worth thinking about:

      - **What happens when they disagree?** One signal at 0.9 and the other at
        0.1 averages to 0.5 — "unsure". Is that what you want? It might be
        exactly right: two methods disagreeing IS uncertainty. Or you might
        decide one signal is more trustworthy when they split.

      - **Which way do you want to be wrong?** Weighting toward the signal that
        reads more human means fewer false accusations and more AI text
        getting through. There's no weighting that avoids the trade.

      - Milestone 4 asks you to find a case where your two signals split and
        write it down. That case is what this rule exists to handle.

    ── THE RULE (Milestone 4) ──────────────────────────────────────────────────
    Written down before it was coded. The same wording is in the README.

      1. Average the two scores, weighted by config.WEIGHT_MODEL_SIGNAL and
         config.WEIGHT_STYLE_SIGNAL (0.5 each).
      2. Look at how far apart the two scores are.
           - Under config.DISAGREEMENT_START (0.30) apart: they agree, so the
             average is the answer.
           - Wider than that: they disagree, and disagreement is evidence of
             uncertainty. Move the average toward 0.5 by a fraction that grows
             in a straight line with the gap, from 0 at 0.30 apart up to
             config.DISAGREEMENT_MAX_PULL (half the way) at 0.70 apart or more.

    Worked example, the funeral piece from the README: model 0.127, style 0.632.
    Average 0.380. Gap 0.505, so the pull is (0.505 - 0.30) / (0.70 - 0.30) *
    0.5 = 0.256. Moved 25.6% of the way from 0.380 toward 0.5: 0.411.

    What it deliberately does NOT do: it can't rescue a writer when both
    signals agree and are both wrong. Plain, short-sentence writing scores high
    on both, so the average is high and nothing here changes that. That
    protection lives in the label thresholds (Milestone 5), not here.

    The pull works in both directions. A disagreeing pair that averages below
    0.5 is pulled UP toward "unsure" too, which makes a confident "human" label
    slightly harder to earn. That is the intended trade: when two methods
    disagree, neither answer should be stated confidently.
    """
    # Squeeze inputs into 0..1 so one bad value can't push the result outside it.
    model_score = min(max(model_score, 0.0), 1.0)
    style_score = min(max(style_score, 0.0), 1.0)

    # Step 1: the weighted average. Dividing by the weights' sum means they
    # don't have to add to 1; only their proportions matter.
    w_model, w_style = config.WEIGHT_MODEL_SIGNAL, config.WEIGHT_STYLE_SIGNAL
    average = (w_model * model_score + w_style * style_score) / (w_model + w_style)

    # Step 2: how much to distrust the average. `ramp` goes from 0 (they agree)
    # to 1 (they disagree as much as we ever act on), in a straight line.
    gap = abs(model_score - style_score)
    span = config.DISAGREEMENT_FULL - config.DISAGREEMENT_START
    ramp = min(max((gap - config.DISAGREEMENT_START) / span, 0.0), 1.0)
    pull = ramp * config.DISAGREEMENT_MAX_PULL

    # Slide the average `pull` of the way toward 0.5 ("we can't tell").
    combined = average + pull * (0.5 - average)
    return round(min(max(combined, 0.0), 1.0), 4)


def score_to_label(score: float) -> tuple[str, str]:
    """
    Turn a score into a guess and the text a reader actually sees.
    ← TODO (Milestone 5)

    Returns:
        (guess, label_text) — where `guess` is a short machine-readable string
        like "ai" / "human" / "unsure", and `label_text` is the full sentence
        shown to a person.

    ⚠️ Write the label text for someone who has never heard the word
    "threshold".

        ✗ "human, 0.81 confidence"
        ✓ "We think this was probably written by a person."

    All three labels have to be **reachable**. If no score can produce one of
    them, your ranges have a gap — and Milestone 5 asks you to submit text that
    produces each one, which is how you'd find out.

    The hardest one to write is "unsure". It has to admit uncertainty without
    sounding like an accusation, because the person reading it may well have
    written every word themselves. Your breakout asks your group what they'd
    think if they got it on their own work. That question is the whole
    milestone.
    """
    # TODO: replace this — thresholds are in config.py
    if score >= config.AI_THRESHOLD:
        return "ai", "PLACEHOLDER — write the high-confidence AI label."
    if score <= config.HUMAN_THRESHOLD:
        return "human", "PLACEHOLDER — write the high-confidence human label."
    return "unsure", "PLACEHOLDER — write the unsure label."


def label_ranges() -> list[tuple[str, str]]:
    """
    The score range each label covers. Your README needs these beside the
    label text — given to you so the numbers can't drift apart from config.py.
    """
    return [
        ("high-confidence human", f"0.00 – {config.HUMAN_THRESHOLD:.2f}"),
        ("unsure", f"{config.HUMAN_THRESHOLD:.2f} – {config.AI_THRESHOLD:.2f}"),
        ("high-confidence AI", f"{config.AI_THRESHOLD:.2f} – 1.00"),
    ]
