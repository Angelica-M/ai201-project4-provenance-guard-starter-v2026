# Acceptance criteria — Provenance Guard

Five criteria that say what "working" means for this service, written in unit 7
**before** you built it.

**All five are yours.** None are given.

An acceptance criterion names a number or something plainly observable. *"The
detector is accurate"* is an opinion — and perfect AI detection isn't possible
anyway, so it's an opinion about something nobody can deliver. *"Of 10 pieces I
wrote myself, at most 1 is labelled high-confidence AI"* is a criterion.

Under each, write a sentence or two on **why that target**. *"I allow at most 1
false positive in 10 because on a writing site a wrong accusation costs more
than a missed detection"* is a real answer.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

---

## Pick numbers you can defend

**Cover at least three of these five areas.** They're prompts, not a form.

| Area | A question it could answer |
|---|---|
| False positives | How often may a human's writing get called AI? |
| Score spread | How far apart should clearly-AI and clearly-human text score? |
| Label coverage | Is every one of your three labels actually reachable? |
| The appeal path | Does an appeal always change status and always get recorded? |
| Bad input | What happens when `text` is missing, empty, or enormous? |

Two things worth knowing before you pick numbers:

- **The expensive mistake is one-sided.** Missing some AI text costs the site a
  little. Accusing a real writer costs that person a lot. A criterion that
  treats both errors as equally bad is describing a system nobody would ship.
- **Unit 8 tests across three trials, and the target has to hold across all
  three.** Your first signal runs a model, so identical input can score
  differently twice. A target of "at most 1 in 10" against trials of 2, 1, 2 is
  a **miss**.

---
## 1. Few of my own pieces get accused of being AI

Of 10 pieces I wrote myself, at most 1 is labelled high-confidence AI. This
must hold in each of the three trials, not on average across them. At least 3
of the 10 are deliberately plain: short sentences, common words, no flourish,
the way a second-language or younger writer might write.

*Area: false positives.*

*How it's checked:* the "my own writing" scenario in `scenarios.py`, run three
times by `run_eval.py`. Its check, `check_false_positives`, counts how many of
the 10 come back with the high-confidence AI label in each trial.

**Why this target:**

On a writing site a wrong accusation costs one person their standing, while a
missed AI piece costs the site very little, so this is the strictest target of
the five. I allow 1 in 10 and not 0 because perfect detection isn't possible.
A target of zero could only be met by labelling nearly everything "unsure",
which would make the service useless. I don't allow 2 in 10 because a 20%
false-accusation rate would mean one in five real writers gets wrongly
accused. The plain pieces are in the set on purpose. Plain writing is the known
weak spot of both signals, and a set of only polished prose would make this
target easy to hit without telling me anything.

---

## 2. Clearly-AI and clearly-human text score far apart

Take 5 pieces I'm confident are AI-generated and 5 I'm confident a person wrote
(different pieces from criterion 1). In each trial, the mean `confidence` of the
AI group is at least 0.30 higher than the mean of the human group, and at least
4 of 5 in each group land on their own side of 0.50 (AI above, human below).

*Area: score spread.*

*How it's checked:* the "score spread" scenario in `scenarios.py` (5 clearly-AI
pieces, then 5 clearly-human). `check_score_spread` averages the `confidence` of
each group per trial and compares them.

**Why this target:**

A score that barely moves between obviously different inputs is a coin flip
dressed up as a number. I picked 0.30 because that is about the width of the
"unsure" band I plan to use (0.35 to 0.65). If the two groups are closer than
the band is wide, the labels can't separate them. I allow one miss in five per
group because the detector is imperfect and I'd rather set a target I can
defend than one that assumes it isn't.

---

## 3. All three labels are reachable and always real

Across 12 inputs I choose in advance (4 clearly AI, 4 clearly human, 4
borderline), each of the three labels appears at least once in every trial, and
at least 3 of the 4 borderline inputs get the "unsure" label. In 100% of
responses, `label` is exactly one of the three written label sentences: never
empty, never a placeholder.

*Area: label coverage.*

*How it's checked:* the "label coverage" scenario in `scenarios.py`, in a fixed
order (1-4 clearly AI, 5-8 clearly human, 9-12 borderline), so each trial's
guesses can be read straight off. `check_label_coverage` also confirms each
`label` is one of three distinct, non-empty, non-placeholder sentences.

**Why this target:**

A label no score can produce is a hole in the product, and it would only show
up when a real person landed there. The "unsure" label matters most, because
the design relies on it to protect real writers who sit near the line, so
hitting it once isn't enough. It has to catch most of the borderline cases.
The 100% on valid labels is deliberate: this is a plain mapping from score to
text, so any exception means a bug, not noise.

---

## 4. An appeal always changes status and is always recorded

For 10 submissions, each followed by an appeal using the returned `content_id`:
10 of 10 return 200 with `status` equal to `under_review`, and the audit log
shows an appeal entry carrying the writer's reasoning for each, after the
original decision entry, whose fields are unchanged. For 5 appeals using a
`content_id` that doesn't exist: 5 of 5 return 404 and none writes an appeal
entry.

*Area: the appeal path.*

*How it's checked:* the "appeal path" scenario, using the appeal runner I added
to `run_eval.py`. For each of 10 texts it submits, reads `/log`, appeals with the
returned `content_id`, and reads `/log` again, so "decision unchanged" and
"appeal recorded after it" are compared facts. Then it appeals 5 ids that were
never issued. `check_appeal_path` gives the yes/no.

**Why this target:**

The appeal is the only thing between a wrong accusation and nothing at all, so
unlike the detector it has no excuse for being unreliable. There's no model
noise here, which is why the target is every case and not most of them. The
original entry must stay unchanged because an audit log that can be rewritten
can't be trusted. The 404 half matters as much: an appeal that silently
succeeds on a typo'd id tells the writer it was recorded when it wasn't.

---

## 5. Bad input is refused cleanly, never crashes

I send 8 malformed requests: `text` missing, `text` empty, `text` only
whitespace, `text` null, `text` a number, `creator_id` missing, a body that is
a JSON list and not an object, and `text` of 50,000 words. All 8 get a 4xx
response (400, 413 or 422, as written in my endpoint contract) with a JSON
`error` and `message`. None returns a 500 or a stack trace. Afterwards `/ping`
still answers and the audit log holds 8 rejection entries.

*Area: bad input.*

*How it's checked:* the "bad input" scenario sends all 8 bodies exactly as
written (the JSON list included), then `run_eval.py` calls `/ping` and counts
how many rejection entries `/log` gained. `check_bad_input` gives the yes/no.

**Why this target:**

A crash on malformed input is one of the most common real failures in a web
service, and it's cheap for anyone to trigger on purpose. A service that falls
over on an empty string fails every honest user too. I check `/ping` afterwards
because a request that kills the process wouldn't show up as a failure on its
own response. The rejection entries are in the target because a refused request
that leaves no trace is invisible when someone probes the service.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 8 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath, like this:

         ## 2. Uncertain cases land in the unsure band

         The system handles uncertain cases well.

         **Why this target:** ...

         > **Revised in unit 8:** Text I judged borderline scores between
         > 0.4 and 0.6 in at least 4 of 5 cases.
         >
         > **Why revised:** "well" gave me nothing to check. I couldn't
         > reach a verdict from it at all.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "At most 1 of 10 of my own pieces flagged as AI" → "at most 3
            of 10", because 1 of 10 turned out to be hard.

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
