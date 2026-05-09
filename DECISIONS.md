# Architecture Decision Records

This document explains every major design decision made in this system and why simpler alternatives were rejected.

---

## Decision 1: Multi-Agent Architecture over Single LLM Call

### What we chose
A pipeline of 5 specialized agents: Decomposition, Retrieval, Critique, Synthesis, and Compression.

### What we could have done instead
A single LLM call with a long prompt.

### Why we chose multi-agent
A single LLM call cannot reliably decompose, retrieve, critique, and synthesize in one shot for complex queries. Each agent is specialized and can be independently improved, tested, and replaced. The critique agent catching errors from the synthesis agent is impossible in a single call architecture.

### Tradeoff accepted
More latency per query. More API calls. We accepted this because accuracy and auditability matter more than speed for this use case.

---

## Decision 2: Dynamic Routing over Hardcoded Chain

### What we chose
The orchestrator decides at runtime which agent to call next based on pipeline state.

### What we could have done instead
A fixed chain: decompose → retrieve → synthesize → critique always in that order.

### Why we chose dynamic routing
A hardcoded chain cannot handle cases where the critique agent recommends revision, requiring synthesis to re-run. Dynamic routing allows the system to loop, skip, or reorder agents based on actual results.

### Tradeoff accepted
More complex orchestration logic. Harder to debug. We mitigated this by logging every routing decision with justification.

---

## Decision 3: PostgreSQL over SQLite

### What we chose
PostgreSQL running in Docker container.

### What we could have done instead
SQLite file-based database, zero setup required.

### Why we chose PostgreSQL
SQLite does not support concurrent writes from multiple services. Our system has an API server, background worker, and eval runner all writing simultaneously. PostgreSQL handles this correctly.

### Tradeoff accepted
Requires Docker. More complex setup. Mitigated by docker-compose automating everything.

---

## Decision 4: Groq LLaMA over OpenAI GPT

### What we chose
Groq API with LLaMA 3.3 70B model.

### What we could have done instead
OpenAI GPT-4 or GPT-3.5.

### Why we chose Groq
Groq offers a free tier with very fast inference. LLaMA 3.3 70B is a capable open model. For a take-home assessment, minimizing cost while maximizing capability is the pragmatic choice.

### Tradeoff accepted
Slightly less instruction-following than GPT-4. Mitigated by structured JSON prompts with explicit format requirements.

---

## Decision 5: Custom Scoring over Third-Party Eval Framework

### What we chose
Built all scoring logic ourselves in scorer.py.

### What we could have done instead
Used frameworks like RAGAS, DeepEval, or LangSmith.

### Why we chose custom scoring
The assignment explicitly required building scoring logic ourselves. Additionally, custom scoring gives us full control over what each dimension measures and produces human-readable justification strings, not just numbers.

### Tradeoff accepted
More code to maintain. More potential for bugs. Mitigated by keeping each scoring function simple and independently testable.

---

## Decision 6: Server-Sent Events over WebSockets

### What we chose
SSE (Server-Sent Events) for streaming agent outputs to the client.

### What we could have done instead
WebSockets for bidirectional real-time communication.

### Why we chose SSE
Our streaming is one-directional: server pushes updates to client. SSE is simpler, works over standard HTTP, requires no special client library, and is natively supported by browsers. WebSockets would add unnecessary complexity for a one-way stream.

### Tradeoff accepted
No bidirectional communication. Cannot push updates from client mid-stream. Acceptable for our use case.

---

## Decision 7: Shared Context Object over Direct Agent Calls

### What we chose
All inter-agent communication passes through a shared context dictionary managed by the orchestrator.

### What we could have done instead
Agents calling each other directly as functions or via message queues.

### Why we chose shared context
Direct agent calls create tight coupling and make it impossible to audit what information was passed between agents. A shared context object gives full visibility into the pipeline state at every step and allows the orchestrator to compress or modify context before passing it forward.

### Tradeoff accepted
Single point of failure at the context object. Mitigated by the context manager tracking budget and flagging violations.

---

## Decision 8: Lossless Compression for Structured Data

### What we chose
The compression agent preserves all structured data (tool outputs, scores, citations) exactly and only compresses conversational filler.

### What we could have done instead
Compress everything uniformly to fit within token budget.

### Why we chose selective compression
Losing a citation score or tool output would corrupt downstream reasoning. Conversational filler adds no value to agent reasoning. Selective compression maximizes information density within the token budget.

### Tradeoff accepted
More complex compression logic. Requires the compression agent to distinguish structured from unstructured content.