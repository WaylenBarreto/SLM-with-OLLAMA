import os
import platform
import psutil
from .ollama import OllamaClient, OllamaUnavailable
from .schemas import HardwareInfo


def _gpu_name() -> str | None:
    if platform.system() == "Windows":
        try:
            import subprocess
            output = subprocess.check_output(["powershell", "-NoProfile", "-Command", "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"], text=True, timeout=3)
            return output.strip().splitlines()[0] if output.strip() else None
        except (OSError, subprocess.SubprocessError, IndexError):
            return None
    return None


async def collect_hardware(client: OllamaClient) -> HardwareInfo:
    try:
        version = await client.version()
    except OllamaUnavailable:
        version = None
    memory = psutil.virtual_memory()
    return HardwareInfo(
        os=f"{platform.system()} {platform.release()}",
        cpu=platform.processor() or "Unknown CPU",
        cores=os.cpu_count() or 1,
        threads=os.cpu_count() or 1,
        ram_gb=round(memory.total / (1024 ** 3), 2),
        gpu=_gpu_name(),
        ollama_version=version,
    )
