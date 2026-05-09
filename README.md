# Real-Time Multi-Agent LLM Orchestration and Evaluation System

A containerized, production-grade multi-agent system with a self-improving evaluation loop, dynamic tool orchestration, and adversarial robustness testing.

## Architecture
Orchestrator Agent (master)
├── Decomposition Agent
├── Retrieval Agent
├── Critique Agent
└── Synthesis Agent
Tools Layer
├── Web Search Tool
├── Code Executor Tool
├── Database Lookup Tool
└── Self Reflection Tool
Infrastructure
├── FastAPI Server (Port 8000)
├── PostgreSQL Database
└── Background Worker

## Agents Description

**Orchestrator Agent** - Dynamically decides which sub-agent to invoke at runtime. No hardcoded chains. All routing decisions logged with justification.

**Decomposition Agent** - Breaks ambiguous queries into typed sub-tasks with explicit dependency graphs.

**Retrieval Agent** - Performs multi-hop reasoning across at least two retrieved chunks. Cites which chunk contributed to which part of the answer.

**Critique Agent** - Reviews every agent output. Assigns confidence scores per claim. Flags specific spans it disagrees with.

**Synthesis Agent** - Merges all agent outputs. Resolves contradictions. Produces final answer with full provenance map.

**Compression Agent** - Activates when context budget exceeded. Lossless for structured data, lossy only for filler text.

## Tools Description

**Web Search** - Returns structured results with URLs and relevance scores. Handles timeout, empty results, malformed input.

**Code Executor** - Runs Python snippets. Returns stdout, stderr, exit code. Timeout protected.

**Database Lookup** - Natural language converted to SQL. Returns structured data.

**Self Reflection** - Agent re-reads its own previous outputs. Identifies contradictions.

## Setup Instructions

### Requirements
- Docker Desktop installed and running
- Gemini API key (free at https://aistudio.google.com/)

### Steps

1. Clone the repository:
```bash
git clone https://github.com/yourusername/multi-agent-system.git
cd multi-agent-system
```

2. Create your env file:
```bash
cp .env.example .env
```

3. Add your Gemini API key to .env file

4. Run everything with one command:
```bash
docker-compose up --build
```

5. Visit http://localhost:8000

## API Endpoints

POST /api/query - Submit query, get streaming SSE response

GET /api/job/{job_id}/trace - Get full execution trace

GET /api/eval/latest - Get latest eval run summary

POST /api/prompt-rewrite/{id}/approve - Approve or reject prompt rewrite

POST /api/eval/rerun-failed - Re-run failed test cases

POST /api/eval/run - Run full evaluation pipeline

## Evaluation

15 test cases across 3 categories:
- 5 straightforward queries
- 5 ambiguous queries
- 5 adversarial queries

Scoring dimensions:
- Answer correctness 30%
- Citation accuracy 20%
- Contradiction resolution 15%
- Tool efficiency 15%
- Budget compliance 10%
- Critique agreement 10%

## Self Improving Loop

After each eval run the meta-agent reads failure cases, identifies worst performing prompt, proposes a rewrite with justification. Human approves or rejects via API. If approved, system re-runs eval on failed cases and logs performance delta.

## Known Limitations

- Web search uses stub data not live internet
- Code executor runs in subprocess not fully isolated
- Gemini API rate limits may slow eval runs

## AI Collaboration

This project was built with AI assistance from Claude by Anthropic. All code was reviewed and tested before submission. AI was used for code generation, architecture decisions, and debugging.

## What I Would Build Next

- Live web search via SerpAPI
- Fully isolated Docker sandbox for code execution
- Vector database for real RAG
- Frontend dashboard for real-time monitoring