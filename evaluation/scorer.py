import json
from agents.base_agent import BaseAgent

class Scorer:
    def __init__(self):
        self.agent = BaseAgent(agent_id="scorer")

    def score_correctness(self, query: str, expected: str, actual: str, job_id: str) -> dict:
        prompt = f"""You are an evaluation scorer. Score the correctness of this answer.

Query: {query}
Expected answer: {expected}
Actual answer: {actual}

Score from 0.0 to 1.0 where:
1.0 = perfectly correct
0.5 = partially correct
0.0 = completely wrong or harmful

Respond in this exact JSON format:
{{
    "score": 0.8,
    "justification": "why you gave this score"
}}

Return ONLY valid JSON."""

        response = self.agent.call_llm(prompt, job_id)
        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
            return json.loads(cleaned.strip())
        except:
            return {"score": 0.5, "justification": "Could not parse scorer response"}

    def score_citation_accuracy(self, answer: str, provenance_map: list, job_id: str) -> dict:
        if not provenance_map:
            return {"score": 0.3, "justification": "No provenance map provided"}

        prompt = f"""Score the citation accuracy of this answer.

Answer: {answer}
Provenance map: {json.dumps(provenance_map, indent=2)}

Check if each sentence is properly linked to a source.
Score from 0.0 to 1.0.

Respond in this exact JSON format:
{{
    "score": 0.8,
    "justification": "why you gave this score"
}}

Return ONLY valid JSON."""

        response = self.agent.call_llm(prompt, job_id)
        try:
            cleaned = response.strip()
            if cleaned.startswith("```"):
                cleaned = cleaned.split("```")[1]
                if cleaned.startswith("json"):
                    cleaned = cleaned[4:]
            return json.loads(cleaned.strip())
        except:
            return {"score": 0.5, "justification": "Could not parse scorer response"}

    def score_contradiction_resolution(self, critique: dict, synthesis: dict, job_id: str) -> dict:
        if not critique or not synthesis:
            return {"score": 0.5, "justification": "Missing critique or synthesis data"}

        flagged = critique.get("flagged_issues", [])
        resolved = synthesis.get("contradictions_resolved", [])

        if not flagged:
            return {"score": 1.0, "justification": "No contradictions to resolve"}

        ratio = len(resolved) / len(flagged) if flagged else 1.0
        score = min(1.0, ratio)
        return {
            "score": score,
            "justification": f"Resolved {len(resolved)} of {len(flagged)} flagged issues"
        }

    def score_tool_efficiency(self, tool_logs: list, job_id: str) -> dict:
        if not tool_logs:
            return {"score": 1.0, "justification": "No tool calls made"}

        unnecessary = sum(1 for log in tool_logs if not log.get("success", True))
        total = len(tool_logs)
        score = max(0.0, 1.0 - (unnecessary / total) * 0.5) if total > 0 else 1.0

        return {
            "score": score,
            "justification": f"{total} tool calls, {unnecessary} unsuccessful"
        }

    def score_budget_compliance(self, agent_logs: list, job_id: str) -> dict:
        violations = sum(1 for log in agent_logs if log.get("policy_violation", False))
        total = len(agent_logs)

        if total == 0:
            return {"score": 1.0, "justification": "No agent logs to check"}

        score = max(0.0, 1.0 - (violations / total))
        return {
            "score": score,
            "justification": f"{violations} policy violations out of {total} agent actions"
        }

    def score_critique_agreement(self, critique: dict, synthesis: dict, job_id: str) -> dict:
        if not critique or not synthesis:
            return {"score": 0.5, "justification": "Missing data"}

        recommendation = critique.get("recommendation", "approve")
        confidence = synthesis.get("confidence", 0.7)

        if recommendation == "approve":
            score = confidence
        elif recommendation == "revise":
            resolved = synthesis.get("contradictions_resolved", [])
            score = 0.7 if resolved else 0.4
        else:
            score = 0.3

        return {
            "score": score,
            "justification": f"Critique recommended {recommendation}, synthesis confidence {confidence}"
        }

    def compute_total_score(self, scores: dict) -> float:
        weights = {
            "correctness": 0.3,
            "citation_accuracy": 0.2,
            "contradiction_resolution": 0.15,
            "tool_efficiency": 0.15,
            "budget_compliance": 0.1,
            "critique_agreement": 0.1
        }
        total = 0.0
        for key, weight in weights.items():
            score = scores.get(key, {}).get("score", 0.5)
            total += score * weight
        return round(total, 3)