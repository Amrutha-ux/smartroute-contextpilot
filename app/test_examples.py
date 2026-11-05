
from app.main import validate_answer

task = "Explain database indexes. Give exactly 2 examples."

tests = [
    (
        "Numbered list",
        "Indexes speed up searches.\n"
        "1. Finding employees by name.\n"
        "2. Finding stores by city."
    ),
    (
        "Example headings",
        "Indexes speed up searches.\n\n"
        "**Example 1:** Finding employees by name.\n\n"
        "**Example 2:** Finding stores by city."
    ),
    (
        "Prose examples",
        "Indexes speed up searches. "
        "For example, an index finds employees by name faster. "
        "Another example is finding stores by city."
    ),
]

for name, answer in tests:
    issues = validate_answer(answer, task)
    print(f"{name}: {'PASS' if not issues else 'FAIL'}")
    print("Issues:", issues)
