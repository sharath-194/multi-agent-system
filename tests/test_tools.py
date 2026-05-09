import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from tools.web_search import WebSearchTool
from tools.code_executor import CodeExecutorTool
from tools.tool_manager import ToolManager

# =========================================================================
# WEB SEARCH TOOL TESTS
# =========================================================================

def test_web_search_returns_results():
    tool = WebSearchTool()
    result = tool.run(query="machine learning", job_id="test_job_1")
    assert "results" in result
    assert len(result["results"]) > 0

def test_web_search_result_structure():
    tool = WebSearchTool()
    result = tool.run(query="python programming", job_id="test_job_2")
    for r in result["results"]:
        assert "title" in r
        assert "url" in r
        assert "relevance_score" in r

def test_web_search_malformed_input():
    tool = WebSearchTool()
    result = tool.run(query="", job_id="test_job_3")
    assert "error" in result

def test_web_search_none_input():
    tool = WebSearchTool()
    result = tool.run(query=None, job_id="test_job_4")
    assert "error" in result

def test_web_search_relevance_scores():
    tool = WebSearchTool()
    result = tool.run(query="test query", job_id="test_job_5")
    for r in result.get("results", []):
        assert 0.0 <= r["relevance_score"] <= 1.0

# =========================================================================
# CODE EXECUTOR TOOL TESTS
# =========================================================================

def test_code_executor_simple_code():
    tool = CodeExecutorTool()
    result = tool.run(code="print('hello world')", job_id="test_job_6")
    assert "stdout" in result
    assert "hello world" in result["stdout"]

def test_code_executor_returns_exit_code():
    tool = CodeExecutorTool()
    result = tool.run(code="x = 1 + 1", job_id="test_job_7")
    assert "exit_code" in result
    assert result["exit_code"] == 0

def test_code_executor_handles_error():
    tool = CodeExecutorTool()
    result = tool.run(code="raise ValueError('test error')", job_id="test_job_8")
    assert "stderr" in result
    assert result["exit_code"] != 0

def test_code_executor_malformed_input():
    tool = CodeExecutorTool()
    result = tool.run(code="", job_id="test_job_9")
    assert "error" in result

def test_code_executor_none_input():
    tool = CodeExecutorTool()
    result = tool.run(code=None, job_id="test_job_10")
    assert "error" in result

def test_code_executor_math():
    tool = CodeExecutorTool()
    result = tool.run(code="print(2 + 2)", job_id="test_job_11")
    assert "4" in result["stdout"]

# =========================================================================
# TOOL MANAGER TESTS
# =========================================================================

def test_tool_manager_init():
    manager = ToolManager()
    assert "web_search" in manager.tools
    assert "code_executor" in manager.tools
    assert "database_lookup" in manager.tools
    assert "self_reflection" in manager.tools

def test_tool_manager_get_available_tools():
    manager = ToolManager()
    tools = manager.get_available_tools()
    assert len(tools) == 4

def test_tool_manager_unknown_tool():
    manager = ToolManager()
    result = manager.run_tool("unknown_tool", job_id="test_job_12")
    assert "error" in result
    assert result["error"] == "tool_not_found"

def test_tool_manager_web_search():
    manager = ToolManager()
    result = manager.run_tool("web_search", job_id="test_job_13", query="test")
    assert "results" in result

def test_tool_manager_code_executor():
    manager = ToolManager()
    result = manager.run_tool("code_executor", job_id="test_job_14", code="print('test')")
    assert "stdout" in result