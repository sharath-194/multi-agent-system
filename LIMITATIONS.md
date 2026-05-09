# Honest Limitations and What I Would Do Differently

This document is an honest assessment of where this system falls short and what a production version would look like.

---

## Current Limitations

### 1. Web Search Uses Stub Data
The web search tool returns hardcoded results instead of real internet search.

**Impact:** Citation accuracy is artificially limited. Real queries would benefit from live search results.

**Production fix:** Integrate SerpAPI or Brave Search API. Cost approximately $50/month for moderate usage.

---

### 2. Code Executor Is Not Fully Isolated
The code executor runs Python in a subprocess on the same machine.

**Impact:** Malicious code could theoretically affect the host system.

**Production fix:** Run code execution in a Docker container with no network access, limited CPU and memory, and automatic cleanup after each run.

---

### 3. Retrieval Does Not Use Vector Database
The retrieval agent uses LLM knowledge instead of real document retrieval.

**Impact:** Cannot retrieve from custom document collections. Citation sources are not real URLs.

**Production fix:** Integrate ChromaDB or Pinecone with real document ingestion pipeline. Embed documents at startup and retrieve by semantic similarity.

---

### 4. Self-Improving Loop Has No Memory Across Restarts
Proposed prompt rewrites are stored in PostgreSQL but approved prompts are not automatically applied to agent code.

**Impact:** Improvements are logged but not persisted across Docker restarts.

**Production fix:** Store approved prompts in database and load them at agent startup instead of using hardcoded prompts.

---

### 5. Single LLM Provider
System depends entirely on Groq. If Groq is down, entire system fails.

**Impact:** No fallback if primary LLM provider has outage.

**Production fix:** Add fallback chain: Groq then OpenAI then Anthropic with automatic failover.

---

### 6. No Authentication on API
All endpoints are publicly accessible with no authentication.

**Impact:** Anyone with the URL can submit queries and trigger eval runs.

**Production fix:** Add API key authentication middleware to FastAPI. Rate limit per key.

---

### 7. Commit History Was Made in One Session
All commits were made in a single development session rather than spread over multiple days.

**Impact:** Does not reflect real-world iterative development pattern.

**What I would do differently:** Start earlier and commit incrementally as each component is built and tested.

---

## What I Would Build Next

1. Live web search via SerpAPI
2. ChromaDB vector store for real document retrieval
3. Isolated Docker sandbox for code execution
4. Frontend dashboard showing real-time agent activity
5. Automated A/B testing comparing prompt versions
6. Multi-provider LLM fallback chain
7. API key authentication and rate limiting
8. Webhook notifications when eval scores drop below threshold