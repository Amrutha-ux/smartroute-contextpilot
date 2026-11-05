
from app.quality_evaluator import stem_word

expected_keywords = ["repeats", "play", "connect", "walk"]
answer = "The process repeatedly plays, connected and walks."

answer_words = {
    stem_word(word)
    for word in answer.split()
    if stem_word(word)
}

matched_keywords = [
    keyword
    for keyword in expected_keywords
    if stem_word(keyword) in answer_words
]

keyword_coverage = (
    round(len(matched_keywords) / len(expected_keywords) * 100, 2)
    if expected_keywords
    else 0
)

print("Expected keywords:", expected_keywords)
print("Matched keywords:", matched_keywords)
print("Keyword coverage:", keyword_coverage, "%")
