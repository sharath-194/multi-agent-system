import json
from agents.base_agent import BaseAgent

class CompressionAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_id="compression_agent", max_context_budget=2000)

    def run(self, context: dict) -> dict:
        job_id = context.get("job_id", "unknown")
        context_str = json.dumps(context, default=str)
        token_count = self.count_tokens(context_str)

        if token_count <= 3000:
            return context

        prompt = f"""You are a compression agent. Compress this context.

Rules:
- Keep ALL structured data (tool outputs, scores, citations) EXACTLY as is
- Only compress conversational filler and redundant text
- Never remove JSON objects, scores, or source citations

Context to compress:
{context_str[:3000]}

Return compressed version as JSON with same structure but shorter text values."""

        response = self.call_llm(prompt, job_id)
        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
            compressed = json.loads(cleaned.strip())
            self.log_event(
                job_id=job_id,
                event_type="compression_complete",
                input_data={"original_tokens": token_count},
                output_data={"compressed": True}
            )
            return compressed
        except:
            return context