import json
import asyncio
from contextlib import asynccontextmanager
from uuid import uuid4
from fastapi import BackgroundTasks, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse, Response
from .database import create_run, get_run, init_db, list_runs
from .hardware import collect_hardware
from .ollama import OllamaClient, OllamaUnavailable
from .runner import execute
from .reports import csv_report, markdown_report, summarize
from .schemas import BenchmarkConfig

client = OllamaClient()


@asynccontextmanager
async def lifespan(_: FastAPI):
    init_db()
    yield


app = FastAPI(title="Local SLM Benchmark", version="0.1.0", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])


@app.get("/api/health")
async def health():
    try:
        version = await client.version()
        return {"ollama": "available", "version": version}
    except OllamaUnavailable as exc:
        return {"ollama": "unavailable", "error": str(exc)}


@app.get("/api/hardware")
async def hardware():
    return (await collect_hardware(client)).model_dump()


@app.get("/api/models")
async def models():
    try:
        return [model.model_dump() for model in await client.models()]
    except OllamaUnavailable as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc


@app.get("/api/datasets")
async def datasets():
    path = __import__("pathlib").Path(__file__).resolve().parents[2] / "benchmark_data" / "v1.json"
    return json.loads(path.read_text(encoding="utf-8"))


@app.post("/api/benchmarks", status_code=202)
async def create_benchmark(config: BenchmarkConfig, background_tasks: BackgroundTasks):
    try:
        installed = {model.name for model in await client.models()}
    except OllamaUnavailable as exc:
        raise HTTPException(status_code=503, detail="Ollama is unavailable") from exc
    missing = set(config.models) - installed
    if missing:
        raise HTTPException(status_code=400, detail=f"Models not installed: {', '.join(sorted(missing))}")
    run_id = str(uuid4())
    hardware_info = (await collect_hardware(client)).model_dump()
    create_run(run_id, config.model_dump(), hardware_info)
    background_tasks.add_task(execute, config, client, run_id, hardware_info)
    return {"status": "started", "run_id": run_id}


@app.get("/api/runs")
async def runs():
    return list_runs()


@app.get("/api/runs/{run_id}")
async def run(run_id: str):
    result = get_run(run_id)
    if not result:
        raise HTTPException(status_code=404, detail="Run not found")
    result["summary"] = summarize(result)
    return result


def _load_run_or_404(run_id: str) -> dict:
    result = get_run(run_id)
    if not result:
        raise HTTPException(status_code=404, detail="Run not found")
    return result


@app.get("/api/runs/{run_id}/export/json")
async def export_json(run_id: str):
    return _load_run_or_404(run_id)


@app.get("/api/runs/{run_id}/export/csv")
async def export_csv(run_id: str):
    return Response(content=csv_report(_load_run_or_404(run_id)), media_type="text/csv", headers={"Content-Disposition": f"attachment; filename={run_id}.csv"})


@app.get("/api/runs/{run_id}/export/markdown")
async def export_markdown(run_id: str):
    return PlainTextResponse(markdown_report(_load_run_or_404(run_id)), media_type="text/markdown", headers={"Content-Disposition": f"attachment; filename={run_id}.md"})
