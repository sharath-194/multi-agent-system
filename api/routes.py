import uuid
import json
import asyncio
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database.connection import get_db
from database.models import Job, AgentLog, ToolLog, EvalRun, PromptRewrite
from agents.orchestrator import OrchestratorAgent
from evaluation.eval_runner import EvalRunner
from evaluation.meta_agent import MetaAgent

router = APIRouter(prefix="/api")

# Request models
class QueryRequest(BaseModel):
    query: str

class ApprovalRequest(BaseModel):
    approved: bool
    reason: Optional[str] = None

# Endpoint 1: Submit query with streaming SSE response
@router.post("/query")
async def submit_query(request: QueryRequest, db: Session = Depends(get_db)):
    job_id = str(uuid.uuid4())

    job = Job(id=job_id, query=request.query, status="pending")
    db.add(job)
    db.commit()

    async def generate():
        try:
            yield f"data: {json.dumps({'event': 'job_started', 'job_id': job_id, 'agent': 'orchestrator'})}\n\n"
            await asyncio.sleep(0.1)

            yield f"data: {json.dumps({'event': 'agent_start', 'agent': 'decomposition_agent', 'job_id': job_id, 'context_budget_remaining': 8000})}\n\n"
            await asyncio.sleep(0.1)

            orchestrator = OrchestratorAgent()
            context = {"job_id": job_id, "query": request.query}

            yield f"data: {json.dumps({'event': 'processing', 'agent': 'orchestrator', 'message': 'Running multi-agent pipeline...'})}\n\n"
            await asyncio.sleep(0.1)

            loop = asyncio.get_event_loop()
            result_context = await loop.run_in_executor(None, orchestrator.run, context)

            synthesis = result_context.get("synthesis", {})
            final_answer = synthesis.get("final_answer", str(result_context))

            job.status = "completed"
            job.result = {
                "final_answer": final_answer,
                "synthesis": synthesis,
                "agents_used": result_context.get("completed_agents", [])
            }
            db.commit()

            yield f"data: {json.dumps({'event': 'agent_complete', 'agent': 'synthesis_agent', 'job_id': job_id})}\n\n"
            yield f"data: {json.dumps({'event': 'job_complete', 'job_id': job_id, 'final_answer': final_answer[:500]})}\n\n"
            yield f"data: {json.dumps({'event': 'done'})}\n\n"

        except Exception as e:
            job.status = "failed"
            db.commit()
            yield f"data: {json.dumps({'event': 'error', 'job_id': job_id, 'error': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no"
        }
    )

# Endpoint 2: Get full execution trace for a job
@router.get("/job/{job_id}/trace")
async def get_job_trace(job_id: str, db: Session = Depends(get_db)):
    job = db.query(Job).filter(Job.id == job_id).first()
    if not job:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "JOB_NOT_FOUND",
                "message": f"Job {job_id} not found",
                "job_id": job_id
            }
        )

    agent_logs = db.query(AgentLog).filter(
        AgentLog.job_id == job_id
    ).order_by(AgentLog.created_at).all()

    tool_logs = db.query(ToolLog).filter(
        ToolLog.job_id == job_id
    ).order_by(ToolLog.created_at).all()

    trace = []
    for log in agent_logs:
        trace.append({
            "type": "agent_action",
            "agent_id": log.agent_id,
            "event_type": log.event_type,
            "input_data": log.input_data,
            "output_data": log.output_data,
            "latency_ms": log.latency_ms,
            "token_count": log.token_count,
            "policy_violation": log.policy_violation,
            "timestamp": str(log.created_at)
        })

    for log in tool_logs:
        trace.append({
            "type": "tool_call",
            "tool_name": log.tool_name,
            "input_data": log.input_data,
            "output_data": log.output_data,
            "latency_ms": log.latency_ms,
            "success": log.success,
            "retry_count": log.retry_count,
            "timestamp": str(log.created_at)
        })

    trace.sort(key=lambda x: x.get("timestamp", ""))

    return {
        "job_id": job_id,
        "query": job.query,
        "status": job.status,
        "result": job.result,
        "created_at": str(job.created_at),
        "execution_trace": trace,
        "total_agent_actions": len(agent_logs),
        "total_tool_calls": len(tool_logs)
    }

# Endpoint 3: Get latest eval run summary
@router.get("/eval/latest")
async def get_latest_eval(db: Session = Depends(get_db)):
    eval_runs = db.query(EvalRun).order_by(
        EvalRun.created_at.desc()
    ).limit(15).all()

    if not eval_runs:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "NO_EVAL_RUNS",
                "message": "No evaluation runs found. Run /api/eval/run first.",
                "job_id": None
            }
        )

    by_category = {}
    by_dimension = {
        "correctness": [],
        "citation_accuracy": [],
        "contradiction_resolution": [],
        "tool_efficiency": [],
        "budget_compliance": [],
        "critique_agreement": []
    }

    for run in eval_runs:
        cat = run.category
        if cat not in by_category:
            by_category[cat] = []
        by_category[cat].append(run.total_score or 0)

        if run.correctness_score: by_dimension["correctness"].append(run.correctness_score)
        if run.citation_score: by_dimension["citation_accuracy"].append(run.citation_score)
        if run.contradiction_score: by_dimension["contradiction_resolution"].append(run.contradiction_score)
        if run.tool_efficiency_score: by_dimension["tool_efficiency"].append(run.tool_efficiency_score)
        if run.budget_compliance_score: by_dimension["budget_compliance"].append(run.budget_compliance_score)
        if run.critique_agreement_score: by_dimension["critique_agreement"].append(run.critique_agreement_score)

    category_summary = {
        cat: round(sum(scores)/len(scores), 3)
        for cat, scores in by_category.items() if scores
    }

    dimension_summary = {
        dim: round(sum(scores)/len(scores), 3)
        for dim, scores in by_dimension.items() if scores
    }

    all_scores = [run.total_score or 0 for run in eval_runs]
    overall = round(sum(all_scores)/len(all_scores), 3) if all_scores else 0

    return {
        "total_runs": len(eval_runs),
        "overall_average": overall,
        "by_category": category_summary,
        "by_dimension": dimension_summary,
        "runs": [
            {
                "test_case_id": r.test_case_id,
                "category": r.category,
                "query": r.query,
                "total_score": r.total_score,
                "timestamp": str(r.created_at)
            }
            for r in eval_runs
        ]
    }

# Endpoint 4: Approve or reject prompt rewrite
@router.post("/prompt-rewrite/{rewrite_id}/approve")
async def approve_rewrite(
    rewrite_id: str,
    request: ApprovalRequest,
    db: Session = Depends(get_db)
):
    rewrite = db.query(PromptRewrite).filter(
        PromptRewrite.id == rewrite_id
    ).first()

    if not rewrite:
        raise HTTPException(
            status_code=404,
            detail={
                "error_code": "REWRITE_NOT_FOUND",
                "message": f"Prompt rewrite {rewrite_id} not found",
                "job_id": None
            }
        )

    if request.approved:
        rewrite.status = "approved"
        message = "Prompt rewrite approved. Re-run eval to measure improvement."
    else:
        rewrite.status = "rejected"
        message = "Prompt rewrite rejected."

    db.commit()

    return {
        "rewrite_id": rewrite_id,
        "status": rewrite.status,
        "agent_id": rewrite.agent_id,
        "message": message,
        "reason": request.reason
    }

# Endpoint 5: Trigger re-eval on failed cases
@router.post("/eval/rerun-failed")
async def rerun_failed_eval(db: Session = Depends(get_db)):
    failed_runs = db.query(EvalRun).filter(
        EvalRun.total_score < 0.5
    ).all()

    if not failed_runs:
        return {
            "message": "No failed test cases found",
            "rerun_count": 0
        }

    failed_ids = list(set([r.test_case_id for r in failed_runs]))

    runner = EvalRunner()
    results = runner.run_failed_tests(failed_ids)

    return {
        "message": f"Re-ran {len(failed_ids)} failed test cases",
        "rerun_count": len(failed_ids),
        "results": results
    }

# Bonus: Trigger full eval run
@router.post("/eval/run")
async def run_full_eval():
    runner = EvalRunner()
    results = runner.run_all_tests()

    meta = MetaAgent()
    improvement = meta.run_improvement_loop(results)

    return {
        "eval_results": results,
        "improvement_suggestions": improvement
    }

# Bonus: Get pending rewrites
@router.get("/prompt-rewrites/pending")
async def get_pending_rewrites(db: Session = Depends(get_db)):
    rewrites = db.query(PromptRewrite).filter(
        PromptRewrite.status == "pending"
    ).all()

    return {
        "pending_count": len(rewrites),
        "rewrites": [
            {
                "id": r.id,
                "agent_id": r.agent_id,
                "diff": r.diff,
                "justification": r.justification,
                "created_at": str(r.created_at)
            }
            for r in rewrites
        ]
    }