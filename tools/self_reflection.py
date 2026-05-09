import time
import json
from agents.base_agent import BaseAgent
from database.connection import SessionLocal
from database.models import AgentLog, ToolLog

class SelfReflectionTool:
    def __init__(self):
        self.tool_name = "self_reflection"
        self.agent = BaseAgent(agent_id="self_reflection_tool")

    def log_tool(self, job_id, input_data, output_data, latency_ms, success, retry_count=0):
        try:
            db = SessionLocal()
            log = ToolLog(
                job_id=job_id,
                tool_name=self.tool_name,
                input_data=input_data,
                output_data=output_data,
                latency_ms=latency_ms,
                success=success,
                retry_count=retry_count
            )
            db.add(log)
            db.commit()
            db.close()
        except Exception as e:
            print(f"Tool log error: {e}")

    def run(self, job_id: str, retry_count: int = 0) -> dict:
        start = time.time()

        try:
            db = SessionLocal()
            logs = db.query(AgentLog).filter(AgentLog.job_id == job_id).all()
            db.close()

            previous_outputs = []
            for log in logs:
                if log.output_data:
                    previous_outputs.append({
                        "agent": log.agent_id,
                        "event": log.event_type,
                        "output_preview": str(log.output_data)[:300]
                    })

            if not previous_outputs:
                return {"contradictions": [], "summary": "No previous outputs found", "confidence": 1.0}

            outputs_text = json.dumps(previous_outputs, indent=2)
            prompt = f"""You are a self-reflection agent. Review these previous outputs from this session.

Previous outputs:
{outputs_text}

Identify any contradictions or inconsistencies between the outputs.

Respond in this exact JSON format:
{{
    "contradictions": [
        {{
            "agents_involved": ["agent1", "agent2"],
            "description": "what contradicts what",
            "severity": "high|medium|low"
        }}
    ],
    "summary": "overall assessment",
    "confidence": 0.9
}}

Return ONLY valid JSON."""

            response = self.agent.call_llm(prompt, job_id)
            try:
                cleaned = response.strip()
                if cleaned.startswith("```"):
                    cleaned = cleaned.split("```")[1]
                    if cleaned.startswith("json"):
                        cleaned = cleaned[4:]
                result = json.loads(cleaned.strip())
            except:
                result = {"contradictions": [], "summary": response, "confidence": 0.7}

            latency = (time.time() - start) * 1000
            self.log_tool(job_id, {"job_id": job_id}, result, latency, True, retry_count)
            return result

        except Exception as e:
            result = {"error": str(e), "contradictions": [], "summary": "Error during reflection"}
            self.log_tool(job_id, {"job_id": job_id}, result, 0, False, retry_count)
            return result