import uuid
import json
from evaluation.test_cases import TEST_CASES
from evaluation.scorer import Scorer
from agents.orchestrator import OrchestratorAgent
from database.connection import SessionLocal
from database.models import EvalRun, AgentLog, ToolLog

class EvalRunner:
    def __init__(self):
        self.scorer = Scorer()
        self.orchestrator = OrchestratorAgent()

    def run_single_test(self, test_case: dict) -> dict:
        job_id = str(uuid.uuid4())
        query = test_case["query"]
        expected = test_case.get("expected_answer", "")
        category = test_case["category"]

        print(f"Running test {test_case['id']}: {query[:50]}...")

        try:
            context = {"job_id": job_id, "query": query}
            result_context = self.orchestrator.run(context)

            synthesis = result_context.get("synthesis", {})
            actual_answer = synthesis.get("final_answer", str(result_context))
            provenance_map = synthesis.get("provenance_map", [])
            critique = result_context.get("critique", {})

            db = SessionLocal()
            agent_logs = db.query(AgentLog).filter(AgentLog.job_id == job_id).all()
            tool_logs = db.query(ToolLog).filter(ToolLog.job_id == job_id).all()
            db.close()

            agent_logs_data = [{"policy_violation": log.policy_violation} for log in agent_logs]
            tool_logs_data = [{"success": log.success} for log in tool_logs]

            correctness = self.scorer.score_correctness(query, expected, actual_answer, job_id)
            citation = self.scorer.score_citation_accuracy(actual_answer, provenance_map, job_id)
            contradiction = self.scorer.score_contradiction_resolution(critique, synthesis, job_id)
            tool_eff = self.scorer.score_tool_efficiency(tool_logs_data, job_id)
            budget = self.scorer.score_budget_compliance(agent_logs_data, job_id)
            critique_agree = self.scorer.score_critique_agreement(critique, synthesis, job_id)

            scores = {
                "correctness": correctness,
                "citation_accuracy": citation,
                "contradiction_resolution": contradiction,
                "tool_efficiency": tool_eff,
                "budget_compliance": budget,
                "critique_agreement": critique_agree
            }

            total = self.scorer.compute_total_score(scores)

            db = SessionLocal()
            eval_record = EvalRun(
                test_case_id=test_case["id"],
                category=category,
                query=query,
                expected_answer=expected,
                actual_answer=actual_answer,
                correctness_score=correctness["score"],
                citation_score=citation["score"],
                contradiction_score=contradiction["score"],
                tool_efficiency_score=tool_eff["score"],
                budget_compliance_score=budget["score"],
                critique_agreement_score=critique_agree["score"],
                total_score=total,
                justification=scores
            )
            db.add(eval_record)
            db.commit()
            db.close()

            return {
                "test_case_id": test_case["id"],
                "category": category,
                "query": query,
                "actual_answer": actual_answer,
                "scores": scores,
                "total_score": total,
                "job_id": job_id
            }

        except Exception as e:
            print(f"Error running test {test_case['id']}: {e}")
            return {
                "test_case_id": test_case["id"],
                "category": category,
                "query": query,
                "error": str(e),
                "total_score": 0.0,
                "job_id": job_id
            }

    def run_all_tests(self) -> dict:
        results = []
        for test_case in TEST_CASES:
            result = self.run_single_test(test_case)
            results.append(result)

        summary = self.generate_summary(results)
        return {"results": results, "summary": summary}

    def run_failed_tests(self, failed_ids: list) -> dict:
        failed_cases = [tc for tc in TEST_CASES if tc["id"] in failed_ids]
        results = []
        for test_case in failed_cases:
            result = self.run_single_test(test_case)
            results.append(result)
        summary = self.generate_summary(results)
        return {"results": results, "summary": summary}

    def generate_summary(self, results: list) -> dict:
        if not results:
            return {}

        by_category = {}
        for result in results:
            cat = result.get("category", "unknown")
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(result.get("total_score", 0.0))

        category_averages = {
            cat: round(sum(scores) / len(scores), 3)
            for cat, scores in by_category.items()
        }

        all_scores = [r.get("total_score", 0.0) for r in results]
        overall_average = round(sum(all_scores) / len(all_scores), 3) if all_scores else 0.0

        dimension_averages = {}
        dimensions = ["correctness", "citation_accuracy", "contradiction_resolution",
                     "tool_efficiency", "budget_compliance", "critique_agreement"]

        for dim in dimensions:
            dim_scores = []
            for r in results:
                scores = r.get("scores", {})
                if dim in scores:
                    dim_scores.append(scores[dim].get("score", 0.0))
            if dim_scores:
                dimension_averages[dim] = round(sum(dim_scores) / len(dim_scores), 3)

        return {
            "total_tests": len(results),
            "overall_average": overall_average,
            "by_category": category_averages,
            "by_dimension": dimension_averages,
            "failed_tests": [r["test_case_id"] for r in results if r.get("total_score", 0) < 0.5]
        }