
import json
import time
import ollama

MODEL_NAME = "qwen2.5:1.5b-instruct"

tests = [
    {
        "question": "What is 2 + 2? Answer briefly.",
        "expected_answer": "4",
        "reference_facts": [
            "The answer is 4."
        ]
    },
    {
        "question": "What is the capital of France? Answer briefly.",
        "expected_answer": "Paris",
        "reference_facts": [
            "Paris is the capital of France."
        ]
    },
    {
        "question": "Does the Sun orbit the Earth? Answer briefly.",
        "expected_answer": "No",
        "reference_facts": [
            "The Earth orbits the Sun."
        ]
    }
]

results = []

for test in tests:
    print("\n" + "=" * 50)
    print("Question:", test["question"])

    start = time.perf_counter()

    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {"role": "user", "content": test["question"]}
        ],
        options={"temperature": 0}
    )

    answer = response["message"]["content"]
    elapsed = round(time.perf_counter() - start, 2)

    print("Model answer:", answer)
    print("Expected answer contains:", test["expected_answer"])
    print("Response time:", elapsed, "seconds")

    results.append({
        "question": test["question"],
        "answer": answer,
        "expected_answer": test["expected_answer"],
        "response_time_seconds": elapsed
    })

print("\n" + "=" * 50)
print("BENCHMARK SUMMARY")
print(json.dumps(results, indent=2))
