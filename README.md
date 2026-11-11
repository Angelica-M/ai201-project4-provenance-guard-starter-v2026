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

A few terms used below, in plain words:

- **Endpoint:** one web address the service answers at, such as `/submit`.
- **Signal:** one independent way of guessing. This service has two, and they
  look at different things.
- **Token:** a chunk of text (usually a word or part of a word) that the
  language model reads as one unit.
- **Perplexity:** a measure of how surprised a language model is by a piece of
  text. Low means the text was easy to predict.
- **Stylometry:** measuring the *style* of writing (sentence lengths, word
  variety, punctuation) with numbers instead of reading for meaning.
- **Combined score:** the single 0 to 1 number made from both signals. 0 means
  confidently human and 1 means confidently AI.
- **Threshold:** the score at which one label turns into another.

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

**What comes back.** Every `/submit` reply carries a `content_id` (the handle
for any later appeal), a `guess` (`ai`, `human` or `unsure`), a `confidence`
(0 to 1, how far the text leans toward AI), the `label` sentence a reader sees,
and the two signal scores, `model_score` and `style_score`, so a surprising
result can be traced to the signal that caused it. There are three labels: "We
think this was probably written by a person" (a score of 0.40 or lower), a
"we can't tell" label (anything between), and a hedged "may have been written
with an AI tool" label (0.85 or higher). The exact wording is under *Label
Variants*.

**The appeal.** If a label is wrong, the writer sends `POST /appeal` with the
`content_id` and their reasoning. The service checks the id really exists
(a typo gets a clear 404), records the appeal in the audit log *after* the
original decision, marks the item `under_review`, and confirms. The log only
ever appends, so the original decision is never edited or deleted. There is no
automatic re-check.

**What it can't do.** Both signals read plain, short-sentence writing (the way
a second-language or younger writer might write) as machine-like, so a real
person who writes plainly can score as high as AI text, and no way of combining
the two numbers can fix that. I set the "AI" line high (0.85) for that reason.
The price is that a lot of ordinary AI text, and lightly-edited AI, comes back
"unsure" and not "AI". Fewer wrong accusations means more AI text getting
through. See *Label Variants* for who pays for that trade.

**Running and testing it.** `python app.py` starts the service (see
`RUNNING.md` for the commands). There are four test files, none of which needs
the service running or the model downloaded: `python test_stylometry.py`,
`python test_scoring.py`, `python test_app.py` and
`python test_eval_harness.py`.

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
(`stylometry.py`). Three things are measured: how much sentence length varies
(the standard deviation of sentence lengths divided by their mean), how varied
the vocabulary is (unique words over total words, over the first 100 words),
and how much punctuation there is (marks per word). Each is scaled to a 0 to 1
score and combined into one score where higher means more likely AI. **In
practice only the first carries weight.** On my 24 test texts, sentence-length
spread separated AI from human well (AI 0.09 to 0.19, human 0.41 to 0.99), but
vocabulary variety did not (the AI texts scored slightly higher, 0.81 to 0.90
against 0.77 to 0.92) and punctuation density did not (both 0.06 to 0.11). The
other two are still measured and reported but have weight 0, and one line in
`stylometry.py` raises a weight if longer texts show they matter.

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

**The rule:** Each signal gives a score from 0 (human) to 1 (AI). The rule
works in two steps.

1. **Average the two scores.** Each signal counts equally. Both were shown on
   their own to separate clearly-AI text from clearly-human text, and neither
   was reliably the better one when they split, so I have no evidence to
   trust one more.
2. **Check whether they agree.** If the two scores are less than 0.30 apart,
   they agree, and the average is the answer. If they are further apart, the
   signals are disagreeing, and two methods disagreeing *is* uncertainty. So
   the average is moved toward 0.5 (the middle of "unsure"). The further apart
   they are, the further it moves, starting at nothing at 0.30 apart and
   reaching half the distance to 0.5 at 0.70 apart or more.

In plain terms: when the signals agree, trust them. When they disagree, don't
let either one produce a confident answer. The rule works both ways, so a
disagreeing pair that averages low is also nudged up toward "unsure", which
makes a confident "human" label slightly harder to earn too. That is the
price of being cautious about disagreement.

**What the rule cannot do:** rescue a writer when *both* signals agree and are
both wrong. Plain writing in short, simple sentences scores high on both
signals (model 0.84 to 0.86, style 0.69 to 0.81 on my three plain test pieces),
so their average is high and no rule for combining the numbers can change
that. That protection has to come from where the label thresholds sit, not
from this rule. I name the limit here so the rule isn't credited with something
it doesn't do.

**The numbers:** All in `config.py`.

| Setting | Value | Meaning |
|---|---|---|
| `WEIGHT_MODEL_SIGNAL` | 0.5 | Share of the average from the model signal |
| `WEIGHT_STYLE_SIGNAL` | 0.5 | Share of the average from the style signal |
| `DISAGREEMENT_START` | 0.30 | Gap below which the signals count as agreeing |
| `DISAGREEMENT_FULL` | 0.70 | Gap at which the pull reaches its maximum |
| `DISAGREEMENT_MAX_PULL` | 0.5 | The most the average is moved toward 0.5 (half the way) |

Why these values: 0.30 so ordinary noise doesn't trigger the rule (in my 24
test texts only a few pairs are further apart than that), and a maximum pull
of one half and not all the way because two signals that disagree still know
something. They just shouldn't be allowed to produce a confident answer.

**Where it lives:** `scoring.py::combine_signals`

<!-- ⚠️ The grader checks your code against that line. If your rule lives
     somewhere else, say where. -->

**A case where my two signals split, and what my rule does with it:**

*The case.* A short human piece about a funeral ("Funeral on Thursday, rain,
the kind that gets in behind your collar. Uncle Ray's brass band played 'Danny
Boy' slightly flat..."). The model signal gives it **0.127**, very human. The
style signal gives it **0.632**, leaning AI. They are 0.505 apart, the widest
split among my 24 test texts.

*Why they split.* The model signal sees unusual words and names (perplexity
150.3, far above the 45 midpoint), so it calls the text human. The style signal
sees only three sentences of 12, 19 and 28 words. That is a steady climb, not
the lumpy mix of very short and very long sentences it treats as human, so it
reads the text as fairly even. In this case the model signal is right and the
style signal is wrong. The opposite also happens: a piece about a cracked
pavement ("Neat. Black. Smug.") has three one-word sentences, so the style
signal scores it **0.000**, as human as possible, while the model signal sits
on the fence at **0.540**. Neither signal is reliably the better one, so
neither can simply be trusted when they split.

*What my rule does with it.* The two scores are 0.505 apart, past the 0.30
point where the rule switches on. Their average is 0.380. The pull is
(0.505 - 0.30) / (0.70 - 0.30) x 0.5 = 0.256, so the average moves about a
quarter of the way toward 0.5, to **0.411**. Without the rule the piece would
read as a fairly confident human (0.380). With it, it lands closer to
"unsure", which fits the facts: one method said very human and the other said
leaning AI. For the cracked-pavement piece (model 0.540, style 0.000), the
average of 0.270 moves to about 0.339. The rule is mild on these two, and its
bigger job is next unit, when edited AI text is likely to split the two
signals.



---

## Label Variants

<!-- The exact text of all three labels, as a reader would see them, and the
     score range each covers.

     Write them for someone who has never heard the word "threshold". -->

| Label | Score range | The exact text a reader sees |
|---|---|---|
| high-confidence human | 0.00 to 0.40 (a score of 0.40 or lower) | We think this was probably written by a person. |
| unsure | Above 0.40 and below 0.85 | We can't tell whether this was written by a person or with an AI tool. Our checks aren't perfect, and plain or very formal writing can look the same to them either way. This is not a finding that anything is wrong. |
| high-confidence AI | 0.85 to 1.00 (a score of 0.85 or higher) | Our checks found signs that this may have been written with an AI tool. We can't be sure, and we sometimes get this wrong. If you wrote it yourself, you can appeal and explain how you wrote it, and your appeal will be recorded and marked for review. |

**How to read the score ranges.** The score is the `confidence` the service
returns: a number from 0 to 1 for how far the text leans toward AI, where 0 is
"definitely a person" and 1 is "definitely an AI". A **threshold** is just the
line where one label turns into the next. There are two: at 0.40, below which
the label is "human", and at 0.85, above which it is "AI". Everything in
between is "unsure". A score landing exactly on a line gets the label on the
outer side of it (0.40 is "human", 0.85 is "AI"). The three ranges together
cover every score from 0 to 1 with no gap, so every score gets a label.

**Why the two lines are not symmetrical.** The two mistakes cost different
amounts. Calling a real writer's work AI is the expensive one. Wrongly saying
"probably a person" costs the site very little. So the "AI" line is set very
high (0.85) and the "human" line is more generous (0.40). I set 0.85 because
plain human writing, which is the case most likely to be wrongly accused,
scored 0.765 to 0.830 on my test texts, and clearly-AI text started at 0.885.
The line had to sit above 0.830. The cost is real: a lot of ordinary AI text
(and lightly-edited AI) will be labelled "unsure" instead of "AI", so the site
gets less protection in exchange for fewer false accusations. The margin on
each side of 0.85 is thin, and it comes from a small set of test texts, so it
is the first number to revisit.

**Why I worded the "unsure" one this way:**
<!-- It's the hardest of the three. It has to admit uncertainty without
     sounding like an accusation, because the person reading it may well have
     written every word themselves. -->

"Unsure" is the label a real writer is most likely to meet. Plain writing, very
formal writing and lightly-edited AI all land in it, so I wrote it for someone
who wrote every word themselves and is reading it with a sinking feeling.

- **It opens with what we don't know, not what we suspect.** "We can't tell"
  comes first. It never says "possibly AI" or "flagged", which a worried reader
  would hear as an accusation.
- **It names the reason in plain terms.** "Plain or very formal writing can look
  the same to them either way" tells the reader the uncertainty is about the
  checks, not about them. A plain writer will recognise their own writing in it.
- **It says outright that nothing is being alleged.** "This is not a finding
  that anything is wrong." A reader who has been uncertain-labelled should not
  have to guess whether they are in trouble.
- **It avoids jargon.** No "threshold", "score" or "confidence", and no number.
  "0.62" means nothing to a writer.
- **It asks nothing of the reader.** There is no instruction and no deadline,
  because the person may have done nothing wrong. (The "AI" label is the one
  that mentions appealing, since that is the label that can wrongly accuse.)



---

## Sample Run

<!-- One submission and one appeal, pasted as text: the request, the response,
     and the log entries. -->

> The commands below were run with `curl.exe` on one line (Windows PowerShell)
> on port 5001, because port 5000 was in use on my machine. On a free machine,
> use 5000. All output is pasted as text, exactly as it came back.

**A submission**

<!-- The response needs content_id, guess, confidence, label, AND both
     signal scores - model_score and style_score. Unit 8's tools read those
     two off the response, so leaving them out costs you next unit's
     diagnostics. -->

Three submissions, one for each label, from three different writers. Together
they show that all three labels are reachable.

*1. A high-confidence AI result.* The text is AI-style prose and both signals
lean AI (model 0.8394, style 1.0), so the combined `confidence` is 0.9197, above
the 0.85 line:

```bash
$ curl.exe -X POST http://127.0.0.1:5001/submit -H "Content-Type: application/json" -d '{\"text\": \"Time management is a crucial skill that can significantly impact both personal and professional success. By setting clear goals, prioritizing tasks, and minimizing distractions, individuals can make the most of their available time.\", \"creator_id\": \"writer_ana\"}'
```

```json
{
  "confidence": 0.9197,
  "content_id": "1cfcb48a-d890-412f-bc0a-357a63d8138b",
  "guess": "ai",
  "label": "Our checks found signs that this may have been written with an AI tool. We can't be sure, and we sometimes get this wrong. If you wrote it yourself, you can appeal and explain how you wrote it, and your appeal will be recorded and marked for review.",
  "model_score": 0.8394,
  "style_score": 1.0
}
```

*2. A high-confidence human result.* The text is specific and a bit odd, and
both signals lean human (model 0.3881, style 0.131), so `confidence` is 0.2596,
below the 0.40 line:

```bash
$ curl.exe -X POST http://127.0.0.1:5001/submit -H "Content-Type: application/json" -d '{\"text\": \"The ferry smelled of diesel and wet dog. Tomasz, who had not spoken since Calais, suddenly asked whether I thought gulls ever got bored. I said no. He said that was a shame, because he was, terribly, and then he laughed so hard he had to sit down on a coil of rope.\", \"creator_id\": \"writer_ben\"}'
```

```json
{
  "confidence": 0.2596,
  "content_id": "7207a307-9e45-496c-887a-73ac58a818af",
  "guess": "human",
  "label": "We think this was probably written by a person.",
  "model_score": 0.3881,
  "style_score": 0.131
}
```

*3. An unsure result.* Plain, ordinary first-person writing. Both signals lean
AI (model 0.7114, style 0.864) and `confidence` is 0.7877, which is high but
under the 0.85 line, so the service says it can't tell instead of accusing:

```bash
$ curl.exe -X POST http://127.0.0.1:5001/submit -H "Content-Type: application/json" -d '{\"text\": \"Learning a second language takes patience, and I have learned that the hard way. Some days the words come easily and other days nothing sticks. What helps me most is practising a little every day, even when I do not feel like it.\", \"creator_id\": \"writer_cara\"}'
```

```json
{
  "confidence": 0.7877,
  "content_id": "d0fe666d-6240-4d4f-9b9d-132a7d79fc10",
  "guess": "unsure",
  "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't perfect, and plain or very formal writing can look the same to them either way. This is not a finding that anything is wrong.",
  "model_score": 0.7114,
  "style_score": 0.864
}
```

Example 3 is the case the thresholds exist for. At the placeholder line of 0.65
this writer would have been told their work looked like AI.

*A request the service refuses* (empty text). It gets a clear 400 and is also
written to the log:

```bash
$ curl.exe -X POST http://127.0.0.1:5001/submit -H "Content-Type: application/json" -d '{\"text\": \"\", \"creator_id\": \"writer_ben\"}'
```

```json
{
  "error": "invalid_input",
  "message": "text must be a non-empty string."
}
```

**An appeal**

Suppose writer_ana's text was labelled "high-confidence AI" above, but they
wrote it themselves. (The three writers in this section are made up to show the
service working.) They appeal using the `content_id` from their `/submit`
response (`1cfcb48a-...`) and say why:

```bash
$ curl.exe -X POST http://127.0.0.1:5001/appeal -H "Content-Type: application/json" -d '{\"content_id\": \"1cfcb48a-d890-412f-bc0a-357a63d8138b\", \"reasoning\": \"I wrote this myself for a time-management workshop. I tend to write in short, tidy sentences.\"}'
```

```json
{
  "content_id": "1cfcb48a-d890-412f-bc0a-357a63d8138b",
  "message": "Your appeal has been recorded and this result is marked under review.",
  "status": "under_review"
}
```

The same appeal with one character of the `content_id` changed (`...138c`
instead of `...138b`). This is the typo that makes an appeal endpoint look
broken, so it is refused with a clear 404 that says what to check, and it is
logged too, not silently dropped:

```bash
$ curl.exe -X POST http://127.0.0.1:5001/appeal -H "Content-Type: application/json" -d '{\"content_id\": \"1cfcb48a-d890-412f-bc0a-357a63d8138c\", \"reasoning\": \"Same writer, wrong id.\"}'
```

```json
{
  "error": "unknown_content_id",
  "message": "No submission has that content_id. Check it was copied exactly from the /submit response."
}
```

**What the log shows afterwards**

All six requests above (three decisions, the empty-text refusal, the appeal, and
the typo'd appeal), read back from the audit log (`logs/audit.jsonl`):

```bash
$ curl.exe "http://127.0.0.1:5001/log?limit=6"
```

How to read it:

- **Entry 1** is writer_ana's original decision, with the "AI" label. It is
  *unchanged*: its `status` is still `decided`. The log only ever appends, so
  an appeal never edits or deletes what was decided.
- **Entry 5** is the appeal, with `"status": "under_review"`, the writer's own
  `reasoning`, and the same `content_id` as entry 1. That is the status change:
  it is a new line after the decision, so anyone reading the log can see what
  was decided, that it was challenged, and in what order.
- **Entry 6** is the typo'd appeal, recorded as a rejection with the reason
  `unknown_content_id`. It did not create an appeal.

```json
{
  "count": 6,
  "entries": [
    {
      "combined_score": 0.9197,
      "content_id": "1cfcb48a-d890-412f-bc0a-357a63d8138b",
      "creator_id": "writer_ana",
      "guess": "ai",
      "label": "Our checks found signs that this may have been written with an AI tool. We can't be sure, and we sometimes get this wrong. If you wrote it yourself, you can appeal and explain how you wrote it, and your appeal will be recorded and marked for review.",
      "model_score": 0.8394,
      "status": "decided",
      "style_score": 1.0,
      "timestamp": "2026-10-30T20:31:34+00:00"
    },
    {
      "combined_score": 0.2596,
      "content_id": "7207a307-9e45-496c-887a-73ac58a818af",
      "creator_id": "writer_ben",
      "guess": "human",
      "label": "We think this was probably written by a person.",
      "model_score": 0.3881,
      "status": "decided",
      "style_score": 0.131,
      "timestamp": "2026-10-30T20:31:35+00:00"
    },
    {
      "combined_score": 0.7877,
      "content_id": "d0fe666d-6240-4d4f-9b9d-132a7d79fc10",
      "creator_id": "writer_cara",
      "guess": "unsure",
      "label": "We can't tell whether this was written by a person or with an AI tool. Our checks aren't perfect, and plain or very formal writing can look the same to them either way. This is not a finding that anything is wrong.",
      "model_score": 0.7114,
      "status": "decided",
      "style_score": 0.864,
      "timestamp": "2026-10-30T20:31:35+00:00"
    },
    {
      "creator_id": "writer_ben",
      "event": "rejected",
      "reason": "invalid_input",
      "status": "rejected",
      "timestamp": "2026-10-30T20:31:35+00:00"
    },
    {
      "content_id": "1cfcb48a-d890-412f-bc0a-357a63d8138b",
      "creator_id": "writer_ana",
      "event": "appeal",
      "reasoning": "I wrote this myself for a time-management workshop. I tend to write in short, tidy sentences.",
      "status": "under_review",
      "timestamp": "2026-10-30T20:33:40+00:00"
    },
    {
      "creator_id": "unknown",
      "event": "rejected",
      "reason": "unknown_content_id",
      "status": "rejected",
      "timestamp": "2026-10-30T20:33:40+00:00"
    }
  ]
}
```

---

## How I Used AI

**Moment 1: the `curl` command that wouldn't run in PowerShell**

- *What I asked for:* How to fix the errors I got when I pasted the README's
  `curl -X POST ... \` example into PowerShell (`-H` and `-d` "not recognized",
  `Cannot bind parameter 'Headers'`).
- *What came back:* An explanation that in PowerShell `curl` is an alias for a
  different tool (`Invoke-WebRequest`) and that `\` is not a line continuation
  there. The fix was `curl.exe` on one line, with the quotes inside the JSON
  escaped (`'{\"message\": \"hello\"}'`). It also offered other options,
  including sending the body from a file with `-d "@body.json"`.
- *What I changed:* I first tried the file version, and it failed with
  `Failed to open body.json`, because nothing had created that file. The advice
  had skipped that step. I went back to the one-line inline version, which
  worked, and used it for every command in this README. The lesson I took away
  was to check what a suggested command depends on before running it.

**Moment 2: building the style signal**

- *What I asked for:* The second signal in `stylometry.py`, built from the three
  measures the brief names (sentence-length spread, unique words over total
  words, and punctuation density) and combined into one 0 to 1 score.
- *What came back:* Working code for all three measures and a weighted average
  of them, built on the brief's idea that AI text has a narrower vocabulary and
  more even sentences.
- *What I changed:* I did not take the idea on faith. I had the three measures
  run over the 24 test texts first. Only sentence-length spread separated AI from
  human (AI 0.09 to 0.19, human 0.41 to 0.99). Vocabulary variety ran the wrong
  way (AI 0.81 to 0.90, human 0.77 to 0.92), and punctuation density overlapped
  completely (0.06 to 0.11 for both). So I gave the other two measures weight 0,
  kept them measured and visible, and wrote the finding down in `stylometry.py`
  and in *Signal two* above, instead of weighting a measure the data
  contradicted. I also fixed a mismatch the first version had: the code counted
  full stops as punctuation, but the numbers I had checked did not, so I made
  the code match the evidence.

**One more thing to be clear about.** The example texts in the Sample Run were
drafted by Claude as stand-ins, and the writers named there (`writer_ana`,
`writer_ben`, `writer_cara`) are made up. The clearly-human and borderline
scenario texts in `scenarios.py` are also AI-drafted stand-ins and do not yet
provide evidence for criteria 2 and 3. The ten pieces in the criterion 1
scenario are my supplied writing and are evaluated separately.

<!-- ═══════════════════════ UNIT 8 — THE TEST ═══════════════════════ -->

---

## Rate Limiting

**My limits:** 5 per minute, 50 per day, for each caller, on `POST /submit` only.
(Set in `config.py` as `RATE_LIMIT_PER_MINUTE` and `RATE_LIMIT_PER_DAY`, with
`RATE_LIMITING_ENABLED = True`.) `GET /health` reports that limiting is on.

**Why those numbers and not others:**

A **rate limit** caps how many requests one caller can make in a window of time.
Here it matters for two reasons: each submission runs a language model, which
costs real time, and each answer tells the caller a little about where my
thresholds sit. A script that sends a thousand slightly different texts and
watches which label comes back can *map* those thresholds, then write text that
lands just under them. A limit can't stop that, but it can make it slow. I chose
the numbers by setting the two people the brief describes side by side:

| | A real writer | A script mapping my thresholds |
|---|---|---|
| What they do | Submit a piece, read the label, maybe edit and submit again | Send hundreds or thousands of variations and watch the labels |
| How fast | Each round trip takes a person tens of seconds, so even an impatient writer manages 3 or 4 a minute at most | As fast as the service answers |
| How many in a day | A heavy honest day (many pieces, many revisions) is perhaps 15 to 25 | Finding one threshold on one text by repeated halving takes about 7 probes to get within 0.01, so mapping a range of texts takes hundreds |

- **5 a minute** leaves the impatient writer some room and makes one submission
  every 12 seconds the fastest any single caller can go. It also protects the
  machine, since every submission runs the model for a second or two.
- **50 a day** is roughly double the heaviest honest day I can imagine, so a real
  writer should never meet it. It is the number that actually slows a script: a
  thousand probes from one identity takes about 20 days at 50 a day. The
  starter's default of 200 a day would take 5.
- I rejected 10 a minute because it would let a script run twice as fast for no
  benefit to any writer, and I rejected a day limit under about 30 because a
  writer revising several pieces in one sitting could hit it by honest use.

**What the limit does not do.** It doesn't make threshold-mapping impossible,
only slower, and it can be sidestepped (see the next paragraph). It also doesn't
touch `POST /appeal`, `/log`, `/health` or `/ping`. That is deliberate: a writer
who has been wrongly labelled, and who has also used up their submissions, must
still be able to appeal. A test checks this.

**What a caller counts as:** The limit is counted per **`creator_id`** when the
request has a usable one, and per network address when it doesn't (so a request
with no or an invalid `creator_id` can't escape being counted either). The two
ways of counting fail differently, and I chose with that in mind:

- **Per `creator_id`** treats each writer separately, so one heavy writer can't
  use up anyone else's allowance. Its weakness is that the caller chooses their
  own `creator_id`: a script that invents a fresh one for every request looks
  like a thousand different callers and is **never limited at all**. I know this
  is a real hole. Every row of the attack set uses its own `creator_id`, so those
  attacks will not trip the limit, and I expect that to show up in the attack run.
- **Per address** is much harder to dodge, but a household, school or library
  looks like one caller and shares one allowance. On this machine it would be
  worse: every request, including my evaluation harness and the attack run, comes
  from `127.0.0.1`, so everything would share one bucket and block my own testing.

I kept `creator_id` as the main key because the project's own tooling depends on
it and because shared allowances punish honest writers, who are the people this
service is supposed to protect. A real deployment would count both, with a looser
per-address limit behind the per-creator one. Every request to `/submit` counts
toward the limit, including ones that are then refused for bad input, so sending
junk is no way around it.

**The run of status codes when I pushed past it:**

```bash
$ python run_attacks.py --flood 15
15 submissions as 'flood_tester' against http://127.0.0.1:5000
```

```
200 200 200 200 200 429 429 429 429 429 429 429 429 429 429
```

Exactly 5 pass, then every one after is `429`, which is my 5-per-minute limit
working exactly as set. `GET /log` confirms both halves: the 5 passing requests
each wrote a normal `decided` entry (with real scores and a label), and all 10
refused requests wrote a `rejected` entry with `"reason": "rate_limited"` and
`"limit": "5 per 1 minute"`, attributed to `flood_tester`. Nothing was lost
silently.

---

## Attack Run — Before

<!-- Every attack with its outcome and a held-or-broke mark.
     `run_attacks.py --label before` produces the table. -->

The full run is in `results/attack_run_2026-11-10_1833_before.md`: 56 of 56
requests completed, with no crash or 5xx. I mark an evasion **BROKE** whenever
AI-targeted text avoids the AI label, including an `unsure` result; an unsure
result avoids an accusation, but it also means this detector did not identify
the AI text. For false-positive attacks, only an `ai` label is a break. The
flood is held as a batch because the first five are within the stated quota and
the next seven are rejected. `RQ10` and `RQ11` are held by the limiter before
the route, so they do not prove how `/submit` handles those content types.

**Count:** 15 broke, 41 held.

| ID | Result | Verdict |
|---|---|---|
| EV01 | 200, unsure, 0.537 | BROKE |
| EV02 | 200, human, 0.372 | BROKE |
| EV03 | 200, unsure, 0.624 | BROKE |
| EV04 | 200, unsure, 0.769 | BROKE |
| EV05 | 200, human, 0.286 | BROKE |
| EV06 | 200, human, 0.359 | BROKE |
| EV07 | 200, unsure, 0.543 | BROKE |
| EV08 | 200, unsure, 0.518 | BROKE |
| EV09 | 200, unsure, 0.625 | BROKE |
| EV10 | 200, unsure, 0.805 | BROKE |
| FP01 | 200, unsure, 0.589 | HELD |
| FP02 | 200, unsure, 0.805 | HELD |
| FP03 | 200, unsure, 0.775 | HELD |
| FP04 | 200, unsure, 0.761 | HELD |
| FP05 | 200, unsure, 0.810 | HELD |
| FP06 | 200, unsure, 0.653 | HELD |
| FP07 | 200, unsure, 0.513 | HELD |
| FP08 | 200, unsure, 0.459 | HELD |
| PI01 | 200, human, 0.365 | BROKE |
| PI02 | 200, human, 0.244 | BROKE |
| PI03 | 200, unsure, 0.659 | HELD |
| PI04 | 200, unsure, 0.574 | HELD |
| PI05 | 200, unsure, 0.591 | HELD |
| PI06 | 200, unsure, 0.568 | HELD |
| MF01 | 400, rejected | HELD |
| MF02 | 422, rejected | HELD |
| MF03 | 200, human, 0.312 | BROKE |
| MF04 | 200, human, 0.313 | BROKE |
| MF05 | 200, unsure, 0.687 | HELD |
| MF06 | 200, unsure, 0.687 | BROKE |
| MF07 | 200, unsure, 0.676 | HELD |
| MF08 | 413, rejected | HELD |
| RQ01 | 400, rejected | HELD |
| RQ02 | 400, rejected | HELD |
| RQ03 | 400, rejected | HELD |
| RQ04 | 400, rejected | HELD |
| RQ05 | 400, rejected | HELD |
| RQ06 | 400, rejected | HELD |
| RQ07 | 400, rejected | HELD |
| RQ08 | 400, rejected | HELD |
| RQ09 | 400, rejected | HELD |
| RQ10 | 429, rate-limited before route | HELD |
| RQ11 | 429, rate-limited before route | HELD |
| RQ12 | 400, rejected | HELD |
| FL01_01 | 200, within five-request quota | HELD |
| FL01_02 | 200, within five-request quota | HELD |
| FL01_03 | 200, within five-request quota | HELD |
| FL01_04 | 200, within five-request quota | HELD |
| FL01_05 | 200, within five-request quota | HELD |
| FL01_06 | 429, rate_limited | HELD |
| FL01_07 | 429, rate_limited | HELD |
| FL01_08 | 429, rate_limited | HELD |
| FL01_09 | 429, rate_limited | HELD |
| FL01_10 | 429, rate_limited | HELD |
| FL01_11 | 429, rate_limited | HELD |
| FL01_12 | 429, rate_limited | HELD |

**Ten audit log entries from the run**

<!-- Choose entries that show the interesting failures, not the ten easiest. -->

```json
[
  {"timestamp":"2026-11-11T00:32:58+00:00","content_id":"d4042fc0-9d63-45c5-9363-7e4c25222bbe","creator_id":"attacker_EV02","guess":"human","model_score":0.5943,"style_score":0.001,"combined_score":0.3718,"label":"We think this was probably written by a person.","status":"decided"},
  {"timestamp":"2026-11-11T00:32:59+00:00","content_id":"9b16e0d0-7822-4c9f-9d1b-87c902d4b9df","creator_id":"attacker_EV05","guess":"human","model_score":0.3212,"style_score":0.25,"combined_score":0.2856,"label":"We think this was probably written by a person.","status":"decided"},
  {"timestamp":"2026-11-11T00:33:01+00:00","content_id":"ed02066d-e0ce-4a46-ad3c-860bd8e8656c","creator_id":"attacker_FP05","guess":"unsure","model_score":0.8005,"style_score":0.819,"combined_score":0.8097,"label":"We can't tell whether this was written by a person or with an AI tool. Our checks aren't perfect, and plain or very formal writing can look the same to them either way. This is not a finding that anything is wrong.","status":"decided"},
  {"timestamp":"2026-11-11T00:33:02+00:00","content_id":"d76be38f-9fb6-42ef-a7d2-a0d640dee4b1","creator_id":"attacker_PI02","guess":"human","model_score":0.2044,"style_score":0.283,"combined_score":0.2437,"label":"We think this was probably written by a person.","status":"decided"},
  {"timestamp":"2026-11-11T00:33:02+00:00","creator_id":"attacker_MF02","event":"rejected","status":"rejected","reason":"text_too_short"},
  {"timestamp":"2026-11-11T00:33:03+00:00","content_id":"d1e399d9-61fd-4cde-aa93-c15357f8349b","creator_id":"attacker_MF03","guess":"human","model_score":0.0,"style_score":0.5,"combined_score":0.3125,"label":"We think this was probably written by a person.","status":"decided"},
  {"timestamp":"2026-11-11T00:33:03+00:00","content_id":"ee5e113a-5ea5-454b-a3c2-931cf4823a62","creator_id":"attacker_MF04","guess":"human","model_score":0.0112,"style_score":0.5,"combined_score":0.3133,"label":"We think this was probably written by a person.","status":"decided"},
  {"timestamp":"2026-11-11T00:33:04+00:00","creator_id":"attacker_MF08","event":"rejected","status":"rejected","reason":"text_too_long"},
  {"timestamp":"2026-11-11T00:33:04+00:00","creator_id":"unknown","event":"rejected","status":"rejected","reason":"rate_limited","limit":"5 per 1 minute"},
  {"timestamp":"2026-11-11T00:33:05+00:00","creator_id":"attacker_flood","event":"rejected","status":"rejected","reason":"rate_limited","limit":"5 per 1 minute"}
]
```

**The single worst outcome** — the one I'd least want to explain to a writer
whose work got caught by it:

FP05, the human-targeted technical documentation sample, scored 0.8097 and was
labelled `unsure`, only 0.0403 below the 0.85 AI threshold. No false-positive
sample was actually labelled AI, so this is a near miss rather than a false
accusation. The more severe overall detector failure is EV05: heavily edited
AI-style text was labelled human at 0.2856.

---

## Run Log and Verdicts

<!-- Your five criteria across three trials. `run_eval.py --label before`. -->

| Criterion | Target | Run 1 | Run 2 | Run 3 | Verdict |
|---|---|---|---|---|---|
| 1. Own-writing false positives | At most 1 of 10 labelled AI | missed | missed | missed | MISS: 2/10 plain pieces labelled AI |
| 2. Score spread | AI mean at least 0.30 above human; 4/5 each side of 0.50 | met | met | met | Provisional; human set is AI-drafted |
| 3. Label coverage | All labels; 3/4 borderline unsure; real label text | met | met | met | Provisional; human/borderline sets are AI-drafted |
| 4. Appeal path | 10/10 appeals recorded; 5/5 unknown ids refused | met | met | met | MET |
| 5. Bad input | 8/8 JSON 4xx errors, service alive, 8 rejections | met | met | met | MET; see 429 note below |

Criterion 1 now uses the ten pieces I supplied. It missed in all three trials:
2 of 10 were labelled high-confidence AI, against the limit of 1. The two
false positives were the plain routine description (0.9053) and grocery-trip
description (0.8957); both have a style score of 1.0. Criteria 2 and 3 still
use the AI-drafted clearly-human and borderline stand-ins documented in
`scenarios.py`, so their passing results are provisional until those sets are
replaced with my own writing.

Criterion 5 met its written 4xx contract, but one or two requests without a
usable `creator_id` received 429 in some trials. Those requests were rejected
and logged by the address-based limiter before `/submit` ran; that proves the
fallback limit worked, not that the route's malformed-body checks handled those
specific requests. The focused Flask tests exercise those route cases directly.

**Real output from one trial**, pasted as text, naming the file and function
that produced it:

```json
[
  {"status":400,"json_ok":true,"sent":"{\"creator_id\": \"eval_bad_missing\"}","error":"invalid_input","message":"text must be a non-empty string."},
  {"status":400,"json_ok":true,"sent":"(empty text)","error":"invalid_input","message":"text must be a non-empty string."},
  {"status":400,"json_ok":true,"sent":"   \\n\\t  ","error":"invalid_input","message":"text must be a non-empty string."},
  {"status":400,"json_ok":true,"sent":"{\"text\": null, \"creator_id\": \"eval_bad_null\"}","error":"invalid_input","message":"text must be a non-empty string."},
  {"status":400,"json_ok":true,"sent":"{\"text\": 12345, \"creator_id\": \"eval_bad_number\"}","error":"invalid_input","message":"text must be a non-empty string."},
  {"status":400,"json_ok":true,"sent":"{\"text\": \"This one is fine apart from the missing creator.\"}","error":"invalid_input","message":"creator_id must be a non-empty string."},
  {"status":400,"json_ok":true,"sent":"[1, 2, 3]","error":"invalid_input","message":"Send a JSON object with text and creator_id."},
  {"status":413,"json_ok":true,"sent":"word word word word word word word word word word word word word word ","error":"text_too_long","message":"text is over 20,000 characters."}
]
```

From `results/run_2026-11-10_1928_before.md`, produced by
`run_eval.py::run_submit_trial`, Trial 1 of **bad input**. The report also
records `{"alive_after": true, "new_rejections": 8}` for this trial.

Trial 1 of **my own writing** from the same report shows the two plain-text
false positives (items 8 and 9):

```json
[
  {"guess":"ai","confidence":0.9053,"model_score":0.8106,"style_score":1.0,"sent":"I wake up at seven in the morning, brush my teeth, and turn on the cof"},
  {"guess":"ai","confidence":0.8957,"model_score":0.7913,"style_score":1.0,"sent":"I drove down to the local grocery store on Tuesday afternoon using the"}
]
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

The attack set has no 5xx or crashes; the “broke” marks above mean the attack
achieved its stated classification/input goal, not that the process crashed.

- **Evasion, 10/10:** The label mapping is the final weakness: AI-targeted text
  never reached the 0.85 AI line. EV02 and EV06 drove the style signal to 0.001
  and 0.000 by adding extreme sentence-length variation, pulling the combined
  scores to 0.3718 and 0.3592. EV05 lowered both signals (0.3212 and 0.2500),
  so the combination could not recover the AI origin. The other seven were
  `unsure`, which avoids an AI finding but still lets the evasion avoid the AI
  label.
- **Own-writing false positives, 2/10:** In each trial, pieces 8 and 9 crossed
  the 0.85 AI threshold. Their sentences are similar in length, which makes the
  sentence-spread measure report a maximum AI-like style score of 1.0. The
  model scores (0.8106 and 0.7913) also lean high. Because each signal pair is
  less than 0.30 apart, the disagreement rule does not pull the average toward
  unsure; the combined scores are 0.9053 and 0.8957, and label mapping calls
  both AI. This is a false positive at the signal/combining/threshold path, not
  a route or logging failure.
- **Prompt injection, 2/6:** PI01 and PI02 received the requested `human`
  label. The route does not execute the text as instructions; instead, the
  detector treats the injected words as ordinary text. The model and style
  signals both landed low (PI02: 0.2044 and 0.2830), and the combined score
  crossed the human threshold. PI04's hostile markup did not change the fixed
  label, and PI05's supplied JSON fragment did not become audit fields.
- **Malformed text, 3/20:** The route checked that text was a non-empty string,
  but not that it contained usable text. Control characters, punctuation-only
  text, and emoji-only text reached the detector and received decisions. This
  was a route-validation gap, fixed below. The giant single token remained
  accepted but did not crash and was labelled unsure; the right-to-left Arabic
  sample is valid writing and should remain supported.
- **False positives, 0/8:** None of the human-targeted samples received an AI
  label. FP05 was the closest to the line at 0.8097. These samples are still
  AI-drafted stand-ins, so they do not establish the false-positive rate on my
  own writing.
- **Flood and malformed-request limit, held:** The shared-creator flood passed
  five requests and then produced 429s. RQ10 and RQ11 also got 429s under the
  address fallback, before the route could inspect their content types.

---

## The Improvement

**What I changed:**

I added route-level checks in `app.py` to reject Unicode control characters
(except normal line breaks/tabs) and text with no alphanumeric character. These
return a logged 400 before either signal runs. Arabic letters still pass. I
added regression tests for control characters, punctuation-only input, and
right-to-left text.

**Which diagnosis pointed at it:**

The three malformed-content cases that were scored as decisions (MF03, MF04,
MF06) showed the route's non-empty-string check was too weak. The change fixes
that specific route gap; it does not change either signal, the combination, or
the label thresholds.

### Attack Run — After

<!-- Same format. `run_attacks.py --label after` -->

The full report is `results/attack_run_2026-11-10_1850_after.md`. All 56
requests completed without a crash or 5xx. The same verdict rule gives **12
broke, 44 held**: the three invalid-content cases now return 400, while all ten
evasion cases and the two successful prompt-injection cases remain unchanged.

| ID | Result | Verdict |
|---|---|---|
| EV01 | 200, unsure, 0.537 | BROKE |
| EV02 | 200, human, 0.372 | BROKE |
| EV03 | 200, unsure, 0.624 | BROKE |
| EV04 | 200, unsure, 0.769 | BROKE |
| EV05 | 200, human, 0.286 | BROKE |
| EV06 | 200, human, 0.359 | BROKE |
| EV07 | 200, unsure, 0.543 | BROKE |
| EV08 | 200, unsure, 0.518 | BROKE |
| EV09 | 200, unsure, 0.625 | BROKE |
| EV10 | 200, unsure, 0.805 | BROKE |
| FP01 | 200, unsure, 0.589 | HELD |
| FP02 | 200, unsure, 0.805 | HELD |
| FP03 | 200, unsure, 0.775 | HELD |
| FP04 | 200, unsure, 0.761 | HELD |
| FP05 | 200, unsure, 0.810 | HELD |
| FP06 | 200, unsure, 0.653 | HELD |
| FP07 | 200, unsure, 0.513 | HELD |
| FP08 | 200, unsure, 0.459 | HELD |
| PI01 | 200, human, 0.365 | BROKE |
| PI02 | 200, human, 0.244 | BROKE |
| PI03 | 200, unsure, 0.659 | HELD |
| PI04 | 200, unsure, 0.574 | HELD |
| PI05 | 200, unsure, 0.591 | HELD |
| PI06 | 200, unsure, 0.568 | HELD |
| MF01 | 400, rejected | HELD |
| MF02 | 422, rejected | HELD |
| MF03 | 400, rejected | HELD |
| MF04 | 400, rejected | HELD |
| MF05 | 200, unsure, 0.687 | HELD |
| MF06 | 400, rejected | HELD |
| MF07 | 200, unsure, 0.676 | HELD |
| MF08 | 413, rejected | HELD |
| RQ01 | 400, rejected | HELD |
| RQ02 | 400, rejected | HELD |
| RQ03 | 400, rejected | HELD |
| RQ04 | 400, rejected | HELD |
| RQ05 | 400, rejected | HELD |
| RQ06 | 400, rejected | HELD |
| RQ07 | 400, rejected | HELD |
| RQ08 | 400, rejected | HELD |
| RQ09 | 400, rejected | HELD |
| RQ10 | 429, rate-limited before route | HELD |
| RQ11 | 429, rate-limited before route | HELD |
| RQ12 | 400, rejected | HELD |
| FL01_01 | 200, within five-request quota | HELD |
| FL01_02 | 200, within five-request quota | HELD |
| FL01_03 | 200, within five-request quota | HELD |
| FL01_04 | 200, within five-request quota | HELD |
| FL01_05 | 200, within five-request quota | HELD |
| FL01_06 | 429, rate_limited | HELD |
| FL01_07 | 429, rate_limited | HELD |
| FL01_08 | 429, rate_limited | HELD |
| FL01_09 | 429, rate_limited | HELD |
| FL01_10 | 429, rate_limited | HELD |
| FL01_11 | 429, rate_limited | HELD |
| FL01_12 | 429, rate_limited | HELD |

**Did it help, and how do I know:**

Yes, for the narrow malformed-text gap: MF03, MF04, and MF06 changed from 200
decisions to 400 rejections. Arabic MF07 remains accepted, as it should. It did
not improve evasion detection or the plain-writing false positives: all ten EV
outcomes, both prompt-injection human labels, and the two 0.85+ own-writing
scores are unchanged. Criterion 1 therefore still misses in every after trial;
criteria 2 and 3 remain provisional until their AI-drafted stand-ins are
replaced with my own writing.
<!-- Widening the unsure band usually fixes one problem and creates another.
     Reporting that trade honestly is worth full credit. -->



---

## What's Still Broken

<!-- For each attack still getting through and each criterion still missed:
     what you'd do, and why you stopped. -->

The remaining evasion cases need better evidence or a more informative review
path, not a threshold lowered just to make this test pass. Lowering the 0.85 AI
line would make the unsure outputs look more decisive but would increase the
risk to plain, formal, and second-language writers. PI01 and PI02 also remain
human-labelled because the two signals measure predictability and sentence
shape, not authorship or the truth of an instruction embedded in the text.

MF05, the long single-token input, is still accepted and scored; I stopped
short of banning unusual words because that would reject legitimate names and
technical terms. MF07's Arabic is valid text, not malformed input. RQ10 and
RQ11 remain untested at the route because the fallback address quota returns
429 first. The evaluation harness also encountered 429s for creator-less
requests after earlier requests from the same local address; a production
evaluation should isolate the limiter state or run after its window resets.

Criterion 1 is now measured on my supplied writing and misses its target: the
two plain routine descriptions are called AI in every trial. Criteria 2 and 3
still need five distinct clearly-human pieces and four borderline pieces of my
own; their current stand-ins are AI-drafted, so those criteria cannot yet be
claimed as validated.

**Repository URL:** https://github.com/Angelica-M/ai201-project4-provenance-guard-starter-v2026

**The trade I'd make if this ran for real:**

<!-- Two sentences. Fewer wrong accusations means more AI text getting through.
     Say which way you'd go and WHO PAYS FOR IT. -->

I would keep the high AI threshold and wide unsure band: writers with plain or
formal prose get more protection, while readers and moderators bear the cost
of more AI text remaining undecided. I would pair the per-creator quota with a
looser, privacy-aware address quota so inventing new creator ids cannot bypass
all rate limits, while accounting for shared networks.

<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 7

         [x] criteria.md has five numbered criteria, each naming a target
         [x] Each has a reason underneath
         [x] POST /submit returns content_id, guess, confidence, label,
           model_score and style_score
         [x] Two signals that measure DIFFERENT things, each with a named blind spot
         [x] Three label variants, all reachable, written out in full
         [x] POST /appeal changes status and writes to the log
         [x] Signals and Scoring names scoring.py::combine_signals
         [x] Sample Run: a submission AND an appeal, as pasted text
         [x] At least four new commits (8 commits dated 2026-11-10)
         [x] Repository URL submitted: see URL above

     SUBMISSION CHECKLIST — unit 8

      [x] Rate limiting on /submit, with your numbers justified
      [x] The pasted run of status codes showing 429
      [x] Audit log with all nine fields, recording rejections too
      [x] The attack set run IN FULL, every input with an outcome
      [x] Ten audit log entries pasted as text
      [x] Five criteria across three trials (criterion 1 missed; criteria 2–3 provisional)
      [x] A diagnosis for every miss and every broken attack — stage AND mechanism
      [x] One improvement, with Attack Run — After
      [x] What's Still Broken, including the production trade
      [x] At least four new commits (8 commits dated 2026-11-10)
      [x] The SAME repository URL as last unit: see URL above

     Do not delete and recreate this repository.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
