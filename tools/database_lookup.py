import time
import json
from agents.base_agent import BaseAgent
from database.connection import SessionLocal
from database.models import ToolLog

class DatabaseLookupTool:
    def __init__(self):
        self.tool_name = "database_lookup"
        self.agent = BaseAgent(agent_id="database_lookup_tool")

        self.sample_data = {
            "products": [
                {"id": 1, "name": "Laptop", "price": 999, "category": "electronics"},
                {"id": 2, "name": "Phone", "price": 699, "category": "electronics"},
                {"id": 3, "name": "Desk", "price": 299, "category": "furniture"}
            ],
            "users": [
                {"id": 1, "name": "Alice", "age": 30, "city": "New York"},
                {"id": 2, "name": "Bob", "age": 25, "city": "London"},
                {"id": 3, "name": "Charlie", "age": 35, "city": "Tokyo"}
            ],
            "sales": [
                {"id": 1, "product_id": 1, "quantity": 5, "revenue": 4995},
                {"id": 2, "product_id": 2, "quantity": 10, "revenue": 6990},
                {"id": 3, "product_id": 3, "quantity": 3, "revenue": 897}
            ]
        }

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

    def natural_language_to_sql(self, query: str, job_id: str) -> str:
        prompt = f"""Convert this natural language query to SQL.
Available tables: products(id, name, price, category), users(id, name, age, city), sales(id, product_id, quantity, revenue)

Query: {query}

Return ONLY the SQL query, nothing else."""
        return self.agent.call_llm(prompt, job_id)

    def run(self, query: str, job_id: str, retry_count: int = 0) -> dict:
        start = time.time()

        if not query or not isinstance(query, str):
            result = {"error": "malformed_input", "data": [], "sql": ""}
            self.log_tool(job_id, {"query": query}, result, 0, False, retry_count)
            return result

        try:
            sql = self.natural_language_to_sql(query, job_id)
            
            results = []
            query_lower = query.lower()
            
            if "product" in query_lower:
                results = self.sample_data["products"]
            elif "user" in query_lower or "customer" in query_lower:
                results = self.sample_data["users"]
            elif "sale" in query_lower or "revenue" in query_lower:
                results = self.sample_data["sales"]
            else:
                results = self.sample_data["products"]

            latency = (time.time() - start) * 1000
            output = {"data": results, "sql": sql, "row_count": len(results)}
            self.log_tool(job_id, {"query": query}, output, latency, True, retry_count)
            return output

        except Exception as e:
            result = {"error": str(e), "data": [], "sql": ""}
            self.log_tool(job_id, {"query": query}, result, 0, False, retry_count)
            return result