import pytest
from app.ollama import OllamaClient


@pytest.mark.asyncio
async def test_client_reads_local_ollama_version():
    version = await OllamaClient().version()
    assert version
