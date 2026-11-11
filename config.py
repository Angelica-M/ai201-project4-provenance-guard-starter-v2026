"""
Settings for Provenance Guard.

Everything you're likely to change lives here, at the top, on purpose.

You'll edit the thresholds in Milestone 5 and the rate limits in unit 8.
"""

import os
from pathlib import Path

ROOT = Path(__file__).parent


# ─── The service ─────────────────────────────────────────────────────────────

# `127.0.0.1` is loopback — only your own machine can reach it, which is what
# you want all through units 7 and 8. A host somewhere else has to accept
# traffic from outside the box, and that means `0.0.0.0`. Setting the env var
# is how you get it; the default keeps your local `curl` commands unchanged.
HOST = os.getenv("HOST", "127.0.0.1")
PORT = int(os.getenv("PORT", "5000"))

# Flask's debug mode gives anyone who can reach the service an interactive
# Python prompt inside your process. Fine on loopback, a gift to strangers
# anywhere else — so it turns itself off the moment HOST isn't loopback.
DEBUG = os.getenv("AI201_DEBUG", "1") == "1" and HOST in ("127.0.0.1", "localhost")


# ─── The local model ─────────────────────────────────────────────────────────
# Your first signal runs a language model ON YOUR OWN MACHINE. No account, no
# key, no card. It downloads about 550 MB the first time — do that before
# class, not during it.
#
# What it measures: how *predictable* your text is to a language model. Text a
# model finds easy to predict tends to be text a model wrote.
#
# The first call is the slow one — ten to twenty seconds while the model loads,
# longer on an older laptop. After that it stays in memory and a submission
# takes a second or two. That cost is part of what you're learning: this is
# what running a model inline in a request actually looks like.

DETECTOR_MODEL = os.getenv("AI201_DETECTOR_MODEL", "gpt2")

# Longer text gives a steadier reading but takes longer. 400 tokens is roughly
# 300 words, which is enough for the signal to mean something.
DETECTOR_MAX_TOKENS = 400

# The longest `text` /submit will accept, in characters. Only the first 400
# tokens are ever scored, so a huge body adds cost and no accuracy; refusing it
# up front (413) is cheaper than reading it and then ignoring most of it.
MAX_TEXT_CHARS = 20_000

# The longest appeal `reasoning` /appeal will accept, in characters. An appeal is
# a few sentences from a person; 5,000 characters is several pages. The cap
# stops one request writing an enormous line into an append-only log that can
# never be trimmed.
MAX_REASONING_CHARS = 5_000


# ─── Scoring (Milestone 4) ───────────────────────────────────────────────────
# How much each signal counts toward the combined score.
#
# ⚠️ These are placeholders. Milestone 4 asks you to write your combining rule
# down BEFORE you code it, and to put the numbers in your README. Whatever you
# decide, it goes here.

#
# The rule itself is in scoring.py::combine_signals and is written out in words
# in the README. It has two parts, and every number in it is here:
#
#   1. A weighted average of the two scores. Equal weights, because each signal
#      was shown on its own to separate clearly-AI from clearly-human text and
#      neither was reliably the better one when they split (see the README).
#      Only the proportions matter; they are divided by their sum.
#   2. A disagreement rule. Two signals far apart is itself evidence of
#      uncertainty, so the average is pulled toward 0.5 (the middle of "unsure")
#      the further apart they are.

WEIGHT_MODEL_SIGNAL = 0.5
WEIGHT_STYLE_SIGNAL = 0.5

# Signals closer together than this are treated as agreeing, and the average is
# left alone. Chosen so ordinary noise doesn't trigger the rule: in the 24 test
# texts most pairs sit under 0.30 apart, and only the three widest split by more.
DISAGREEMENT_START = 0.30

# At this gap or wider, the pull is at its maximum. Between START and FULL the
# pull grows in a straight line.
DISAGREEMENT_FULL = 0.70

# The most the average is ever pulled toward 0.5: 0.5 means "halfway there".
# Not 1.0, because two signals that disagree still know something; they just
# shouldn't be allowed to produce a confident answer.
DISAGREEMENT_MAX_PULL = 0.5


# ─── Thresholds (Milestone 5) ────────────────────────────────────────────────
# Where one label becomes another. Scores run 0.0 (confidently human) to 1.0
# (confidently AI).
#
#   score <= HUMAN_THRESHOLD         -> high-confidence human
#   between the two                  -> unsure
#   score >= AI_THRESHOLD            -> high-confidence AI
#
# ⚠️ This is where your false-positive decision from Milestone 1 actually gets
# made. Widening the unsure band means fewer wrong accusations and more AI text
# getting through. There is no setting that avoids the trade — only settings
# that decide who pays for it.
#
# WHO PAYS, AND WHY THESE TWO NUMBERS
#
# The two labels are not equally expensive to get wrong, so the two lines are
# not placed symmetrically:
#
#   AI_THRESHOLD = 0.85. Calling a real writer's work AI is the costly mistake.
#   Measured in Milestone 4, plain human writing (short, simple sentences) scores
#   0.765 to 0.830 on the combined score, because BOTH signals read it as
#   machine-like, and no rule for combining them can fix that. The clearly-AI
#   test texts start at 0.885. So the line has to sit above 0.830 to protect
#   plain writers, and 0.85 leaves a little room on each side. That is a thin
#   margin on a small set of stand-in texts, and it is the first number to
#   revisit. The price is real: lightly-edited AI (0.666) and a lot of ordinary
#   AI text will be "unsure" and not "AI". The readers pay for that, in less
#   protection, instead of the writers, in false accusations.
#
#   HUMAN_THRESHOLD = 0.40. Saying "probably a person" wrongly costs the site
#   very little (some AI text gets through), so this line can be more generous.
#   Clearly-human test texts land at 0.115 to 0.410.
#
# The unsure band, 0.40 to 0.85, is wide on purpose. It is where plain writers,
# formal writers and edited AI all end up, so its wording has to be safe for
# someone who wrote every word themselves.

HUMAN_THRESHOLD = 0.40
AI_THRESHOLD = 0.85

# Both labels have to be REACHABLE, and the combined score is what decides that.
# combine_signals can produce anything from 0.0 to 1.0, so both lines are
# reachable in principle. In practice, "AI" needs BOTH signals high at once
# (about 0.85 or above on each, or one near 1.0), which the clearly-AI test
# texts do reach (0.885 to 0.924). `scoring.label_ranges()` prints the bands;
# whether an input actually lands in one is a different question, and the way
# to know is to submit text that does.


# ─── Rate limiting (UNIT 8) ──────────────────────────────────────────────────
# Turned on in unit 8, Milestone 1. It limits POST /submit only: /appeal, /log,
# /health and /ping are not limited, so a writer who has been (wrongly) labelled
# is never locked out of appealing.
#
# WHAT A RATE LIMIT IS FOR HERE. Each submission runs a language model, which
# costs real time, and each answer tells a caller a little about where the
# thresholds sit. A script that sends a thousand slightly different texts and
# watches which label comes back can MAP those thresholds and then write text
# that lands just under them. A limit can't stop that, but it can make it slow.
#
# The numbers come from setting two people side by side:
#
#   A real writer submits a piece, reads the label, perhaps edits and submits
#   again. Each round trip takes a person tens of seconds at least, so even an
#   impatient writer is at 3 or 4 submissions a minute at the very most. A heavy
#   honest day (many pieces, many revisions) is perhaps 15 to 25 submissions.
#
#   A script mapping thresholds needs volume. Finding one threshold on one text
#   by repeated halving takes about 7 probes to get within 0.01, so mapping a
#   range of texts takes hundreds.
#
# So: 5 a minute leaves the impatient writer room and puts one submission about
# every 12 seconds as the fastest a single caller can go, which also protects the
# CPU. 50 a day is roughly double the heaviest honest day, and it is the number
# that actually bites a script: a thousand probes from one identity takes 20
# days at 50 a day, against 5 days at the starter's 200.
#
# THE KNOWN HOLE. A "caller" is a creator_id when the request has one (see
# app.py::rate_limit_key), so a script that invents a fresh creator_id for every
# request is never limited at all. It is deliberate in this project: counting by
# network address instead would put every request from this laptop in one
# bucket and block the attack run and the evaluation harness, which all come from
# 127.0.0.1. The README says so and the attack run in later milestones will show
# whether it matters.
#
# Set to True in this milestone. (The starter read an environment variable here;
# tests that need limiting off switch it at runtime instead. See test_app.py.)

RATE_LIMITING_ENABLED = True

RATE_LIMIT_PER_MINUTE = 5
RATE_LIMIT_PER_DAY = 50

# Flask-Limiter warns loudly without this. In-memory is right for one laptop
# and wrong for anything real — a restart forgets every count, and two copies
# of the service wouldn't share limits.
RATE_LIMIT_STORAGE = "memory://"


# ─── Paths ───────────────────────────────────────────────────────────────────

LOG_DIR = ROOT / "logs"
AUDIT_LOG = LOG_DIR / "audit.jsonl"
RESULTS_DIR = ROOT / "results"
