import json
import time
from agents.base_agent import BaseAgent
from agents.decomposition_agent import DecompositionAgent
from agents.retrieval_agent import RetrievalAgent
from agents.critique_agent import CritiqueAgent
from agents.synthesis_agent import SynthesisAgent
from agents.compression_agent import CompressionAgent
from agents.context_manager import ContextManager

class OrchestratorAgent(BaseAgent):
    def __init__(self):
        super().__init__(agent_id="orchestrator", max_context_budget=8000)
        self.decomposition = DecompositionAgent()
        self.retrieval = RetrievalAgent()
        self.critique = CritiqueAgent()
        self.synthesis = SynthesisAgent()
        self.compression = CompressionAgent()

    def decide_next_agent(self, context: dict) -> str:
        completed = context.get("completed_agents", [])
        
        if "decomposition_agent" not in completed:
            return "decomposition_agent"
        if "retrieval_agent" not in completed:
            return "retrieval_agent"
        if "synthesis_agent" not in completed:
            return "synthesis_agent"
        if "critique_agent" not in completed:
            return "critique_agent"
        
        critique = context.get("critique", {})
        if critique.get("recommendation") == "revise" and context.get("revision_count", 0) < 1:
            context["revision_count"] = context.get("revision_count", 0) + 1
            completed.remove("synthesis_agent")
            completed.remove("critique_agent")
            return "synthesis_agent"
        
        return "done"

    def run(self, context: dict) -> dict:
        job_id = context.get("job_id", "unknown")
        context["completed_agents"] = []
        context_mgr = ContextManager(max_budget=8000)
        context_mgr.update("job_id", job_id)
        context_mgr.update("query", context.get("query", ""))

        self.log_event(
            job_id=job_id,
            event_type="orchestration_start",
            input_data={"query": context.get("query", "")}
        )

        max_steps = 10
        steps = 0

        while steps < max_steps:
            steps += 1
            
            if not context_mgr.check_budget():
                context_mgr.summarize_old_context()
                current_context = context_mgr.get_all()
                compressed = self.compression.run(current_context)
                for k, v in compressed.items():
                    context_mgr.update(k, v)

            current_context = context_mgr.get_all()
            next_agent = self.decide_next_agent(current_context)

            self.log_event(
                job_id=job_id,
                event_type="routing_decision",
                input_data={"completed": current_context.get("completed_agents", [])},
                output_data={"next_agent": next_agent, "justification": f"Selected {next_agent} based on pipeline state"}
            )

            if next_agent == "done":
                break

            agent_map = {
                "decomposition_agent": self.decomposition,
                "retrieval_agent": self.retrieval,
                "synthesis_agent": self.synthesis,
                "critique_agent": self.critique
            }

            agent = agent_map.get(next_agent)
            if agent:
                updated_context = agent.run(current_context)
                for k, v in updated_context.items():
                    context_mgr.update(k, v)
                completed = context_mgr.get("completed_agents") or []
                completed.append(next_agent)
                context_mgr.update("completed_agents", completed)

        final_context = context_mgr.get_all()
        self.log_event(
            job_id=job_id,
            event_type="orchestration_complete",
            output_data={"steps": steps, "agents_used": final_context.get("completed_agents", [])}
        )
        return final_context