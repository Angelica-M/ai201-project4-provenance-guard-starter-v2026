# Running Provenance Guard

This repository contains the implemented Flask service, including `POST
/submit` and `POST /appeal`. Run commands from the repository root.

The recorded local verification used Windows and Python 3.13.7. The Linux
Gunicorn instructions are provided for deployment; Docker and hosted deployment
have not been verified end to end.

## Requirements

- Python 3.13.7 is the recorded development version. The project preflight
  accepts Python 3.11, 3.12, or 3.13; Python 3.14 is not supported by the
  pinned stack.
- Allow about 9 GB of free disk space. The preflight warns below 4 GB of RAM;
  4 GB or more is recommended.
- The app uses CPU-only PyTorch; no GPU or API key is required.
- The first model download needs internet access and about 550 MB of cache
  space. The model runs locally after it has been downloaded.
- Direct dependencies are pinned in `requirements.txt`. Transitive
  dependencies are resolved by pip and are not all locked to exact versions.

## Install

### Windows PowerShell

Install Python 3.13 (use 3.13.7 to match the recorded development version),
then create and activate a virtual environment:

```powershell
py -3.13 -m venv .venv
.\.venv\Scripts\Activate.ps1
python --version
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python detector.py
python test.py
python test_stylometry.py
python test_scoring.py
python test_app.py
python test_eval_harness.py
```

`python detector.py` downloads GPT-2 if it is not cached, then scores a sample.
`python test.py` checks the Python version, active virtual environment,
dependencies, machine resources, model cache, and the `/ping` route. It is an
environment preflight, not a substitute for the four test files. If you run
`test.py` before downloading the model, it reports a model-cache warning.

### Linux

Use Python 3.13 and activate the environment:

```bash
python3.13 -m venv .venv
source .venv/bin/activate
python --version
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python detector.py
python test.py
python test_stylometry.py
python test_scoring.py
python test_app.py
python test_eval_harness.py
```

The test files use Python's built-in `unittest`; no separate test framework
install is needed.

macOS has not been validated with the CPU-only PyTorch pin in
`requirements.txt`; it may need a platform-specific PyTorch installation.

## Start the service

### Local development

On Windows, run:

```powershell
python app.py
```

By default, the Flask development server listens only on `127.0.0.1:5000`.
To use port 8000 for the capstone evaluator, set the port before starting:

```powershell
$env:PORT = "8000"
python app.py
```

On Linux or macOS, `python app.py` also uses `127.0.0.1:5000` by default.
Do not expose Flask's development server to the public internet.

### Production-style Linux server

Gunicorn is POSIX-only and is not a supported native Windows server. On Linux,
start one worker and two request threads with:

```bash
gunicorn --workers 1 --threads 2 --bind 0.0.0.0:8000 app:app
```

One worker avoids loading a separate GPT-2 model copy per worker process. Two
threads still allow requests to overlap; this setting does not serialize all
inference or telemetry writes. SQLite serializes its own database writes.

Check that the server is responding:

```bash
curl http://127.0.0.1:8000/health
```

Use `curl.exe` instead of `curl` in Windows PowerShell. With the local
development server on its default port, use `http://127.0.0.1:5000`.

The health response includes `model_loaded`. It is `false` until this
**service process** loads GPT-2. Running `python detector.py` downloads the
weights into the cache but does not preload the model into the separately
started service. The first valid `/submit` may therefore take longer or
return a degraded result if model loading exceeds the inference timeout.

## Check the API

The service provides:

| Method and route | Purpose |
|---|---|
| `GET /health` | Service status, model-loaded state, config hash, and rate-limit status |
| `POST /ping` | Lightweight connectivity check; does not load the model |
| `POST /submit` | Scores text and returns a `content_id` and decision |
| `POST /appeal` | Marks an existing decision under review; does not rescore it |
| `GET /log` | Returns audit entries; `?limit=10` requests the latest ten |

Example request from PowerShell:

```powershell
curl.exe -X POST http://127.0.0.1:5000/submit -H "Content-Type: application/json" -d '{"text":"The reviewer compared the submitted draft with the source material and checked the evidence carefully. They recorded the review date, noted the reasoning, and explained how the writer could appeal. The system keeps each decision with its score and configuration hash for later review.","creator_id":"local-demo"}
```

The scoring path requires at least 30 words and 3 sentences. Inputs shorter
than that return `unsure` without model scoring. Text over 25,000 characters
is rejected; longer valid text is evaluated up to the 400-token model limit.
The first successful inference loads the model into the service process.

## Logs and configuration

The service creates `logs/` as needed. By default it writes:

- `logs/audit.sqlite3`: transactional audit database in SQLite WAL mode.
- `logs/audit.jsonl`: human-readable audit entries.
- `logs/telemetry.jsonl`: structured request telemetry; the same telemetry is
  also written to stdout.

Supported environment variables:

| Variable | Default | Purpose |
|---|---|---|
| `HOST` | `127.0.0.1` | Bind address when running `python app.py` |
| `PORT` | `5000` | Port when running `python app.py`; the Gunicorn command above binds to 8000 explicitly |
| `AI201_DEBUG` | `1` | Enables Flask debug mode only for loopback hosts |
| `AI201_DETECTOR_MODEL` | `gpt2` | Hugging Face model ID |
| `THRESHOLD_HUMAN` | `0.40` | Human-label threshold |
| `THRESHOLD_AI` | `0.85` | AI-label threshold |
| `AUDIT_DB_PATH` | `logs/audit.sqlite3` | SQLite database path; useful for a persistent volume |

Rate limiting is enabled in `config.py`: 5 submissions per minute and 50 per
day per valid creator ID; requests without one use the remote address. Limits
use in-memory storage, reset when the service restarts, and are not shared
across multiple worker processes. This app has no authentication, and callers
control their submitted creator IDs; do not expose it as a public service
without adding appropriate access controls and production rate-limit storage.

## Run the capstone acceptance evaluator

The evaluator expects the normal service on port 8000 and the local
timeout-injection fixture on port 8001. Start each in a separate terminal.

Terminal 1, normal service:

- Linux: use the Gunicorn command above.
- Windows PowerShell:

  ```powershell
  $env:PORT = "8000"
  python app.py
  ```

Terminal 2, timeout fixture:

```powershell
python capstone_timeout_server.py
```

The fixture runs a local Flask server on `127.0.0.1:8001` and delays
perplexity inference to exercise the timeout path. In Terminal 3, run:

```powershell
python run_capstone_eval.py --run-number 1
python run_capstone_eval.py --run-number 2
python run_capstone_eval.py --run-number 3
```

Each run writes detailed request and response evidence to
`results/capstone_run_<n>.json`. These are local evaluation helpers, not
production services.

## Optional Docker run

The `Dockerfile` installs the requirements, downloads GPT-2 into the image,
and runs Gunicorn bound to container port 8000. Build and run it with a named
volume for persistent database and log files:

```bash
docker build -t provenance-guard .
docker run --rm -p 8000:8000 -v provenance-guard-logs:/app/logs -e AUDIT_DB_PATH=/app/logs/audit.sqlite3 -e THRESHOLD_HUMAN=0.40 -e THRESHOLD_AI=0.85 provenance-guard
```

The image's Gunicorn command is fixed to port 8000 and does not read a
platform-provided `PORT`. A hosting platform must route traffic to container
port 8000, or the Docker startup command must be changed to use that
platform's assigned port. For Render or another host, verify its port and
persistent-disk requirements before deploying; this Docker/hosted path has
not been verified end to end.

The database, audit JSONL, and telemetry JSONL are under `/app/logs` in this
example, so the volume preserves all three. If you instead set
`AUDIT_DB_PATH=/app/data/audit.sqlite3`, that preserves only the database
unless `/app/logs` is also mounted.

There is no `.dockerignore` in the repository. Docker's `COPY . .` can
therefore include local `.venv`, `.git`, logs, and results in the build
context. Create a `.dockerignore` before building to keep local environments,
repository history, and local audit data out of the image. For example:

```text
.venv/
.git/
__pycache__/
*.py[cod]
logs/
results/
```
