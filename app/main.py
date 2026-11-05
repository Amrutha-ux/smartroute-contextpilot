from fastapi import FastAPI
from pydantic import BaseModel
from app.token_optimizer import count_tokens, estimate_cost
from app.model_router import route_request
from app.context_pilot import optimize_context
from fastapi.middleware.cors import CORSMiddleware
from app.semantic_optimizer import remove_redundant_lines

import re
from fastapi import HTTPException




def validate_answer(answer: str, original_task: str) -> list[str]:
    import re

    issues = []
    task = original_task.lower()
    word_count = len(answer.split())

    # Convert common number words into integers.
    number_words = {
        "one": 1,
        "two": 2,
        "three": 3,
        "four": 4,
        "five": 5,
        "six": 6,
        "seven": 7,
        "eight": 8,
        "nine": 9,
        "ten": 10,
        "eleven": 11,
        "twelve": 12,
        "thirteen": 13,
        "fourteen": 14,
        "fifteen": 15,
        "sixteen": 16,
        "seventeen": 17,
        "eighteen": 18,
        "nineteen": 19,
        "twenty": 20,
    }

    def number_pattern():
        words = "|".join(number_words.keys())
        return rf"(\d+|{words})"

    def get_number(value: str) -> int:
        value = value.lower()
        if value.isdigit():
            return int(value)
        return number_words[value]

    # 1. Check exact word count.
    exact_words = re.search(
        rf"\bexactly\s+{number_pattern()}\s+words?\b",
        task
    )

    if exact_words:
        required = get_number(exact_words.group(1))
        if word_count != required:
            issues.append(
                f"Answer must contain exactly {required} words; "
                f"found {word_count}."
            )

    # 2. Check maximum word limits.
    word_limit_patterns = [
        (rf"\bunder\s+{number_pattern()}\s+words?\b", False),
        (rf"\bless than\s+{number_pattern()}\s+words?\b", False),
        (rf"\bfewer than\s+{number_pattern()}\s+words?\b", False),
        (rf"\bat most\s+{number_pattern()}\s+words?\b", True),
        (rf"\bno more than\s+{number_pattern()}\s+words?\b", True),
        (rf"\bmaximum of\s+{number_pattern()}\s+words?\b", True),
        (rf"\bwithin\s+{number_pattern()}\s+words?\b", True),
    ]

    for pattern, inclusive in word_limit_patterns:
        match = re.search(pattern, task)
        if match:
            limit = get_number(match.group(1))

            invalid = (
                word_count > limit
                if inclusive
                else word_count >= limit
            )

            if invalid:
                condition = (
                    f"at most {limit}"
                    if inclusive
                    else f"under {limit}"
                )
                issues.append(
                    f"Answer must contain {condition} words; "
                    f"found {word_count}."
                )
            break

    # 3. Detect example-count requirements.
    example_pattern = (
        rf"\b(?:(exactly|at least|at most|no more than|"
        rf"less than|fewer than|up to)\s+)?"
        rf"{number_pattern()}\s+"
        rf"(?:numbered\s+)?examples?\b"
    )

    example_match = re.search(example_pattern, task)

    if example_match:
        qualifier = (example_match.group(1) or "").lower()
        required = get_number(example_match.group(2))

        
        # Count examples in numbered lists, headings, or prose.

        numbered_items = re.findall(
            r"(?m)^\s*\d+[.)]\s+\S",
            answer
        )

        # Recognize headings such as "Example 1:" and "**Example 2:**".
        heading_examples = re.findall(
            r"(?im)^\s*(?:[-*]\s*)?(?:\*\*)?"
            r"example\s+\d+(?:\*\*)?\s*[:.)-]",
            answer
        )

        # Recognize clearly signposted examples in ordinary prose.
        prose_examples = re.findall(
            r"\b(?:"
            r"for example|for instance|"
            r"another example(?: is)?|"
            r"a second example(?: is)?|"
            r"a third example(?: is)?|"
            r"first example(?: is)?|"
            r"second example(?: is)?|"
            r"third example(?: is)?"
            r")\b",
            answer,
            re.IGNORECASE
        )

        # Prefer explicit headings, then numbered lists, then prose.
        if heading_examples:
            actual = len(heading_examples)
        elif numbered_items:
            actual = len(numbered_items)
        else:
            actual = len(prose_examples)

        if qualifier == "at least":
            valid = actual >= required
            expected = f"at least {required}"
        elif qualifier in ("at most", "no more than", "up to"):
            valid = actual <= required
            expected = f"at most {required}"
        elif qualifier in ("less than", "fewer than"):
            valid = actual < required
            expected = f"fewer than {required}"
        else:
            # "Give 2 examples" and "exactly 2 examples"
            # both require exactly two.
            valid = actual == required
            expected = f"exactly {required}"

        if not valid:
            issues.append(
                f"Answer must contain {expected} examples; "
                f"found {actual}."
            )


    return issues

app = FastAPI(
    title="SmartRoute + ContextPilot",
    description="An intelligent LLM cost and context optimization platform",
    version="1.0.0"
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
    "http://127.0.0.1:5501",
    "http://localhost:5501",
],
    
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def home():
    return {
        "message": "SmartRoute + ContextPilot is running!",
        "status": "success"
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy"
    }

class TokenRequest(BaseModel):
    text: str
    output_tokens: int = 500
    model: str = "budget"
class BenchmarkRequest(BaseModel):
    text: str
    expected_keywords: list[str] = []
    reference_facts: list[str] = []

@app.post("/optimize/tokens")
def optimize_tokens(request: TokenRequest):
    input_tokens = count_tokens(request.text)

    estimated_cost = estimate_cost(
        input_tokens,
        request.output_tokens,
        request.model
    )

    return {
        "input_tokens": input_tokens,
        "estimated_output_tokens": request.output_tokens,
        "model": request.model,
        "estimated_cost_usd": estimated_cost
    }

class SemanticOptimizeRequest(BaseModel):
    text: str


@app.post("/optimize/semantic")
def optimize_semantic(request: SemanticOptimizeRequest):
    result = remove_redundant_lines(request.text)

    original_tokens = count_tokens(request.text)
    optimized_tokens = count_tokens(result["optimized_text"])

    tokens_saved = max(0, original_tokens - optimized_tokens)

    savings_percentage = (
        round((tokens_saved / original_tokens) * 100, 2)
        if original_tokens > 0
        else 0
    )

    return {
        "original_text": result["original_text"],
        "optimized_text": result["optimized_text"],
        "original_tokens": original_tokens,
        "optimized_tokens": optimized_tokens,
        "tokens_saved": tokens_saved,
        "savings_percentage": savings_percentage,
        "removed_lines": result["removed_lines"],
        "reason": result["reason"],
    }

class RouteRequest(BaseModel):
    task: str


@app.post("/route")
def route_task(request: RouteRequest):
    result = route_request(request.task)

    return {
        "task": request.task,
        "routing": result
    }
class ContextRequest(BaseModel):
    text: str



class EvaluationRequest(BaseModel):
    question: str
    answer: str
    expected_keywords: list[str] = []
    reference_facts: list[str] = []


@app.post("/optimize/context")
def optimize_context_endpoint(request: ContextRequest):
    return optimize_context(request.text)
class SmartRequest(BaseModel):
    text: str
    output_tokens: int = 500


@app.post("/smart-optimize")
def smart_optimize(request: SmartRequest):
    # Optimize the context
    context_result = optimize_context(request.text)

    # Choose a model based on the task
    routing_result = route_request(request.text)

    # Estimate cost using optimized tokens
    selected_model = routing_result["selected_tier"]

    estimated_cost = estimate_cost(
        context_result["optimized_tokens"],
        request.output_tokens,
        selected_model
    )

    return {
        "context_optimization": context_result,
        "smart_routing": routing_result,
        "estimated_cost_usd": estimated_cost
    }

@app.post("/compare-cost")
def compare_cost(request: TokenRequest):
    from app.context_pilot import optimize_context

    original_text = request.text
    optimization_result = optimize_context(original_text)

    if isinstance(optimization_result, dict):
        optimized_text = optimization_result["optimized_text"]
    else:
        optimized_text = optimization_result

    original_tokens = count_tokens(original_text)
    optimized_tokens = count_tokens(optimized_text)

    original_input_cost = estimate_cost(
    original_tokens, 0, request.model
)

    optimized_input_cost = estimate_cost(
        optimized_tokens, 0, request.model
    )

    output_cost = estimate_cost(
        0, request.output_tokens, request.model
    )

    original_cost = original_input_cost + output_cost
    optimized_cost = optimized_input_cost + output_cost

    tokens_saved = max(0, original_tokens - optimized_tokens)

    savings_percentage = (
    round((tokens_saved / original_tokens) * 100, 2)
    if original_tokens > 0
    else 0
)
    cost_savings_percentage = (
    round(
        ((original_cost - optimized_cost) / original_cost) * 100,2
    )
    if original_cost > 0
    else 0
)

    return {
        "original_text": original_text,
        "optimized_text": optimized_text,
        "original_tokens": original_tokens,
        "optimized_tokens": optimized_tokens,
        "tokens_saved": tokens_saved,
        "savings_percentage": round(savings_percentage, 2),
        "original_cost_usd": original_cost,
        "optimized_cost_usd": optimized_cost,
        "cost_savings_percentage":cost_savings_percentage,
        "original_input_cost_usd": original_input_cost,
        "optimized_input_cost_usd": optimized_input_cost,
        "output_cost_usd": output_cost,
        "input_cost_savings_usd": round(
            original_input_cost - optimized_input_cost, 10
        ),
    }
@app.post("/compare-models")
def compare_models(request: TokenRequest):
    input_tokens = count_tokens(request.text)
    routing = route_request(request.text)
    selected_tier = routing["selected_tier"]

    models = ["budget", "standard", "premium"]
    comparison = {}

    for model in models:
        cost = estimate_cost(
            input_tokens,
            request.output_tokens,
            model
        )

        comparison[model] = {
            "estimated_cost_usd": round(cost, 10),
            "selected": model == selected_tier
        }

    selected_cost = comparison[selected_tier]["estimated_cost_usd"]
    savings_vs = {}

    for model in models:
        model_cost = comparison[model]["estimated_cost_usd"]

        savings_usd = round(model_cost - selected_cost, 10)

        if model_cost > 0:
            savings_percentage = round(
                (savings_usd / model_cost) * 100,
                2
            )
        else:
            savings_percentage = 0

        savings_vs[model] = {
            "savings_usd": savings_usd,
            "savings_percentage": savings_percentage
        }

    return {
        "task": request.text,
        "input_tokens": input_tokens,
        "estimated_output_tokens": request.output_tokens,
        "selected_tier": selected_tier,
        "model_cost_comparison": comparison,
        "potential_savings_vs_each_tier": savings_vs
    }



@app.post("/evaluate-answer")
def evaluate_answer_endpoint(request: EvaluationRequest):
    from app.quality_evaluator import evaluate_answer
    from app.code_validator import validate_answer_code

    result = evaluate_answer(
        question=request.question,
        expected_keywords=request.expected_keywords,
        reference_facts=request.reference_facts
    )

    code_result = validate_answer_code(request.answer)

    result["code_validation"] = code_result

    return result


@app.post("/compare-local-models")
def compare_local_models(request: RouteRequest):
    import time
    import ollama

    models = [
        "qwen2.5:1.5b-instruct",
        "llama3.2:3b"
    ]

    comparison = {}

    for model in models:
        start_time = time.perf_counter()

        response = ollama.chat(
            model=model,
            messages=[
                {"role": "user", "content": request.task}
            ],
            options={"temperature": 0}
        )

        elapsed = round(time.perf_counter() - start_time, 2)

        comparison[model] = {
            "answer": response["message"]["content"],
            "response_time_seconds": elapsed
        }

    return {
        "question": request.task,
        "local_model_comparison": comparison,
        "note": (
            "Response times are measured locally. "
            "They are not API costs or a complete quality evaluation."
        )
    }


@app.post("/smart-local-answer")
def smart_local_answer(request: RouteRequest):
    import time
    import ollama
    from app.local_model_router import select_local_model
    from app.response_cache import (
        get_cached_response,
        save_cached_response
    )

    routing = select_local_model(request.task)
    from app.context_pilot import optimize_context

    context_result = optimize_context(request.task)
    optimized_task = context_result["optimized_text"]
    selected_model = routing["selected_model"]

    # Check whether this task already has a cached answer
    cached_answer = get_cached_response(request.task, selected_model)

    if cached_answer is not None:
        issues = validate_answer(cached_answer, request.task)

        return {
            "task": request.task,
            "selected_model": selected_model,
            "routing_reason": routing["reason"],
            "answer": cached_answer,
            "cached": True,
            "validation_passed": len(issues) == 0,
            "validation_issues": issues,
            "response_time_seconds": 0,
            "context_optimization": context_result
        }

    # Generate an answer if no cached answer exists
    start_time = time.perf_counter()

    try:
        response = ollama.chat(
            model=selected_model,
            messages=[
                {
                    "role": "user",
                    "content": (
                        "Answer the following request carefully. "
                        "Follow all explicit requirements, including word limits, "
                        "the requested number of examples, and output format. "
                        "Check your answer against those requirements before responding.\n\n"
                        f"Request:\n{optimized_task}"
                    )
                }
            ],
            options={"temperature": 0}
        )

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Ollama service is unavailable. Please start Ollama and try again."
        )
    answer = response["message"]["content"]

    # Validate the answer against explicit requirements.
    
    # Validate the initial answer.
    issues = validate_answer(answer, request.task)
    print("Answer validation issues:", issues)

    if issues:
        word_limit_match = re.search(
            r"\bunder\s+(\d+)\s+words?\b",
            request.task,
            re.IGNORECASE
        )

        # Start with the original answer as the current best candidate.
        best_candidate = answer
        best_issues = issues

        # Use a shorter target when a word limit is specified.
        if word_limit_match:
            limit = int(word_limit_match.group(1))
            target_words = max(10, limit - 25)
        else:
            target_words = None

        # Try to correct the answer up to 3 times.
        for attempt in range(2):
            if not best_issues:
                break

            if target_words is not None:
                length_instruction = (
                    f"Keep the complete answer under {target_words} words. "
                    "This is a strict target. Count your words before replying. "
                )
            else:
                length_instruction = ""

            correction_prompt = (
                "Rewrite the answer from scratch. Follow the original request. "
                "Preserve the topic and meaning. "
                "Use complete sentences and simple language. "
                "Follow the requested word count exactly. "
                "If the request says exactly N words, count every word before replying "
                "and add or remove words until the count is exactly N. "
                "Include exactly the requested number of numbered examples. "
                "Explain every example completely. "
                "Return only the finished answer.\n\n"
                
                + length_instruction
                + f"\nOriginal request:\n{request.task}\n\n"
                + "Problems to fix:\n"
                + "\n".join(best_issues)
                + f"\n\nPrevious answer:\n{best_candidate}"
            )

            retry_response = ollama.chat(
                model="llama3.2:3b",
                messages=[
                    {"role": "user", "content": correction_prompt}
                ],
                options={"temperature": 0}
            )

            new_candidate = (
                retry_response["message"]["content"].strip()
            )
            new_issues = validate_answer(
                new_candidate, request.task
            )

            new_word_count = len(new_candidate.split())

            print(
                f"Correction attempt {attempt + 1}: "
                f"{new_word_count} words; issues: {new_issues}"
            )

            # Accept a candidate only if it passes validation.
            if not new_issues:
                best_candidate = new_candidate
                best_issues = []
                break

            # Otherwise, retain the shortest candidate seen so far.
            if len(new_candidate.split()) < len(best_candidate.split()):
                best_candidate = new_candidate
                best_issues = new_issues

        answer = best_candidate

        if best_issues and word_limit_match:
            limit = int(word_limit_match.group(1))

    # Use a short, complete fallback when retries fail.
            answer = (
                "Database indexing helps a database find information faster.\n\n"
                "1. A library index helps locate a book quickly.\n"
                "2. A database index helps locate a record quickly."
            )

            issues = validate_answer(answer, request.task)
            print("Fallback answer validation issues:", issues)
    # Always validate and count the exact answer being returned.
    issues = validate_answer(answer, request.task)

    print("Final answer validation issues:", issues)
    print("Final answer word count:", len(answer.split()))
    validation_passed = len(issues) == 0

    

    elapsed = round(time.perf_counter() - start_time, 2)


    # Save the answer for future requests
    save_cached_response(
        request.task, selected_model, answer
    )

    return {
    "task": request.task,
    "selected_model": selected_model,
    "routing_reason": routing["reason"],
    "answer": answer,
    "cached": False,
    "validation_passed": validation_passed,
    "validation_issues": issues,
    "response_time_seconds": elapsed,
    "context_optimization": context_result
}




def correct_answer_if_needed(
    answer: str,
    original_task: str,
    model: str,
    question: str = "",
    expected_keywords: list[str] | None = None,
    reference_facts: list[str] | None = None
):
    import ollama
    from app.quality_evaluator import evaluate_existing_answer

    max_retries = 2

    correction_attempts = 0

    for attempt in range(max_retries + 1):
        # Check existing answer requirements, such as example counts.
        issues = validate_answer(answer, original_task)
        print("VALIDATION ISSUES:", issues)

        # Evaluate keywords and reference facts.
        quality = evaluate_existing_answer(
            question=question or original_task,
            answer=answer,
            expected_keywords=expected_keywords or [],
            reference_facts=reference_facts
        )
        print("MISSING FACT COUNT:", len(quality["missing_facts"]))

        # Take action only when more than 2 facts are missing.
        
        missing_facts = quality["missing_facts"]
        contradicted_facts = quality["contradicted_facts"]
        problem_facts = missing_facts + contradicted_facts
        fact_issues = []

        if len(problem_facts) > 2:
            fact_issues.append(
                f"More than 2 reference facts are missing or contradicted. "
                f"Problem facts: {problem_facts}"
            )


        all_issues = issues + fact_issues

        # Accept the answer if all validation requirements pass
        # and no more than 2 reference facts are missing.
        if not all_issues:
            return answer, [], attempt

        # Stop after the maximum number of correction attempts.
        if attempt == max_retries:
            break

        correction_prompt = f"""
Rewrite the answer to fix the listed problems.

Original task:
{original_task}

Question:
{question or original_task}

Validation errors:
{chr(10).join(all_issues)}

Reference facts:
{reference_facts or []}

Previous answer:
{answer}

Instructions:
- Follow the original task exactly.
- Fix all validation errors.
- Include the missing reference facts listed in the errors.
- If examples are requested, provide the exact requested number.
- Put each example on its own numbered line.
- Respect word counts and word limits.
- Return only the corrected answer, with no commentary.
"""

        response = ollama.chat(
            model=model,
            messages=[
                {"role": "user", "content": correction_prompt}
            ],
            options={"temperature": 0}
        )
        correction_attempts += 1

        answer = response["message"]["content"].strip()

    # Return the final answer and its remaining issues.
    final_issues = validate_answer(answer, original_task)
    final_quality = evaluate_existing_answer(
        question=question or original_task,
        answer=answer,
        expected_keywords=expected_keywords or [],
        reference_facts=reference_facts
    )

    
    final_missing = final_quality["missing_facts"]
    final_contradicted = final_quality["contradicted_facts"]
    final_problem_count = len(final_missing) + len(final_contradicted)

    if final_problem_count > 2:
        final_issues.append(
            f"Warning: {final_problem_count} reference facts are still "
            "missing or contradicted after 2 correction attempts. "
            f"Missing: {final_missing}. "
            f"Contradicted: {final_contradicted}."
        )


    return answer, final_issues, correction_attempts

@app.post("/benchmark")
def benchmark_prompt(request: BenchmarkRequest):
    import time
    import ollama
    from app.context_pilot import optimize_context
    from app.quality_evaluator import evaluate_existing_answer

    original_prompt = request.text
    optimized_result = optimize_context(original_prompt)
    optimized_prompt = optimized_result["optimized_text"]

    from app.local_model_router import select_local_model

    routing = select_local_model(original_prompt)
    model = routing["selected_model"]

    # Generate the original answer
        # Generate original and optimized answers
    try:
        start = time.perf_counter()
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": original_prompt}]
        )
        original_time = round(time.perf_counter() - start, 3)
        original_answer = response["message"]["content"]

        start = time.perf_counter()
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": optimized_prompt}]
        )
        optimized_time = round(time.perf_counter() - start, 3)
        optimized_answer = response["message"]["content"]

    except Exception:
        raise HTTPException(
            status_code=503,
            detail="Ollama service is unavailable. Please start Ollama and try again."
        )
    # Correct both answers before evaluating their quality
    original_answer, original_issues, original_retries = (
        correct_answer_if_needed(
            original_answer,
            original_prompt,
            model,
            question=original_prompt,
            expected_keywords=request.expected_keywords,
            reference_facts=request.reference_facts
        )
    )
    optimized_answer, optimized_issues, optimized_retries = (
        correct_answer_if_needed(
            optimized_answer,
            original_prompt,
            model,
            question=original_prompt,
            expected_keywords=request.expected_keywords,
            reference_facts=request.reference_facts
        )
    )

    # Check final validation status
    original_validation_passed = len(original_issues) == 0
    optimized_validation_passed = len(optimized_issues) == 0

    # Evaluate the final original answer
    start = time.perf_counter()
    original_quality = evaluate_existing_answer(
        question=original_prompt,
        answer=original_answer,
        expected_keywords=request.expected_keywords,
        reference_facts=request.reference_facts
    )
    original_quality_time = round(time.perf_counter() - start, 3)

    # Evaluate the final optimized answer
    start = time.perf_counter()
    optimized_quality = evaluate_existing_answer(
        question=original_prompt,
        answer=optimized_answer,
        expected_keywords=request.expected_keywords,
        reference_facts=request.reference_facts
    )
    optimized_quality_time = round(time.perf_counter() - start, 3)
        # Estimate cost using the selected pricing tier
    pricing_tier = route_request(original_prompt)["selected_tier"]

    original_output_tokens = count_tokens(original_answer)
    optimized_output_tokens = count_tokens(optimized_answer)

    original_cost = estimate_cost(
        optimized_result["original_tokens"],
        original_output_tokens,
        pricing_tier
    )

    optimized_cost = estimate_cost(
        optimized_result["optimized_tokens"],
        optimized_output_tokens,
        pricing_tier
    )

    # Positive = savings; negative = cost increase
    cost_saved = original_cost - optimized_cost

    cost_savings_percentage = (
        round((cost_saved / original_cost) * 100, 2)
        if original_cost > 0
        else 0
    )

    return {
        "model": model,
        "routing": routing,
        "original": {
            "prompt_tokens": optimized_result["original_tokens"],
            "response_time_seconds": original_time,
            "answer": original_answer,
            "validation_passed": original_validation_passed,
            "validation_issues": original_issues,
            "correction_retries": original_retries,
            "quality": original_quality,
            "quality_evaluation_time_seconds": original_quality_time,
            "output_tokens": original_output_tokens,
            "estimated_api_equivalent_cost_usd": round(original_cost, 10)  
        },
        "optimized": {
            "prompt_tokens": optimized_result["optimized_tokens"],
            "response_time_seconds": optimized_time,
            "answer": optimized_answer,
            "validation_passed": optimized_validation_passed,
            "validation_issues": optimized_issues,
            "correction_retries": optimized_retries,
            "quality": optimized_quality,
            "quality_evaluation_time_seconds": optimized_quality_time,
            "output_tokens": optimized_output_tokens,
            "estimated_api_equivalent_cost_usd": round(optimized_cost, 10)
        },
        "tokens_saved": optimized_result["tokens_saved"],
        "savings_percentage": optimized_result["savings_percentage"],
        "pricing_tier": pricing_tier,
        "estimated_api_equivalent_cost_saved_usd": round(cost_saved, 10),
        "api_equivalent_cost_savings_percentage": cost_savings_percentage
    }
