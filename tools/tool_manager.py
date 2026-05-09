import time
from tools.web_search import WebSearchTool
from tools.code_executor import CodeExecutorTool
from tools.database_lookup import DatabaseLookupTool
from tools.self_reflection import SelfReflectionTool

class ToolManager:
    def __init__(self):
        self.tools = {
            "web_search": WebSearchTool(),
            "code_executor": CodeExecutorTool(),
            "database_lookup": DatabaseLookupTool(),
            "self_reflection": SelfReflectionTool()
        }
        self.max_retries = 2

    def run_tool(self, tool_name: str, job_id: str, **kwargs) -> dict:
        if tool_name not in self.tools:
            return {
                "error": "tool_not_found",
                "message": f"Tool {tool_name} does not exist",
                "available_tools": list(self.tools.keys())
            }

        tool = self.tools[tool_name]
        last_result = None

        for attempt in range(self.max_retries + 1):
            result = tool.run(job_id=job_id, retry_count=attempt, **kwargs)

            if "error" not in result:
                return result

            if attempt < self.max_retries:
                print(f"Tool {tool_name} failed attempt {attempt + 1}, retrying...")
                time.sleep(0.5)
                last_result = result
            else:
                last_result = result

        return last_result or {"error": "all_retries_failed", "tool": tool_name}

    def get_available_tools(self) -> list:
        return list(self.tools.keys())