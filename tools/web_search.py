import time
import hashlib
from database.connection import SessionLocal
from database.models import ToolLog

class WebSearchTool:
    def __init__(self):
        self.tool_name = "web_search"
        self.timeout_seconds = 5

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

    def run(self, query: str, job_id: str, retry_count: int = 0) -> dict:
        start = time.time()
        
        if not query or not isinstance(query, str):
            result = self.on_malformed_input(query)
            self.log_tool(job_id, {"query": query}, result, 0, False, retry_count)
            return result

        try:
            time.sleep(0.1)
            
            results = [
                {
                    "title": f"Result 1 for: {query}",
                    "url": f"https://example.com/result1?q={query.replace(' ', '+')}",
                    "snippet": f"Comprehensive information about {query} from reliable sources.",
                    "relevance_score": 0.95
                },
                {
                    "title": f"Result 2 for: {query}",
                    "url": f"https://example.com/result2?q={query.replace(' ', '+')}",
                    "snippet": f"Additional details and analysis regarding {query}.",
                    "relevance_score": 0.87
                },
                {
                    "title": f"Result 3 for: {query}",
                    "url": f"https://example.com/result3?q={query.replace(' ', '+')}",
                    "snippet": f"Expert perspectives on {query} with citations.",
                    "relevance_score": 0.82
                }
            ]

            latency = (time.time() - start) * 1000
            output = {"results": results, "query": query, "total": len(results)}
            self.log_tool(job_id, {"query": query}, output, latency, True, retry_count)
            return output

        except TimeoutError:
            return self.on_timeout(query, job_id, retry_count)
        except Exception as e:
            return self.on_error(str(e), query, job_id, retry_count)

    def on_timeout(self, query, job_id, retry_count):
        result = {"error": "timeout", "results": [], "query": query}
        self.log_tool(job_id, {"query": query}, result, self.timeout_seconds * 1000, False, retry_count)
        return result

    def on_malformed_input(self, query):
        return {"error": "malformed_input", "results": [], "query": str(query)}

    def on_error(self, error, query, job_id, retry_count):
        result = {"error": error, "results": [], "query": query}
        self.log_tool(job_id, {"query": query}, result, 0, False, retry_count)
        return result