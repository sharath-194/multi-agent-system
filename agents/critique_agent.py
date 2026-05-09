import json
from agents.base_agent import BaseAgent

class CritiqueAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_id="critique_agent", max_context_budget=3000)

    def run(self, context: dict) -> dict:
        job_id = context.get("job_id", "unknown")
        content_to_review = context.get("synthesis_draft", 
                           context.get("retrieval_summary", "No content to review"))

        prompt = f"""You are a critique agent. Review this content carefully.

Content to review:
{content_to_review}

Assign confidence scores and flag disagreements at the span level.

Respond in this exact JSON format:
{{
    "claims": [
        {{
            "span": "exact text from the content",
            "confidence_score": 0.9,
            "verdict": "agree|disagree|uncertain",
            "reason": "why you agree or disagree"
        }}
    ],
    "overall_confidence": 0.85,
    "flagged_issues": ["list of specific issues"],
    "recommendation": "approve|revise|reject"
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
                "claims": [],
                "overall_confidence": 0.7,
                "flagged_issues": [],
                "recommendation": "approve"
            }

        context["critique"] = result
        self.log_event(
            job_id=job_id,
            event_type="critique_complete",
            input_data={"content_preview": str(content_to_review)[:200]},
            output_data=result
        )
        return context