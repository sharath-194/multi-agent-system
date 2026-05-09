# Real-Time Multi-Agent LLM Orchestration and Evaluation System

A containerized, production-grade multi-agent system with a self-improving evaluation loop, dynamic tool orchestration, and adversarial robustness testing — built with FastAPI, PostgreSQL, and LLaMA 3.3 70B via Groq.

## Quick Start — Run in 5 Minutes

**Prerequisites:** Docker Desktop + Groq API key (free at https://console.groq.com)

```bash
# 1. Clone the repo
git clone https://github.com/sharath-194/multi-agent-system.git
cd multi-agent-system

# 2. Create env file
cp .env.example .env
# Add your GROQ_API_KEY to .env

# 3. Start everything
docker-compose up --build

# 4. Open interactive docs
# http://localhost:8000/docs
```

---

## Architecture

```
User Query
     │
     ▼
Orchestrator Agent  ──── Dynamic routing, no hardcoded chains
     │
     ├──► Decomposition Agent  ──── Breaks query into typed sub-tasks
     │
     ├──► Retrieval Agent  ──────── Multi-hop reasoning across 2+ chunks
     │
     ├──► Synthesis Agent  ──────── Draft answer with provenance map
     │
     ├──► Critique Agent  ───────── Scores claims, flags issues
     │
     └──► Synthesis Agent  ──────── Final answer, contradictions resolved
                │
                ▼
          Tool Layer
     ┌──────────────────┐
     │ Web Search       │
     │ Code Executor    │
     │ Database Lookup  │
     │ Self Reflection  │
     └────────┬─────────┘
              │
              ▼
        PostgreSQL
     ┌──────────────────┐
     │ jobs             │
     │ agent_logs       │
     │ tool_logs        │
     │ eval_runs        │
     │ prompt_rewrites  │
     └──────────────────┘
```

---

## Agents

| Agent | Role |
|-------|------|
| Orchestrator | Dynamically decides which agent to call next based on pipeline state. Every routing decision logged with justification. |
| Decomposition | Breaks ambiguous queries into typed sub-tasks with dependency graphs. Dependent tasks wait for dependencies. |
| Retrieval | Multi-hop reasoning across 2+ chunks. Cites which chunk contributed to which part of the answer. |
| Critique | Reviews every agent output. Assigns confidence score per claim. Flags specific spans it disagrees with. |
| Synthesis | Merges all outputs. Resolves contradictions. Produces final answer with full provenance map. |
| Compression | Triggers when context budget exceeded. Lossless for structured data. Lossy only for filler text. |

---

## Tools

| Tool | Description | Failure Handling |
|------|-------------|-----------------|
| Web Search | Structured results with URLs and relevance scores | Timeout, empty results, malformed input |
| Code Executor | Runs Python snippets, returns stdout/stderr/exit code | 10s timeout, subprocess isolation |
| Database Lookup | Natural language to SQL conversion | Malformed input, empty results |
| Self Reflection | Re-reads previous outputs, finds contradictions | Missing logs, parse errors |

---

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/query | Submit query, receive streaming SSE response |
| GET | /api/job/{job_id}/trace | Full execution trace for any job |
| GET | /api/eval/latest | Latest eval summary by category and dimension |
| POST | /api/prompt-rewrite/{id}/approve | Approve or reject prompt rewrite |
| POST | /api/eval/rerun-failed | Re-run only failed test cases |
| POST | /api/eval/run | Run full 15-case evaluation pipeline |

---

## Evaluation Pipeline

15 test cases across 3 categories:

| Category | Count | Purpose |
|----------|-------|---------|
| Straightforward | 5 | Baseline scoring with known correct answers |
| Ambiguous | 5 | Tests decomposition quality on vague inputs |
| Adversarial | 5 | Prompt injections and false premises |

Scoring dimensions per test case:

| Dimension | Weight | What It Measures |
|-----------|--------|-----------------|
| Answer Correctness | 30% | Is the answer factually right? |
| Citation Accuracy | 20% | Are sources properly linked to claims? |
| Contradiction Resolution | 15% | Were critique flags resolved? |
| Tool Efficiency | 15% | Were tool calls necessary and justified? |
| Budget Compliance | 10% | Were token limits respected? |
| Critique Agreement | 10% | Did critique align with final output? |

---

## Self-Improving Loop

```
Eval Run Completes
        │
        ▼
Meta-Agent reads failure cases
        │
        ▼
Identifies worst performing prompt by dimension
        │
        ▼
Proposes rewrite with diff and justification
        │
        ▼
Stored as PENDING — NOT auto-applied
        │
        ▼
Human approves or rejects via API
        │
        ▼
If approved → re-run eval on failed cases only
        │
        ▼
Performance delta logged with timestamp
```

---

## Observability

Every agent action logged with:
- Timestamp, Agent ID, Event type
- Input hash + Output hash
- Latency in milliseconds
- Token count
- Policy violation flag

Single endpoint `/api/job/{job_id}/trace` returns complete execution trace reconstructing exact sequence of agent decisions, tool calls, and handoffs in order.

---

## Context Budget Management

| Agent | Max Budget |
|-------|-----------|
| Orchestrator | 8000 tokens |
| Synthesis Agent | 4000 tokens |
| Decomposition Agent | 3000 tokens |
| Retrieval Agent | 3000 tokens |
| Critique Agent | 3000 tokens |
| Compression Agent | 2000 tokens |

If budget exceeded → policy violation logged → compression agent triggered automatically.

---

## Reproducibility

- Docker pins all dependency versions exactly
- PostgreSQL stores every run with full inputs and outputs
- Re-running eval on same inputs produces diff-able output
- No credentials hardcoded anywhere — environment variables only
- Every eval run stored with exact prompts, tool calls, outputs, scores, and timestamps

---

## Known Limitations

- Web search uses stub data, not live internet
- Code executor uses subprocess, not fully isolated container
- Groq free tier has rate limits — wait 60s between heavy tests
- Self-improving loop requires human approval before applying rewrites

---

## What I Would Build Next

- Live web search via SerpAPI
- Fully isolated Docker sandbox for code execution
- Vector database for real RAG
- Frontend dashboard for real-time agent monitoring
- Automated A/B testing for prompt rewrites

---

## Documentation

| File | Contents |
|------|----------|
| [DECISIONS.md](DECISIONS.md) | Why every major design choice was made |
| [TESTING.md](TESTING.md) | How to test every component step by step |
| [DATA_FLOW.md](DATA_FLOW.md) | How data moves through the system |

---

---

## Troubleshooting

**Docker not starting?**
- Make sure Docker Desktop is open and whale icon is in taskbar
- Run `docker-compose down -v` then `docker-compose up --build`

**Database error?**
- Make sure POSTGRES_USER=postgres in .env
- Run `docker-compose down -v` to reset database volume

**Groq API error?**
- Check your GROQ_API_KEY is correct in .env and docker-compose.yml
- Free tier has rate limits — wait 60 seconds between requests

**Port 8000 already in use?**
- Stop other services using port 8000
- Or change port in docker-compose.yml from 8000:8000 to 8001:8000

---

## Example API Responses

**POST /api/query**
```json
{
  "event": "job_started",
  "job_id": "df53dae5-868c-4a94-946e-2c1ab96b1d8a",
  "agent": "orchestrator"
}
{
  "event": "agent_start",
  "agent": "decomposition_agent",
  "context_budget_remaining": 8000
}
{
  "event": "job_complete",
  "job_id": "df53dae5-868c-4a94-946e-2c1ab96b1d8a",
  "final_answer": "Machine learning is a subset of AI..."
}
```

**GET /api/job/{job_id}/trace**
```json
{
  "job_id": "df53dae5-868c-4a94-946e-2c1ab96b1d8a",
  "query": "What is machine learning?",
  "status": "completed",
  "execution_trace": [
    {
      "type": "agent_action",
      "agent_id": "decomposition_agent",
      "event_type": "decomposition_complete",
      "latency_ms": 834.2,
      "token_count": 120
    }
  ]
}
```

**GET /api/eval/latest**
```json
{
  "overall_average": 0.78,
  "by_category": {
    "straightforward": 0.88,
    "ambiguous": 0.72,
    "adversarial": 0.65
  },
  "by_dimension": {
    "correctness": 0.82,
    "citation_accuracy": 0.76,
    "contradiction_resolution": 0.80
  }
}

---

## AI Collaboration

Built with AI assistance from Claude by Anthropic. All code reviewed and tested before submission. AI used for code generation, architecture decisions, and debugging. Every component verified end to end.