
import json
import re
import requests


OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL_NAME = "qwen2.5:1.5b-instruct"


def has_protected_requirement(line: str) -> bool:
    """Return True when a line may contain an important constraint."""

    text = line.lower()

    protected_patterns = [
        r"\b\d+\b",
        r"\bmust\b",
        r"\bmust not\b",
        r"\bdo not\b",
        r"\bdon't\b",
        r"\bonly\b",
        r"\bat least\b",
        r"\bat most\b",
        r"\bminimum\b",
        r"\bmaximum\b",
        r"\bunder\b.*\bwords?\b",
        r"\bexactly\b",
        r"\binclude\b",
        r"\bexclude\b",
        r"\bavoid\b",
        r"\bformat\b",
        r"\bjson\b",
        r"\bexample\b",
        r"\bexamples\b",
        r"\bcode\b",
        r"\bbullet points?\b",
        r"\bparagraphs?\b",
        r"\bsentences?\b",
    ]

    return any(
        re.search(pattern, text)
        for pattern in protected_patterns
    )


import re


def clearly_same_text(first: str, second: str) -> bool:
    """Return True only when lines match after basic normalization."""
    def normalize(text: str) -> str:
        text = text.lower()
        text = re.sub(r"[^\w\s]", "", text)
        return " ".join(text.split())

    return normalize(first) == normalize(second)

def validate_redundant_pair(first: str, second: str) -> bool:
    """Return True only when both lines preserve the same information."""
    print("DEBUG: validate_redundant_pair was called")


    def fully_preserves(source: str, target: str) -> bool:
        
        prompt = f"""
Determine whether SOURCE preserves the complete meaning
and all useful information in TARGET.

SOURCE:
{source}

TARGET:
{target}

Return only JSON:
{{"fully_preserved": true}}

Rules:
- Compare meaning, not exact wording.
- Treat clear paraphrases as equivalent.
- For example, "speeds up data retrieval" and
  "helps find records faster" express the same benefit
  when they refer to the same database index.
- SOURCE must preserve every fact, claim, benefit,
  cause, effect, exception, and qualification in TARGET.
- If TARGET contains any additional information not
  present in SOURCE, return false.
- Sharing the same topic is not enough.
- If uncertain, return false.
"""


        try:
            response = requests.post(
                OLLAMA_URL,
                json={
                    "model": MODEL_NAME,
                    "prompt": prompt,
                    "stream": False,
                    "format": "json",
                    "options": {"temperature": 0},
                },
                timeout=60,
            )
            response.raise_for_status()

            result = json.loads(response.json()["response"])

            return (
                isinstance(result, dict)
                and type(result.get("fully_preserved")) is bool
                and result["fully_preserved"] is True
            )

        except (
            requests.RequestException,
            ValueError,
            KeyError,
            TypeError,
        ):
            return False

    # Require both directions to pass.
    first_preserves_second = fully_preserves(first, second)
    second_preserves_first = fully_preserves(second, first)

    print("First preserves second:", first_preserves_second)
    print("Second preserves first:", second_preserves_first)

    return first_preserves_second and second_preserves_first

def detect_semantic_redundancy(text: str) -> dict:
    """Detect redundant line pairs and validate them conservatively."""

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    if len(lines) < 2:
        return {
            "redundant_lines": [],
            "reason": "Not enough lines to compare.",
        }

    numbered_lines = "\n".join(
        f"{i + 1}. {line}"
        for i, line in enumerate(lines)
    )

    prompt = f"""
Identify pairs of lines that express the same meaning.

A line may be removed only if the other line fully preserves
its meaning and all useful information.

Return ONLY valid JSON in this format:
{{
  "redundant_pairs": [[1, 2]],
  "reason": "short explanation"
}}

Rules:
- Use only line numbers shown below.
- Each pair must contain exactly two different line numbers.
- Do not pair lines that merely discuss the same topic.
- Do not pair lines when either adds a distinct fact, example,
  qualification, exception, or requirement.
- If uncertain, return an empty list.

Lines:
{numbered_lines}
"""

    try:
        response = requests.post(
            OLLAMA_URL,
            json={
                "model": MODEL_NAME,
                "prompt": prompt,
                "stream": False,
                "format": "json",
                "options": {"temperature": 0},
            },
            timeout=60,
        )
        response.raise_for_status()

        result = json.loads(response.json()["response"])

        if not isinstance(result, dict):
            raise ValueError("Expected a JSON object.")

        pairs = result.get("redundant_pairs", [])

        if not isinstance(pairs, list):
            raise ValueError("Invalid redundant_pairs field.")

        redundant_lines = set()
        protected_lines = {
            index
            for index, line in enumerate(lines, start=1)
            if has_protected_requirement(line)
        }

        for pair in pairs:
            if not isinstance(pair, list) or len(pair) != 2:
                continue

            first, second = pair

            if (
                not isinstance(first, int)
                or isinstance(first, bool)
                or not isinstance(second, int)
                or isinstance(second, bool)
                or not (1 <= first <= len(lines))
                or not (1 <= second <= len(lines))
                or first == second
            ):
                continue

            # Never remove a line containing a possible constraint.
            if first in protected_lines or second in protected_lines:
                continue
            first_text = lines[first - 1].lower()
            second_text = lines[second - 1].lower()

            # Preserve distinct cost and access benefits.
            if (
                ("cost" in first_text and any(
                    word in second_text
                    for word in ["access", "remote", "location"]
                ))
                or
                ("cost" in second_text and any(
                    word in first_text
                    for word in ["access", "remote", "location"]
                ))
            ):
                continue
            # The AI identifies equivalent sentences.
            # Protected requirements are filtered out above.

            # Validate the pair before removing the second line.
            first_text = lines[first - 1]
            second_text = lines[second - 1]

      
            if not validate_redundant_pair(first_text, second_text):
                  continue
            
            redundant_lines.add(second)
            
        if not pairs:
            reason = "The model did not identify any redundant pairs."
        elif not redundant_lines:
            reason = "Pairs were suggested, but none passed safety validation."
        else:
            reason = "Redundant lines validated and removed."
        return {
            "redundant_lines": sorted(redundant_lines),
            "reason": reason,
        }

    except (
        requests.RequestException,
        ValueError,
        KeyError,
        TypeError,
    ):
        return {
            "redundant_lines": [],
            "reason": "Detection failed; keeping the original text.",
        }



def remove_redundant_lines(text: str) -> dict:
    result = detect_semantic_redundancy(text)
    redundant = set(result["redundant_lines"])

    if not redundant:
        return {
            "original_text": text,
            "optimized_text": text,
            "removed_lines": [],
            "reason": result["reason"],
        }

    original_lines = text.splitlines(keepends=True)

    # The detector numbers only non-empty lines, so map those
    # numbers to their actual positions in the original text.
    nonempty_positions = [
        index
        for index, line in enumerate(original_lines)
        if line.strip()
    ]

    positions_to_remove = {
        nonempty_positions[number - 1]
        for number in redundant
        if 1 <= number <= len(nonempty_positions)
    }

    optimized_text = "".join(
    line
    for index, line in enumerate(original_lines)
    if index not in positions_to_remove
    )

    import re
    optimized_text = re.sub(r"\n{3,}", "\n\n", optimized_text)

    return {
        "original_text": text,
        "optimized_text": optimized_text,
        "removed_lines": sorted(redundant),
        "reason": result["reason"],
    }
