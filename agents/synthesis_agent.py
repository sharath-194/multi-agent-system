import json
from agents.base_agent import BaseAgent

class SynthesisAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_id="synthesis_agent", max_context_budget=4000)

    def run(self, context: dict) -> dict:
        job_id = context.get("job_id", "unknown")
        query = context.get("query", "")
        chunks = context.get("retrieved_chunks", [])
        critique = context.get("critique", {})

        chunks_text = json.dumps(chunks, indent=2)
        critique_text = json.dumps(critique, indent=2)

        prompt = f"""You are a synthesis agent. Merge all agent outputs into a final answer.

Original query: {query}

Retrieved chunks:
{chunks_text}

Critique feedback:
{critique_text}

Create a final answer that:
1. Resolves any contradictions flagged by the critique agent
2. Includes a provenance map linking each sentence to its source chunk
3. Is clear and directly answers the query

Respond in this exact JSON format:
{{
    "final_answer": "your complete answer here",
    "provenance_map": [
        {{
            "sentence": "sentence from the answer",
            "source_agent": "retrieval_agent",
            "source_chunk": "chunk_1"
        }}
    ],
    "contradictions_resolved": ["list of contradictions you resolved"],
    "confidence": 0.9
}}

Return ONLY valid JSON."""

        response = self.call_llm(prompt, job_id)
        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
            result = json.loads(cleaned.strip())
        except:
            result = {
                "final_answer": response,
                "provenance_map": [],
                "contradictions_resolved": [],
                "confidence": 0.7
            }

        context["synthesis"] = result
        context["synthesis_draft"] = result.get("final_answer", "")
        self.log_event(
            job_id=job_id,
            event_type="synthesis_complete",
            input_data={"query": query},
            output_data=result
        )
        return context