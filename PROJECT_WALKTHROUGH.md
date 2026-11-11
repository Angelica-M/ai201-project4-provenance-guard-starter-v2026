# Unit 7 — Building a Safety Layer

Sites where people publish their own writing have a problem nobody has solved. Someone submits a poem. Was it theirs?

Detection tools get this wrong in both directions, and the two directions are not equally bad. Missing an AI-generated submission is a nuisance. Accusing a real writer of cheating is the kind of mistake that ends someone's relationship with a platform. Which means the interesting engineering here isn't the detector at all. It's what the system does when it isn't sure.

For your project you're building **Provenance Guard**: a small backend service a writing site could plug into. Text goes in. What comes back is a guess, a confidence score, a plain-English label a reader would actually see, and a way for the writer to push back on it.

This is also the unit the course stops handing you a script and starts handing you a service. The instructor half is a live build of the backend scaffolding (routing, POST, JSON in and out, testing an endpoint), and you'll leave class with a running service and one empty route. Everything past that route is yours.

This project runs for two units. In this unit, you build it and commit your criteria. Next unit you add the instrumentation that lets you see an attack, and then somebody attacks it with a set you didn't write. Same repository both units.

You write all five acceptance criteria. None are given.

**Why this matters:** Every AI feature that touches users eventually needs this layer: a decision, a confidence, a disclosure, and an appeal. The judgment it takes to decide where the threshold sits, what the unsure label says, and who bears the cost of a wrong call is not a machine learning skill. It's the thing that makes the difference between a model and a product, and it's increasingly what "responsible AI" means in a job description rather than a press release.

### Learning Objectives

By the end of this unit, you will be able to:

- Build an HTTP endpoint that accepts JSON and returns structured JSON
- Combine two genuinely different signals into a single confidence score
- Choose a threshold and defend where you put it
- Write user-facing text that communicates uncertainty honestly
- Design an appeal path for the case where your system is wrong
- Write acceptance criteria for a system where a false positive is expensive

**What you're building in this unit:** A running service with a `POST /submit` endpoint, two independent signals, a confidence score that varies, three written label variants, a `POST /appeal` path, and five acceptance criteria, all your own, committed before any results exist.

---

# Provenance Guard

Sites where people post their own writing have a new problem. Somebody submits a poem. Was it theirs?

Nobody can answer that reliably. Detection tools get it wrong in both directions, and the wrong direction that matters most is accusing a real writer of cheating. So the interesting engineering is not the detector. It's what the system does when it isn't sure.

In this unit you'll build **Provenance Guard**, a small backend service a writing site could plug into. Text comes in. What comes back is:

- a guess,
- a number saying how confident that guess is,
- a plain-English label the reader would see, and
- a way for the writer to push back.

This project runs for two units:

1. **This unit:** you build it and write down what "working" would mean.
2. **Next unit:** you add the parts that let you see an attack coming, then run one, using an attack set you didn't write.

Same repository both units.

You write all five acceptance criteria. None are given.

---

## 🎯 Goals

By the end of this unit you'll be able to:

- Build an endpoint that takes JSON in and sends structured JSON back
- Combine two different signals into one number
- Turn a number into something a non-technical reader would understand
- Write acceptance criteria for a system where being wrong has a cost

---

## 📖 Words you'll need

| Term | What it means |
| --- | --- |
| **Endpoint** | One address your service answers at. `/submit` is an endpoint. |
| **POST** | The kind of request that sends data in. A GET just asks for something. |
| **JSON** | A text format for structured data. Both sides of your service speak it. |
| **Signal** | One way of guessing. Yours will have two, measuring different things. |
| **Confidence score** | A number from 0 to 1 saying how sure the system is. |
| **Threshold** | The line where one label becomes another. You choose where it sits. |
| **False positive** | Calling a human's writing AI-generated. The expensive mistake here. |
| **Appeal** | A writer telling you they think you got it wrong. |

---

## 🚀 How to start the app

Run these from the project folder in PowerShell.

1. **Create and activate a virtual environment** (once to create, every new terminal to activate):

   ```powershell
   python -m venv .venv
   .venv\Scripts\Activate.ps1
   ```

   The prompt should start with `(.venv)`. If PowerShell blocks the script, run `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` once.

2. **Install dependencies** (torch is large, so this can take several minutes):

   ```powershell
   pip install -r requirements.txt
   ```

3. **Check the setup:**

   ```powershell
   python test.py
   ```

4. **Start the server** (leave this terminal running):

   ```powershell
   python app.py
   ```

5. **From a second terminal, check the control route.** On Windows, use `curl.exe` (not `curl`) and keep it on one line:

   ```powershell
   curl.exe -X POST http://127.0.0.1:5000/ping -H "Content-Type: application/json" -d '{\"message\": \"hello\"}'
   ```

   JSON coming back means the service is working. Leave `/ping` alone as a control: if it still answers when something else breaks, the problem is in your handler.

6. **Try the route you're about to build.** It should return `501`, meaning not built yet, which is the correct starting position:

   ```powershell
   curl.exe -i -X POST http://127.0.0.1:5000/submit -H "Content-Type: application/json" -d '{\"text\": \"hello world\", \"creator_id\": \"user1\"}'
   ```

---

## 🧠 What I learned

_To be filled in as the project progresses._

- **Windows vs. bash `curl`:** in PowerShell, `curl` is an alias for `Invoke-WebRequest`. Use `curl.exe` on one line, with the JSON quotes escaped as `\"`.
- **Virtual environments:** activate `.venv` before installing or running anything, so packages don't land in the system Python.

---

## 🏆 Showcasing the learning

_To be filled in: pasted curl responses, screenshots, and notes that show the project working._

---

## 🧭 Milestones

Each milestone below is recorded as it is worked on. Where the README has a section for the answer, the full answer lives there and this file summarizes it. Where it doesn't, the full answer lives here.

### Milestone 1: Trace a submission before you build one

**The idea:** Seven pieces have to work together. Build them one at a time without knowing how they connect and you get a service that works feature by feature and breaks at the seams. So write the path down first.

**Where the answers went**

| Step | Answer lives in |
| --- | --- |
| 1. The path a submission takes | README, *What This Does* |
| 2. What the two signals measure, and their blind spots | README, *Signals and Scoring* (signal one and signal two) |
| 3. Trace the false positive | This file, below |
| 4. The shape of the two endpoints | This file, below |

**1. The path, at a glance**

```
request -> content_id -> signal one -> signal two -> combine -> label -> log + response
app.py     app.py        detector.py   stylometry.py  scoring.py  scoring.py  audit.py
```

Each step and what it adds is written out in the README.

**2. The two signals, at a glance**

| | Signal one (`detector.py`) | Signal two (`stylometry.py`) |
| --- | --- | --- |
| Measures | How predictable the text is to a language model | Shape of the text: sentence length spread, word variety, punctuation |
| Why it might differ | AI picks likely words, so it is easy to predict | AI tends toward even sentences and narrower vocabulary |
| Blind spot | Predictable is not the same as AI. Plain human writing scores as AI, ornate AI scores as human | Can't read. Typos, chopped sentences, or pasted quotes change the shape without changing the substance |

Both blind spots are real. The next unit's attack set is built out of them.

**3. Trace the false positive**

*A real writer submits real work and the system calls it AI.* Take someone writing in English as a second language. They stick to vocabulary they're sure of and write short, plain sentences. Every word is theirs.

| Stop | What happens |
| --- | --- |
| `POST /submit` | The text is valid, so it goes through. Nothing in the route can tell that this person is a real writer. |
| Signal one | Common words in short sentences are highly predictable, so the model score is high, probably 0.8 or more. |
| Signal two | Short, even sentences and a small vocabulary look machine-like, so the style score is high too, probably 0.6 to 0.8. |
| Combining | With the starter's 50/50 average the combined score lands around 0.7 to 0.8, which is over the 0.65 AI threshold. |
| Label | They are told the text was probably written by an AI. This is the failure. |
| Appeal | They can send `POST /appeal` with the `content_id` and their reasoning. The item moves to `under_review` and the log keeps both the decision and the appeal. No one re-checks it automatically. |

These numbers are my estimates from reading the code, not measured results. Milestone 4 has me run a plainly written human paragraph through the signals to check them.

What this shows:

- **Both signals fail in the same direction for this person.** They aren't independent for plain writing, so averaging them doesn't rescue the writer. Two agreeing signals feel like strong evidence, and here they are one mistake counted twice.
- **The people most likely to be accused have the least room to argue back.** Someone writing in a second language is the person least able to argue with an accusation written in fluent English.
- **The appeal is the only safety net, and the writer has to know it exists.** The `content_id` has to be in the response, and the AI label text has to say plainly that they can appeal.

What this decides, for Milestones 4 and 5:

- The "AI" label should be hard to earn. Leaning toward a wide unsure band and a high AI threshold, so that both signals have to be confident before anyone is accused.
- The cost is that more AI text will be labelled "unsure" instead of "AI". The people who pay for that are the readers, who get less protection, instead of the writers, who get falsely accused. That is the trade I would choose, and the thresholds in `config.py` are where it gets made.
- The unsure label must not read like an accusation, because the person reading it may have written every word.

**4. The contract for the two endpoints**

Fields marked *required* must be present. Every response is JSON. Every error has the shape `{"error": "<code>", "message": "<plain English>"}`. Every refused request is written to the audit log as a rejection.

*`POST /submit`*

Request:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `text` | string | yes | The writing to check. Must be non-empty. Too short to score (a few words) is an error. Capped at 20,000 characters. Only the first 400 tokens are scored. |
| `creator_id` | string | yes | Who submitted it. Non-empty. Used for the log, and in unit 8 for rate limiting. |

Response, `200`:

| Field | Type | Meaning |
| --- | --- | --- |
| `content_id` | string | Unique id for this submission. The only handle for an appeal. |
| `guess` | string | One of `"ai"`, `"human"`, `"unsure"`. |
| `confidence` | number, 0 to 1 | The combined score. 0 is confidently human, 1 is confidently AI. It measures how far the text leans toward AI, not how sure the system is of its guess. |
| `label` | string | The full sentence a reader sees. Always one of the three written variants. |
| `model_score` | number, 0 to 1 | Signal one on its own. Higher means more likely AI. |
| `style_score` | number, 0 to 1 | Signal two on its own. Same direction. |

Errors:

| Status | `error` | When |
| --- | --- | --- |
| 400 | `invalid_input` | Body isn't a JSON object, or `text` or `creator_id` is missing, empty or not a string. |
| 413 | `text_too_long` | `text` is over 20,000 characters. |
| 422 | `text_too_short` | Too little text to score. |
| 503 | `detector_unavailable` | The model couldn't be loaded. |

*`POST /appeal`*

Request:

| Field | Type | Required | Notes |
| --- | --- | --- | --- |
| `content_id` | string | yes | From the `/submit` response. |
| `reasoning` | string | yes | The writer's own words. Non-empty. |

Response, `200`:

| Field | Type | Meaning |
| --- | --- | --- |
| `content_id` | string | Echoed back. |
| `status` | string | Always `"under_review"`. |
| `message` | string | Plain-English confirmation that the appeal was recorded. |

Errors:

| Status | `error` | When |
| --- | --- | --- |
| 400 | `invalid_input` | Body isn't a JSON object, or `content_id` or `reasoning` is missing or empty. |
| 404 | `unknown_content_id` | No submission has that `content_id`. |

Appealing twice is allowed. Each appeal is recorded and the status stays `under_review`. Nothing is re-checked automatically.

**Read it back: could someone else build against this without asking me a question?**

I checked it for the questions a builder would ask. These were open until I wrote them down:

- *What does `confidence` mean?* It is the combined score, not certainty. It is written into the contract.
- *Which way do scores point?* Higher is more AI for `model_score`, `style_score` and `confidence`.
- *What are the allowed values of `guess`?* Exactly three.
- *What happens on bad input?* Named status codes and error codes, not a crash.
- *What does an appeal do to the log?* It appends. The original decision is never overwritten.

**Before moving on:** I can describe the path end to end, I can name both signals with their blind spots, and both endpoint shapes are written down. Done.

### Milestone 2: Write your acceptance criteria

**The idea:** An acceptance criterion says what "working" means, specifically enough that someone else could check it. "The detector is accurate" is an opinion. "Of 10 pieces I wrote myself, at most 1 is labelled high-confidence AI" is a criterion, because it names a number. The criteria are written before building, so that next unit I find out how I did against a standard I set when I couldn't know the answer.

**Where the answers went:** The criteria and their reasons are in [criteria.md](criteria.md). The README has no section for this milestone, so nothing was added there.

**The five criteria, at a glance**

| # | Criterion | Area | Target |
| --- | --- | --- | --- |
| 1 | Few of my own pieces get accused of being AI | False positives | At most 1 of 10 own pieces (3+ deliberately plain) labelled high-confidence AI, in every trial |
| 2 | Clearly-AI and clearly-human text score far apart | Score spread | Mean `confidence` gap of at least 0.30, and 4 of 5 per group on the right side of 0.50, in every trial |
| 3 | All three labels are reachable and always real | Label coverage | Each label appears at least once in every trial, 3 of 4 borderline inputs get "unsure", and 100% of labels are one of the three written sentences |
| 4 | An appeal always changes status and is always recorded | Appeal path | 10 of 10 appeals return 200 and `under_review` with a log entry, original entry unchanged. 5 of 5 unknown ids return 404 with no entry |
| 5 | Bad input is refused cleanly, never crashes | Bad input | 8 of 8 malformed requests get a JSON 4xx, 0 return a 500, `/ping` still answers, and 8 rejection entries are logged |

This covers all five areas in the brief, where the brief only asks for three. Criterion 1 is the one the others hang off, because it is where the false-positive decision from Milestone 1 becomes a number.

**How the criteria were designed (the concepts worth keeping)**

- **A criterion is a test someone else could run.** Each one names a count, a threshold, a status code or a log entry. If I couldn't say how to check it, it wasn't ready. Vague words like "well" or "accurate" are how a criterion ends up unmeasurable.
- **Pick the number from the cost of being wrong, not from what is easy to hit.** A wrong accusation costs one person their standing, and a missed AI piece costs the site little. So criterion 1 is the strictest, and it is deliberately not zero, because zero could only be met by labelling everything "unsure". Each reason in `criteria.md` says why that number and not the one either side of it.
- **Targets must hold in every trial, not on average.** The first signal runs a model, so the same input can score differently twice. Every target is written as a rule for each of the three trials. Criteria 4 and 5 involve no model, so they target every case rather than most.
- **Build the test set to be hard, not flattering.** Criterion 1 requires plain pieces because plain writing is the known weak spot from Milestone 1. A set of polished prose would pass without proving anything.
- **Set the target before seeing results, and never edit it afterwards.** The git history is the evidence. If I miss a target next unit, I diagnose it and try a fix. I don't lower the number. A revision is only allowed when a criterion turns out to be unmeasurable, and then it goes underneath the original.
- **Criteria connect back to the design.** Criterion 3 requires most borderline inputs to land in "unsure" because Milestone 1's design relies on a wide unsure band to protect real writers. Criterion 5 matches the error codes in the Milestone 1 contract.

**The test sets**

The criteria need something to run against, so the inputs were written now, before any score exists. They live in [scenarios.py](scenarios.py), which `run_eval.py` runs three times in unit 8.

| Set | Size | Used by | What it is |
| --- | --- | --- | --- |
| My own writing | 10 | Criterion 1 | 7 expressive pieces and 3 deliberately plain ones (short sentences, common words) |
| Clearly AI | 5 | Criteria 2, 3, 4 | Generic, evenly paced, stock phrases like "in today's fast-paced world" |
| Clearly human | 5 | Criteria 2, 3, 4 | Specific, uneven in length, with a detail only one person would write |
| Borderline | 4 | Criterion 3 | Ambiguous in four different ways: lightly edited AI, formal human prose, plain generic first-person, and AI structure around a personal claim |
| Label coverage | 12 | Criterion 3 | 4 clearly AI, 4 clearly human, 4 borderline, in a fixed order so each trial can be read straight off |
| Appeal path | 10 + 5 | Criterion 4 | The clearly-AI and clearly-human texts are submitted and then appealed; 5 more appeals use ids that were never issued |
| Bad input | 8 | Criterion 5 | Missing text, empty, whitespace only, null, a number, missing `creator_id`, a bare JSON list, and 50,000 words |

**Important: who wrote this text.** Claude drafted all of it as stand-ins, so none of it was written by me. That matters differently for each set:

- The *clearly AI* pieces are fine, because they really are AI-written.
- The *my own writing*, *clearly human* and *borderline* pieces are **not** mine. An AI imitating human writing is the weakest possible test of an AI detector, and criterion 1 literally says "pieces I wrote myself". Before the unit 8 results count as evidence for criteria 1, 2 and 3, I need to replace those sets with real writing of my own. The banner at the top of `scenarios.py` says the same.
- This should also be recorded honestly under *How I Used AI* in the README when I write it.

**Things to watch for later**

- Criterion 3's "all three labels reachable" depends on the style signal actually varying. While `style_signal` is still the 0.5 stub, the combined score can't leave 0.25 to 0.75 (a note in `config.py` explains this).
- Until `/submit` and `/appeal` are built (Milestones 3 to 5), the harness can only report misses against the real service. That is correct, and it is the reason the harness is tested against a stand-in service (below).
- The pieces' "clearly" and "borderline" labels were decided before any score existed. If a score later disagrees with my judgement, the criterion stays as written and the disagreement gets diagnosed, not edited away.

**Making every criterion testable: the harness**

A criterion is only testable if running it produces a yes or no. Two files do that, and a third proves they are right.

- **[scenarios.py](scenarios.py)** holds, for each criterion, the inputs *and* a `check` function. The check turns the target from `criteria.md` into code, such as "at most 1 of 10 labelled AI", and returns a yes/no plus the numbers behind it. Targets are copied exactly. Nothing is loosened to get a pass.
- **[run_eval.py](run_eval.py)** is the runner. It runs each scenario three times against the live service and prints `target met: yes/no` per trial and whether it *held in all three*. I extended it for two criteria the starter couldn't test:
  - **Criterion 4 (appeals)** needs a submission, then an appeal quoting the `content_id` that came back. The runner reads `/log` before and after the appeal and compares the two, which is how "the original decision is unchanged" and "the appeal was appended after it" become checkable facts. It then appeals ids that don't exist and confirms they are refused and leave no trace.
  - **Criterion 5 (bad input)** needs to send things that aren't normal text, including a body that is a bare list. After the batch it calls `/ping` to prove the service survived, and counts the new rejection entries in the log.
- **[test_eval_harness.py](test_eval_harness.py)** tests the measuring tool itself, so I can trust a "met". It needs no model and no running service. Run it with `python test_eval_harness.py`.

**How the harness was tested (the concepts worth keeping)**

- **Test the tester.** A check that wrongly says "met" is worse than no check, because it hides a failure. So each check is tested directly at its edges: exactly at the limit (passes), one past it (fails). Bugs live at boundaries.
- **Prove it can fail.** The harness is run against a small *stand-in service* that follows the Milestone 1 contract. With the stand-in behaving, all five criteria must read "met". Then it is made to misbehave one way at a time (accuse a writer, rewrite the log instead of appending, skip logging rejections, return a 500) and the matching criterion must read "missed". A harness that can't fail proves nothing.
- **A crash is a miss, never a pass.** If a request dies, a field is missing, or a check itself raises, the result is "missed" with the reason attached. Silence must never read as success.
- **The harness measures; it doesn't judge.** The report's Verdict column stays blank. Meeting a target is a measurement. The verdict is a judgement made after diagnosing why.
- **Keep tests from leaving mess.** Reports from the tests go to a throwaway folder, so the repo's `results/` stays reserved for real evidence.

**Results of that testing:** 36 tests pass (`python test_eval_harness.py`). I also ran the real harness against the unbuilt starter service as a smoke test. It finished without crashing and reported "target met: NO" for all five criteria, which is the correct starting position. That run also showed that the starter's placeholder `/submit` returns a 500, not a clean error, on a null, numeric or list `text`, which is exactly what the bad-input criterion is there to catch once I build the real route.

**Terms from this milestone**

| Term | What it means |
| --- | --- |
| **Acceptance criterion** | A statement of what "working" means, specific enough that someone else could check it. It names a number or something plainly observable. |
| **False positive** | A real person's writing labelled AI. The costly error on a writing site. |
| **False negative** | AI text labelled human. The cheaper error here. |
| **Trial** | One full run of a test set. The model can score the same input differently twice, so each criterion has to hold in all three trials. |
| **Test set** | The fixed collection of inputs a criterion is checked against. It is chosen before results exist. |
| **Borderline** | Text that honestly could be either. Where the "unsure" label is supposed to catch it. |
| **Score spread** | How far apart the scores of clearly-different inputs land. Little spread means the score isn't telling anything apart. |
| **Label coverage** | Whether every label can actually be produced by some input. |
| **Harness** | The program that runs the tests: it sends the inputs, collects the responses, and applies each criterion's check. |
| **Stand-in service (a fake)** | A small imitation of the real service that behaves predictably, used to prove the harness works before the real service exists. |
| **Boundary testing** | Testing exactly at and just beyond a limit (such as 1 versus 2 accused writers), because mistakes cluster at edges. |
| **Revision vs. lowering a target** | A criterion can be revised if it turned out to be unmeasurable. Lowering a number because it was missed is not a revision, and is not allowed. |

**Before moving on:** `criteria.md` has 5 numbered criteria, each names a number or an observable outcome, and each has a reason underneath. Done.

### Milestone 3: Get the endpoint running with one signal

**The idea:** One route, one signal, one real response. The second signal is deliberately not added yet. One working signal is easy to debug. Two broken ones are not, and you can't tell which is lying.

**Where the answers went:** The code is in [app.py](app.py) (`submit`). The README's *Sample Run* section holds the pasted requests and responses (step 5). Each step below was committed on its own.

**A note on testing:** an older `app.py` from an earlier smoke test was still holding port 5000 and couldn't be stopped from the tooling, so these steps were run on port 5001 (`PORT=5001 python app.py`). The code is identical either way. Use `5000` on your own machine.

**Step 1. Fill in `submit`: a hardcoded answer first**

What changed: the starter's `501 not_implemented` reply in `submit()` was replaced with a fixed JSON response: a placeholder `content_id`, `guess`, `confidence`, `label` and `model_score`. Nothing is computed.

Why do it this way: it separates two kinds of failure. If `curl` gets the hardcoded answer back, the route, the JSON handling and the server all work, so anything that breaks once real logic goes in is the logic's fault. The same idea is why `/ping` is left alone as a control.

How it was checked: `/ping` and `/submit` both answered `200` with JSON (see the README's Sample Run for the final version).

**Step 2. Run the first signal on its own**

Before wiring a signal into the route, run it from a terminal (`python detector.py "some writing here"`) on text whose answer is known. If a number looks wrong here, the signal is at fault. If it only looks wrong later, the wiring is. The first run downloads about 550 MB (the gpt2 model).

Real output, three inputs chosen before running (the text is from `scenarios.py`):

| Input | Perplexity | `model_signal` (higher = more likely AI) | Reading |
| --- | --- | --- | --- |
| Clearly AI ("In today's fast-paced digital landscape, effective communication...") | 19.4 | **0.7941** | Leans AI, as expected |
| Clearly human (the sourdough piece, "Mine's called Gerald") | 95.7 | **0.2301** | Leans human, as expected |
| In between (lightly casual city-life paragraph) | 32.4 | **0.6285** | Between the two, but closer to AI than human |

So the signal does separate obviously different text, and the in-between case lands in the middle. Perplexity is the raw "how surprised was the model" number. `model_signal` squashes it onto 0 to 1 (a logistic curve centred on perplexity 45), which is why 19.4 maps to 0.79 and 95.7 to 0.23.

**An extra check, and the most important finding so far.** Milestone 1 predicted this signal would call plain human writing machine-like. I ran the three deliberately plain pieces (short sentences, common words) to test that:

| Plain piece (drafted as a stand-in for a second-language or younger writer) | Perplexity | `model_signal` |
| --- | --- | --- |
| "I came to this country four years ago..." | 16.1 | **0.8385** |
| "My school is near my house..." | 14.8 | **0.8560** |
| "Last weekend I went to the lake..." | 15.5 | **0.8459** |

All three score *higher* than the clearly-AI paragraph (0.79). The prediction was right, and it was worse than expected: for this signal alone, plain writing is more machine-like than machine writing. That is the false-positive case from Milestone 1, now measured instead of estimated. It is why the second signal and the careful thresholds matter, and why criterion 1 includes plain pieces. (Caveat: those three pieces were drafted by Claude as stand-ins, not written by me, but the pattern is the point and matches the documented behaviour of the detector.)

No code changed in this step. The result was recorded here.

**Step 3. Wire the signal into the route**

What changed in [app.py](app.py) (`submit`), in the order a request now flows:

1. **Read the body** with `get_json(silent=True)`, so a body that isn't JSON gives `None` instead of crashing.
2. **Refuse what can't be scored**, with a status and a reason: not an object (400), `text` missing, empty or not a string (400), `creator_id` missing or empty (400), `text` over 20,000 characters (413, a new `MAX_TEXT_CHARS` in [config.py](config.py)). The checks run in that order because each assumes the one before passed.
3. **Run signal one**, `detector.model_signal(text)`. Two different faults are kept separate: text too short for the model to score is the caller's problem (422), and the model failing to load is the service's problem (503).
4. **Answer** with a fresh `content_id` (a UUID), the real `model_score`, and placeholders for `guess`, `confidence` and `label`.

Why the placeholders are constants and not derived from `model_score`: scoring and labelling are Milestones 4 and 5. Inventing a quick mapping now would put something that looks real under work that isn't done, and the later milestones need to start from a known blank.

Why `content_id` is generated now: `/appeal` has to find a decision again later, and a student who skips it rebuilds this whole flow afterwards (the starter says so in `app.py`).

Why bad input is handled now and not later: the error codes are the contract written in Milestone 1, and criterion 5 tests them. Every refusal goes through one small helper, `_error`, so they all share the same `{"error": ..., "message": ...}` shape.

Checked with `curl.exe` against the running service:

| Request | Result |
| --- | --- |
| Normal text | `200`, a UUID `content_id`, real `model_score` 0.8394, placeholder label |
| `text` empty | `400 invalid_input` |
| `creator_id` missing | `400 invalid_input` |
| Body is a JSON list | `400 invalid_input` |
| `text` is "Hi" | `422 text_too_short` |
| `/ping` | still `200` (the control) |

Not done yet, and expected at this point: nothing is written to the log (step 4), and rejections aren't logged either.

**Step 4. Write every submission to the audit log**

What changed in [app.py](app.py): after signal one runs, `submit()` calls `audit.log_decision(...)` with the content id, creator id, guess, `model_score` and a status of `decided`. [audit.py](audit.py) was given and writes one JSON object per line to `logs/audit.jsonl`. It is a file that can be read back, not `print()`.

Why a file and not `print()`: next unit an attack runs against this service, and an attack you can't see in a log is an attack you can't diagnose. A printed line scrolls away. A line in a file stays.

Decisions worth understanding:

- **Log before answering.** If the reply goes out first and the write then fails, the caller holds a decision the service has no record of, and an appeal against it would find nothing.
- **Blanks stay blank.** `style_score`, `combined_score` and `label` are logged as `null`, because those don't exist yet. An honest blank is better than a made-up value, and the entry already has the shape it will keep, so early and late entries can be compared later. All nine fields the unit 8 rubric needs are present from the start.
- **Refusals are logged too.** `_error()` now also calls `audit.log_rejection(...)`, because a request that is turned away and leaves no trace looks exactly like a quiet afternoon. If the log write itself fails, the error is swallowed so a clean `400` doesn't become a `500`.
- **Who sent a bad request.** The early validation errors pass `creator_id` through, so a rejected request with a usable `creator_id` is attributed to it. The first version logged `unknown` for an empty-text request from `user2`. I caught that by reading the log back, and fixed it.

How it was checked: one good submission and two bad ones were sent, then `logs/audit.jsonl` was read directly. The good one wrote a `decided` entry with a real `model_score`. Each bad one wrote a `rejected` entry with the reason `invalid_input` and the right creator.

**Step 5. Check it worked, and paste the evidence**

`GET /log` already works in the starter and returns the recent log entries as JSON, so it wasn't built. It was used to see whether the log entries were actually landing. That is the whole point of this step: don't assume the write worked, read it back through a different route.

What was done:

1. The test entries from step 4 were cleared, so the evidence starts clean.
2. Two submissions (one AI-style, one specific and odd, from two different writers) and one refused request (empty text) were sent with `curl.exe`.
3. `GET /log?limit=3` returned all three, in order: two `decided` entries and one `rejected`.
4. The requests and responses were pasted, as text, into the README under *Sample Run* (a screenshot would get no credit). The appeal block there is left marked "not built yet", because `POST /appeal` is Milestone 5.
5. `logs/audit.jsonl` was committed. The starter deliberately doesn't ignore `logs/`, because the log is evidence.

What the evidence shows:

| Check | Result |
| --- | --- |
| `/submit` returns a `content_id` and a real signal result | Yes, `model_score` 0.8394 and 0.3881 for the two texts |
| Every call writes an entry to `logs/audit.jsonl` | Yes, three calls and three lines |
| `GET /log` shows them | Yes, `count: 3`, and `/health` agrees (`log_entries: 3`, `detector_loaded: true`) |
| The signal moves with the text | Yes, the AI-style text scored far higher than the specific, odd one |

Extra checks that weren't in the steps: a text over 20,000 characters returns `413`, a number for `text` and a non-JSON body each return `400`, and all three were logged as rejections (run in-process with the log redirected to a temp folder, so the sample-run log wasn't touched). The 36 harness tests still pass, so the evaluation tooling wasn't disturbed.

**Milestone 3 summary: what is true now**

- `POST /submit` returns JSON with a `content_id` and a real signal result. `confidence`, `guess` and `label` are placeholders by design.
- Every call, good or refused, writes an entry to `logs/audit.jsonl`. `GET /log` shows them.
- What is still missing, on purpose: the style signal and `style_score` (Milestone 4), the combining rule and a real `confidence` (Milestone 4), the labels (Milestone 5), and `POST /appeal` (Milestone 5).

**What this milestone taught**

- **Build in an order that tells you which part is broken.** Hardcoded route, then the signal alone, then the two joined. At each step only one new thing could be wrong.
- **Run a component by itself before wiring it in.** Step 2 produced a real finding (plain human writing scores more machine-like than machine writing) before any route code depended on the signal.
- **Check by reading back through a different path.** The log was written by `submit()` and verified through `GET /log` and the file itself. That caught a real bug, a wrong creator on a refusal, that a response alone wouldn't have shown.
- **Prefer honest blanks to invented values.** Placeholders are labelled as placeholders, and missing fields are `null`.

**Before moving on:** `POST /submit` returns JSON with a `content_id` and a real signal result. Every call writes an entry to `logs/audit.jsonl`. `GET /log` shows them. Done.

**If it gets stuck** (the starter's advice, kept for reference): if the route isn't responding after about 40 minutes, go back to `/ping`. If `/ping` answers, the problem is in the handler. If it doesn't, it's the service itself. On Windows, check `curl.exe` is being used on one line before blaming the code. If the signal isn't working after about 40 minutes, make it return a fixed number with a comment saying so and move on, since Milestones 4 and 5 are the graded part.

### Milestone 4: Add the second signal and score confidence

**The idea:** The pipeline becomes multi-signal, and two numbers have to become one. This is the milestone people rush. The scoring function is where the false-positive decision from Milestone 1 actually gets made, and a careless one undoes everything built on top of it.

**Where the answers went:** The code is in [stylometry.py](stylometry.py) (signal two), [scoring.py](scoring.py) (`combine_signals`) and [config.py](config.py) (weights and thresholds). The README's *Signals and Scoring* section holds the combining rule and the split case. Each step below was committed on its own.

**Step 1. Build the second signal in `stylometry.py`**

What it does: turns a piece of writing into one number from 0 to 1, higher meaning more likely AI (the same direction as signal one). It measures the *shape* of the text without understanding a word, in three stages:

1. **Measure** three plain properties.
2. **Scale** each onto 0 to 1 ("AI-ness"). Raw numbers live on different scales (a ratio, a count), so adding them as they are would let whichever has the bigger numbers win by default.
3. **Combine** them as a weighted average.

| Measure | What it counts | Which way is "more human" |
| --- | --- | --- |
| Sentence length spread | Standard deviation of sentence lengths divided by their mean (a *coefficient of variation*; dividing by the mean makes long and short texts comparable) | Higher spread (lumpier) |
| Type-token ratio | Unique words over total words, over the first 100 words only | Higher (more varied vocabulary) |
| Punctuation density | Marks per word (commas, semicolons, colons, dashes, quotes, brackets, `?`, `!`, ellipses; not single full stops or apostrophes) | Higher |

**The finding: only one of the three measures works.** Before choosing weights, the raw values were computed for all 24 test texts. This is what came back:

| Measure | Clearly AI | Clearly human | Verdict |
| --- | --- | --- | --- |
| Sentence spread | 0.09 to 0.19 | 0.41 to 0.99 | **Separates well** |
| Type-token ratio | 0.81 to 0.90 | 0.77 to 0.92 | **Doesn't separate, and runs the wrong way.** The AI texts scored slightly *higher*, so the idea that AI uses a narrower vocabulary didn't show up at this length. |
| Punctuation density | 0.06 to 0.11 | 0.06 to 0.11 | **Doesn't separate.** The ranges overlap completely, and rare marks like semicolons are almost absent from texts this short. |

So the style score is built from the one measure that earns it. The other two are still computed, tested and printed in the terminal, but carry weight 0 in `WEIGHTS`. They were kept instead of deleted so the numbers stay visible, and so a weight can be raised in one line if longer texts show they matter. Orienting a measure the way the hypothesis says when the data says the opposite would add noise on purpose, so it wasn't done. This matches the milestone's own advice: *a signal that doesn't discriminate is a real finding, not something to hide.*

What this costs: with one measure carrying the whole score, the blind spot is sharper. Chopping AI text into sentences of different lengths moves the score a long way. That is exactly what next unit's attack set is built from.

Edge cases decided on purpose:

- **One sentence:** there is no spread to measure, and `statistics.stdev` raises on fewer than two values. The measure returns `0.0`, but `style_signal` doesn't read that as "perfectly even" (which would accuse every one-liner). It treats a single sentence as *no information* and returns a neutral `0.5`.
- **Empty text:** every measure returns `0.0` safely, and the style score is a neutral `0.5`.
- **Type-token ratio and length:** the ratio falls as text gets longer because common words repeat. Only the first 100 words are used, so a short text and a long one are compared fairly.

How it was checked:

- `python stylometry.py "some text"` prints every raw number, its scaled value and its weight. Run by itself, before anything depends on it.
- `python test_stylometry.py` runs 23 tests. They cover hand-worked values, the awkward inputs, a score that always stays between 0 and 1, and the direction (even sentences must score *higher*, more AI-like, than lumpy ones; a flipped direction would make everything above it wrong in a way that's hard to see).
- Scores on the test sets: clearly AI 0.94 to 1.00; clearly human 0.00 to 0.63; plain pieces 0.69 to 0.81; borderline 0.58 to 0.76. Notice that the plain pieces land well above the human ones. That is the same weak spot signal one has, and Step 2 deals with it.

**Step 2. Run both signals over the same pieces, and find where they split**

Both signals were run over the same texts. The three pieces from Milestone 3 (one clearly AI, one clearly human, one in between) came first, and then all 24 test texts, to find real disagreements. This is the point of running them side by side: a rule for disagreement has to be written for a disagreement that actually exists.

The three Milestone 3 pieces:

| Piece | Model signal | Style signal | Agree? |
| --- | --- | --- | --- |
| Clearly AI ("In today's fast-paced digital landscape...") | 0.794 | 0.976 | Yes, both lean AI |
| Clearly human (the sourdough piece) | 0.230 | 0.000 | Yes, both lean human |
| In between (the city-life paragraph) | 0.628 | 0.703 | Yes, both lean AI a little |

All 24 texts, grouped (model / style, each 0 to 1, higher = more likely AI):

| Group | Model signal | Style signal | Do they agree? |
| --- | --- | --- | --- |
| Clearly AI (5) | 0.79 to 0.85 | 0.94 to 1.00 | Yes, both high |
| Clearly human (5) | 0.13 to 0.54 | 0.00 to 0.63 | Mostly, with the two biggest splits below |
| My own writing, expressive (7) | 0.27 to 0.60 | 0.00 to 0.60 | Mostly |
| Plain writing (3) | 0.84 to 0.86 | 0.69 to 0.81 | **Yes, both high, and both wrong** |
| Borderline (4) | 0.63 to 0.80 | 0.58 to 0.76 | Yes, both middling to high |

**Where they split.** Two human pieces split by more than 0.5, in opposite directions:

| Piece | Model | Style | Gap | Why |
| --- | --- | --- | --- | --- |
| Funeral ("Uncle Ray's brass band played 'Danny Boy' slightly flat") | **0.127** | **0.632** | 0.505 | The model sees unusual words and names (perplexity 150), so it says human. The style signal sees only three sentences of 12, 19 and 28 words, a steady climb and not a lumpy mix, so it reads them as fairly even. *The model is right, the style signal is wrong.* |
| Cracked pavement ("Neat. Black. Smug.") | 0.540 | **0.000** | 0.540 | Three one-word sentences make the spread enormous, so the style signal calls it as human as possible. The model sits near its midpoint (perplexity 40.7). *The style signal is closer here.* |

This is the case the combining rule has to handle, and it is written up in the README under *A case where my two signals split*. The lesson: neither signal is reliably the better one, so neither can simply be trusted when they split. Disagreement is itself information, and the information is "be less sure".

**The bigger finding: agreement is not the same as being right.** The most dangerous group is not the one where the signals split. It is the *plain-writing* group, where both signals agree and both are wrong. The plain pieces average about 0.77 to 0.83 when the two scores are averaged, against about 0.89 to 0.92 for clearly-AI text, and *above* the lightly-edited-AI piece (about 0.67). Two agreeing signals feel like strong evidence, but here they are one mistake counted twice, because both read "short, even, plain sentences" as machine-like. No rule for combining the two numbers can fix that, because the numbers themselves are wrong in the same direction. Only where the label thresholds sit (Milestone 5) can protect those writers. So the combining rule should be written to handle disagreement well, and the thresholds should carry the false-positive protection.

No code changed in this step. The README's split-case section was started, and its last sentence is completed in Step 3.

**Step 3. Write the combining rule in `scoring.py::combine_signals`**

The brief says to write the rule down *before* coding it. That ordering matters because a rule written after the code just describes whatever the code happened to do. The rule was written in plain words first (now in the README under *The combining rule*), then coded to match.

**The rule, in two steps:**

1. **Average the two scores**, equal weights (0.5 and 0.5).
2. **Check whether they agree.** Less than 0.30 apart: the average is the answer. Further apart: move the average toward 0.5 ("unsure"), by an amount that grows in a straight line from nothing at a 0.30 gap to half the distance at a 0.70 gap or more.

A worked example, the funeral piece from Step 2: model 0.127, style 0.632. The average is 0.380 and the gap is 0.505, so the pull is (0.505 − 0.30) / (0.70 − 0.30) × 0.5 = 0.256. The average moves about a quarter of the way toward 0.5, landing at **0.411**.

**Options that were considered, and why this one:**

| Option | Why not |
| --- | --- |
| Plain average, nothing else | Simple, but it hides disagreement: 0.9 and 0.1 average to 0.5, the same as two signals that both said 0.5. Two methods *disagreeing* is not the same evidence as two methods *both being unsure*. |
| Trust one signal more (unequal weights) | There is no evidence for it. In Step 2 each signal was right where the other was wrong, once each. Picking a favourite would be a guess dressed up as a decision. |
| Take the lower score ("both must agree it's AI") | Protects writers well, but it throws away information whenever the signals differ even slightly, and with one signal blind to plain writing the lower score still isn't low enough for plain writers. |
| Average, then pull toward "unsure" when they disagree (**chosen**) | Uses all the information. Agreement is trusted. Disagreement lowers confidence in proportion to how big it is, and never raises it. |

**Properties the rule has, on purpose:**

- It can never move a score *away* from 0.5. Disagreement can only make the answer less confident, never more. This is tested across a grid of score pairs.
- It is symmetric (swapping the two signals changes nothing when weights are equal) and monotonic (raising either signal never lowers the result).
- Every number lives in [config.py](config.py), none is buried in the function, and `DISAGREEMENT_MAX_PULL = 0` turns the rule off for a plain average. Weights are treated as proportions, so they don't have to add up to 1.
- It works in both directions: a disagreeing pair that averages *low* is nudged *up* toward "unsure" too. That makes a confident "human" label slightly harder to earn. It is a real cost, accepted because when two methods disagree neither answer should be stated confidently.

**What the rule cannot do, written down so it isn't credited with more than it does:** it can't rescue a writer when both signals agree and are both wrong. Plain writing scores high on both, so the average is high, and no way of combining the two numbers fixes numbers that are wrong in the same direction. That protection has to come from the label thresholds in Milestone 5.

**How it was tested:** [test_scoring.py](test_scoring.py), 19 tests, no model needed. It checks hand-worked values (including the funeral example), the edges (exactly at the 0.30 switch-on, at the cap, a pair that averages exactly 0.5), and properties that must hold for *any* pair of scores, swept across a 21 × 21 grid: stays in 0 to 1, symmetric, never moves away from 0.5, monotonic. It also tests that weights act as proportions and that the rule can be switched off. One test of mine was wrong the first time (it expected the wrong value because I forgot a 0.4 gap switches the rule on) and one was vacuous (it compared a call with itself). Both were caught on review and rewritten, which is a reason to read tests, not just run them.

README sections completed here: *The rule*, *The numbers*, *A case where my two signals split, and what my rule does with it*, and the description of signal two (corrected to say only one of its three measures carries weight).

**Step 4. Test four deliberate inputs, and log all three numbers**

*Wiring first.* [app.py](app.py) `submit()` now runs signal two after signal one, calls `scoring.combine_signals(model_score, style_score)`, and uses the result as `confidence`. The response and the log entry both carry all three numbers: `model_score`, `style_score` and `combined_score`. The label is the only field still blank (`null`), because it belongs to Milestone 5.

Why log all three, and not only the combined score: when a score looks wrong, the first question is "which signal was off?". With only the combined number there is no way to answer, and next unit's whole diagnosis (name the stage and the mechanism) depends on being able to. `guess` and `label` are still placeholders until the thresholds exist.

*The four inputs*, chosen to cover the cases that matter, run through the real `/submit` route and read back from the log:

| Input | Model | Style | Combined | Gap |
| --- | --- | --- | --- | --- |
| Clearly AI (the "fast-paced digital landscape" paragraph) | 0.794 | 0.976 | **0.885** | 0.182 |
| Clearly human (the sourdough piece) | 0.230 | 0.000 | **0.115** | 0.230 |
| Formal human (the committee-findings paragraph) | 0.639 | 0.582 | **0.611** | 0.057 |
| Lightly-edited AI (the casual city-life paragraph) | 0.628 | 0.703 | **0.666** | 0.075 |
| *Extra: plain human (the "My school is near my house" piece)* | 0.856 | 0.796 | **0.826** | 0.060 |

What this shows:

- **Clearly AI and clearly human score far apart:** 0.885 against 0.115, a gap of 0.77. That is the milestone's headline result, and it is what criterion 2 asks for (a gap of at least 0.30).
- **The two inputs that matter are not separated.** Formal human writing (0.611) and lightly-edited AI (0.666) land only 0.055 apart. Both are middling, and neither signal can tell a careful human from a lightly edited machine. That is a limit of the signals, not a bug in the wiring.
- **The plain human piece scores higher than the edited AI.** 0.826 against 0.666. This is the Milestone 1 false-positive case, now measured end to end through the full pipeline.

*Across all 24 test texts*, the combined scores sort into these ranges:

| Group | Combined score |
| --- | --- |
| Clearly human (5) | 0.115 to 0.410 |
| My own expressive writing (7) | 0.142 to 0.510 |
| Borderline (4), including formal human and edited AI | 0.611 to 0.783 |
| Plain writing (3) | 0.765 to 0.830 |
| Clearly AI (5) | 0.885 to 0.924 |

The order is: human, then my expressive writing, then borderline, then plain writing, then clearly AI. The plain pieces sit *above* the borderline ones, which is the wrong way round, and only about 0.06 below the lowest clearly-AI score.

**What this means for Milestone 5 (thresholds).** The score now separates clearly-AI from clearly-human, and that works. The false-positive protection now depends entirely on where the "AI" threshold sits, because no rule for combining the signals can fix plain writing (see Step 3). On these test texts, an AI threshold of about 0.85 would call all five clearly-AI pieces AI while leaving every plain piece, the edited AI and the formal human as "unsure". But the margin is thin (the highest plain piece is 0.830, the lowest clearly-AI is 0.885), and two honest caveats apply: the plain and "human" texts are Claude's stand-ins, not my own writing, and a threshold that high means a lot of AI text will be labelled "unsure" instead of "AI". That is the trade from Milestone 1, and the unsure label's wording will matter a great deal. These are observations for Milestone 5, and the threshold is not chosen yet.

*Following the stuck-advice, in spirit:* when scores surprise you, print both signals for every input in one table and look. That is exactly what Step 2 and the table above are. It showed that one signal (style) is carried by a single measure, that the two signals agree where they are wrong together (plain writing), and which texts split. Those are real findings, and next unit's testing is meant to surface exactly this kind of thing.

*README:* the Sample Run was refreshed with a clean log. It now shows `style_score`, a real `confidence`, and log entries with all three numbers.

**Milestone 4 summary: what is true now**

- Both signals run and combine into one score. Clearly-AI and clearly-human text score far apart (0.885 against 0.115).
- The log records all three numbers for every decision.
- Still placeholders, by design: `guess` and `label` (Milestone 5), and `POST /appeal` (Milestone 5).

**What this milestone taught**

- **Check the data before trusting a hypothesis.** The brief's three measures sounded sensible, but only one separated the texts, and one ran the wrong way. Weighting a measure that the data contradicts would have added noise on purpose.
- **A disagreement rule and an agreement problem are different problems.** The rule handles two signals that split. It cannot handle two signals that agree and are both wrong, and pretending otherwise would hide the most important risk.
- **Write the rule before the code, and test the properties, not just examples.** Sweeping every pair of scores across a grid caught the class of bug that a few hand-picked examples miss.
- **Read tests as well as running them.** Two of mine were wrong on the first pass, and a passing suite would have hidden that.
- **Log the inputs to a decision, not just the decision.** Everything next unit depends on being able to see which stage was off.

**Before moving on:** both signals run and combine into one score. Clearly-AI and clearly-human text score noticeably apart. The log records all three numbers. Done.

### Milestone 5: Write the label and the appeal path

**The idea:** These are the last two pieces, and the ones a real person actually meets. A score of 0.62 means nothing to a writer. The label is where the service says what it means, and the appeal is the only thing standing between a wrong accusation and nothing at all.

**Where the answers went:** The label wording and ranges are in the README under *Label Variants*. The code is in [scoring.py](scoring.py) (`score_to_label`) and [app.py](app.py) (`submit` and `appeal`). The thresholds are in [config.py](config.py). The README's *Sample Run* holds the pasted evidence. Each step below was committed on its own.

**Step 1. Write the three labels and the score range each one covers**

Before any code, the exact words a reader sees were written down, in the README under *Label Variants*, with the score range for each:

| Label | Score range | What the reader sees |
| --- | --- | --- |
| High-confidence human | 0.40 or lower | "We think this was probably written by a person." |
| Unsure | Above 0.40, below 0.85 | "We can't tell whether this was written by a person or with an AI tool. Our checks aren't perfect, and plain or very formal writing can look the same to them either way. This is not a finding that anything is wrong." |
| High-confidence AI | 0.85 or higher | "Our checks found signs that this may have been written with an AI tool. We can't be sure, and we sometimes get this wrong. If you wrote it yourself, you can appeal and explain how you wrote it, and your appeal will be recorded and marked for review." |

**How the wording was decided**

- **Write for someone who has never heard the word "threshold".** No numbers, no "score", no "confidence" anywhere a reader can see. "We think this was probably written by a person" beats "human, 0.81 confidence".
- **The "unsure" label is the hard one, and the one a real writer is most likely to meet.** Plain writing, very formal writing and lightly-edited AI all land in it (Milestone 4 measured this). So it is written for a person who wrote every word and is reading it nervously: it leads with what is *not* known, names the reason as a limit of the checks (not of the writer), and says outright that nothing is being alleged. It asks nothing of the reader.
- **Only the "AI" label mentions appealing**, because that is the label that can wrongly accuse. It says "may have", "we can't be sure" and "we sometimes get this wrong", and it promises only what the service actually does: the appeal is *recorded and marked for review*. It does not promise a human will read it, because nothing in the service guarantees that.

**Where the lines sit, and who pays for it**

The thresholds are the false-positive decision from Milestone 1, finally made as numbers. Two lines, deliberately not symmetrical, because the two mistakes do not cost the same:

| Line | Value | Reason |
| --- | --- | --- |
| "AI" at or above | **0.85** | A wrong accusation is the expensive mistake. Plain human writing scored 0.765 to 0.830 in Milestone 4 (both signals misread it the same way), and the clearly-AI texts started at 0.885, so the line has to sit above 0.830. |
| "Human" at or below | **0.40** | Wrongly saying "probably a person" costs the site very little, so this line can be generous. Clearly-human texts landed at 0.115 to 0.410. |

The placeholder lines were 0.35 and 0.65. At 0.65, all three plain-writing pieces (0.765 to 0.830) would have been labelled AI, along with the lightly-edited AI (0.666): exactly the false accusations the unit is about. Moving to 0.85 removes that, and what it costs is stated plainly: a lot of ordinary AI text will be "unsure" and not "AI". The readers (less protection) pay instead of the writers (false accusations). That is the trade from Milestone 1, now a number.

Honest limits: the margin is thin (0.830 against 0.850 on one side, 0.885 against 0.850 on the other). It comes from a small set of test texts, and the plain and "human" ones are Claude's stand-ins, not my writing. So 0.85 is the first number to revisit once real writing is tested. A boundary score goes to the outer label (0.40 is "human", 0.85 is "AI"), and the three ranges cover 0 to 1 with no gap.

Changed in this step: [config.py](config.py) thresholds (0.35 / 0.65 to 0.40 / 0.85) with the reasoning beside them, and the README label table and wording. The wording was checked against the code's range printout (`scoring.label_ranges()`): `0.00 – 0.40`, `0.40 – 0.85`, `0.85 – 1.00`.

**Step 2. Fill in `score_to_label` and wire it into the response**

What changed:

- [scoring.py](scoring.py): the three label sentences are now constants (`LABEL_HUMAN`, `LABEL_UNSURE`, `LABEL_AI`), and `score_to_label` uses them. It is two comparisons and a fallback: at or above the AI line is "ai", at or below the human line is "human", and everything else is "unsure".
- [app.py](app.py): `submit()` now calls `score_to_label(combined_score)` and puts the real `guess` and `label` in the response. The log entry now records the label too, as the exact sentence the reader was shown, so the log says what they were *told* and not just what was computed. Every one of the nine log fields is now filled.

Why the order of the checks matters: testing the two outer labels first and letting everything else fall through to "unsure" is what guarantees there is no gap. Every number from 0 to 1 matches exactly one label. A score exactly on a line goes to the outer label (0.85 is "ai", 0.40 is "human").

**Proving all three labels are reachable.** The starter's advice is that if a label can't be reached, the ranges have a gap. The proof has two parts:

1. *By code:* a test sweeps every score from 0.000 to 1.000 in steps of 0.001 and checks that each gets exactly one of the three labels, that all three appear, and that the label never goes "backwards" as the score rises.
2. *By real submission:* three texts were sent through the running service, one per label:

| Writer | Text | Model | Style | Confidence | Label |
| --- | --- | --- | --- | --- | --- |
| writer_ana | AI-style paragraph | 0.8394 | 1.000 | 0.9197 | **ai** |
| writer_ben | The ferry paragraph | 0.3881 | 0.131 | 0.2596 | **human** |
| writer_cara | Plain first-person language-learning paragraph | 0.7114 | 0.864 | 0.7877 | **unsure** |

The third row is the one the thresholds exist for. At the old placeholder line of 0.65 that writer would have been told their work looked like AI. At 0.85 they are told "we can't tell", with an explanation that doesn't blame them.

**Tests added** ([test_scoring.py](test_scoring.py) grew from 19 to 34; [test_app.py](test_app.py) is new with 14). The new ones check:

- Every score gets one known label, all three are reachable, labels never go backwards, and boundary scores go to the outer label.
- The label wording itself: the three texts differ, none is a placeholder, each is a full sentence, none contains a digit or jargon ("threshold", "score", "confidence"), only the AI label mentions appealing, and the unsure label contains no accusing words.
- **The README shows exactly the text the code returns.** A test reads the README and fails if either label sentence has drifted from the code. The README is the submission, and the grader checks the code against what the README claims, so they must never disagree.
- Through the real route (with the model replaced by a fixed number, so it needs no download): all fields come back, each label is reachable, the log entry has all nine fields filled, the label in the log equals the label in the response, and all eight bad inputs from criterion 5 get a clean 4xx and a log entry.

*A note on how `test_app.py` stays safe:* every test writes to a throwaway log in a temp folder, never to the real `logs/audit.jsonl`, so running the tests cannot disturb the evidence. Confirmed: the real log still had exactly its four sample entries afterwards.

README: *Sample Run* was rewritten with the three submissions (one per label), the refusal, and the log read-back with real labels. The appeal block is still waiting for step 3.

**Step 3. Build `app.py::appeal`**

What it does: takes a `content_id` and the writer's `reasoning`, records the appeal in the log next to the original decision, marks the item `under_review`, and confirms. The appeal is the only thing standing between a wrong accusation and nothing at all, so it was built to fail loudly and never silently.

The route runs in this order, and the order is the design:

1. **Read and check the body**, the same way `/submit` does: it must be a JSON object, and `content_id` and `reasoning` must be non-empty strings (400 otherwise). `reasoning` is capped at 5,000 characters (413), so one request can't write an enormous line into a log that can never be trimmed.
2. **Check the `content_id` really exists** (404 `unknown_content_id` if not). This comes *before* the write, on purpose. Recording an appeal against an id that was never issued would tell the writer "recorded" about something nothing can ever act on. This is also the starter's stuck-advice, and the single most common way this endpoint "doesn't work": a typo'd or stale id fails quietly and looks like a broken route. The 404 message says what to check.
3. **Record the appeal** with `audit.log_appeal`, which *appends* a new line (`event: "appeal"`, `status: "under_review"`, the reasoning) and never edits the decision. The original stays exactly where it was and the appeal sits after it, so anyone reading the log can see what was decided, that it was challenged, and in what order.
4. **Confirm**, promising only what actually happens: "Your appeal has been recorded and this result is marked under review." No automatic re-checking, as the brief says, and no promise that a person will read it.

Decisions worth understanding:

- **"Sets the status to under_review" in an append-only log.** The log is never rewritten, so the status change is a *new line* carrying `under_review`, appearing after the original `decided` line. Reading an item's status means reading its latest line. This is the standard way to get an audit trail: you never lose what was previously true.
- **The creator comes from the decision, not the request.** An appeal is filed under the original writer. A request that includes some other `creator_id` is ignored, so an appeal can't be filed in someone else's name. (A test tries exactly that.)
- **Appealing twice is allowed.** Both appeals are recorded and the status stays `under_review`. Refusing a second appeal would punish a writer for adding detail.
- **Refusals are logged too**, including the typo'd id, so an attack or a mistake never shows up only as an absence.

**Evidence, through the running service** (pasted as text in the README's *Sample Run*):

- writer_ana's text was labelled "AI", but she wrote it herself. She appealed with her real `content_id` and reasoning, and got `200` with `status: under_review`.
- The same appeal with one character of the id changed got `404 unknown_content_id`, with a message saying to check the id was copied exactly. It was logged as a rejection and created no appeal.
- `GET /log` then showed entry 1 (her original decision, still `decided` and unchanged), entry 5 (the appeal, `under_review`, her reasoning, same `content_id`), and entry 6 (the rejected typo).

**Tests added** ([test_app.py](test_app.py), now 29 tests): the appeal is confirmed and appended after the decision; the decision is byte-for-byte unchanged; the creator can't be spoofed; appeals touch only their own item; appealing twice records both; an unknown id and a one-character typo are both a loud 404 with no appeal written; every bad body (nine variants) gets a clean 400 and writes nothing; a reasoning over the limit is refused and one at exactly the limit is accepted; unusual characters (quotes, newlines, accents, a dash) keep the log valid JSON on every line.

**A smoke test against the real service, with a caveat that matters.** The evaluation harness from Milestone 2 was run against the real service (three trials; the service's log and the report went to a scratch folder, so the committed evidence is untouched). All five criteria read "met" in all three trials:

| Criterion | Result in each of 3 trials |
| --- | --- |
| 1. At most 1 of 10 own pieces labelled AI | 0 of 10 labelled AI |
| 2. Clearly-AI and clearly-human far apart | Gap 0.62; 5 of 5 on each correct side |
| 3. All three labels reachable | All three appear; 4 of 4 borderline "unsure" |
| 4. Appeal path | 10 of 10 appeals recorded correctly; 5 of 5 unknown ids refused |
| 5. Bad input | 8 of 8 clean JSON errors; no 500; `/ping` alive; 8 rejections logged |

**This is a smoke test, not the unit 8 evidence, and it should not be read as one**, for two reasons:

1. **It's in-sample.** The 0.85 AI line was chosen in Step 1 *by looking at how these same test texts scored* in Milestone 4. So criterion 1 passing (0 of 10 accused) and criterion 3 passing (4 of 4 borderline "unsure") partly reflect a threshold tuned to the texts being tested, and not an independent result.
2. **The texts are stand-ins.** The "my own writing", "clearly human" and "borderline" texts were drafted by Claude, not written by me. The real test is my own writing, and plain real writing may well score differently.

What it *does* show is that the machinery works end to end (the harness drives real appeals and real bad input against real code, and every check can say yes). Whether the *service* meets its targets will be learned in unit 8 with writing I produce myself. Every score was identical across the three trials, because the model runs deterministically on the CPU here, so the repeats did not show noise; they would if the scores were close to a threshold.

**Milestone 5 summary: what is true now**

- All three labels are reachable and written out in the README (*Label Variants*), with the score range each one covers.
- An appeal changes status (to `under_review`) and shows in the log next to the original decision, which stays unchanged.
- Every route in the Milestone 1 contract is built: `/submit` returns `content_id`, `guess`, `confidence`, `label`, `model_score` and `style_score`; `/appeal` records and confirms; both refuse bad input cleanly and log the refusal.

**What this milestone taught**

- **The label is the product.** The numbers are internal; the sentence is what a person meets. Writing it for someone who has never heard "threshold", and for the worst-case reader (a real writer reading "unsure"), changed what each label says.
- **A threshold is a decision about who pays, not a tuning knob.** Moving the AI line from 0.65 to 0.85 protects plain writers and costs the readers some protection. The number matters less than saying plainly who bears the cost.
- **Check that something exists before you write about it.** The appeal looks up the id *before* recording, so a typo is a loud 404 and not a silent success. The same idea applies anywhere a write depends on a lookup.
- **An append-only log changes how you think about "status".** Nothing is overwritten; the latest line is the truth, and the earlier lines are the history that makes an audit possible.
- **Keep the README and the code from drifting apart.** A test now fails if the README's label text differs from the code's, because the README is the submission.
- **Be honest about circularity.** A target that passes because the threshold was fitted to the same texts is a weaker result than it looks, and saying so is part of reporting it.

**Before moving on:** all 3 labels are reachable and written out in the README. An appeal changes status and shows in the log. Done.

### Milestone 6: Documentation for Unit 7

**The idea:** The code works, but the README is the submission, and the grader checks the code against what the README claims. This milestone makes the README complete and true, then checks the whole repository against the submission checklist before the fork's URL is handed in.

**Where the answers went:** [README.md](README.md) (*What This Does* and *How I Used AI*). The combining-rule line was already in *Signals and Scoring*.

**What was done**

1. **What This Does** was extended. It already held the seven-step path from Milestone 1. It now also says what comes back from `/submit` (and why both signal scores are in the reply), how the appeal works, the honest limit of the service (plain writing reads as machine-like, so the AI line is set high and many AI texts come back "unsure"), and how to run and test it. A first-time reader can now tell what the service does without opening any code.
2. **How I Used AI** now describes two specific moments, each with *what I asked for*, *what came back* and *what I changed*:
   - **The `curl` command that wouldn't run in PowerShell.** The advice was right about the alias and `curl.exe`, but offered a file-based variant that failed with `Failed to open body.json`, because nothing had created the file. The fix was to go back to the inline version. The lesson: check what a suggested command depends on before running it.
   - **Building the style signal.** The first version trusted the brief's idea that AI text has a narrower vocabulary. Checking the three measures against the 24 test texts showed only sentence-length spread worked, so the other two got weight 0, and the code was corrected to match the evidence.
   A short closing note discloses that the example texts in the Sample Run and the test texts in `scenarios.py` are stand-ins, not the author's writing, and that the three writers are invented.
3. **The combining-rule line.** *Signals and Scoring* names `scoring.py::combine_signals`, as the grader expects. This was checked against the code and not just by eye: the function exists in that file, and every number the README quotes (the two weights and the three disagreement settings) equals the value in `config.py`.
4. **Small fixes.** A duplicated divider between two sections was removed, and the appeal example in the Sample Run now says the three writers are made up, so it can't be mistaken for a real person's appeal.

**Why "How I Used AI" is written the way it is.** Two moments, each specific, rather than a general statement that AI was used. A good entry shows a judgement call: something the AI produced that was checked, questioned or corrected. Both moments are real, and both were chosen because something changed as a result.

**The submission checklist, checked by a script and not by eye.** The README's own checklist was turned into checks and run against the repository:

| Checklist item | Result |
| --- | --- |
| `criteria.md` has five numbered criteria, each naming a number, each with a reason underneath | Pass (the reasons are 400+ characters each) |
| The five unit 7 README sections are present and filled | Pass (What This Does, Signals and Scoring, Label Variants, Sample Run, How I Used AI) |
| No placeholder text left anywhere in the README | Pass |
| `POST /submit` returns `content_id`, `guess`, `confidence`, `label`, `model_score`, `style_score` | Pass (the Sample Run shows the real replies) |
| Two signals that measure different things, each with a named blind spot | Pass |
| Three label variants, all reachable, written out in full | Pass (and the README text equals the code's text exactly) |
| `POST /appeal` changes status and writes to the log | Pass (shown in the Sample Run and the log) |
| *Signals and Scoring* names `scoring.py::combine_signals` | Pass (the function is there, and the README's numbers match `config.py`) |
| Sample Run: a submission and an appeal, as pasted text | Pass |
| `logs/audit.jsonl` committed, every decision with all nine fields filled | Pass (six entries: three decisions, one appeal, two rejections) |
| At least four new commits | Pass (16 since the starter's last commit, counting this one) |
| Repository URL: the fork's, not CodePath's | Pass, `origin` is `https://github.com/Angelica-M/ai201-project4-provenance-guard-starter-v2026.git` |

One of those checks failed on its first run, and the cause is worth recording. The script reported criterion 5 as missing its reason, but the criterion was fine. The unit 8 comment block at the bottom of `criteria.md` contains the phrase "Why this target" as an example, so the script saw it twice. The bug was in the checker, not the file, and was fixed by splitting on the first occurrence only. When a check fails, find out *which side* is wrong before changing anything.

All four test suites also still pass (122 tests): `test_app.py` 29, `test_scoring.py` 34, `test_stylometry.py` 23 and `test_eval_harness.py` 36. `test_scoring.py` includes a test that reads the README, so editing the README is itself checked.

**What is still the author's to do**

- **Push this milestone's commit, then submit the fork's URL.** Git's record of the remote (`origin/main`) matched the last Milestone 5 commit when this milestone started, so everything up to Milestone 5 has already been pushed. This milestone's commit has not, and `git push origin main` sends it. Then submit `https://github.com/Angelica-M/ai201-project4-provenance-guard-starter-v2026` and write it down (the README checklist says to). It is the same repository for unit 8, so it must not be deleted or recreated.
- **Read *How I Used AI* and make sure it is an accurate account of how the work was actually done.** It is written in the first person, and only the author can vouch for it.
- **Replace the stand-in test texts with real writing** before unit 8's results count as evidence for criteria 1, 2 and 3.
- **Stop the old server on port 5000** (a leftover process from an earlier smoke test that couldn't be closed from the tools used here).

**Before moving on:** `criteria.md`, the five README sections, `logs/audit.jsonl` and four or more new commits are all in place, and the fork's URL is ready to submit. Done, apart from pushing this last commit.

---

## Unit 8: Testing the safety layer

Unit 7 built the service. Unit 8 tests it: the service is limited and logged properly, then attacked with an attack set I didn't write, then measured against the five criteria, diagnosed, and improved once. Everything below is in the same repository.

### Unit 8, Milestone 1: Rate limiting and the finished audit log

**The idea:** Two things have to be true before anyone attacks the service. A caller can't hammer it without limit, and everything that happens to it, including every request it turns away, leaves a trace that can be read back later. An attack that shows up only as an absence is one that is never found.

**Where the answers went:** The settings are in [config.py](config.py) and the route in [app.py](app.py). The README's *Rate Limiting* section holds the numbers, the reasoning and the pasted status codes. Each step below was committed on its own.

**Step 1. Turn rate limiting on for `/submit`**

Three small changes, all three needed:

1. `RATE_LIMITING_ENABLED = True` in [config.py](config.py).
2. The numbers chosen there: **5 per minute, 50 per day.**
3. The `@limiter.limit(...)` line above `submit()` in [app.py](app.py), uncommented.

Why all three: if config says on but the decorator is commented out, nothing is limited. If the decorator is there but config says off, it is a quiet no-op. `GET /health` reports only the config half, so it can say "on" while nothing is actually limited. That is why a test checks the decorator is really attached.

**Choosing the numbers.** A *rate limit* caps how many requests one caller can make in a window of time. Here it matters because each submission runs a language model (real time and CPU), and because each answer leaks a little about where the thresholds are. A script that sends a thousand slightly different texts and watches the labels can map the thresholds and then write text that lands just under them. A limit can't stop that, only slow it. The numbers came from setting two people side by side:

| | A real writer | A script mapping the thresholds |
| --- | --- | --- |
| Speed | A person needs tens of seconds per round trip, so an impatient writer is at 3 or 4 a minute at most | As fast as the service answers |
| Volume | A heavy honest day is perhaps 15 to 25 submissions | About 7 probes to pin one threshold on one text to within 0.01, so mapping a range of texts takes hundreds |

- **5 a minute:** room for the impatient writer, and one submission every 12 seconds is the fastest any single caller can go. It also protects the machine.
- **50 a day:** about double the heaviest honest day, so a real writer shouldn't meet it. It is the number that actually slows a script: a thousand probes from one identity takes about 20 days, against 5 at the starter's 200 a day.
- Rejected: 10 a minute (lets a script run twice as fast, no benefit to any writer) and a day limit under about 30 (honest revising of several pieces could hit it).

**What counts as a "caller" (and the hole in it).** The starter counts a request against its `creator_id` when it has a usable one, and against the network address when it doesn't. I kept that, and wrote down why and what it costs:

| Count by | Good for | Fails when |
| --- | --- | --- |
| `creator_id` | Treating each writer separately | The caller picks their own id, so a script that invents a new one per request looks like a thousand callers and is **never limited** |
| Network address | Hard to dodge | A household, school or library shares one allowance. Here every request, including my own tests, comes from `127.0.0.1`, so everything would share one bucket and block my evaluation harness and the attack run |

I kept `creator_id` first because the project's tooling depends on it and because shared allowances punish honest writers, the people the service exists to protect. The attack set gives every attack its own `creator_id` (the script itself says so), so those attacks will *not* trip this limit. I expect the attack run to show that, and a real deployment would count both. Two more design points:

- Only `/submit` is limited. `/appeal`, `/log`, `/health` and `/ping` are not, so a writer who has used up their submissions can still appeal a label. A test checks this.
- Every request to `/submit` counts, including ones refused for bad input, so sending junk is no way around the limit.

**Tests** ([test_app.py](test_app.py), 29 to 43 tests). The limit has its own test class, covering: the first 5 pass and the rest get `429`; the refusal has the standard error shape and names the limit; every limited request is logged as a rejection with its creator; limited requests never reach the model or make a decision; one creator being limited doesn't limit another; requests with no usable `creator_id` are counted by address and never crash the key function; junk requests count; the other routes aren't limited; a limited writer can still appeal; and the limit resets.

A side effect worth understanding: switching limiting on would have made the 29 existing tests fail (they submit many times as one creator). Rather than weaken the limit, each test now chooses: limiting is off by default in the test setup and on only in the tests that are about it, with the limiter's counts cleared before and after every test so one test can't affect the next. The starter allowed turning limiting on through an environment variable. Setting the value directly to `True` (as the milestone asks) makes that variable inert, so a note was added to [RUNNING.md](RUNNING.md). A stray over-long divider line that an earlier edit of mine left in `app.py` was tidied.

README: the first three *Rate Limiting* fields (*My limits*, *Why those numbers*, *What a caller counts as*) are filled in. The pasted run of status codes comes in step 2.

**Step 2. Test it: `python run_attacks.py --flood 15`**

Run for real against the live service (`python app.py`, then the flood command in a second terminal), not simulated:

```
200 200 200 200 200 429 429 429 429 429 429 429 429 429 429
```

Exactly 5 pass and the rest are refused, which is the 5-per-minute limit chosen in step 1 working exactly as set. `GET /log` was read back to check both halves landed, not just the response codes: the log held 5 new `decided` entries (real scores, a real label, attributed to `flood_tester`) and 10 new `rejected` entries, each with `"reason": "rate_limited"` and `"limit": "5 per 1 minute"`. Nothing was lost silently, which is the whole reason a rejection gets logged at all.

The script also wrote `results/flood_2026-11-10_1816.md` with the same run. The starter's note that `logs/` and `results/` are deliberately not ignored means both are meant to be committed as evidence, so both go in with this step.

README: *The run of status codes when I pushed past it* is filled in with the pasted command, the status-code run, and a short read of what the log confirmed. *Rate Limiting* is now fully answered.

**Step 3. Finish the audit log, and check one entry by eye**

No code change was needed here: `audit.log_decision` was already writing all nine required fields for every decision since unit 7, Milestone 5, step 2 (`timestamp`, `content_id`, `creator_id`, `guess`, `model_score`, `style_score`, `combined_score`, `label`, `status`). What this step adds is proof, not code: every decided entry in the log was checked, and one was read by eye the way a stranger would.

**The check.** All 8 `decided` entries currently in `logs/audit.jsonl` were scanned for a missing field. None was found; every field is present and non-null in every one.

**Reading one entry by eye**, without opening any code:

```json
{
  "timestamp": "2026-10-30T20:31:34+00:00",
  "content_id": "1cfcb48a-d890-412f-bc0a-357a63d8138b",
  "creator_id": "writer_ana",
  "guess": "ai",
  "model_score": 0.8394,
  "style_score": 1.0,
  "combined_score": 0.9197,
  "label": "Our checks found signs that this may have been written with an AI tool. We can't be sure, and we sometimes get this wrong. If you wrote it yourself, you can appeal and explain how you wrote it, and your appeal will be recorded and marked for review.",
  "status": "decided"
}
```

Could someone reconstruct the decision from this, without the code? Using only this line and the rule written out in the README's *Signals and Scoring*: average the two scores, pull toward 0.5 if they are more than 0.30 apart. Here the gap is `|0.8394 − 1.0| = 0.1606`, under 0.30, so no pull applies and the average alone should be the combined score: `(0.8394 + 1.0) / 2 = 0.9197`. That is exactly the `combined_score` logged. The guess follows from the README's thresholds (0.9197 is at or above 0.85, so "ai"), and the label is word-for-word the "AI" label written there. Every step checks out by hand, with nothing invented. **Yes: who submitted it, what each signal said, how the two numbers became one, what that was called, and the exact words the writer was shown are all there.**

**What it can't reconstruct, said plainly.** The submitted text itself is not logged, by design: the nine fields are the decision, not the content, and the service's job (unit 8's attack run especially) means a lot of adversarial text passing through that need not sit in a permanent file. A bigger limit: the entry doesn't record *which* thresholds or weights were used. If `config.py`'s numbers are ever changed later, this entry's arithmetic would need the config as it stood on 2026-10-30, not whatever it is at the time of reading. Today that is recoverable from git history, but the log entry alone doesn't say it. That is a real gap, written down rather than hidden, and it is not fixed in this step since the brief only asks to check, not to extend the schema further.

**Step 4. Confirm rejections are logged, and that `GET /log` returns everything**

Two kinds of refusal exist, logged by two different pieces of code, and it is worth being precise about which is which:

- **Rate-limit rejections** are logged by the starter's own `429` error handler in `app.py` (`rate_limited`), not by anything built this unit. Step 2 already exercised this.
- **The route's own refusals** (a `400` for missing or empty `text`, a `413` for text too long, a `422` for text too short, and `/appeal`'s `400`/`404`/`413`) are logged through `_error()`, which calls `audit.log_rejection`. This was built back in unit 7, Milestone 3, step 4, and is still in place: `grep` confirms every `_error(...)` call site in `app.py` and the one place `log_rejection` itself is called from inside it.

Why both paths matter being logged, in the brief's own words: **an attack that shows up only as an absence is one you'll never find.** A thousand requests that got a `429` and left no trace would look exactly like a quiet afternoon, and the same is true of a thousand malformed requests that got a quiet `400`.

**The real check**, run against the live service: three pieces of text were submitted by `curl.exe`, one of them deliberately bad, so both kinds of outcome would be exercised in one small run:

| # | Sent | Result |
| --- | --- | --- |
| 1 | A real paragraph, from `writer_dao` | `200`, decided, `human`, confidence 0.3464 |
| 2 | Empty text, same writer | `400 invalid_input` — the route's own refusal, not the rate limiter |
| 3 | A different real paragraph, from `writer_evan` | `200`, decided, `unsure`, confidence 0.502 |

`GET /log?limit=3` was then read, and it returned exactly those three entries, in the order sent: a `decided` entry for writer_dao, a `rejected` entry for writer_dao with `"reason": "invalid_input"` (proving the route-level path, not `rate_limited`), and a `decided` entry for writer_evan. Nothing was missing and nothing extra appeared. The log file grew from 21 lines to 24, matching 3 requests sent.

(Both real submissions happened to log `style_score: 0.5`. That is not a bug: each text was a single sentence, and `stylometry.py`'s own documented rule is that a single sentence carries no spread information and scores a neutral 0.5 rather than being misread as "perfectly even". Noted here only so it isn't mistaken for something broken.)

**Milestone 1 summary: what is true now**

- `POST /submit` is rate limited at 5 a minute and 50 a day per caller, with the numbers defended in the README and the decorator confirmed really attached by a test.
- A real flood past the limit produces exactly the expected run of status codes, and every limited request is logged.
- Every decision in the audit log carries all nine required fields, verified by scanning the whole log and by hand-reconstructing one entry from nothing but the entry and the documented rule.
- Both kinds of refusal — rate-limit and the route's own input checks — are logged, and `GET /log` was shown to return everything sent to it, in order, with nothing missing.

**What this milestone taught**

- **A limit is a decision about two different people, not a single number.** Writing out what an honest writer and an adversarial script each look like made the actual numbers almost choose themselves.
- **"Per creator_id" is a choice with a known hole, and saying so is better than pretending it has none.** A script can dodge it by inventing identities; a real deployment would need both kinds of counting together.
- **Verifying by reading data back is stronger than trusting a status code.** Both the flood test and the three-text test checked `GET /log`, not just the HTTP responses, because a response can lie about what got recorded.
- **"Could a stranger reconstruct this from the entry alone?" is a good test for a log schema.** Doing it by hand, with a calculator and the README, is more convincing than asserting the schema is complete.

**Before moving on:** rate limiting is on for `/submit` with defended numbers, the real flood test produced the expected run of status codes, every decision logs all nine fields (checked by eye), and `GET /log` was confirmed to return every entry, including both kinds of rejection. Done.

---

## Features

- **A `POST /submit` endpoint.** Takes JSON with `text` and `creator_id`. Returns JSON with a `content_id`, a guess, a confidence score, and the label text.
- **Two signals that measure different things.** One reads the text for meaning. One measures it as text: sentence length spread, word variety, punctuation. Two versions of the same idea don't count as two.
- **A confidence score that varies.** 0.51 and 0.95 must produce different labels. A flip at 0.5 is not confidence.
- **Three label variants, written out in full:** high-confidence AI, high-confidence human, and unsure. Every reachable score maps to one of them.
- **A `POST /appeal` endpoint.** Takes a `content_id` and the writer's reasoning. Records it, moves the item to `under_review`, and confirms. No automatic re-checking needed.
- **Five acceptance criteria, written by you, before you see any results.**

---

## 🛠️ Setup

Setup happens before class. The environment setup page has the commands and the versions. This section is the part specific to this project.

This is a web service. It runs on your machine and you talk to it with `curl` from a second terminal. If you've never built a backend, that's assumed. The starter ships one that already answers.

### 1. Fork the starter repo

Fork the Provenance Guard starter repo, then clone your fork locally:

```bash
git clone https://github.com/YOUR-USERNAME/ai201-project4-provenance-guard-starter-v2026.git
cd ai201-project4-provenance-guard-starter-v2026
```

This fork is the repository you submit, both this unit and the next. Its commit history is what shows your criteria existed before your results did.

### 2. Install the dependencies

Create a virtual environment inside the repo, install, and run the check.

**macOS / Linux**

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
pip install -r requirements.txt
python test.py
```

**Windows (PowerShell)**

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
pip install -r requirements.txt
python test.py
```

**No API key for this project.** Nothing here calls a hosted service: no accounts, no keys, no cards. The model that reads your text runs on your own laptop.

Activate the virtual environment every time you open a new terminal, including the second one you'll run `curl` from.

### 3. Download the detector model before class

`test.py` will pass with one warning: `[WARN] Detector model`, followed by `Not downloaded yet (~550 MB)`. Clear it now:

```bash
python detector.py
```

That downloads about 550 MB and scores a sample. Doing it during class costs you a breakout.

### 4. Confirm the service answers

Two terminals. In the first, start the service:

```bash
python app.py
```

In the second, send it something:

```bash
curl -X POST http://127.0.0.1:5000/ping \
  -H "Content-Type: application/json" \
  -d '{"message": "hello"}'
```

JSON comes back. That's the whole idea of a web service: something sent it data, it sent something back.

Leave `/ping` alone. It's your control. When something breaks later, check `/ping` still answers. If it does, the problem is in your handler. If it doesn't, it's the service itself, and that's a help-channel question.

Then try the route you're about to build: `POST /submit` with `text` and `creator_id`. It returns a `501` saying it isn't built yet. That's the correct starting position.

> **On Windows, use `curl.exe` and keep the command on one line.**
>
> In PowerShell, `curl` is an alias for a different tool, and the command above fails with `Cannot bind parameter 'Headers'` before it ever reaches your service. The `\` line breaks don't work there either. This does:
>
> ```powershell
> curl.exe -X POST http://127.0.0.1:5000/ping -H "Content-Type: application/json" -d '{\"message\": \"hello\"}'
> ```
>
> Every `curl` command on this page works the same way: swap `curl` for `curl.exe` and put it on one line. Git Bash needs no change.

`RUNNING.md` in the repo is your reference for everything else: every command, which route is built and which is yours, what each file does, and the troubleshooting table. Read it once now, and come back to it whenever you're stuck.

The first submission takes ten seconds or more while signal one loads the model into memory. Later ones take a second or two. If every submission is slow, something is reloading the model on each call. `GET /health` shows `detector_loaded`, and if that flips back to `false` you have a reload in your handler.
