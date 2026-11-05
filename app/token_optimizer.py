import tiktoken


# Example prices per 1 million tokens.
# These are illustrative prices, not live provider prices.
MODEL_PRICES = {
    "budget": {
        "input": 0.10,
        "output": 0.40
    },
    "standard": {
        "input": 0.50,
        "output": 2.00
    },
    "premium": {
        "input": 2.00,
        "output": 8.00
    }
}


def count_tokens(text: str) -> int:
    """Count tokens in the provided text."""
    encoding = tiktoken.get_encoding("cl100k_base")
    return len(encoding.encode(text))


def estimate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str
) -> float:
    """Estimate the cost of an LLM request in USD."""
    prices = MODEL_PRICES[model]

    input_cost = input_tokens * prices["input"] / 1_000_000
    output_cost = output_tokens * prices["output"] / 1_000_000

    return round(input_cost + output_cost, 8)