# SmartRoute + ContextPilot

### An Intelligent Local LLM Routing and Context Optimization Platform

SmartRoute + ContextPilot is a locally running AI platform designed to improve the efficiency of Large Language Model (LLM) applications through intelligent model selection, context optimization, response caching and performance evaluation.

The system uses locally hosted language models through Ollama, avoiding the need for external LLM API keys.

## 1. Project Overview

The project consists of two main components:

**SmartRoute**
- Selects an appropriate local language model based on task complexity.
- Routes simpler tasks to smaller models and more complex tasks to larger models.
- Reuses previously generated responses through caching.
- Validates generated answers and attempts correction when necessary.

**ContextPilot**
- Reduces unnecessary input tokens by removing redundant lines.
- Compares original and optimized contexts.
- Measures token usage and estimated cost differences.

## 2. Key Features

- **Intelligent Model Routing:** Selects between locally available models based on task complexity.
- **Context Optimization:** Removes redundant lines to reduce unnecessary input tokens.
- **Response Caching:** Reuses cached answers for repeated requests.
- **Answer Validation:** Checks generated answers and attempts corrections when validation fails.
- **Quality Evaluation:** Uses local evaluation methods, including keyword-based evaluation and fact judging.
- **Performance Benchmarking:** Compares original and optimized runs using response time, output tokens and estimated cost.
- **Error Handling:** Provides meaningful error messages when the backend or Ollama service is unavailable.
- **Interactive Dashboard:** Displays generated answers, optimization results and performance comparisons.

## 3. Technologies Used

| Technology | Purpose |
|---|---|
| Python | Backend development |
| FastAPI | REST API development |
| Ollama | Running local language models |
| Qwen 2.5 1.5B Instruct | Local language model |
| Llama 3.2 3B | Local language model |
| NLTK | Text processing and keyword evaluation |
| HTML | Dashboard structure |
| CSS | Dashboard styling |
| JavaScript | Frontend interactions |

## 4. System Architecture

```text
              User Input
                  |
                  v
          Frontend Dashboard
                  |
                  v
             FastAPI
                  |
          +-------+-------+
          |               |
          v               v
      SmartRoute      ContextPilot
          |               |
          v               v
    Model Selection   Context Optimization
          |               |
          v               v
       Ollama          Optimized Context
          |
          v
     Local LLM
          |
          v
   Answer Validation
          |
          v
    Response Cache
          |
          v
    Benchmarking
          |
          v
     Dashboard
```

## 5. How It Works

1. The user enters a question through the dashboard.
2. SmartRoute identifies the task complexity and selects a suitable local model.
3. ContextPilot processes the input and removes unnecessary repeated lines.
4. Ollama runs the selected language model locally.
5. The generated answer undergoes validation.
6. Previously generated responses can be retrieved from the cache.
7. The system compares original and optimized runs.
8. Results are displayed on the dashboard.

## 6. Installation and Setup

### Prerequisites

- Python 3
- Ollama
- VS Code (recommended)

### Step 1: Clone the repository

```bash
git clone https://github.com/Amrutha-ux/smartroute-contextpilot.git
cd smartroute-contextpilot
```

### Step 2: Create and activate a virtual environment

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### Step 3: Install dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Download local models

```bash
ollama pull qwen2.5:1.5b-instruct
ollama pull llama3.2:3b
```

Ensure Ollama is running before starting the application.

### Step 5: Start the backend

```bash
uvicorn app.main:app --reload --port 8001
```

Backend URL:

`http://127.0.0.1:8001`

API documentation:

`http://127.0.0.1:8001/docs`

### Step 6: Start the frontend

Open another terminal:

```bash
cd frontend
python3 -m http.server 5501
```

Open the dashboard:

`http://127.0.0.1:5501`

## 7. API Endpoints

The backend provides endpoints for:

- Health checking
- Token optimization
- Cost comparison
- Model comparison
- Local AI answer generation
- Original versus optimized benchmarking

Refer to the FastAPI interactive documentation at `/docs` for the available endpoints and request formats.

## 8. Performance Evaluation

The system compares original and optimized executions using:

- Input token count
- Output token count
- Response time
- Estimated cost

The estimated cost is calculated using configured pricing assumptions. It does not represent an actual payment or charge for local Ollama execution.

Optimization results may vary depending on the input and model response.

## 9. Current Scope and Future Enhancements

The current implementation provides basic line-based context optimization, local model routing, caching, answer validation, quality evaluation and benchmarking.

Potential future enhancements include:

- Semantic redundancy detection
- More advanced context compression
- Improved model routing based on quality and latency
- Stronger evaluation methods
- More detailed performance analytics
- Additional optimization strategies

## 10. Project Objective

The objective of SmartRoute + ContextPilot is to explore how intelligent model selection and context optimization can improve the efficiency of LLM-based applications while keeping inference local and reducing dependence on external AI services.

---

**Developed as a project in Local LLM Optimization and Intelligent Model Routing.**