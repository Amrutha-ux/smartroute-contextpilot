
from app.quality_evaluator import evaluate_answer

result = evaluate_answer(
    question="What is the capital of France?",
    expected_keywords=["Paris", "capital of France"],
    reference_facts=[
        "Paris is the capital of France."
    ]
)

print("\n--- QUALITY EVALUATION ---")
print("Model:", result["model"])
print("Answer:", result["answer"])
print("Keyword coverage:",
      result["keyword_coverage_percentage"], "%")
print("Matched keywords:", result["matched_keywords"])
print("Fact evaluation:", result["fact_evaluation"])
print("Reference fact coverage:",
      result["reference_fact_coverage_percentage"], "%")
print("Evaluation error:", result["evaluation_error"])
