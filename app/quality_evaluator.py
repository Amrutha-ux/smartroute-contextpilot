import json
import time
import ollama
import re
from nltk.stem import PorterStemmer

MODEL_NAME = "qwen2.5:1.5b-instruct"
stemmer = PorterStemmer()

def judge_reference_fact(
    question: str,
    answer: str,
    fact: str
) -> str:
    """Judge whether an answer supports, misses, or contradicts a fact."""

    prompt = f"""
You are a strict factual evaluator. Evaluate only the reference fact
provided below.

Question:
{question}

AI answer:
{answer}

Reference fact:
{fact}


Choose exactly one status:

- supported: The answer states the fact or clearly expresses the same meaning, even with different wording.
- missing: The answer neither establishes nor denies the fact. It simply does not provide enough information about the claim.
- contradicted: The answer explicitly states something incompatible with the reference fact.

Important rules:
- Missing information is NOT a contradiction.
- A statement about a broad or related effect does not contradict a specific
  reference fact unless it explicitly denies or conflicts with that fact.
- For example, "too many indexes can slow down database management" does not
  contradict "indexes can slow down insert operations"; classify it as missing
  unless the answer specifically denies the effect on insert operations.
- Do not classify a fact as contradicted merely because the answer does not mention it.
- A related topic or shared keyword does not prove that a fact is supported.
- Do not assume unstated details.
- Judge this reference fact independently of all other facts.
- If the answer says nothing about the specific claim, choose missing.
- Choose contradicted only when the answer makes an explicit conflicting claim.

"""

    response = ollama.chat(
        model="llama3.2:3b",
        messages=[{"role": "user", "content": prompt}],
        format="json",
        options={"temperature": 0}
    )
    print("JUDGE PROMPT:", prompt)

    judgment = json.loads(response["message"]["content"])
    status = judgment.get("status")

    if status not in {"supported", "missing", "contradicted"}:
        raise ValueError("Invalid evaluation status")

    # Verify a contradiction before accepting it.
    if status == "contradicted":
        verification_prompt = f"""
Check whether the AI answer explicitly contradicts the reference fact.

AI answer:
{answer}

Reference fact:
{fact}

Rules:
- Return "contradicted" only if the answer explicitly denies
  or conflicts with the reference fact.
- If the answer does not address the specific claim, return "missing".
- If the answer expresses the same meaning, return "supported".

Return JSON with one key named status.
The value must be exactly supported, missing, or contradicted.
"""

        verification_response = ollama.chat(
            model="llama3.2:3b",
            messages=[
                {"role": "user", "content": verification_prompt}
            ],
            format="json",
            options={"temperature": 0}
        )

        verification = json.loads(
            verification_response["message"]["content"]
        )
        verified_status = verification.get("status")

        if verified_status in {"supported", "missing", "contradicted"}:
            status = verified_status
        else:
            raise ValueError("Invalid verification status")
        print("FINAL FACT STATUS:", status, "| FACT:", fact)

    return status


    
def stem_word(word: str) -> str:
        word = re.sub(r"[^a-zA-Z0-9]", "", word.lower())

        # Normalize common adverb endings before stemming
        if word.endswith("ly") and len(word) > 5:
            word = word[:-2]

        return stemmer.stem(word)

def evaluate_answer(
    question: str,
    expected_keywords: list[str],
    reference_facts: list[str] | None = None
) -> dict:
    """Generate an answer and evaluate it against reference facts."""

    start_time = time.perf_counter()

    # Generate the answer
    response = ollama.chat(
        model=MODEL_NAME,
        messages=[
            {"role": "user", "content": question}
        ]
    )

    answer = response["message"]["content"]

    # Check keyword coverage
    
    
    # Check keyword coverage using English stemming
    


    answer_words = {
        stem_word(word)
        for word in answer.split()
        if stem_word(word)
    }

    matched_keywords = [
        keyword
        for keyword in expected_keywords
        if all(
            stem_word(word) in answer_words
            for word in keyword.split()
            if stem_word(word)
        )
    ]

    keyword_coverage = (
        round(len(matched_keywords) / len(expected_keywords) * 100, 2)
        if expected_keywords
        else 0
    )


    fact_results = []
    matched_facts = []
    missing_facts = []
    contradicted_facts = []
    evaluation_error = None

    # Evaluate each reference fact independently
    
    # Evaluate each reference fact independently
    if reference_facts:
        for fact in reference_facts:
            try:
                status = judge_reference_fact(
                    question=question,
                    answer=answer,
                    fact=fact
                )

            except (
                json.JSONDecodeError,
                TypeError,
                AttributeError,
                KeyError,
                ValueError
            ) as error:
                status = "evaluation_error"
                evaluation_error = str(error)

            fact_results.append({
                "fact": fact,
                "status": status
            })

            if status == "supported":
                matched_facts.append(fact)
            elif status == "contradicted":
                contradicted_facts.append(fact)
            elif status == "missing":
                missing_facts.append(fact)

    fact_coverage = (
        round(len(matched_facts) / len(reference_facts) * 100, 2)
        if reference_facts
        else None
    )

    return {
        "model": MODEL_NAME,
        "question": question,
        "answer": answer,
        "response_time_seconds": round(
            time.perf_counter() - start_time, 2
        ),
        "word_count": len(answer.split()),
        "expected_keywords": expected_keywords,
        "matched_keywords": matched_keywords,
        "keyword_coverage_percentage": keyword_coverage,
        "reference_facts": reference_facts or [],
        "fact_evaluation": fact_results,
        "matched_facts": matched_facts,
        "missing_facts": missing_facts,
        "contradicted_facts": contradicted_facts,
        "reference_fact_coverage_percentage": fact_coverage,
        "evaluation_error": evaluation_error
    }

def evaluate_existing_answer(
    question: str,
    answer: str,
    expected_keywords: list[str],
    reference_facts: list[str] | None = None
) -> dict:
    """Evaluate an existing answer without generating a new one."""

    # Check keyword coverage using the existing stemming logic.
    answer_words = {
        stem_word(word)
        for word in answer.split()
        if stem_word(word)
    }

    matched_keywords = [
        keyword
        for keyword in expected_keywords
        if all(
            stem_word(word) in answer_words
            for word in keyword.split()
            if stem_word(word)
        )
    ]

    keyword_coverage = (
        round(len(matched_keywords) / len(expected_keywords) * 100, 2)
        if expected_keywords
        else 0
    )

    fact_results = []
    matched_facts = []
    missing_facts = []
    contradicted_facts = []
    evaluation_errors = []

    if reference_facts:
        for fact in reference_facts:
            try:
                status = judge_reference_fact(
                    question=question,
                    answer=answer,
                    fact=fact
                )
            except Exception as error:
                status = "evaluation_error"
                evaluation_errors.append({
                    "fact": fact,
                    "error": str(error)
                })

            fact_results.append({
                "fact": fact,
                "status": status
            })

            if status == "supported":
                matched_facts.append(fact)
            elif status == "missing":
                missing_facts.append(fact)
            elif status == "contradicted":
                contradicted_facts.append(fact)

    fact_coverage = (
        round(
            len(matched_facts) / len(reference_facts) * 100,
            2
        )
        if reference_facts
        else None
    )

    return {
        "word_count": len(answer.split()),
        "expected_keywords": expected_keywords,
        "matched_keywords": matched_keywords,
        "keyword_coverage_percentage": keyword_coverage,
        "reference_facts": reference_facts or [],
        "fact_evaluation": fact_results,
        "matched_facts": matched_facts,
        "missing_facts": missing_facts,
        "contradicted_facts": contradicted_facts,
        "reference_fact_coverage_percentage": fact_coverage,
        "evaluation_errors": evaluation_errors
    }
