import json
import time
from pathlib import Path
import psutil
from .database import add_result, create_run, update_status
from .evaluation import evaluate
from .hardware import collect_hardware
from .ollama import OllamaClient, OllamaUnavailable
from .schemas import BenchmarkConfig

DATASET = Path(__file__).resolve().parents[2] / "benchmark_data" / "v1.json"


async def execute(config: BenchmarkConfig, client: OllamaClient, run_id: str, hardware: dict) -> str:
    try:
        dataset = json.loads(DATASET.read_text(encoding="utf-8"))
        for model in config.models:
            for task in dataset["tasks"]:
                for repetition in range(1, config.repetitions + 1):
                    started = time.perf_counter()
                    first_token = None
                    response_parts: list[str] = []
                    metrics = {}
                    try:
                        async for chunk in client.generate(model, task["prompt"], {"temperature": config.temperature, "top_p": config.top_p, "num_predict": config.max_tokens}):
                            if first_token is None:
                                first_token = time.perf_counter()
                            response_parts.append(chunk.get("response", ""))
                            if chunk.get("done"):
                                metrics = {"input_tokens": chunk.get("prompt_eval_count"), "output_tokens": chunk.get("eval_count"), "total_duration_ns": chunk.get("total_duration"), "load_duration_ns": chunk.get("load_duration")}
                        response = "".join(response_parts)
                        total_seconds = time.perf_counter() - started
                        output_tokens = metrics.get("output_tokens") or 0
                        metrics.update({"ttft_seconds": (first_token - started) if first_token else None, "total_seconds": total_seconds, "tokens_per_second": output_tokens / total_seconds if output_tokens and total_seconds else None, "ram_used_mb": round(psutil.Process().memory_info().rss / 1024 ** 2, 2)})
                        score, error = evaluate(response, task["evaluation"])
                        add_result(run_id, {"model": model, "prompt_id": task["id"], "repetition": repetition, "response": response, "status": "completed", "metrics": metrics, "evaluation": {"score": score, "error": error}})
                    except (OllamaUnavailable, TimeoutError) as exc:
                        add_result(run_id, {"model": model, "prompt_id": task["id"], "repetition": repetition, "response": "", "status": "failed", "error": str(exc), "metrics": {}, "evaluation": {"score": 0, "error": "Inference failed"}})
        update_status(run_id, "completed")
    except Exception:
        update_status(run_id, "failed")
        raise
    return run_id
