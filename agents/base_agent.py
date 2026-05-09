import os
import time
import hashlib
import json
from groq import Groq
from dotenv import load_dotenv
from database.connection import SessionLocal
from database.models import AgentLog

load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

class BaseAgent:
    def __init__(self, agent_id: str, max_context_budget: int = 4000):
        self.agent_id = agent_id
        self.max_context_budget = max_context_budget

    def hash_data(self, data) -> str:
        return hashlib.md5(json.dumps(data, default=str).encode()).hexdigest()

    def count_tokens(self, text: str) -> int:
        return len(text.split()) * 2

    def check_budget(self, context: dict) -> bool:
        context_str = json.dumps(context, default=str)
        tokens = self.count_tokens(context_str)
        if tokens > self.max_context_budget:
            self.log_event(
                job_id=context.get("job_id", "unknown"),
                event_type="policy_violation",
                input_data={"token_count": tokens, "budget": self.max_context_budget},
                output_data={"violation": "context budget exceeded"},
                policy_violation=True
            )
            return False
        return True

    def log_event(self, job_id: str, event_type: str, input_data=None,
                  output_data=None, latency_ms=None, token_count=None,
                  policy_violation=False):
        try:
            db = SessionLocal()
            log = AgentLog(
                job_id=job_id,
                agent_id=self.agent_id,
                event_type=event_type,
                input_hash=self.hash_data(input_data) if input_data else None,
                output_hash=self.hash_data(output_data) if output_data else None,
                input_data=input_data,
                output_data=output_data,
                latency_ms=latency_ms,
                token_count=token_count,
                policy_violation=policy_violation
            )
            db.add(log)
            db.commit()
            db.close()
        except Exception as e:
            print(f"Logging error: {e}")

    def call_llm(self, prompt: str, job_id: str) -> str:
        start = time.time()
        try:
            response = groq_client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000
            )
            result = response.choices[0].message.content
            latency = (time.time() - start) * 1000
            self.log_event(
                job_id=job_id,
                event_type="llm_call",
                input_data={"prompt_preview": prompt[:200]},
                output_data={"response_preview": result[:200]},
                latency_ms=latency,
                token_count=self.count_tokens(result)
            )
            return result
        except Exception as e:
            self.log_event(
                job_id=job_id,
                event_type="llm_error",
                input_data={"prompt_preview": prompt[:200]},
                output_data={"error": str(e)}
            )
            return f"Error: {str(e)}"

    def run(self, context: dict) -> dict:
        raise NotImplementedError("Each agent must implement run()")