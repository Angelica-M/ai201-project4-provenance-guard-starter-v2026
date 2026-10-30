#!/usr/bin/env python3
"""
Provenance Guard — the web service.

    python app.py

Then, in another terminal:

    curl -X POST http://127.0.0.1:5000/ping \
      -H "Content-Type: application/json" \
      -d '{"message": "hello"}'

That's the example route. It works right now, before you've written anything.
**Leave it alone** — it's your control. When something breaks later, check that
`/ping` still answers: if it does, the problem is in your handler; if it
doesn't, it's the service itself.

Routes:

    POST /ping        the worked example. Already works. Don't edit it
    POST /submit      ← YOU BUILD THIS (Milestone 3, 4, 5)
    POST /appeal      ← YOU BUILD THIS (Milestone 5)
    GET  /log         the audit log. Already works
    GET  /health      is the service up, and is the model loaded
"""

import uuid

from flask import Flask, jsonify, request

import audit
import config
import detector
import scoring
import stylometry

app = Flask(__name__)


def _error(status, code, message, creator_id=None):
    """
    One shape for every refusal: {"error": <short code>, "message": <sentence>}.

    A caller (or the evaluation harness) can branch on `error` without parsing
    prose, and a person can read `message`. Keeping it in one place means every
    route refuses in the same way.

    Every refusal is also written to the audit log. A request that is turned
    away and leaves no trace looks exactly like a quiet afternoon, and an
    attack that shows up only as an absence is one you never find. The log
    can't be allowed to be the thing that breaks a refusal, so a failed write
    is swallowed here rather than turning a clean 4xx into a 500.
    """
    try:
        audit.log_rejection(
            creator_id=creator_id if isinstance(creator_id, str) and creator_id.strip()
            else "unknown",
            reason=code,
        )
    except OSError:
        pass
    return jsonify({"error": code, "message": message}), status


# ── Rate limiting — UNIT 8 ────────────────────────────────────────────────────
# Off until you turn it on. In unit 8, Milestone 1:
#
#   1. Set RATE_LIMITING_ENABLED = True in config.py (or AI201_RATE_LIMITS=1)
#   2. Choose your numbers there
#   3. Uncomment the @limiter.limit(...) line on /submit below
#
# The order doesn't matter. While limiting is off, that decorator is a no-op
# that quietly does nothing, so uncommenting it early costs you nothing — but
# it also means no 429 until you've done step 1.
#
# The storage backend is preconfigured, which stops Flask-Limiter printing a
# warning on every start. In-memory is right for one laptop and wrong for
# anything real — a restart forgets every count.

class _LimiterOff:
    """
    Stands in for the real limiter while rate limiting is off.

    It makes @limiter.limit(...) a decorator that returns the route
    untouched, so uncommenting the line before you flip the setting is
    harmless instead of a crash on startup.
    """

    def limit(self, *args, **kwargs):
        return lambda view: view


limiter = _LimiterOff()
if config.RATE_LIMITING_ENABLED:
    from flask_limiter import Limiter
    from flask_limiter.util import get_remote_address

    def rate_limit_key():
        """
        Who a request counts against.

        Falling back to the caller's address is the easy version. Unit 8's
        stretch asks about per-creator limits instead — and the difference
        matters: one script can look like a thousand callers, and one household
        can look like one.
        """
        payload = request.get_json(silent=True)
        # A body that parses as JSON but isn't an object — a bare list or
        # string — has no .get. Without this guard the key function raises
        # BEFORE the route runs, and a malformed request becomes a 500 that
        # looks like your handler crashed when your handler never ran.
        if not isinstance(payload, dict):
            return get_remote_address()
        creator = payload.get("creator_id")
        return creator if isinstance(creator, str) and creator.strip() else get_remote_address()

    limiter = Limiter(
        key_func=rate_limit_key,
        app=app,
        storage_uri=config.RATE_LIMIT_STORAGE,
        default_limits=[],
    )

    @app.errorhandler(429)
    def rate_limited(exc):
        """
        A rejected request still leaves a trace.

        ⚠️ An attack that shows up only as an absence is one you'll never find.
        """
        payload = request.get_json(silent=True)
        if not isinstance(payload, dict):
            payload = {}
        audit.log_rejection(
            creator_id=payload.get("creator_id", "unknown"),
            reason="rate_limited",
            limit=str(exc.description),
        )
        return jsonify({
            "error": "rate_limited",
            "message": "Too many submissions. Try again shortly.",
            "limit": str(exc.description),
        }), 429


# ── The worked example. Already works. Don't edit. ────────────────────────────

@app.post("/ping")
def ping():
    """
    Everything a route needs, in six lines.

    JSON arrives as a dict. You pull things out of it. You return a dict and
    the framework turns it into a response. That's the whole idea.
    """
    payload = request.get_json(silent=True) or {}
    return jsonify({
        "ok": True,
        "you_sent": payload.get("message"),
        "service": "provenance-guard",
    })


@app.get("/health")
def health():
    """Is the service up, and has the model been downloaded yet?"""
    import detector

    loaded = detector._model is not None
    return jsonify({
        "ok": True,
        "detector_model": config.DETECTOR_MODEL,
        "detector_loaded": loaded,
        "rate_limiting": config.RATE_LIMITING_ENABLED,
        "log_entries": len(audit.read_entries()),
    })


# ── YOU BUILD THIS ────────────────────────────────────────────────────────────

@app.post("/submit")
# @limiter.limit(f"{config.RATE_LIMIT_PER_MINUTE}/minute;{config.RATE_LIMIT_PER_DAY}/day")
def submit():
    """
    Take a piece of text, decide about it, log the decision, answer.
    ← TODO — Milestones 3, 4 and 5

    Expects JSON:
        {"text": "...", "creator_id": "..."}

    Should return JSON with, at minimum:
        {"content_id": "...", "guess": "...", "confidence": 0.0, "label": "...",
         "model_score": 0.0, "style_score": 0.0}

    ⚠️ **Both signal scores go in the response, not just the log.** Unit 8's
    `run_attacks.py` and `run_eval.py` read `model_score` and `style_score`
    straight off this response and put them in your reports. Leave them out and
    every row of next unit's evidence says `null` — which is exactly the
    diagnostic you need to name a stage and a mechanism. You do not want to
    find that out after running the attack set.

    ─────────────────────────────────────────────────────────────────────────
    Build it in three passes. Do not skip ahead — the ordering is how you tell
    a broken route from a broken signal.

    **Milestone 3 — the route answers.**
      1. Return a hardcoded response. Confirm `curl` gets it back before you
         add any logic at all.
      2. Then pull `text` and `creator_id` out of the payload.
      3. Then call ONE signal — `detector.model_signal(text)` — and put the
         real number in. Leave confidence and label as placeholders.
      4. Log every submission with `audit.log_decision(...)`. The content_id
         matters: `/appeal` needs it, and a student who skips it rebuilds this
         whole flow later.

    **Milestone 4 — the second signal and the score.**
      5. Add `stylometry.style_signal(text)`.
      6. Combine them with `scoring.combine_signals(...)`.
      7. Log BOTH signal scores alongside the combined one, and put them in the
         response too. Next unit you can't diagnose anything without them.

    **Milestone 5 — the label.**
      8. `scoring.score_to_label(...)` and put the real label in the response.

    ─────────────────────────────────────────────────────────────────────────
    Worth deciding early, because unit 8's attack set will decide it for you:
    what should this do when `text` is missing, empty, or enormous? A crash on
    a malformed input is one of the most common real failures there is.
    """
    # ── MILESTONE 3, STEP 3: pull the fields out, run signal one, answer. ─────
    # (Step 1 was a hardcoded answer, to prove the route itself worked before
    # any logic went in. Now that logic is in, that proof is what tells a broken
    # signal apart from a broken route.)

    # 1. Read the body. `silent=True` means a body that isn't JSON gives None
    #    instead of raising, so we can answer with our own clean error.
    payload = request.get_json(silent=True)

    # 2. Refuse anything we can't score, with a 4xx and a reason, instead of
    #    letting it crash further down. The checks run in this order because
    #    each one assumes the one before it passed (you can't ask a list for
    #    its "text"). The error codes and statuses are the Milestone 1 contract.
    if not isinstance(payload, dict):
        return _error(400, "invalid_input",
                      "Send a JSON object with text and creator_id.")

    text = payload.get("text")
    creator_id = payload.get("creator_id")

    if not isinstance(text, str) or not text.strip():
        # Pass creator_id along even here: if it is a usable string, the log
        # can say WHO sent the bad request. _error() writes "unknown" itself
        # when it isn't usable.
        return _error(400, "invalid_input", "text must be a non-empty string.",
                      creator_id)
    if not isinstance(creator_id, str) or not creator_id.strip():
        return _error(400, "invalid_input", "creator_id must be a non-empty string.")
    if len(text) > config.MAX_TEXT_CHARS:
        return _error(413, "text_too_long",
                      f"text is over {config.MAX_TEXT_CHARS:,} characters.",
                      creator_id)

    # 3. Run signal one. Two things can go wrong and they are different faults:
    #    the text is too short for the model to score (the caller's problem,
    #    422), or the model itself couldn't load (the service's problem, 503).
    try:
        model_score = detector.model_signal(text)
    except ValueError as exc:
        return _error(422, "text_too_short", str(exc), creator_id)
    except detector.DetectorUnavailable as exc:
        return _error(503, "detector_unavailable", str(exc), creator_id)

    # 4. Run signal two (Milestone 4). It measures the text's shape, never loads
    #    a model, and can't fail on text that already passed the checks above,
    #    so it needs no error handling of its own.
    style_score = stylometry.style_signal(text)

    # 5. Turn two numbers into one. This is the number that will be labelled.
    #    Both inputs are kept as well, and go in the log and the response: when
    #    a score looks wrong, the first question is "which signal was off?",
    #    and without both numbers nothing can answer it.
    combined_score = scoring.combine_signals(model_score, style_score)

    # 6. Turn the number into words (Milestone 5). `guess` is the short
    #    machine-readable answer ("ai", "human" or "unsure") and `label` is the
    #    full sentence a reader sees. Which one a score gets depends only on the
    #    two thresholds in config.py, so the false-positive decision lives in one
    #    place and can be changed without touching this route.
    guess, label = scoring.score_to_label(combined_score)

    # 7. Remember the decision. content_id is generated here and must go back to
    #    the caller: /appeal needs it to find this decision again.
    #    `confidence` is the combined score, the number the label was chosen from.
    content_id = str(uuid.uuid4())
    confidence = combined_score

    # 8. Write it to the audit log BEFORE answering. If the answer is sent first
    #    and the write then fails, the caller holds a decision the service has no
    #    record of, and an appeal against it would find nothing. Every field is
    #    filled now, including the label: it is logged as the exact sentence the
    #    reader was shown, so the log says what they were told, not just what
    #    the service computed.
    audit.log_decision(
        content_id=content_id,
        creator_id=creator_id,
        guess=guess,
        model_score=model_score,
        style_score=style_score,
        combined_score=combined_score,
        label=label,
        status="decided",
    )

    # 9. Answer.
    return jsonify({
        "content_id": content_id,
        "guess": guess,
        "confidence": confidence,
        "label": label,
        "model_score": model_score,
        "style_score": style_score,
    }), 200


@app.post("/appeal")
def appeal():
    """
    A writer says you got it wrong. ← TODO — Milestone 5

    Expects JSON:
        {"content_id": "...", "reasoning": "..."}

    Should:
      1. Check the content_id actually exists — `audit.entries_for(id)` tells
         you. A typo here fails silently and looks like a broken endpoint,
         which is the single most common way this milestone eats an hour.
      2. Record the appeal with `audit.log_appeal(...)`, which moves the item
         to `under_review`.
      3. Confirm to the writer. No automatic re-checking needed.

    This is the smallest endpoint in the project and the one that matters most
    to the person on the other end. It's the only thing standing between a
    wrong accusation and nothing at all.
    """
    payload = request.get_json(silent=True) or {}

    # TODO: delete this and build the route.
    return jsonify({
        "error": "not_implemented",
        "message": "POST /appeal isn't built yet — see the TODO in app.py.",
        "you_sent": payload,
    }), 501


# ── Already works ─────────────────────────────────────────────────────────────

@app.get("/log")
def get_log():
    """
    The audit log, most recent last.

        curl "http://127.0.0.1:5000/log?limit=10"

    You need this in unit 8 to paste entries into your README, and you need it
    now to see whether your logging is actually working.
    """
    limit = request.args.get("limit", type=int)
    entries = audit.read_entries(limit=limit)
    return jsonify({"count": len(entries), "entries": entries})


def main():
    print(f"Provenance Guard on http://{config.HOST}:{config.PORT}")
    print(f"  detector model:  {config.DETECTOR_MODEL}")
    print(f"  rate limiting:   {'ON' if config.RATE_LIMITING_ENABLED else 'off (unit 8)'}")
    print(f"  audit log:       {config.AUDIT_LOG}")
    print()
    print("Check it's alive:")
    print(f'  curl -X POST http://{config.HOST}:{config.PORT}/ping \\')
    print('    -H "Content-Type: application/json" \\')
    print("    -d '{\"message\": \"hello\"}'")
    print()
    # debug=True hands out an interactive debugger, so it's local-only — see config.py
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)


if __name__ == "__main__":
    main()
