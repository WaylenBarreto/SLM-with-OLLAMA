import uuid
from app.database import add_result, create_run, get_run, init_db


def test_run_and_result_are_persisted():
    init_db()
    run_id = str(uuid.uuid4())
    create_run(run_id, {"models": ["test"]}, {"os": "test"})
    add_result(run_id, {"model": "test", "prompt_id": "p1", "repetition": 1, "response": "ok", "status": "completed", "metrics": {"total_seconds": 1}, "evaluation": {"score": 1}})
    run = get_run(run_id)
    assert run is not None
    assert run["results"][0]["evaluation"]["score"] == 1
