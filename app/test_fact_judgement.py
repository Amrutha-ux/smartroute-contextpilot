
import app.quality_evaluator as qe


test_cases = [
    {
        "name": "Faster retrieval expressed differently",
        "answer": "Indexes in databases help to speed up data retrieval, making it easier and faster to find and access data.",
        "fact": "A database index helps retrieve records faster.",
        "expected": "supported"
    },
    {
        "name": "Additional storage expressed differently",
        "answer": "Indexes require additional storage space to store pointers to the primary data.",
        "fact": "An index requires additional storage space.",
        "expected": "supported"
    },
    {
        "name": "Related topic, but specific claim absent",
        "answer": "Having too many indexes can slow down the database as the system manages them.",
        "fact": "An index can slow down insert, update, and delete operations.",
        "expected": "missing"
    },
    {
        "name": "Explicit contradiction",
        "answer": "Indexes never slow down insert operations.",
        "fact": "An index can slow down insert operations.",
        "expected": "contradicted"
    }
]


for test in test_cases:
    result = qe.judge_reference_fact(
        question="Explain database indexes",
        answer=test["answer"],
        fact=test["fact"]
    )

    print(f'\nTest: {test["name"]}')
    print("Expected:", test["expected"])
    print("Actual:", result)
    print("PASS" if result == test["expected"] else "FAIL")
