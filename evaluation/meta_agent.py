import json
import uuid
from agents.base_agent import BaseAgent
from database.connection import SessionLocal
from database.models import EvalRun, PromptRewrite

class MetaAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_id="meta_agent")

    def find_worst_performing_prompt(self, eval_results: dict) -> dict:
        results = eval_results.get("results", [])
        if not results:
            return {}

        by_dimension = {}
        dimensions = ["correctness", "citation_accuracy", "contradiction_resolution",
                     "tool_efficiency", "budget_compliance", "critique_agreement"]

        for dim in dimensions:
            dim_scores = []
            for r in results:
                scores = r.get("scores", {})
                if dim in scores:
                    dim_scores.append(scores[dim].get("score", 0.0))
            if dim_scores:
                by_dimension[dim] = sum(dim_scores) / len(dim_scores)

        if not by_dimension:
            return {}

        worst_dimension = min(by_dimension, key=by_dimension.get)
        worst_score = by_dimension[worst_dimension]

        agent_map = {
            "correctness": "synthesis_agent",
            "citation_accuracy": "retrieval_agent",
            "contradiction_resolution": "critique_agent",
            "tool_efficiency": "orchestrator",
            "budget_compliance": "orchestrator",
            "critique_agreement": "critique_agent"
        }

        return {
            "worst_dimension": worst_dimension,
            "worst_score": worst_score,
            "responsible_agent": agent_map.get(worst_dimension, "orchestrator")
        }

    def propose_rewrite(self, agent_id: str, dimension: str, score: float, eval_results: dict) -> dict:
        job_id = str(uuid.uuid4())

        failed_cases = [
            r for r in eval_results.get("results", [])
            if r.get("scores", {}).get(dimension, {}).get("score", 1.0) < 0.5
        ]

        failed_text = json.dumps(failed_cases[:3], indent=2)

        prompt = f"""You are a meta-agent that improves AI system prompts.

The {agent_id} is performing poorly on {dimension} with score {score:.2f}.

Failed test cases:
{failed_text}

Propose a better system prompt for the {agent_id} that would improve {dimension}.

Respond in this exact JSON format:
{{
    "original_prompt_summary": "what the current prompt does",
    "proposed_rewrite": "the full new prompt text here",
    "diff_summary": "what specifically changed and why",
    "justification": "why this will improve the score",
    "expected_improvement": 0.2
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
                "original_prompt_summary": f"Current {agent_id} prompt",
                "proposed_rewrite": f"Improved prompt for {agent_id} focusing on {dimension}",
                "diff_summary": "Enhanced instructions for better performance",
                "justification": "More specific guidance should improve scores",
                "expected_improvement": 0.1
            }

        try:
            db = SessionLocal()
            rewrite = PromptRewrite(
                agent_id=agent_id,
                original_prompt=result.get("original_prompt_summary", ""),
                rewritten_prompt=result.get("proposed_rewrite", ""),
                diff=result.get("diff_summary", ""),
                justification=result.get("justification", ""),
                status="pending"
            )
            db.add(rewrite)
            db.commit()
            rewrite_id = rewrite.id
            db.close()
            result["rewrite_id"] = rewrite_id
        except Exception as e:
            result["rewrite_id"] = str(uuid.uuid4())
            print(f"Error saving rewrite: {e}")

        return result

    def run_improvement_loop(self, eval_results: dict) -> dict:
        worst = self.find_worst_performing_prompt(eval_results)
        if not worst:
            return {"message": "No improvement needed", "eval_results": eval_results}

        rewrite = self.propose_rewrite(
            agent_id=worst["responsible_agent"],
            dimension=worst["worst_dimension"],
            score=worst["worst_score"],
            eval_results=eval_results
        )

        return {
            "worst_performing": worst,
            "proposed_rewrite": rewrite,
            "status": "pending_approval",
            "message": f"Rewrite proposed for {worst['responsible_agent']} to improve {worst['worst_dimension']}"
        }