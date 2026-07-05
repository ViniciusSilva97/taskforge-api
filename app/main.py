from fastapi import FastAPI

from app.api.routers.task_router import router as task_router

app = FastAPI (
    title = "TaskForge API",
    vesion = "0.1.0",
    description = "API para gerenciamento de tarefas com fluxo de revisão"
)

app.include_router(task_router)

@app.get("/")
async def root():
    return {
        "message": "Welcome to TaskForge API",
        "status":"running",
    }
