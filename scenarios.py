"""
What your test runs. ← UNIT 8, MILESTONE 3

Each of your five criteria needs something run against it. A criterion about
false positives needs your own writing. One about label coverage needs inputs
across the score range. One about the appeal path needs a real content_id.

Working that out is Milestone 3's first step, and this file is where you write
it down. `run_eval.py` runs everything here three times.

Two are filled in as examples. Replace them with what your criteria actually
need — these are a shape, not a set.

A scenario carries **either** of these:

    "texts"   a list of strings. Each is sent as {"text": ..., "creator_id": ...}
              with a creator_id made up for you. Use this for most criteria.

    "bodies"  a list of whole request bodies, sent exactly as written. Use this
              when the malformed request IS the point — empty text, no `text`
              field at all, something enormous. A bad-input criterion needs it,
              because you cannot express "the field is missing" as a string.

──────────────────────────────────────────────────────────────────────────────
WHO WROTE THE TEXT IN THIS FILE  (read this before trusting any result)

The "my own writing" pieces were supplied by the user for criterion 1. The
"clearly AI" pieces are AI-written. The "clearly human" and "borderline"
pieces remain AI-drafted stand-ins, so their results are not valid evidence for
criteria 2 and 3.

Before treating criteria 2 and 3 as evidence, replace the "clearly human" and
"borderline" pieces with distinct real writing supplied by the user, keeping
the lengths roughly similar. The "expected" notes next to each set are what
was decided BEFORE seeing any score. Do not change them after a run.
──────────────────────────────────────────────────────────────────────────────

How the criteria in criteria.md map onto the scenarios here (one each):

    1  my own writing      10 pieces, the last 3 deliberately plain
    2  score spread        5 clearly AI then 5 clearly human, read by position
    3  label coverage      12 inputs: 4 clearly AI, 4 clearly human, 4 borderline
    4  appeal path         10 submit-then-appeal runs, then 5 unknown ids
    5  bad input           the 8 malformed requests, incl. a bare JSON list

Each scenario also carries a `check`: a small function that turns the
criterion's target into a yes/no for one trial. `run_eval.py` calls it after
every trial and prints "target met: yes/no" with the numbers behind it.

TO RUN IT (the service has to be running, and /submit and /appeal built):

    python app.py                       # terminal 1
    python run_eval.py --label before   # terminal 2, three trials by default

To check this file alone, without the service:

    python -c "import scenarios; print(scenarios.validate() or 'ok')"
"""

# ── Criterion 1: my own writing ──────────────────────────────────────────────
# Expected: at most 1 of the 10 comes back as the high-confidence AI label,
# in every trial. The last three are deliberately plain: short sentences,
# common words, the way a second-language or younger writer might write. That
# is the known weak spot of both signals, so they are the real test.

OWN_WRITING = [
    # Expressive pieces (7)
    "The ceramic mug slipped from the soapy sponge right into the sink drain, "
    "splitting cleanly across the handle before I could catch it. I tried "
    "gluing the pieces back together with super glue, but the seam leaked "
    "coffee on my desk five minutes into the work call. I finally threw the "
    "whole thing away and mourned my favorite mug with a sigh.",

    "The morning bus crawled down the avenue while rain smeared diagonal "
    "tracks across the steamed-up window beside my face. I watched an old man "
    "in a bright yellow raincoat carefully shelter a soaked stray cat under "
    "his umbrella at the crossing. The simple kindness made the damp, freezing "
    "commute feel a little less gray and tedious.",

    "My dad always checked every single locked door in the house three "
    "separate times before he finally went to bed. I remember standing in the "
    "dim hallway during a late-night storm while he solemnly clicked the "
    "deadbolt again with his thumb. It drove us crazy growing up, but now I "
    "catch myself doing the exact same thing every night.",

    "I bought a watercolor set on a whim because I wanted to paint loose "
    "botanical prints for the living room wall. The paint bled completely out "
    "of the lines into an uncontrollable, muddy brown puddle the second the "
    "wet brush hit the heavy paper. I laughed out loud, shut the palette lid, "
    "and decided modern abstract art wasn't so hard after all.",

    "I ran into my old college roommate at the grocery store checkout and "
    "pretended I didn't see her at first. She asked how my career was going "
    "while I nervously fumbled with my debit card in the chip reader. I still "
    "remember the exact way her eyes flicked down to check my bargain-brand "
    "groceries before she said goodbye.",

    "We walked down to the lake for a quick evening picnic just as a sudden "
    "gust of wind blew our napkins into the water. We sat on the damp wooden "
    "bench shivering in our light jackets while eating cold sandwiches in the "
    "dark. It was completely miserable weather, but we laughed so hard our "
    "stomachs hurt all the way home.",

    "That heavy brass pocket watch sitting on my bookshelf always reminds me "
    "of my grandfather's kitchen table. I can still picture him winding it "
    "slowly every single Sunday afternoon while listening to the baseball game "
    "on his old radio. Holding the cold metal in my palm makes him feel just a "
    "little closer again.",

    # Deliberately plain pieces (3)
    "I wake up at seven in the morning, brush my teeth, and turn on the coffee "
    "maker. While the coffee brews, I feed the cat and toast a piece of bread "
    "with butter. Then I sit at the kitchen table for twenty minutes to check "
    "my emails before getting dressed for work.",

    "I drove down to the local grocery store on Tuesday afternoon using the "
    "main highway route. I parked near the entrance, grabbed a shopping "
    "basket, and picked up milk, eggs, and fresh vegetables. After paying at "
    "the register, I loaded the bags into my car and drove straight back home.",

    "To change a flat tire, you first loosen the lug nuts with a wrench. Next, "
    "you place the jack under the car frame and pump it until the wheel lifts "
    "off the ground. Finally, you remove the nuts completely, swap the old "
    "tire for the spare, and tighten everything back down securely.",
]

# ── Criteria 2 and 3: clearly AI, clearly human, borderline ──────────────────
# What "clearly" means, decided before any score: AI pieces are generic,
# evenly paced and full of stock phrases ("in today's fast-paced world",
# "in conclusion"). Human pieces are specific, lumpy in length, and contain
# something only one person would write. Borderline pieces are on purpose
# ambiguous, in four different ways (see the notes beside each).

CLEARLY_AI = [
    "In today's fast-paced digital landscape, effective communication is more "
    "important than ever. Organizations must leverage a variety of tools and "
    "strategies to ensure that their message resonates with diverse audiences. "
    "By fostering collaboration, embracing innovation, and prioritizing "
    "clarity, teams can unlock their full potential and achieve sustainable "
    "success. Ultimately, the key to thriving lies in adaptability and a "
    "commitment to continuous improvement.",

    "Regular exercise offers numerous benefits for both physical and mental "
    "well-being. It strengthens the cardiovascular system, improves mood, and "
    "enhances overall energy levels. Additionally, maintaining a consistent "
    "routine can promote better sleep and reduce stress. It is important to "
    "choose activities that you enjoy, as this increases the likelihood of "
    "long-term adherence. In conclusion, incorporating movement into daily "
    "life is a valuable investment in one's health.",

    "The rapid advancement of artificial intelligence presents both "
    "opportunities and challenges for modern society. On one hand, it can "
    "improve efficiency, support decision-making, and drive innovation across "
    "industries. On the other hand, it raises important questions about "
    "privacy, fairness, and accountability. As we navigate this evolving "
    "landscape, it is essential to establish thoughtful guidelines that "
    "balance progress with ethical responsibility.",

    "Sustainable travel is becoming increasingly important as more people seek "
    "to explore the world responsibly. Travelers can reduce their "
    "environmental impact by choosing eco-friendly accommodations, using "
    "public transportation, and supporting local businesses. Furthermore, "
    "being mindful of waste and respecting local cultures contributes to a "
    "more positive experience for everyone involved. By making informed "
    "choices, we can ensure that future generations enjoy the beauty of our "
    "planet.",

    "Time management is a crucial skill that can significantly impact both "
    "personal and professional success. By setting clear goals, prioritizing "
    "tasks, and minimizing distractions, individuals can make the most of "
    "their available time. It is also beneficial to take regular breaks to "
    "maintain focus and prevent burnout. Overall, developing effective time "
    "management habits leads to increased productivity and a greater sense of "
    "balance.",
]

CLEARLY_HUMAN = [
    "The ferry smelled of diesel and wet dog. Tomasz, who had not spoken since "
    "Calais, suddenly asked whether I thought gulls ever got bored. I said no. "
    "He said that was a shame, because he was, terribly, and then he laughed "
    "so hard he had to sit down on a coil of rope. Forty minutes of nothing, "
    "then that. I've been chewing on it since.",

    "Okay so the thing nobody tells you about sourdough is that it's basically "
    "a pet that never loves you back. Mine's called Gerald. Gerald sulked all "
    "February. I tried warmth, I tried rye, I tried talking to him in a calm "
    "voice like a hostage negotiator. Then one morning: bubbles. Triumph. I "
    "ate the whole loaf standing up, still warm, butter running down my wrist, "
    "no regrets whatsoever.",

    "Funeral on Thursday, rain, the kind that gets in behind your collar. "
    "Uncle Ray's brass band played 'Danny Boy' slightly flat and somehow that "
    "was right, he'd have hated it perfect. Afterwards in the car park my "
    "cousin Dee handed round a flask of something unspeakable and we toasted "
    "him with plastic cups, coughing, laughing, soaked to the bone.",

    "There's a crack in the pavement outside the chemist that I have stepped "
    "over every working day for eleven years. Last week someone filled it in "
    "with tarmac. Neat. Black. Smug. I stood there like an idiot for a full "
    "minute, mourning a crack. Then a woman with a pushchair asked if I was "
    "all right and I said, 'Fine, fine, just paying respects.' She walked "
    "faster.",

    "Nobody warned me that learning the cello at forty-three means sounding "
    "like a wounded goose in front of your own children. My daughter, nine, "
    "asked politely if I could practise in the shed. My son recorded me and "
    "played it back at dinner. And yet, last night, one clean note, long and "
    "low, and the cat looked up. The cat! I'll take it.",
]

# Four borderline pieces, each ambiguous in a different way. Expected: at least
# 3 of the 4 get the "unsure" label.
BORDERLINE = [
    # AI-written, then lightly edited by a person to sound more casual.
    "Cities are changing fast, and honestly not always for the better. More "
    "people means more traffic, higher rents, and fewer places to just sit and "
    "breathe. But there are bright spots too. Community gardens, bike lanes "
    "and little parks tucked between buildings show what's possible when "
    "residents get a say. The challenge is making sure those voices are heard "
    "before the bulldozers arrive.",

    # Human-written, but formal and measured, the register AI often imitates.
    "The committee's findings, while not wholly unexpected, nonetheless "
    "warrant careful consideration. Participation among younger members "
    "declined over the review period, and the reasons offered were varied: "
    "cost, scheduling, and a perception that decisions were made elsewhere. "
    "Whether these concerns are well founded is a separate matter. What is "
    "clear is that they are widely held, and that ignoring them would be "
    "imprudent.",

    # Human-style first person, but plain and generic with no distinct detail.
    "Learning a second language takes patience, and I have learned that the "
    "hard way. Some days the words come easily and other days nothing sticks. "
    "What helps me most is practising a little every day, even when I do not "
    "feel like it. Speaking with native speakers is scary at first, but it is "
    "the fastest way to improve, and people are usually kinder than I expect.",

    # AI-style structure wrapped around a personal claim.
    "Last summer I volunteered at a local animal shelter, and it taught me a "
    "great deal about responsibility and compassion. Each morning I would help "
    "feed the dogs, clean the kennels, and spend time with the animals. "
    "Although the work was tiring, it was incredibly rewarding to see a "
    "nervous rescue slowly learn to trust people again. I would encourage "
    "anyone to give it a try.",
]

# ── The checks: criteria.md, written as code ─────────────────────────────────
# Each check answers one question for ONE trial: did it meet the target in
# criteria.md? It receives that trial's `results` (one row per request, see
# run_eval.py) and `extras` (anything measured around the batch), and returns
# (met, note), where `note` shows the numbers behind the answer.
#
# They only measure. Whether a miss means the criterion was too strict or the
# service too weak is for the diagnosis in unit 8, not for these functions.
# The targets are copied from criteria.md. Never loosen one here to get a pass:
# a number that was missed stays where it is.

LABELS = ("ai", "human", "unsure")      # the three values of `guess`


def _unscored(results):
    """Rows that did not come back as a normal 200 response."""
    return [r for r in results if r.get("status") != 200]


def check_false_positives(results, extras):
    """Criterion 1: at most 1 of my 10 pieces is labelled high-confidence AI."""
    if len(results) != 10:
        return False, f"expected 10 pieces, found {len(results)}"
    if _unscored(results):
        statuses = sorted({str(r.get("status")) for r in _unscored(results)})
        return False, f"{len(_unscored(results))} of 10 did not score (status {', '.join(statuses)})"
    n_ai = sum(1 for r in results if r.get("guess") == "ai")
    return n_ai <= 1, f"{n_ai} of 10 labelled AI (limit 1)"


def check_score_spread(results, extras):
    """
    Criterion 2: the first 5 results are the clearly-AI set and the last 5 the
    clearly-human set. The AI mean must beat the human mean by at least 0.30,
    and at least 4 of 5 in each group must sit on their own side of 0.50.
    """
    if len(results) != 10:
        return False, f"expected 10 pieces (5 AI + 5 human), found {len(results)}"
    if _unscored(results) or any(not isinstance(r.get("confidence"), (int, float))
                                 for r in results):
        return False, "some pieces came back without a numeric confidence"
    ai = [r["confidence"] for r in results[:5]]
    human = [r["confidence"] for r in results[5:]]
    gap = round(sum(ai) / 5 - sum(human) / 5, 4)
    ai_side = sum(1 for c in ai if c > 0.5)
    human_side = sum(1 for c in human if c < 0.5)
    met = gap >= 0.30 and ai_side >= 4 and human_side >= 4
    return met, (f"gap {gap:+.2f} (need 0.30+), {ai_side}/5 AI above 0.50, "
                 f"{human_side}/5 human below 0.50 (need 4+ each)")


def check_label_coverage(results, extras):
    """
    Criterion 3: results 1-4 are clearly AI, 5-8 clearly human, 9-12
    borderline. All three labels must appear, at least 3 of the 4 borderline
    inputs must be "unsure", and every response must carry one of exactly three
    real label sentences.
    """
    if len(results) != 12:
        return False, f"expected 12 inputs, found {len(results)}"
    if _unscored(results):
        return False, f"{len(_unscored(results))} of 12 did not score"
    seen = {r.get("guess") for r in results}
    missing = [g for g in LABELS if g not in seen]
    borderline_unsure = sum(1 for r in results[8:] if r.get("guess") == "unsure")

    # "Exactly one of three written sentences": every response with the same
    # guess must carry the same non-empty, non-placeholder text, and the three
    # texts must differ from each other.
    label_by_guess, label_problem = {}, None
    for r in results:
        text = r.get("label")
        if not isinstance(text, str) or not text.strip() or "PLACEHOLDER" in text:
            label_problem = f"empty or placeholder label for guess {r.get('guess')!r}"
            break
        if label_by_guess.setdefault(r["guess"], text) != text:
            label_problem = f"guess {r['guess']!r} came back with two different label texts"
            break
    if label_problem is None and len(set(label_by_guess.values())) != len(label_by_guess):
        label_problem = "two different guesses share one label text"

    met = not missing and borderline_unsure >= 3 and label_problem is None
    parts = [f"labels seen: {sorted(g for g in seen if g)}"]
    if missing:
        parts.append(f"never produced: {missing}")
    parts.append(f"borderline->unsure {borderline_unsure}/4 (need 3+)")
    if label_problem:
        parts.append(label_problem)
    return met, "; ".join(parts)


def check_appeal_path(results, extras):
    """
    Criterion 4: 10 of 10 real appeals return 200 + under_review, are logged,
    and leave the decision untouched; 5 of 5 appeals on unknown ids return 404
    and write nothing.
    """
    real = [r for r in results if r.get("kind") == "appeal"]
    fake = [r for r in results if r.get("kind") == "unknown"]
    good = [r for r in real
            if r.get("appeal_status") == 200 and r.get("state") == "under_review"
            and r.get("appeal_logged") and r.get("decision_unchanged")]
    refused = [r for r in fake
               if r.get("appeal_status") == 404 and not r.get("appeal_logged")]
    met = len(real) == 10 and len(good) == 10 and len(fake) == 5 and len(refused) == 5
    return met, (f"real appeals recorded correctly {len(good)}/{len(real)} (need 10/10), "
                 f"unknown ids refused cleanly {len(refused)}/{len(fake)} (need 5/5)")


def check_bad_input(results, extras):
    """
    Criterion 5: all 8 malformed requests get a 4xx with a JSON error and
    message, none returns a 500 or a non-JSON body, /ping still answers
    afterwards, and the audit log gained 8 rejection entries.
    """
    clean = [r for r in results
             if isinstance(r.get("status"), int) and 400 <= r["status"] < 500
             and r.get("json_ok") and r.get("error") and r.get("message")]
    crashed = [r for r in results if not isinstance(r.get("status"), int) or r["status"] >= 500]
    alive = extras.get("alive_after") is True
    rejections = extras.get("new_rejections")
    met = (len(results) == 8 and len(clean) == 8 and not crashed
           and alive and rejections == 8)
    return met, (f"clean 4xx JSON errors {len(clean)}/{len(results)} (need 8/8), "
                 f"500s or crashes {len(crashed)} (need 0), /ping alive: {alive}, "
                 f"new rejection log entries {rejections} (need 8)")


# ── The scenarios: one per criterion ─────────────────────────────────────────
# `target` is copied from criteria.md and printed in the report. `check` is the
# function above that measures it. `kind` tells run_eval.py to do more than
# post text: "appeal" (submit, then appeal) or "bad_input" (also ping and count
# rejections afterwards).

SCENARIOS = [
    {
        "name": "my own writing",
        "criterion": 1,
        "target": "At most 1 of 10 own pieces labelled high-confidence AI, every trial",
        # User-supplied writing: seven expressive pieces followed by three
        # deliberately plain pieces, as required by criterion 1.
        "texts": OWN_WRITING,
        "check": check_false_positives,
    },
    {
        "name": "score spread",
        "criterion": 2,
        "target": "AI-set mean confidence 0.30+ above human-set mean; 4 of 5 each on the right side of 0.50",
        # The first 5 are clearly AI, the last 5 clearly human. The check reads
        # them by position, so keep that order. The human five are stand-ins
        # drafted by Claude; replace them with real writing of your own.
        "texts": CLEARLY_AI + CLEARLY_HUMAN,
        "check": check_score_spread,
    },
    {
        "name": "label coverage",
        "criterion": 3,
        "target": "All 3 labels appear every trial; 3 of 4 borderline get unsure; labels always real text",
        # 12 inputs in a fixed order so a trial's guesses can be read straight
        # off: positions 1-4 clearly AI, 5-8 clearly human, 9-12 borderline.
        "texts": CLEARLY_AI[:4] + CLEARLY_HUMAN[:4] + BORDERLINE,
        "check": check_label_coverage,
    },
    {
        "name": "appeal path",
        "criterion": 4,
        "target": "10 of 10 appeals: 200, under_review, logged, decision untouched; 5 of 5 unknown ids: 404, nothing logged",
        # Ten real submissions to appeal against (the clearly-AI and
        # clearly-human sets reused: what is being tested is the appeal route,
        # not the text), then 5 appeals on ids that were never issued.
        "kind": "appeal",
        "texts": CLEARLY_AI + CLEARLY_HUMAN,
        "unknown_ids": 5,
        "check": check_appeal_path,
    },
    {
        "name": "bad input",
        "criterion": 5,
        "target": "8 of 8 malformed requests: JSON 4xx, no 500, /ping alive, 8 rejections logged",
        # The 8 malformed requests from criterion 5, sent exactly as written.
        "kind": "bad_input",
        "bodies": [
            {"creator_id": "eval_bad_missing"},                # no text field at all
            {"text": "", "creator_id": "eval_bad_empty"},      # empty string
            {"text": "   \n\t  ", "creator_id": "eval_bad_blank"},  # whitespace only
            {"text": None, "creator_id": "eval_bad_null"},     # null
            {"text": 12345, "creator_id": "eval_bad_number"},  # wrong type
            {"text": "This one is fine apart from the missing creator."},  # no creator_id
            [1, 2, 3],                                         # JSON list, not an object
            {"text": "word " * 50000, "creator_id": "eval_bad_huge"},  # 50,000 words
        ],
        "check": check_bad_input,
    },
]


def validate() -> list[str]:
    """
    Complain about anything malformed, before a long run rather than during.

    A "bodies" scenario is deliberately exempt from the empty check — an empty
    string is the whole point of a bad-input case, and refusing to run one
    would make that criterion untestable.
    """
    problems = []
    for i, scenario in enumerate(SCENARIOS, 1):
        if not scenario.get("name"):
            problems.append(f"scenario {i} has no name")

        if scenario.get("kind") not in (None, "appeal", "bad_input"):
            problems.append(
                f"scenario {i} ('{scenario.get('name')}') has an unknown kind "
                f"{scenario.get('kind')!r} — use 'appeal' or 'bad_input', or omit it"
            )
        if scenario.get("kind") == "appeal" and not scenario.get("texts"):
            problems.append(
                f"scenario {i} ('{scenario.get('name')}') is an appeal scenario, "
                f"so it needs 'texts' to submit before it appeals"
            )

        texts = scenario.get("texts")
        bodies = scenario.get("bodies")

        if texts and bodies:
            problems.append(
                f"scenario {i} ('{scenario.get('name')}') has both texts and "
                f"bodies — pick one"
            )
            continue

        if bodies:
            for j, body in enumerate(bodies, 1):
                # A body is a whole request body: normally a dict, but a bare
                # list is allowed because "the body isn't an object" is itself
                # a bad input worth testing. A string or number is not: it
                # would almost always be a typo for a dict.
                if not isinstance(body, (dict, list)):
                    problems.append(
                        f"scenario {i}, body {j} is not a dict or list — bodies are "
                        f"whole request bodies, like {{'text': '', 'creator_id': 'x'}}"
                    )
            continue

        if not texts:
            problems.append(f"scenario {i} has no texts and no bodies")
            continue

        for j, text in enumerate(texts, 1):
            if not str(text).strip():
                problems.append(
                    f"scenario {i}, text {j} is empty — if an empty submission is what "
                    f"you're testing, use 'bodies' instead of 'texts'"
                )
            elif str(text).startswith("REPLACE ME"):
                problems.append(
                    f"scenario {i} ('{scenario.get('name')}'), text {j} is still "
                    f"the placeholder"
                )
    return problems
