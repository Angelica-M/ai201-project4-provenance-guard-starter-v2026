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
