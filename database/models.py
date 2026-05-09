from sqlalchemy import Column, String, Integer, Float, DateTime, Text, JSON, Boolean
from sqlalchemy.sql import func
from database.connection import Base
import uuid

def generate_uuid():
    return str(uuid.uuid4())

class Job(Base):
    __tablename__ = "jobs"
    id = Column(String, primary_key=True, default=generate_uuid)
    query = Column(Text, nullable=False)
    status = Column(String, default="pending")
    result = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

class AgentLog(Base):
    __tablename__ = "agent_logs"
    id = Column(String, primary_key=True, default=generate_uuid)
    job_id = Column(String, nullable=False)
    agent_id = Column(String, nullable=False)
    event_type = Column(String, nullable=False)
    input_hash = Column(String, nullable=True)
    output_hash = Column(String, nullable=True)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    latency_ms = Column(Float, nullable=True)
    token_count = Column(Integer, nullable=True)
    policy_violation = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ToolLog(Base):
    __tablename__ = "tool_logs"
    id = Column(String, primary_key=True, default=generate_uuid)
    job_id = Column(String, nullable=False)
    tool_name = Column(String, nullable=False)
    input_data = Column(JSON, nullable=True)
    output_data = Column(JSON, nullable=True)
    latency_ms = Column(Float, nullable=True)
    success = Column(Boolean, default=True)
    retry_count = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class EvalRun(Base):
    __tablename__ = "eval_runs"
    id = Column(String, primary_key=True, default=generate_uuid)
    test_case_id = Column(String, nullable=False)
    category = Column(String, nullable=False)
    query = Column(Text, nullable=False)
    expected_answer = Column(Text, nullable=True)
    actual_answer = Column(Text, nullable=True)
    correctness_score = Column(Float, nullable=True)
    citation_score = Column(Float, nullable=True)
    contradiction_score = Column(Float, nullable=True)
    tool_efficiency_score = Column(Float, nullable=True)
    budget_compliance_score = Column(Float, nullable=True)
    critique_agreement_score = Column(Float, nullable=True)
    total_score = Column(Float, nullable=True)
    justification = Column(JSON, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class PromptRewrite(Base):
    __tablename__ = "prompt_rewrites"
    id = Column(String, primary_key=True, default=generate_uuid)
    agent_id = Column(String, nullable=False)
    original_prompt = Column(Text, nullable=False)
    rewritten_prompt = Column(Text, nullable=False)
    diff = Column(Text, nullable=False)
    justification = Column(Text, nullable=False)
    status = Column(String, default="pending")
    performance_delta = Column(Float, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    approved_at = Column(DateTime(timezone=True), nullable=True)