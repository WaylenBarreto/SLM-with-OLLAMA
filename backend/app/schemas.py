from datetime import datetime
from typing import Any
from pydantic import BaseModel, Field


class ModelInfo(BaseModel):
    name: str
    size: int | None = None
    parameter_size: str | None = None
    quantization: str | None = None
    modified_at: str | None = None


class HardwareInfo(BaseModel):
    os: str
    cpu: str
    cores: int
    threads: int
    ram_gb: float
    gpu: str | None = None
    vram_gb: float | None = None
    gpu_metrics_available: bool = False
    ollama_version: str | None = None


class BenchmarkConfig(BaseModel):
    models: list[str] = Field(min_length=1)
    dataset_version: str = "1.0.0"
    repetitions: int = Field(default=1, ge=1, le=20)
    temperature: float = Field(default=0.0, ge=0, le=2)
    top_p: float = Field(default=0.9, gt=0, le=1)
    max_tokens: int = Field(default=256, ge=1, le=4096)


class RunSummary(BaseModel):
    id: str
    status: str
    created_at: datetime
    config: dict[str, Any]
    results: list[dict[str, Any]] = []
