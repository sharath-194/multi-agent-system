from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import router
from database.connection import init_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Multi-Agent LLM Orchestration System",
    description="A production-grade multi-agent system with self-improving evaluation loop",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("Starting up...")
    try:
        init_db()
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {e}")

app.include_router(router)

@app.get("/")
async def root():
    return {
        "message": "Multi-Agent LLM Orchestration System",
        "version": "1.0.0",
        "status": "running",
        "endpoints": [
            "/api/query",
            "/api/job/{job_id}/trace",
            "/api/eval/latest",
            "/api/prompt-rewrite/{rewrite_id}/approve",
            "/api/eval/rerun-failed"
        ]
    }

@app.get("/health")
async def health():
    return {"status": "healthy"}