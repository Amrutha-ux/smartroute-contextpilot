
from app.token_optimizer import count_tokens
from app.semantic_optimizer import remove_redundant_lines

# Phrases that express the same simple-language instruction.
SEMANTIC_REDUNDANCY_RULES = [
    (
        "Use easy-to-understand language.",
        [
            "explain this topic simply",
            "explain databases simply",
        ],
    ),
]


def optimize_context(text: str) -> dict:
    # Preserve the original prompt for comparison.
    original_text = text

    # Remove blank lines and unnecessary spaces.
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    # Remove exact duplicate lines while preserving order.
    unique_lines = list(dict.fromkeys(lines))

    # Apply recognized semantic redundancy rules.
    optimized_lines = unique_lines.copy()

    for phrase_two, possible_first_phrases in SEMANTIC_REDUNDANCY_RULES:
        normalized_lines = [
            line.lower().rstrip(".!?").strip()
            for line in optimized_lines
        ]

        second = phrase_two.lower().rstrip(".!?").strip()

        if second not in normalized_lines:
            continue

        for phrase_one in possible_first_phrases:
            first = phrase_one.lower().rstrip(".!?").strip()

            if first in normalized_lines:
                second_index = normalized_lines.index(second)
                optimized_lines.pop(second_index)
                break

    # Apply the tested Ollama-based semantic optimizer.
    cleaned_text = "\n".join(optimized_lines)
    semantic_result = remove_redundant_lines(cleaned_text)
    optimized_text = semantic_result["optimized_text"]

    # Count tokens before and after optimization.
    original_tokens = count_tokens(original_text)
    optimized_tokens = count_tokens(optimized_text)

    tokens_saved = max(0, original_tokens - optimized_tokens)

    savings_percentage = (
        round(tokens_saved / original_tokens * 100, 2)
        if original_tokens > 0
        else 0
    )

    return {
        "original_text": original_text,
        "optimized_text": optimized_text,
        "original_tokens": original_tokens,
        "optimized_tokens": optimized_tokens,
        "tokens_saved": tokens_saved,
        "savings_percentage": savings_percentage,
        "semantic_removed_lines": semantic_result["removed_lines"],
        "semantic_reason": semantic_result["reason"],
    }
