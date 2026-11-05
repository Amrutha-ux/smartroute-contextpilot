
const taskInput = document.getElementById("task");
const runButton = document.getElementById("run-btn");
const statusText = document.getElementById("status");
const resultBox = document.getElementById("result");


runButton.addEventListener("click", async () => {
    const task = taskInput.value.trim();

    if (!task) {
        statusText.textContent = "Please enter a question first.";
        return;
    }

    runButton.disabled = true;
    runButton.textContent = "Processing...";
    statusText.textContent = "Optimizing context and generating your answer...";
    resultBox.classList.add("hidden");

    const optimizationBox = document.getElementById("optimization-result");
    optimizationBox.classList.add("hidden");

    try {
        // 1. Generate the local AI answer using your existing endpoint.
        const answerPromise = fetch(
            "http://127.0.0.1:8001/smart-local-answer",
            {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ task })
            }
        );

        // 2. Optimize the input context using ContextPilot.
        
const benchmarkPromise = fetch(
    "http://127.0.0.1:8001/benchmark",
    {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
            text: task,
            expected_keywords: [],
            reference_facts: []
        })
    }
);

        const answerResponse = await answerPromise;

        if (!answerResponse.ok) {
            const errorData = await answerResponse.json();
            throw new Error(
                errorData.detail || `Answer endpoint error: ${answerResponse.status}`
            );
        }

        const data = await answerResponse.json();
        const benchmarkResponse = await benchmarkPromise;

        if (!benchmarkResponse.ok) {
            const errorData = await benchmarkResponse.json();
            throw new Error(
                errorData.detail || `Benchmark endpoint error: ${benchmarkResponse.status}`
            );
        }

        const benchmark = await benchmarkResponse.json();
        
        const original = benchmark.original;
        const optimized = benchmark.optimized;

        document.getElementById("benchmark-original-time").textContent =
            `${original.response_time_seconds} sec`;

        document.getElementById("benchmark-optimized-time").textContent =
            `${optimized.response_time_seconds} sec`;

        document.getElementById("benchmark-original-cost").textContent =
            `$${original.estimated_api_equivalent_cost_usd}`;

        document.getElementById("benchmark-optimized-cost").textContent =
            `$${optimized.estimated_api_equivalent_cost_usd}`;

        const costChange =
            original.estimated_api_equivalent_cost_usd -
            optimized.estimated_api_equivalent_cost_usd;

        document.getElementById("benchmark-cost-change").textContent =
            `${costChange >= 0 ? "Savings" : "Cost increase"}: $${Math.abs(costChange).toFixed(10)}`;

        document.getElementById("benchmark-original-tokens").textContent =
            original.output_tokens;

        document.getElementById("benchmark-optimized-tokens").textContent =
            optimized.output_tokens;

        document.getElementById("benchmark-optimized-answer").textContent =
            optimized.answer;
        const context = data.context_optimization;

        document.getElementById("model").textContent = data.selected_model;
        document.getElementById("time").textContent =
            `${data.response_time_seconds} seconds`;
        document.getElementById("answer").textContent = data.answer;
        const validationStatus = document.getElementById("validation-status");

        if (data.validation_passed) {
            validationStatus.textContent = "✓ Answer passed validation";
            validationStatus.style.color = "green";
        } else {
            validationStatus.textContent =
                "⚠ Answer failed validation: " +
                (data.validation_issues || []).join(" ");
            validationStatus.style.color = "red";
        }
        document.getElementById("routing-reason").textContent =
            data.routing_reason;
        document.getElementById("cache-status").textContent =
            data.cached ? "✓ Cached answer" : "Newly generated";

        resultBox.classList.remove("hidden");
        statusText.textContent = "Answer generated successfully.";

        // Display ContextPilot results returned by SmartRoute.
        if (context) {
            document.getElementById("original-tokens").textContent =
                context.original_tokens;
            document.getElementById("optimized-tokens").textContent =
                context.optimized_tokens;
            document.getElementById("tokens-saved").textContent =
                context.tokens_saved;
            document.getElementById("savings-percentage").textContent =
                `${context.savings_percentage}%`;
            document.getElementById("optimized-text").textContent =
                context.optimized_text;

            optimizationBox.classList.remove("hidden");
        } else {
            console.warn("No ContextPilot result returned by SmartRoute.");
        }

    } catch (error) {
        statusText.textContent =
            error.message || "Something went wrong. Please try again.";
        console.error(error);
    } 
    finally {
        runButton.disabled = false;
        runButton.textContent = "Run SmartRoute";
    }
});
