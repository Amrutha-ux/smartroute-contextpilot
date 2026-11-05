
COMPLEX_KEYWORDS = [
    "debug",
    "architecture",
    "multi-step",
    "step by step",
    "trade-off",
    "tradeoff",
    "analyze",
    "reason through",
    "complex",
]


def select_local_model(task: str) -> dict:
    task_lower = task.lower()
    word_count = len(task.split())

    if any(keyword in task_lower for keyword in COMPLEX_KEYWORDS) or word_count > 40:
        return {
            "selected_model": "llama3.2:3b",
            "reason": "The task appears complex, so the larger local model was selected."
        }

    return {
        "selected_model": "qwen2.5:1.5b-instruct",
        "reason": "The task appears simple, so the smaller, faster local model was selected."
    }
