# Backend Architecture Agent

I built this because I kept running into the same problem — every time I started a new backend project, the first few days were always the same back-and-forth: what stack should I use? how should I structure the folders? what are the core API routes? It's not that these questions are hard, they're just slow and repetitive.

This agent takes a plain-English product requirement and spits out a full backend blueprint — tech stack, API routes, database schema, folder structure, and deployment advice — all as structured, validated JSON that code can actually consume downstream. Not a wall of markdown text that you have to read and interpret yourself.

It runs against OpenAI's `gpt-4o` when you have an API key, and falls back to a local `Qwen2-1.5B-Instruct` model (on CPU or GPU) when you don't.

---

## Why this problem?

Picking the wrong database or skipping a caching layer at the start of a project is the kind of mistake you pay for over months, not days. Senior architects who can guide these decisions are expensive and hard to get time with.

The other issue is that general-purpose AI tools (including Cursor's Claude) give you architecture advice in freeform prose. That's useful for reading, but you can't parse it. You can't score it. You can't feed it into another tool. Every run looks slightly different even for the same input.

This agent fixes both of those things. The output is always the same shape — a `ArchitectureBlueprint` object with typed fields — so it's actually usable beyond just reading it on screen.

---

## What it generates

Give it a requirement like *"a food delivery platform with real-time order tracking"* and you get back:

- **Tech stack** — language, framework, database, cache, message queue
- **API routes** — HTTP method, path, and description for each endpoint
- **Database schema** — entities with typed fields, primary/foreign keys
- **Folder structure** — a sensible project layout for the chosen stack
- **Deployment & scaling advice** — Docker setup, cloud provider recommendations, caching strategy

Everything validated by Pydantic. Every response is scored automatically on a 1–10,000 scale.

---

## Setup

You'll need Python 3.11 or 3.12. Python 3.14 has known incompatibilities with `pydantic-core` and the PyTorch CUDA wheels don't exist for it yet.

```bash
git clone <repo-url>
cd backend-architect-agent

python -m venv venv
venv\Scripts\Activate.ps1        # Windows
# source venv/bin/activate        # macOS / Linux

pip install -r requirements.txt
```

Copy `.env.example` to `.env` and fill in your keys:

```bash
cp .env.example .env
```

If you leave `OPENAI_API_KEY` blank, the local Qwen2 model kicks in automatically. If you have an NVIDIA GPU (4GB+ VRAM), install the CUDA version of PyTorch for much faster local inference:

```bash
pip install torch --index-url https://download.pytorch.org/whl/cu124
```

Then start the server:

```bash
python run.py
# http://localhost:8000
# http://localhost:8000/docs  ← Swagger UI
```

---

## API

### POST /generate

```json
{
  "requirement": "A scalable e-commerce platform handling 10,000 concurrent users during flash sales"
}
```

Returns:

```json
{
  "blueprint": {
    "recommended_stack": {
      "language": "Python",
      "framework": "FastAPI",
      "database": "PostgreSQL",
      "cache": "Redis",
      "message_queue": "RabbitMQ"
    },
    "api_routes": [
      { "method": "GET",    "path": "/products",      "description": "List all products" },
      { "method": "POST",   "path": "/products",      "description": "Create a product" },
      { "method": "PUT",    "path": "/products/{id}", "description": "Update a product" },
      { "method": "DELETE", "path": "/products/{id}", "description": "Delete a product" }
    ],
    "database_schema": [
      {
        "name": "product",
        "fields": [
          { "name": "id",    "type": "UUID",    "is_primary": true,  "is_foreign": false },
          { "name": "title", "type": "VARCHAR", "is_primary": false, "is_foreign": false },
          { "name": "price", "type": "DECIMAL", "is_primary": false, "is_foreign": false }
        ],
        "relationships": ["One-to-Many with sale via product_id"]
      }
    ],
    "folder_structure": ["app/", "app/models/", "app/routers/", "app/services/", "tests/"],
    "deployment_recommendations": "Containerise with Docker, deploy to AWS ECS behind an Application Load Balancer. Use RDS for PostgreSQL and ElastiCache for Redis.",
    "scaling_recommendations": "Enable read replicas on RDS for heavy read traffic. Use Redis for session and product catalogue caching with LRU eviction. Add a CDN in front of static assets."
  },
  "metrics": {
    "completeness_score": 100.0,
    "scalability_score": 100.0,
    "api_quality_score": 100.0,
    "structure_accuracy_score": 100.0,
    "latency_score": 77.8,
    "latency_seconds": 6.0,
    "final_metric_score": 9778
  },
  "token_usage": {
    "prompt_tokens": 612,
    "completion_tokens": 1204,
    "total_tokens": 1816
  }
}
```

### GET /health

Returns `{"status": "ok"}`. Useful for container health checks — no API key needed.

---

## How the score is calculated

Every blueprint gets scored immediately after generation using `app/evaluator.py`. No LLM involved — it's all deterministic checks so scores are reproducible across runs.

| Metric | Weight | What it checks |
|---|---|---|
| Completeness | 30% | Has cache/queue, 3+ routes, 2+ DB entities, 4+ folders, non-trivial deployment text |
| Scalability | 25% | Keyword scan: docker, kubernetes, redis, CDN, load balancer, sharding, replica, etc. |
| API Quality | 20% | Each route has a valid HTTP verb and a properly formatted path |
| Structure Accuracy | 15% | All required fields are populated and non-empty |
| Latency | 10% | 100 pts under 2s, scales linearly down to 0 pts at 20s |

The formula:

```
Raw  = (Completeness × 0.30) + (Scalability × 0.25) + (API Quality × 0.20)
     + (Structure Accuracy × 0.15) + (Latency × 0.10)

Final Score = floor(Raw × 100)    ← always between 1 and 10,000
```

A typical gpt-4o run scores around **9700–9800**. The local Qwen2 model scores around **8000–8500** — lower mainly because of slower latency on CPU.

---

## Compared to just asking Claude in Cursor

I ran both against the same e-commerce requirement to see where they differ.

| | This agent | Cursor / Claude |
|---|---|---|
| Output format | Structured JSON, Pydantic-typed | Freeform markdown |
| Can code consume it? | Yes — same schema every time | No — needs manual parsing |
| Tech stack | FastAPI + PostgreSQL + Redis + RabbitMQ | Usually "Node or Python, try PostgreSQL" |
| API routes | Typed list with method + path | Mentioned in prose, inconsistent |
| DB schema | Entities with field types and keys | Described in text, no types |
| Score | 9778 / 10,000 | Not measurable |
| Works offline | Yes — local Qwen2 fallback | Requires Cursor subscription |
| Latency | 3–8s | Real-time streaming |

Claude is better when you want to have a conversation — ask follow-ups, adjust based on your existing codebase, iterate. This agent is better when you want a reliable, consistent, machine-readable result you can build on top of.

---

## Project layout

```
backend-architect-agent/
├── app/
│   ├── agent.py          # picks OpenAI or local model based on env
│   ├── local_agent.py    # Qwen2-1.5B inference, GPU/CPU auto-detection
│   ├── evaluator.py      # 1–10,000 scoring logic
│   ├── main.py           # FastAPI endpoints + startup model preload
│   ├── tools.py          # Pydantic schemas (ArchitectureBlueprint etc.)
│   ├── prompts.py        # system + user prompt templates
│   ├── config.py         # settings loaded from .env
│   ├── scenarios.py      # shared benchmark scenario definitions
│   ├── benchmarking.py   # runs agent across 3 scenarios, prints report
│   └── utils.py          # logging setup
├── tests/
│   └── test_cases.py
├── .cursorrules          # tells Cursor how to code in this project
├── .env.example
├── requirements.txt
└── run.py
```

---

## Security

API keys are never in the code. Everything goes through `pydantic-settings` which reads from `.env`, and `.env` is in `.gitignore`. The `.env.example` file is safe to commit — it only has placeholder values. If you run in offline mode with the local model, no credentials are needed at all.

---

## Cursor setup

The `.cursorrules` file tells Cursor's AI assistant to follow the same standards as the rest of the codebase: async-first I/O, full type hints, Google-style docstrings, no hardcoded secrets, and always returning Pydantic models instead of raw JSON strings from LLM calls.

Open the folder in Cursor and it picks up the rules automatically.

---

## What's next

A few things I'd like to add:

- Generate an actual project scaffold as a downloadable ZIP
- Support microservices and event-driven architectures as output styles
- Terraform / Pulumi output alongside the deployment recommendations
- A simple web UI so non-technical stakeholders can use it directly

---

*Built by [Nitin Choudhary](https://www.linkedin.com/in/nitin-choudhary-b51a69255/)*
