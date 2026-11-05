MODEL_CONFIG = {
    "budget": {
        "name": "Small Model",
        "cost_per_million_input_tokens": 0.10,
        "cost_per_million_output_tokens": 0.40
    },
    "standard": {
        "name": "Medium Model",
        "cost_per_million_input_tokens": 0.50,
        "cost_per_million_output_tokens": 2.00
    },
    "premium": {
        "name": "Large Model",
        "cost_per_million_input_tokens": 2.00,
        "cost_per_million_output_tokens": 8.00
    }
}


def classify_task(task: str) -> str:
    """Choose a model tier based on task complexity."""

    task = task.lower()

    complex_keywords = [
        "debug", "analyze", "architecture",
        "reason", "complex", "compare"
    ]

    if any(keyword in task for keyword in complex_keywords):
        return "premium"

    if len(task.split()) > 30:
        return "standard"

    return "budget"


def route_request(task: str) -> dict:
    """Select a model tier and return its configuration."""

    selected_tier = classify_task(task)

    return {
        "selected_tier": selected_tier,
        **MODEL_CONFIG[selected_tier]
    }