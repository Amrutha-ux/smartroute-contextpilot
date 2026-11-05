
import time
import ollama

MODELS = [
    "qwen2.5:1.5b-instruct",
    "llama3.2:3b",
]

TESTS = [
    {
        "question": "What is 2 + 2? Answer briefly.",
        "expected": "4",
    },
    {
        "question": "What is the capital of France? Answer briefly.",
        "expected": "Paris",
    },
    {
        
    "question": (
        "Does the Sun orbit the Earth? "
        "Answer briefly and explain the correct relationship."
    ),
    "accepted_phrases": [
        "earth orbits the sun",
        "earth and other planets in our solar system orbit the sun",
        "orbit the sun",
        "revolve around the sun",
    ],
},
    
]

results = []

for test in TESTS:
    print("\n" + "=" * 65)
    print("QUESTION:", test["question"])
    print("EXPECTED:", test.get("expected", test.get("accepted_phrases")))
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

        # Basic correctness check for this initial benchmark
        accepted_phrases = test.get(
              "accepted_phrases",
              [test.get("expected", "")]
          )

        correct = any(
              phrase.lower() in answer.lower()
              for phrase in accepted_phrases
          )

        result = {
            "model": model,
            "question": test["question"],
            "answer": answer,
            "expected": test.get("expected", test.get("accepted_phrases")),
            "basic_check": "PASS" if correct else "CHECK",
            "response_time_seconds": elapsed,
        }
        results.append(result)

        print(f"\nModel: {model}")
        print("Answer:", answer)
        print("Basic check:", result["basic_check"])
        print("Response time:", elapsed, "seconds")


print("\n" + "=" * 65)
print("FINAL MODEL COMPARISON")

for model in MODELS:
    model_results = [
        result for result in results
        if result["model"] == model
    ]

    total = len(model_results)
    passed = sum(
        result["basic_check"] == "PASS"
        for result in model_results
    )

    average_time = (
        sum(
            result["response_time_seconds"]
            for result in model_results
        ) / total
        if total else 0
    )

    pass_rate = passed / total * 100 if total else 0

    print(f"\nModel: {model}")
    print(f"Tests passed: {passed}/{total}")
    print(f"Pass rate: {pass_rate:.2f}%")
    print(f"Average response time: {average_time:.2f} seconds")

for result in results:
    print(
        f'{result["model"]} | '
        f'{result["basic_check"]} | '
        f'{result["response_time_seconds"]} seconds'
    )
