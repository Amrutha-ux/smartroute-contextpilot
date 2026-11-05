
from unittest.mock import patch
import app.quality_evaluator as qe

mock_responses = [
    {
        "message": {
            "content": "The process repeatedly plays, connected and walks."
        }
    },
    {
        "message": {
            "content": '{"status": "supported"}'
        }
    }
]

with patch(
    "app.quality_evaluator.ollama.chat",
    side_effect=mock_responses
):
    result = qe.evaluate_answer(
        question="Explain the process",
        expected_keywords=["repeats", "play", "connect", "walk"],
        reference_facts=["The process repeats."]
    )

print("Matched keywords:", result["matched_keywords"])
print(
    "Keyword coverage:",
    result["keyword_coverage_percentage"],
    "%"
)
print("Matched facts:", result["matched_facts"])
print("Missing facts:", result["missing_facts"])
print("Contradicted facts:", result["contradicted_facts"])
print(
    "Reference fact coverage:",
    result["reference_fact_coverage_percentage"],
    "%"
)
