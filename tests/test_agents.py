import pytest
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from agents.context_manager import ContextManager
from agents.decomposition_agent import DecompositionAgent
from agents.retrieval_agent import RetrievalAgent
from agents.critique_agent import CritiqueAgent
from agents.synthesis_agent import SynthesisAgent

# =========================================================================
# CONTEXT MANAGER TESTS
# =========================================================================

def test_context_manager_init():
    cm = ContextManager(max_budget=4000)
    assert cm.max_budget == 4000
    assert cm.context == {}

def test_context_manager_update_and_get():
    cm = ContextManager()
    cm.update("query", "test query")
    assert cm.get("query") == "test query"

def test_context_manager_budget_check():
    cm = ContextManager(max_budget=4000)
    cm.update("query", "short query")
    assert cm.check_budget() == True

def test_context_manager_remaining_budget():
    cm = ContextManager(max_budget=4000)
    remaining = cm.get_remaining_budget()
    assert remaining > 0
    assert remaining <= 4000

def test_context_manager_get_all():
    cm = ContextManager()
    cm.update("key1", "value1")
    cm.update("key2", "value2")
    all_context = cm.get_all()
    assert "key1" in all_context
    assert "key2" in all_context

def test_context_manager_summarize():
    cm = ContextManager()
    cm.update("conversation_history", ["msg1", "msg2", "msg3", "msg4", "msg5"])
    cm.summarize_old_context()
    history = cm.get("conversation_history")
    assert len(history) <= 4

# =========================================================================
# DECOMPOSITION AGENT TESTS
# =========================================================================

def test_decomposition_agent_init():
    agent = DecompositionAgent()
    assert agent.agent_id == "decomposition_agent"
    assert agent.max_context_budget == 3000

def test_decomposition_agent_has_run_method():
    agent = DecompositionAgent()
    assert hasattr(agent, "run")
    assert callable(agent.run)

# =========================================================================
# RETRIEVAL AGENT TESTS
# =========================================================================

def test_retrieval_agent_init():
    agent = RetrievalAgent()
    assert agent.agent_id == "retrieval_agent"
    assert agent.max_context_budget == 3000

def test_retrieval_agent_has_run_method():
    agent = RetrievalAgent()
    assert hasattr(agent, "run")
    assert callable(agent.run)

# =========================================================================
# CRITIQUE AGENT TESTS
# =========================================================================

def test_critique_agent_init():
    agent = CritiqueAgent()
    assert agent.agent_id == "critique_agent"
    assert agent.max_context_budget == 3000

def test_critique_agent_has_run_method():
    agent = CritiqueAgent()
    assert hasattr(agent, "run")

# =========================================================================
# SYNTHESIS AGENT TESTS
# =========================================================================

def test_synthesis_agent_init():
    agent = SynthesisAgent()
    assert agent.agent_id == "synthesis_agent"
    assert agent.max_context_budget == 4000

def test_synthesis_agent_has_run_method():
    agent = SynthesisAgent()
    assert hasattr(agent, "run")

# =========================================================================
# BASE AGENT TESTS
# =========================================================================

def test_base_agent_hash_data():
    from agents.base_agent import BaseAgent
    agent = BaseAgent(agent_id="test_agent")
    hash1 = agent.hash_data({"key": "value"})
    hash2 = agent.hash_data({"key": "value"})
    assert hash1 == hash2
    assert len(hash1) == 32

def test_base_agent_count_tokens():
    from agents.base_agent import BaseAgent
    agent = BaseAgent(agent_id="test_agent")
    tokens = agent.count_tokens("hello world this is a test")
    assert tokens > 0

def test_base_agent_run_raises():
    from agents.base_agent import BaseAgent
    agent = BaseAgent(agent_id="test_agent")
    with pytest.raises(NotImplementedError):
        agent.run({})