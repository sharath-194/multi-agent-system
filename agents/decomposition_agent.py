import json
from agents.base_agent import BaseAgent

class DecompositionAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_id="decomposition_agent", max_context_budget=3000)

    def run(self, context: dict) -> dict:
        job_id = context.get("job_id", "unknown")
        query = context.get("query", "")

        prompt = f"""You are a query decomposition agent.
Break down this query into typed sub-tasks with explicit dependencies.

Query: {query}

Respond in this exact JSON format:
{{
    "sub_tasks": [
        {{
            "id": "task_1",
            "type": "research|analysis|synthesis|retrieval",
            "description": "what needs to be done",
            "dependencies": []
        }},
        {{
            "id": "task_2", 
            "type": "analysis",
            "description": "analyze findings from task_1",
            "dependencies": ["task_1"]
        }}
    ],
    "reasoning": "why you decomposed it this way"
}}

Return ONLY valid JSON, no other text."""

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
                "sub_tasks": [
                    {
                        "id": "task_1",
                        "type": "research",
                        "description": query,
                        "dependencies": []
                    }
                ],
                "reasoning": "Failed to parse, using single task fallback"
            }

        context["decomposition"] = result
        self.log_event(
            job_id=job_id,
            event_type="decomposition_complete",
            input_data={"query": query},
            output_data=result
        )
        return context