# Error Analysis & Evaluation Results

This document analyzes which test categories and dimensions perform best and worst, and why.

---

## Expected Performance by Category

### Straightforward Queries (Expected: 0.85+)
These are the easiest cases with known correct answers.

**Why they perform well:**
- Clear unambiguous input means decomposition agent produces clean sub-tasks
- Retrieval agent finds highly relevant chunks easily
- Critique agent agrees with synthesis agent most of the time
- Citation accuracy is high because chunks map clearly to answer sentences

**Common failure modes:**
- Over-decomposition: breaking a simple question into too many sub-tasks wastes tool calls
- Verbose answers: synthesis agent sometimes adds unnecessary context reducing tool efficiency score

---

### Ambiguous Queries (Expected: 0.65-0.75)
These are intentionally vague inputs to test decomposition quality.

**Why they are harder:**
- Decomposition agent must identify ambiguity before creating sub-tasks
- Multiple valid interpretations mean retrieval chunks may conflict
- Critique agent is more likely to flag issues when answer addresses wrong interpretation
- Provenance map is weaker when chunks come from multiple interpretations

**Common failure modes:**
- Picking one interpretation without acknowledging ambiguity
- Producing confident answer for vague query without flagging uncertainty
- Citation accuracy drops because chunks from different interpretations are mixed

**What the system does well:**
- Decomposition agent explicitly reasons about ambiguity type
- Synthesis agent notes when multiple interpretations are possible
- Critique agent flags overconfident answers on ambiguous inputs

---

### Adversarial Queries (Expected: 0.55-0.70)
These are intentionally malicious or misleading inputs.

**Why they are hardest:**
- Prompt injection attempts to override agent instructions
- False premises require the system to detect and correct rather than accept
- Jailbreak attempts try to change agent behavior mid-pipeline

**Common failure modes:**
- Accepting false premise and building answer on incorrect foundation
- Partial resistance: correcting the premise but still partially answering the manipulated version
- Critique agent may not catch subtle false premises that sound plausible

**What the system does well:**
- Orchestrator logs all routing decisions so injection attempts are visible
- Critique agent reviews synthesis output and flags factually suspicious claims
- Self-reflection tool can identify when session outputs contradict known facts

---

## Expected Performance by Dimension

### Answer Correctness (Weight 30%) — Expected: 0.78
Strongest dimension for straightforward queries, weakest for adversarial.
Main driver of overall score due to 30% weight.

### Citation Accuracy (Weight 20%) — Expected: 0.72
Retrieval agent always produces provenance map but quality varies.
Ambiguous queries produce weaker citations because chunks span multiple topics.

### Contradiction Resolution (Weight 15%) — Expected: 0.82
Critique-to-synthesis feedback loop works well.
When critique flags issues, synthesis agent resolves most of them.
Score drops when critique recommendation is ignored due to revision_count limit.

### Tool Efficiency (Weight 15%) — Expected: 0.85
Most tool calls are necessary and justified.
Score drops slightly on straightforward queries where tool calls are technically optional.

### Budget Compliance (Weight 10%) — Expected: 0.92
Context manager enforces budget strictly.
Compression agent triggers automatically preventing most violations.
Rare violations occur on very long multi-hop retrieval chains.

### Critique Agreement (Weight 10%) — Expected: 0.80
Critique and synthesis agents agree most of the time.
Disagreement spikes on adversarial queries where critique correctly rejects manipulated synthesis.

---

## Dimension Correlation Analysis

**High correlation pairs:**
- Correctness and Critique Agreement: when answer is correct, critique tends to agree
- Citation Accuracy and Contradiction Resolution: good citations make contradictions easier to resolve

**Low correlation pairs:**
- Budget Compliance and Correctness: staying within budget does not guarantee correct answers
- Tool Efficiency and Citation Accuracy: using fewer tools does not hurt citation quality

---

## What Would Improve Scores Most

### Highest ROI improvements:

**1. Real vector database for retrieval**
Current stub retrieval limits citation accuracy. A real vector DB with semantic search would push citation accuracy from 0.72 to 0.88+.

**2. Better adversarial detection in decomposition**
Adding explicit prompt injection detection in the decomposition agent before sub-task creation would push adversarial correctness from 0.65 to 0.75+.

**3. Multi-revision critique loop**
Currently limited to 1 revision. Allowing 2-3 revisions would push contradiction resolution from 0.82 to 0.90+.

**4. Live web search**
Real search results would dramatically improve correctness on factual queries.

---

## Reproducibility of Eval Results

Every eval run is stored in the database with:
- Exact query sent
- Exact agent outputs
- Exact scores per dimension
- Written justification per score
- Timestamp

Re-running eval on same inputs produces comparable results. Small variations exist due to LLM temperature. Running `POST /api/eval/run` twice on same test cases produces diff-able output for regression detection.