"""
Signal two: the style signal.  (Built in Milestone 4)

Signal one reads the text for meaning. This one measures it *as text* — the
shape of it, without understanding a word.

─────────────────────────────────────────────────────────────────────────────
WHAT THIS FILE DOES, IN SHORT

It turns a piece of writing into one number from 0 to 1, where higher means
more likely AI (the same direction as `detector.model_signal`). It does this in
three steps:

  1. MEASURE three plain properties of the text:
        sentence_length_spread   do sentences vary in length, or march in step?
        type_token_ratio         how much of the vocabulary repeats?
        punctuation_density      how much punctuation is there?
  2. SCALE each measure onto 0 to 1 ("AI-ness"), so they can be added up.
     Raw numbers live on different scales (a ratio, a count), and adding them
     as they are would let whichever has the bigger numbers win by default.
  3. COMBINE them as a weighted average (`style_signal`).

TO TRY IT, with no model and no service needed:

    python stylometry.py "some text to look at"      # one text, every number
    python stylometry.py                             # a built-in sample

TO RUN ITS TESTS:

    python test_stylometry.py

─────────────────────────────────────────────────────────────────────────────
WHAT THE EVIDENCE SAYS ABOUT THE THREE MEASURES  (the honest part)

The idea behind them: generated prose tends toward even, mid-length sentences
and a narrower band of vocabulary, because "most likely next word" averages out.
Human writing is lumpier, a three-word sentence next to a forty-word one.

Checked against the 24 test texts in `scenarios.py` (roughly 50 to 80 words
each), only ONE of the three measures held up:

    sentence_length_spread   separates well. Clearly-AI text sits at 0.09 to
                             0.19, clearly-human at 0.41 to 0.99.
    type_token_ratio         does NOT separate, and runs the wrong way: the
                             AI texts scored slightly HIGHER (0.81 to 0.90)
                             than the human ones (0.77 to 0.92). The hypothesis
                             that AI uses a narrower vocabulary did not show up
                             at this length.
    punctuation_density      does NOT separate. AI and human texts both land at
                             0.06 to 0.11, and rare marks (semicolons, dashes)
                             are almost absent from texts this short.

So the score is built from the one measure that earns it, and the other two are
measured and reported but carry weight 0 in WEIGHTS below. They are kept, rather
than deleted, so the numbers stay visible in the terminal and so a weight can be
raised in one line if longer texts show they discriminate. A signal that
doesn't discriminate is a real finding, not something to hide.

⚠️ **The blind spot, which you have to name in Milestone 1.**

This signal cannot read. It has no idea what the text says. Anything that
changes the shape without changing the substance moves it — adding typos,
breaking up sentences, pasting in a quotation. That is a very cheap thing for
someone to do on purpose, and unit 8's attack set will do it to you. With one
measure carrying the whole score, chopping AI text into sentences of different
lengths moves it a long way, which makes this blind spot sharper, not softer.

It also shares signal one's weak spot: a person who writes in short, even,
plain sentences (a second-language or younger writer) has low spread and so
looks machine-like here too. See "The false-positive problem" in the README.
"""

import re
import statistics


def sentences(text: str) -> list[str]:
    """Split into sentences. Rough and good enough — given to you."""
    parts = re.split(r"(?<=[.!?])\s+", text.strip())
    return [p for p in parts if p.strip()]


def words(text: str) -> list[str]:
    """Split into lowercase words, punctuation stripped. Given to you."""
    return re.findall(r"[a-z0-9']+", text.lower())


# ── Settings: how each measure is scaled and weighted ────────────────────────
# Every number a decision hangs on is here, named, so none of them is buried
# inside a function.

# Sentence-length spread is measured as the coefficient of variation: the
# standard deviation of sentence lengths divided by their mean. Dividing by the
# mean makes a long text and a short one comparable. At or below SPREAD_AI the
# text is treated as fully machine-even (AI-ness 1.0); at or above SPREAD_HUMAN
# it is treated as fully lumpy (0.0); in between it slides linearly. The two
# ends come from where the test texts actually fell (see the evidence above).
SPREAD_AI = 0.15
SPREAD_HUMAN = 0.85

# Type-token ratio is measured over only the first this-many words. The ratio
# falls as a text gets longer (common words repeat), so comparing a 40-word text
# with a 400-word one would measure length, not style. Capping the window
# compares like with like.
TTR_WINDOW = 100
TTR_HUMAN = 0.95   # at or above this reads as fully varied (AI-ness 0.0)
TTR_AI = 0.65      # at or below this reads as fully repetitive (AI-ness 1.0)

# Punctuation density is marks per word. At or above PUNCT_HUMAN it reads as
# fully "expressive" (AI-ness 0.0), and at 0 as fully bare (AI-ness 1.0).
PUNCT_HUMAN = 0.12

# How much each measure counts toward the style score. They are normalised, so
# only the proportions matter. Spread carries everything because it is the only
# measure that separated the test texts; the other two are 0 for the reason
# given in the module docstring. A weight is the one thing to change if that
# stops being true.
WEIGHTS = {"spread": 1.0, "ttr": 0.0, "punct": 0.0}

# Punctuation that counts. Two kinds are left out on purpose. Apostrophes mostly
# sit inside contractions and possessives, which says little about punctuation
# style. Single full stops just end sentences, so counting them would measure
# sentence count, which sentence_length_spread already covers. An ellipsis
# (three dots) does count.
_PUNCTUATION = re.compile(r"[,;:!?()\"—–]|\.\.\.|\s-\s")


def _clip(value: float) -> float:
    """Squeeze a number into 0 to 1."""
    return min(max(value, 0.0), 1.0)


# ── The three measures ───────────────────────────────────────────────────────

def sentence_length_spread(text: str) -> float:
    """
    How much sentence length varies, as a coefficient of variation.

    Returns:
        A float of 0 or more. **Higher means more human** (lumpier). Typical
        values: machine-even prose around 0.1 to 0.2, lively human writing 0.5
        or more. 0.0 means every sentence is the same length, or that there is
        only one sentence.

    The edge case the brief warns about: a one-sentence text has no spread at
    all and `statistics.stdev` raises on fewer than two values. This returns
    0.0 for that case. 0.0 reads as "perfectly even", which would wrongly look
    machine-like, so `style_signal` does NOT take that 0.0 at face value. It
    checks the sentence count itself and treats a single sentence as "no
    information" (a neutral 0.5) instead.
    """
    lengths = [len(words(s)) for s in sentences(text)]
    lengths = [n for n in lengths if n > 0]
    if len(lengths) < 2:
        return 0.0
    mean = statistics.mean(lengths)
    return statistics.stdev(lengths) / mean


def type_token_ratio(text: str) -> float:
    """
    Unique words over total words, over the first TTR_WINDOW words.

    Returns:
        A float between 0 and 1. Higher means more varied vocabulary. An empty
        text returns 0.0.

    Worth knowing before you rely on it: this measure falls as text gets
    longer, because common words repeat, which is why only the first
    TTR_WINDOW words are used. On the test texts it did not separate AI from
    human, so it carries no weight (see the module docstring).
    """
    tokens = words(text)[:TTR_WINDOW]
    if not tokens:
        return 0.0
    return len(set(tokens)) / len(tokens)


def punctuation_density(text: str) -> float:
    """
    Punctuation marks per word.

    Returns:
        A float of 0 or more. Counts commas, semicolons, colons, question and
        exclamation marks, brackets, double quotes, dashes and ellipses (not
        single full stops or apostrophes, see _PUNCTUATION). An empty text
        returns 0.0. On the test texts this did not
        separate AI from human, so it carries no weight.
    """
    n_words = len(words(text))
    if n_words == 0:
        return 0.0
    return len(_PUNCTUATION.findall(text)) / n_words


# ── Combining them ───────────────────────────────────────────────────────────

def style_parts(text: str) -> dict:
    """
    Every measure, raw and scaled, so you can see what drove the score.

    This is what to print when a score surprises you: it shows which of the
    three measures is the one that's off. For each measure it returns the raw
    value and `*_ai`, the same thing scaled to 0 to 1 where higher means more
    likely AI.
    """
    n_sentences = len([s for s in sentences(text) if words(s)])

    spread = sentence_length_spread(text)
    ttr = type_token_ratio(text)
    punct = punctuation_density(text)

    # Direction and scale, one measure at a time. Each line reads: how far along
    # the "human" to "AI" slide does this raw value sit?
    #
    #   spread: LOW spread is machine-like, so it is flipped (1 minus ...).
    #   ttr:    LOW variety is machine-like, so it is flipped too.
    #   punct:  LOW density is machine-like, so it is flipped too.
    #
    # A single sentence has no spread to measure; call it unknown (0.5) and
    # not "perfectly even" (1.0), which would accuse every one-liner.
    if n_sentences < 2:
        spread_ai = 0.5
    else:
        spread_ai = 1.0 - _clip((spread - SPREAD_AI) / (SPREAD_HUMAN - SPREAD_AI))
    ttr_ai = _clip((TTR_HUMAN - ttr) / (TTR_HUMAN - TTR_AI))
    punct_ai = 1.0 - _clip(punct / PUNCT_HUMAN)

    return {
        "sentences": n_sentences,
        "spread": round(spread, 3), "spread_ai": round(spread_ai, 3),
        "ttr": round(ttr, 3), "ttr_ai": round(ttr_ai, 3),
        "punct": round(punct, 3), "punct_ai": round(punct_ai, 3),
    }


def style_signal(text: str) -> float:
    """
    The style signal as a 0–1 score. **Higher means more likely AI.**

    A weighted average of the three scaled measures, using WEIGHTS. It points
    the same way as `detector.model_signal`, so `scoring.combine_signals` can
    treat the two alike. An empty text, which carries no information, returns
    a neutral 0.5.

    The two decisions the brief asks to be written down:

      1. Direction. Every measure is oriented so higher = more AI-like: low
         spread, low vocabulary variety and low punctuation each push the score
         up, which is why each is flipped inside `style_parts`.
      2. Scale. Each raw value is slid onto 0 to 1 between two stated
         endpoints (SPREAD_AI/SPREAD_HUMAN and so on) before averaging, so no
         measure wins just because its raw numbers are bigger.
    """
    if not words(text):
        return 0.5

    parts = style_parts(text)
    total_weight = sum(WEIGHTS.values())
    score = (
        WEIGHTS["spread"] * parts["spread_ai"]
        + WEIGHTS["ttr"] * parts["ttr_ai"]
        + WEIGHTS["punct"] * parts["punct_ai"]
    ) / total_weight
    return round(_clip(score), 4)


if __name__ == "__main__":
    import sys

    text = " ".join(sys.argv[1:]) or (
        "The system works well. It handles most cases correctly and provides "
        "good results. Users generally find it easy to use and understand."
    )

    parts = style_parts(text)
    print(f"{parts['sentences']} sentences, {len(words(text))} words\n")
    print(f"                         raw      as AI-ness (0 human .. 1 AI)   weight")
    print(f"sentence_length_spread   {parts['spread']:<8} {parts['spread_ai']:<29} {WEIGHTS['spread']}")
    print(f"type_token_ratio         {parts['ttr']:<8} {parts['ttr_ai']:<29} {WEIGHTS['ttr']}")
    print(f"punctuation_density      {parts['punct']:<8} {parts['punct_ai']:<29} {WEIGHTS['punct']}")
    print(f"\nstyle_signal             {style_signal(text)}   (higher = more likely AI)")
