import json
from agents.base_agent import BaseAgent

class RetrievalAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_id="retrieval_agent", max_context_budget=3000)

    def run(self, context: dict) -> dict:
        job_id = context.get("job_id", "unknown")
        query = context.get("query", "")
        sub_tasks = context.get("decomposition", {}).get("sub_tasks", [])

        chunks = []
        for task in sub_tasks:
            prompt = f"""You are a retrieval agent doing multi-hop reasoning.

Main query: {query}
Current task: {task['description']}

Retrieve and reason across at least 2 information chunks.
For each chunk, cite which part of the answer it contributes to.

Respond in this exact JSON format:
{{
    "chunks": [
        {{
            "chunk_id": "chunk_1",
            "content": "information retrieved",
            "source": "source description",
            "relevance_score": 0.9,
            "contributes_to": "which part of the answer this helps with"
        }},
        {{
            "chunk_id": "chunk_2",
            "content": "more information",
            "source": "another source",
            "relevance_score": 0.8,
            "contributes_to": "which part of the answer this helps with"
        }}
    ],
    "reasoning": "how these chunks connect"
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
                chunks.extend(result.get("chunks", []))
            except:
                chunks.append({
                    "chunk_id": f"chunk_{task['id']}",
                    "content": f"Retrieved information for: {task['description']}",
                    "source": "internal knowledge",
                    "relevance_score": 0.7,
                    "contributes_to": task['description']
                })

        context["retrieved_chunks"] = chunks
        self.log_event(
            job_id=job_id,
            event_type="retrieval_complete",
            input_data={"query": query},
            output_data={"chunk_count": len(chunks)}
        )
        return context