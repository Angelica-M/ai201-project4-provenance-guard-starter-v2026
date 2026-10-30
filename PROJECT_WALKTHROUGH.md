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
