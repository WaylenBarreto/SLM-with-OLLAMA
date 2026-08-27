import json
from typing import Any


def evaluate(response: str, rule: dict[str, Any]) -> tuple[float, str | None]:
    kind = rule.get("type")
    expected = rule.get("expected", [])
    normalized = response.strip().lower()
    if kind == "exact":
        score = 1.0 if normalized == str(expected[0]).lower() else 0.0
    elif kind in {"contains", "criteria"}:
        hits = sum(str(value).lower() in normalized for value in expected)
        score = hits / len(expected) if expected else 0.0
    elif kind == "json":
        try:
            parsed = json.loads(response)
            score = sum(key in parsed for key in expected) / len(expected)
        except (json.JSONDecodeError, TypeError):
            score = 0.0
    else:
        score = 0.0
    return score, None if score == 1.0 else "Evaluation criteria not fully satisfied"
