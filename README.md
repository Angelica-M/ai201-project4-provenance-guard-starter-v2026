# Provenance Guard

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first.**
>
> Once `python test.py` passes, in one terminal:
>
> ```bash
> python app.py
> ```
>
> and in another:
>
> ```bash
> curl -X POST http://127.0.0.1:5000/ping \
>   -H "Content-Type: application/json" \
>   -d '{"message": "hello"}'
> ```
>
> That's a web service. Something sent it text and it sent something back.
> Everything this unit is filling in the middle.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     Unit 7 asks for the first five sections. Unit 8 adds the five below.

     Everything is pasted as TEXT. A pasted curl response gets full credit;
     a picture of your terminal gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 7 — THE BUILD ═══════════════════════ -->

## What This Does

<!-- The path a submission takes, from arriving to the label a reader sees.
     Six or seven steps — this is the trace you wrote in Milestone 1. -->

Provenance Guard is a small backend a writing site can plug into. A site sends
it a piece of text and who submitted it. It sends back a guess about whether a
person or an AI wrote it, a number for how strongly the text leans one way, and
a plain-English label a reader can understand. If the label is wrong, the
writer can appeal it.

The path a submission takes, in seven steps:

1. **The request arrives** (`app.py`, `POST /submit`). The site sends JSON with
   `text` and `creator_id`. The route checks that both are there and usable.
   *It adds:* nothing to the text. It decides whether the text is worth scoring
   at all. Bad input is refused with a clear error and logged as a rejection.
2. **A `content_id` is assigned** (`app.py`). *It adds:* the handle that ties
   this decision, its log entries, and any later appeal together.
3. **Signal one reads the text** (`detector.py`, `model_signal`). A local
   language model measures how predictable the text is. *It adds:*
   `model_score`, 0 to 1, higher meaning more likely AI.
4. **Signal two measures the text as text** (`stylometry.py`, `style_signal`).
   Sentence length spread, word variety and punctuation, without understanding
   a word. *It adds:* `style_score`, same direction as `model_score`.
5. **The two scores become one** (`scoring.py`, `combine_signals`). *It adds:*
   the combined score, 0 to 1. This is the `confidence` in the response.
6. **The score becomes words** (`scoring.py`, `score_to_label`, using the
   thresholds in `config.py`). *It adds:* the `guess` (`ai`, `human` or
   `unsure`) and the label text a reader sees.
7. **The decision is logged and answered** (`audit.py`, `log_decision`, then
   the route's response). *It adds:* a permanent line in `logs/audit.jsonl`
   with every score and the status `decided`. Later, `POST /appeal` finds that
   entry by `content_id` and appends an appeal with status `under_review`.

---

---

## Signals and Scoring

<!-- For each signal: what property it measures, why that might differ between
     human and AI writing, and WHAT IT CAN'T SEE.

     The blind spot is not optional. If you can't name it you don't understand
     the signal yet — and unit 8's attack set is built out of blind spots. -->

### Signal one — the model signal

**What it measures:** How predictable the text is to a language model
(`detector.py`, gpt2 running on my own machine). It computes perplexity, which
is how surprised the model is by each next word on average, and squashes it to
a 0 to 1 score where higher means more likely AI. Only the first 400 tokens
(about 300 words) are read.

**Why that might differ between human and AI writing:** A language model
writes by picking likely next words, so what it writes is easy for another
model to predict. Human writing wanders more: odd word choices, abrupt turns,
the specific instead of the typical. Low surprise points toward AI, high
surprise toward human.

**What it can't see:** Authorship. It only sees predictability, and plenty of
real people write predictably: someone writing in a second language with
vocabulary they're sure of, a younger writer, anyone writing plainly on
purpose. Those writers score as machine-like. The reverse also holds: ornate
AI text full of rare words can score as human. It also can't see anything past
the first 400 tokens, and an old, small model like gpt2 is easy to fool with
light paraphrasing. This is the signal most likely to accuse the writers with
the least room to argue back.

### Signal two — the style signal

**What it measures:** The shape of the text, without understanding any of it
(`stylometry.py`, which I build in Milestone 4). Three things: how much
sentence length varies, how varied the vocabulary is (unique words over total
words), and how much punctuation there is and of what kind. Each is turned into
a 0 to 1 piece and combined into one score where higher means more likely AI.

**Why that might differ between human and AI writing:** Generated prose tends
toward even, mid-length sentences and a narrower band of vocabulary, because
"most likely next word" averages out. Human writing is lumpier: a three-word
sentence next to a forty-word one, an unexpected semicolon or dash.

**What it can't see:** Meaning. It can't read, so anything that changes the
shape without changing the substance moves it: adding typos (which raise word
variety), chopping or joining sentences, pasting in a quotation. All of that
is cheap to do on purpose. It is also unreliable on short text, where there is
too little to measure spread, and word variety falls as text gets longer, so
two texts of different lengths can't be compared on it directly. It shares
signal one's weakness too: a person who writes in short, even, plain sentences
looks like a machine to it.

### The combining rule

<!-- Write the rule in words, then give the numbers. What happens when the two
     signals disagree? -->

**The rule:**

**The numbers:**

**Where it lives:** `scoring.py::combine_signals`

<!-- ⚠️ The grader checks your code against that line. If your rule lives
     somewhere else, say where. -->

**A case where my two signals split, and what my rule does with it:**



---

## Label Variants

<!-- The exact text of all three labels, as a reader would see them, and the
     score range each covers.

     Write them for someone who has never heard the word "threshold". -->

| Label | Score range | The exact text a reader sees |
|---|---|---|
| high-confidence human |  |  |
| unsure |  |  |
| high-confidence AI |  |  |

**Why I worded the "unsure" one this way:**
<!-- It's the hardest of the three. It has to admit uncertainty without
     sounding like an accusation, because the person reading it may well have
     written every word themselves. -->



---

## Sample Run

<!-- One submission and one appeal, pasted as text: the request, the response,
     and the log entries. -->

**A submission**

<!-- The response needs content_id, guess, confidence, label, AND both
     signal scores - model_score and style_score. Unit 8's tools read those
     two off the response, so leaving them out costs you next unit's
     diagnostics. -->

```bash
$ curl -X POST http://127.0.0.1:5000/submit \
  -H "Content-Type: application/json" \
  -d '{"text": "...", "creator_id": "..."}'
```

```json

```

**An appeal**

```bash
$ curl -X POST http://127.0.0.1:5000/appeal \
  -H "Content-Type: application/json" \
  -d '{"content_id": "...", "reasoning": "..."}'
```

```json

```

**What the log shows afterwards**

```bash
$ curl "http://127.0.0.1:5000/log?limit=3"
```

```json

```

---

## How I Used AI

**Moment 1**

- *What I asked for:*
- *What came back:*
- *What I changed:*

**Moment 2**

- *What I asked for:*
- *What came back:*
- *What I changed:*

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** ___ per minute, ___ per day

**Why those numbers and not others:**
<!-- Think about two people: a real writer submitting their own work a few
     times an hour, and a script sending a thousand variations to map your
     thresholds. Your numbers have to be liveable for the first and hostile to
     the second. -->

**What a caller counts as:** <!-- per address, or per creator_id? They fail
differently — one script can look like a thousand callers, and one household
can look like one. -->

**The run of status codes when I pushed past it:**

<!-- python run_attacks.py --flood 15 -->

```

```

---

## Attack Run — Before

<!-- Every attack with its outcome and a held-or-broke mark.
     `run_attacks.py --label before` produces the table. -->



**Ten audit log entries from the run**

<!-- Choose entries that show the interesting failures, not the ten easiest. -->

```json

```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:



---

## Run Log and Verdicts

<!-- Your five criteria across three trials. `run_eval.py --label before`. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1.  |  |  |  |  |  |
| 2.  |  |  |  |  |  |
| 3.  |  |  |  |  |  |
| 4.  |  |  |  |  |  |
| 5.  |  |  |  |  |  |

**Real output from one trial**, pasted as text, naming the file and function
that produced it:

```json

```

**Diagnoses**

<!-- For each miss AND each broken attack: the stage and the mechanism.

     Your service has five stages: the route, signal one, signal two, the
     combining rule, and the label mapping.

     Not a diagnosis:  "The evasion attacks got through."
     A diagnosis:      "Four evasion inputs got through. All four had typos
                        added to AI-generated text. My second signal measures
                        word variety, and typos raise word variety — so it read
                        them as more human. My combining rule weights that
                        signal at 0.6, so it dragged the whole score down."

     Look for a pattern. Five failures on one signal is one problem, not five. -->



---

## The Improvement

**What I changed:**

**Which diagnosis pointed at it:**

### Attack Run — After

<!-- Same format. `run_attacks.py --label after` -->



**Did it help, and how do I know:**

<!-- Widening the unsure band usually fixes one problem and creates another.
     Reporting that trade honestly is worth full credit. -->



---

## What's Still Broken

<!-- For each attack still getting through and each criterion still missed:
     what you'd do, and why you stopped. -->



**The trade I'd make if this ran for real:**

<!-- Two sentences. Fewer wrong accusations means more AI text getting through.
     Say which way you'd go and WHO PAYS FOR IT. -->



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 7

       [ ] criteria.md has five numbered criteria, each naming a target
       [ ] Each has a reason underneath
       [ ] POST /submit returns content_id, guess, confidence, label,
           model_score and style_score
       [ ] Two signals that measure DIFFERENT things, each with a named blind spot
       [ ] Three label variants, all reachable, written out in full
       [ ] POST /appeal changes status and writes to the log
       [ ] Signals and Scoring names scoring.py::combine_signals
       [ ] Sample Run: a submission AND an appeal, as pasted text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN

     SUBMISSION CHECKLIST — unit 8

       [ ] Rate limiting on /submit, with your numbers justified
       [ ] The pasted run of status codes showing 429
       [ ] Audit log with all nine fields, recording rejections too
       [ ] The attack set run IN FULL, every input with an outcome
       [ ] Ten audit log entries pasted as text
       [ ] Five criteria across three trials
       [ ] A diagnosis for every miss and every broken attack — stage AND mechanism
       [ ] One improvement, with Attack Run — After
       [ ] What's Still Broken, including the production trade
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
