from app.evaluation import evaluate


def test_json_evaluation_requires_keys():
    score, error = evaluate('{"person":"Ada","role":"mathematician"}', {"type": "json", "expected": ["person", "role"]})
    assert score == 1
    assert error is None


def test_exact_evaluation_is_case_insensitive():
    score, _ = evaluate("Tokyo", {"type": "exact", "expected": ["Tokyo"]})
    assert score == 1
