# Data Flow Documentation

This document explains how data flows through the system from input to output.

---

## Overview

User Query enters the Orchestrator Agent which dynamically routes through:
1. Decomposition Agent - breaks query into typed sub-tasks
2. Retrieval Agent - fetches chunks with citations
3. Synthesis Agent - creates draft answer
4. Critique Agent - scores and flags issues
5. Synthesis Agent - produces final answer with contradictions resolved
6. Final Response streamed to User via SSE

---

## Shared Context Object Schema

Every agent reads from and writes to a shared context object. No agent calls another agent directly. The orchestrator mediates all handoffs.

```json
{
    "job_id": "uuid-string",
    "query": "original user query",
    "completed_agents": ["decomposition_agent", "retrieval_agent"],
    "decomposition": {
        "sub_tasks": [
            {
                "id": "task_1",
                "type": "research",
                "description": "what needs to be done",
                "dependencies": []
            }
        ],
        "reasoning": "why decomposed this way"
    },
    "retrieved_chunks": [
        {
            "chunk_id": "chunk_1",
            "content": "retrieved information",
            "source": "source description",
            "relevance_score": 0.95,
            "contributes_to": "which part of answer"
        }
    ],
    "synthesis_draft": "first draft of answer",
    "critique": {
        "claims": [
            {
                "span": "exact text from answer",
                "confidence_score": 0.9,
                "verdict": "agree",
                "reason": "why"
            }
        ],
        "overall_confidence": 0.85,
        "flagged_issues": [],
        "recommendation": "approve"
    },
    "synthesis": {
        "final_answer": "complete final answer",
        "provenance_map": [
            {
                "sentence": "sentence from answer",
                "source_agent": "retrieval_agent",
                "source_chunk": "chunk_1"
            }
        ],
        "contradictions_resolved": [],
        "confidence": 0.9
    }
}
```

---

## Database Tables

### jobs
Stores every query submitted to the system.
- id: UUID primary key
- query: TEXT original user query
- status: STRING pending/completed/failed
- result: JSON final answer and metadata
- created_at: TIMESTAMP

### agent_logs
Stores every agent action for full auditability.
- id: UUID primary key
- job_id: UUID links to jobs table
- agent_id: STRING which agent ran
- event_type: STRING what happened
- input_hash: STRING MD5 of input
- output_hash: STRING MD5 of output
- input_data: JSON full input
- output_data: JSON full output
- latency_ms: FLOAT how long it took
- token_count: INTEGER tokens used
- policy_violation: BOOLEAN budget exceeded

### tool_logs
Stores every tool call with retry tracking.
- id: UUID primary key
- job_id: UUID links to jobs table
- tool_name: STRING which tool
- input_data: JSON what was sent
- output_data: JSON what came back
- latency_ms: FLOAT how long it took
- success: BOOLEAN did it work
- retry_count: INTEGER how many retries

### eval_runs
Stores every evaluation run for full reproducibility.
- id: UUID primary key
- test_case_id: STRING which test case
- category: STRING straightforward/ambiguous/adversarial
- query: TEXT the query tested
- expected_answer: TEXT what we expected
- actual_answer: TEXT what system produced
- correctness_score: FLOAT 0.0 to 1.0
- citation_score: FLOAT 0.0 to 1.0
- contradiction_score: FLOAT 0.0 to 1.0
- tool_efficiency_score: FLOAT 0.0 to 1.0
- budget_compliance_score: FLOAT 0.0 to 1.0
- critique_agreement_score: FLOAT 0.0 to 1.0
- total_score: FLOAT weighted average
- justification: JSON written reason per dimension

### prompt_rewrites
Stores every proposed prompt improvement.
- id: UUID primary key
- agent_id: STRING which agent needs improvement
- original_prompt: TEXT current prompt summary
- rewritten_prompt: TEXT proposed new prompt
- diff: TEXT what changed
- justification: TEXT why this improves things
- status: STRING pending/approved/rejected
- performance_delta: FLOAT improvement after approval

---

## No Data Leakage Policy

The evaluation pipeline is completely separated from the agent pipeline:
- Test cases in evaluation/test_cases.py are never seen by agents
- Agents have no access to expected answers at any point
- Scoring happens after agent pipeline completes independently
- Each eval run stored independently with timestamp
- Re-running eval on same inputs produces comparable results

---

## Token Budget Per Agent

- Orchestrator: 8000 tokens
- Decomposition Agent: 3000 tokens
- Retrieval Agent: 3000 tokens
- Critique Agent: 3000 tokens
- Synthesis Agent: 4000 tokens
- Compression Agent: 2000 tokens

If budget exceeded:
1. Policy violation logged to database
2. Compression agent triggered automatically
3. Older context summarized
4. Structured data preserved exactly
5. Conversational filler compressed

---

## Tool Failure Contracts

Every tool handles three failure modes explicitly:
- Timeout: returns error with empty results and logs latency
- Empty results: returns empty list with success flag false
- Malformed input: returns malformed_input error immediately

Orchestrator handles each failure differently:
- Timeout: retry up to 2 times with separate logging per attempt
- Empty results: continue pipeline with available data
- Malformed input: log violation and skip tool call