import time
import subprocess
import sys
from database.connection import SessionLocal
from database.models import ToolLog

class CodeExecutorTool:
    def __init__(self):
        self.tool_name = "code_executor"
        self.timeout_seconds = 10

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

    def run(self, code: str, job_id: str, retry_count: int = 0) -> dict:
        start = time.time()

        if not code or not isinstance(code, str):
            result = {"error": "malformed_input", "stdout": "", "stderr": "Invalid code input", "exit_code": 1}
            self.log_tool(job_id, {"code": str(code)}, result, 0, False, retry_count)
            return result

        try:
            process = subprocess.run(
                [sys.executable, "-c", code],
                capture_output=True,
                text=True,
                timeout=self.timeout_seconds
            )
            latency = (time.time() - start) * 1000
            output = {
                "stdout": process.stdout,
                "stderr": process.stderr,
                "exit_code": process.returncode,
                "success": process.returncode == 0
            }
            self.log_tool(job_id, {"code_preview": code[:200]}, output, latency, True, retry_count)
            return output

        except subprocess.TimeoutExpired:
            result = {"error": "timeout", "stdout": "", "stderr": "Code execution timed out", "exit_code": 1}
            self.log_tool(job_id, {"code_preview": code[:200]}, result, self.timeout_seconds * 1000, False, retry_count)
            return result
        except Exception as e:
            result = {"error": str(e), "stdout": "", "stderr": str(e), "exit_code": 1}
            self.log_tool(job_id, {"code_preview": code[:200]}, result, 0, False, retry_count)
            return result