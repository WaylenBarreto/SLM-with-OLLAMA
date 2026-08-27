# Local SLM Benchmark

> A local-first benchmarking workbench for answering a practical question: **which Ollama model offers the best quality, speed, and resource tradeoff on this machine?**

[![Python](https://img.shields.io/badge/Python-3.14-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/API-FastAPI-009688?logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/UI-React%20%2B%20TypeScript-61DAFB?logo=react&logoColor=111111)](https://react.dev/)
[![Runtime](https://img.shields.io/badge/Inference-Ollama-black)](https://ollama.com/)

## Why this project

Cloud model leaderboards are useful, but they do not answer the question developers often face at deployment time: **what works best on the hardware I actually have?** This project compares local language models under controlled conditions using the same prompts, generation settings, repetitions, and host machine.

It is designed as an AI/ML engineering portfolio project, not a chatbot demo. The code demonstrates local inference integration, benchmark design, streaming token measurement, deterministic evaluation, resource inspection, persistence, API design, and a research-oriented dashboard.

## What it does

- Detects whether Ollama is reachable and lists installed models.
- Runs the same version-controlled benchmark suite against each selected model.
- Streams responses from Ollama without using cloud inference APIs.
- Measures time to first token, total latency, token counts, throughput, and RAM usage.
- Evaluates factual, structured, coding, reasoning, summarization, and instruction tasks.
- Stores raw responses, metrics, evaluation results, configuration, and hardware snapshots in SQLite.
- Polls active runs and displays per-model comparison summaries in the React dashboard.
- Exports run data as JSON, CSV, or Markdown.
- Preserves unavailable telemetry as `n/a` instead of inventing measurements.

## Architecture

```text
React + TypeScript dashboard
					|
					v
FastAPI HTTP API ---- SQLite run storage
					|
					+---- Ollama client ---- local Ollama runtime ---- local models
					|
					+---- benchmark runner ---- metrics collector
					|
					+---- deterministic evaluation ---- report generator
```

### Project layout

```text
backend/
	app/
		main.py          FastAPI routes and application lifecycle
		ollama.py        Ollama health, model discovery, and streaming client
		runner.py        Identical model/prompt/repetition execution loop
		hardware.py      Host and runtime inspection
		evaluation.py    Deterministic response scoring
		reports.py       Aggregation and export formatting
		database.py      SQLite schema and persistence functions
	tests/
benchmark_data/
	v1.json            Reproducible benchmark dataset
frontend/
	src/main.tsx       Dashboard workflow and live run polling
	src/styles.css     Dashboard visual system
docs/
	tradeoffs.md       Methodology and interpretation guidance
```

## Quick start

### Prerequisites

- Windows, macOS, or Linux
- Python 3.12+
- Node.js 20+
- Ollama installed and running
- At least one Ollama chat model downloaded

Install a few candidate models, for example:

```powershell
ollama pull llama3.2
ollama pull qwen3:4b
ollama pull llama3.1
```

Confirm the runtime:

```powershell
ollama list
ollama --version
```

### Start the backend

From the repository root:

```powershell
cd backend
..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload --port 8000
```

### Start the frontend

In a second terminal:

```powershell
cd frontend
npm install
npm run dev
```

Open [http://localhost:5173](http://localhost:5173). The backend expects Ollama at `http://127.0.0.1:11434`.

## Running a benchmark

1. Open the dashboard.
2. Select two or more installed chat models.
3. Choose the repetition count.
4. Keep the shared deterministic settings for a fair primary comparison.
5. Select **Run benchmark**.
6. Watch the run status and collected prompt count update.
7. Review quality, latency, throughput, memory, and failures by model.
8. Export the run when the status is `completed`.

The runner executes models sequentially. This avoids memory contention and makes comparisons more interpretable on modest hardware.

## Benchmark methodology

The dataset in [benchmark_data/v1.json](benchmark_data/v1.json) is versioned and currently contains six categories:

| Category | Evaluation approach |
| --- | --- |
| Reasoning | Required result text |
| Factual QA | Normalized exact match |
| Summarization | Required criteria coverage |
| Structured JSON | JSON parsing and required-key validation |
| Coding | Required function and operator checks |
| Instruction following | Required numbered-list criteria |

Every selected model receives the same prompt and configuration. The default primary settings are temperature `0`, top-p `0.9`, and a maximum of `256` output tokens. Results include raw responses so evaluation decisions remain inspectable.

The report layer currently calculates:

- Mean quality percentage
- Average latency
- P95 latency
- Average tokens per second
- Peak recorded backend RAM
- Completed and failed prompt counts

See [docs/tradeoffs.md](docs/tradeoffs.md) for interpretation rules and limitations.

## Results

Results are generated from the machine that runs the benchmark. This repository intentionally does not include made-up model scores or screenshots presented as measured evidence.

After starting a run, the dashboard polls its run ID and displays:

- Per-model quality percentage
- Average and P95 latency
- Tokens per second
- Recorded RAM usage
- Completed and failed prompt counts
- Raw prompt responses and evaluation details through the run API

Results can be exported directly from the API:

```text
GET /api/runs/{run_id}/export/json
GET /api/runs/{run_id}/export/csv
GET /api/runs/{run_id}/export/markdown
```

For a portfolio report, include the generated Markdown export together with the hardware snapshot, dataset version, model tags, repetition count, and generation settings. This makes the conclusion auditable and prevents performance claims from being separated from the conditions that produced them.

The first recommended comparison on the development machine is `llama3.2:latest`, `qwen3:4b`, and `llama3.1:latest`. The expected tradeoff is a hypothesis only: smaller models may be faster and lighter, while larger models may score better on reasoning and coding. The benchmark must provide the actual evidence.

## API surface

| Method | Endpoint | Purpose |
| --- | --- | --- |
| `GET` | `/api/health` | Ollama availability and version |
| `GET` | `/api/models` | Installed Ollama models |
| `GET` | `/api/hardware` | Host hardware snapshot |
| `GET` | `/api/datasets` | Versioned benchmark tasks |
| `POST` | `/api/benchmarks` | Validate and start a run |
| `GET` | `/api/runs` | Historical run list |
| `GET` | `/api/runs/{id}` | Run status, raw results, and summaries |
| `GET` | `/api/runs/{id}/export/json` | JSON export |
| `GET` | `/api/runs/{id}/export/csv` | CSV export |
| `GET` | `/api/runs/{id}/export/markdown` | Markdown report |

## Testing

Run the backend tests:

```powershell
cd backend
..\.venv\Scripts\python.exe -m pytest -q
```

The suite covers deterministic evaluation, local Ollama client access, and SQLite run/result persistence. Build the frontend with:

```powershell
cd frontend
npm run build
```

## Example machine profile

The development machine used for the initial implementation has:

- Windows 11
- Intel Core i7-1255U, 10 cores / 12 threads
- 15.68 GB RAM
- Intel Iris Xe Graphics
- Ollama `0.32.15`

These are environment observations, not benchmark results. The application collects the active machine profile at run time and does not ship fabricated scores.

## Limitations and roadmap

Current limitations include platform-dependent GPU/VRAM telemetry, simple deterministic checks for open-ended tasks, and polling-based progress updates. The next engineering improvements are richer process-level resource sampling, cold-versus-warm run labels, category charts, historical run comparison, cancellation, and expanded API/runner test coverage.

## Adding benchmark tasks

Add a task to `benchmark_data/v1.json` with a unique ID, category, prompt, and supported evaluation rule. Keep prompts model-neutral and avoid requiring capabilities that only one model has. Bump the dataset version when changing existing prompts so old runs remain reproducible.

## Adding models

No core code changes are required. Install the model through Ollama, refresh the dashboard, and select it from the discovered model list. Model metadata is read from Ollama when available.

## License

No license has been selected yet. Add a license before publishing this repository publicly.
