
import time
import ollama

MODELS = [
    "qwen2.5:1.5b-instruct",
    "llama3.2:3b",
]

TESTS = [
    {
        "question": "Explain the difference between AI and machine learning briefly.",
        "concepts": [
            ["broader field", "broader concept", "broader field of"],
            ["subset of ai", "subset of artificial intelligence"],
            [
    "learn from data",
    "learning from data",
    "learn from and make predictions on data",
    "learn from data and make predictions",
]
        ],
    },
    {
        "question": "Explain supervised vs unsupervised learning briefly.",
        "concepts": [
            ["labeled data", "labelled data"],
            [
    "stores data",
    "store data",
    "storing data",
    "storage system for data",
    "collection of data",
],
[
    "access data",
    "retrieve data",
    "request data",
    "retrieving data",
    "request services from another application",
    "request and receive data",
]
        ],
    },
    {
        "question": "What is the difference between an API and a database?",
        "concepts": [
            ["interface", "communicate", "communication"],
            ["stores data", "store data", "storing data"],
            ["access data", "retrieve data", "request data"],
        ],
    },
    {
        "question": "Explain the difference between a Python list and tuple.",
        "concepts": [
            ["mutable", "can be changed", "modifiable"],
            ["immutable", "cannot be changed", "cannot be modified"],
            ["square brackets", "[ ]", "parentheses", "( )"],
        ],
    },
]

all_results = []

for test in TESTS:
    print("\n" + "=" * 60)
    print("QUESTION:", test["question"])

    for model in MODELS:
        start = time.perf_counter()

        response = ollama.chat(
            model=model,
            messages=[
                {"role": "user", "content": test["question"]}
            ],
            options={"temperature": 0}
        )

        elapsed = round(time.perf_counter() - start, 2)
        answer = response["message"]["content"]
        answer_lower = answer.lower()

        matched = []
        missing = []

        for index, alternatives in enumerate(test["concepts"], start=1):
            if any(phrase.lower() in answer_lower
                   for phrase in alternatives):
                matched.append(index)
            else:
                missing.append(index)

        total = len(test["concepts"])
        coverage = round(len(matched) / total * 100, 2)

        result = {
            "model": model,
            "question": test["question"],
            "coverage": coverage,
            "response_time": elapsed,
            "matched": len(matched),
            "total": total,
        }
        all_results.append(result)

        print(f"\nModel: {model}")
        print("Answer:", answer)
        print(f"Concept coverage: {coverage}%")
        print("Concepts matched:", matched)
        print("Concepts potentially missing:", missing)
        print("Response time:", elapsed, "seconds")

print("\n" + "=" * 60)
print("FINAL QUALITY COMPARISON")

for model in MODELS:
    results = [r for r in all_results if r["model"] == model]

    avg_coverage = sum(r["coverage"] for r in results) / len(results)
    avg_time = sum(r["response_time"] for r in results) / len(results)

    print(f"\nModel: {model}")
    print(f"Average concept coverage: {avg_coverage:.2f}%")
    print(f"Average response time: {avg_time:.2f} seconds")
