
from app.quality_evaluator import judge_reference_fact

tests = [
    {
        "name": "Supported fact",
        "answer": "Paris is the capital of France.",
        "fact": "Paris is the capital of France.",
        "expected": "supported"
    },
    {
        "name": "Missing fact",
        "answer": "France is located in Europe.",
        "fact": "Paris is the capital of France.",
        "expected": "missing"
    },
    {
        "name": "Contradicted fact",
        "answer": "Lyon is the capital of France.",
        "fact": "Paris is the capital of France.",
        "expected": "contradicted"
    }
]

for test in tests:
    actual = judge_reference_fact(
        question="What is the capital of France?",
        answer=test["answer"],
        fact=test["fact"]
    )

    print(f"\nTest: {test['name']}")
    print(f"Expected: {test['expected']}")
    print(f"Actual:   {actual}")
    print("Result:", "PASS" if actual == test["expected"] else "CHECK")
