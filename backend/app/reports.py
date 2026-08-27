import csv
import io
import json
import statistics
from typing import Any


def summarize(run: dict[str, Any]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = {}
    for result in run["results"]:
        grouped.setdefault(result["model"], []).append(result)
    summaries = []
    for model, rows in grouped.items():
        completed = [row for row in rows if row["status"] == "completed"]
        latencies = [row["metrics"].get("total_seconds") for row in completed if row["metrics"].get("total_seconds") is not None]
        throughput = [row["metrics"].get("tokens_per_second") for row in completed if row["metrics"].get("tokens_per_second") is not None]
        memory = [row["metrics"].get("ram_used_mb") for row in completed if row["metrics"].get("ram_used_mb") is not None]
        scores = [row["evaluation"].get("score", 0) for row in completed]
        summaries.append({
            "model": model,
            "total_prompts": len(rows),
            "completed_prompts": len(completed),
            "failed_prompts": len(rows) - len(completed),
            "quality": round(statistics.mean(scores) * 100, 1) if scores else 0,
            "avg_latency_seconds": round(statistics.mean(latencies), 3) if latencies else None,
            "p95_latency_seconds": round(_percentile(latencies, 95), 3) if latencies else None,
            "tokens_per_second": round(statistics.mean(throughput), 2) if throughput else None,
            "ram_used_mb": round(max(memory), 1) if memory else None,
        })
    return summaries


def _percentile(values: list[float], percentile: int) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    index = (len(ordered) - 1) * percentile / 100
    lower = int(index)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (index - lower)


def csv_report(run: dict[str, Any]) -> str:
    output = io.StringIO()
    fields = ["model", "prompt_id", "repetition", "status", "response", "error", "metrics", "evaluation"]
    writer = csv.DictWriter(output, fieldnames=fields)
    writer.writeheader()
    for row in run["results"]:
        writer.writerow({field: json.dumps(row[field]) if isinstance(row.get(field), dict) else row.get(field, "") for field in fields})
    return output.getvalue()


def markdown_report(run: dict[str, Any]) -> str:
    lines = ["# Local SLM Benchmark Report", "", f"- Run: `{run['id']}`", f"- Created: `{run['created_at']}`", f"- Status: `{run['status']}`", "", "## Hardware", "", "```json", json.dumps(run["hardware"], indent=2), "```", "", "## Model Summary", "", "| Model | Quality | Avg latency | P95 latency | Tokens/sec | RAM |", "|---|---:|---:|---:|---:|---:|"]
    for item in summarize(run):
        lines.append(f"| {item['model']} | {item['quality']}% | {item['avg_latency_seconds'] or 'n/a'}s | {item['p95_latency_seconds'] or 'n/a'}s | {item['tokens_per_second'] or 'n/a'} | {item['ram_used_mb'] or 'n/a'} MB |")
    lines.extend(["", "## Methodology", "", "Every selected model receives the same versioned prompts, generation settings, and repetition count. Unavailable hardware telemetry is preserved as unavailable."])
    return "\n".join(lines) + "\n"
