from fastapi import FastAPI

from app.api.routers.task_router import router as task_router
from app.api.routers.user_router import router as user_router

app = FastAPI(
    title="TaskForge API",
    version="0.2.0",
    description="API de tarefas com usuários, workflow, histórico e persistência.",
)

app.include_router(user_router)
app.include_router(task_router)


@app.get("/", tags=["Health"])
def root() -> dict[str, str]:
    return {
        "message": "Welcome to TaskForge API",
        "status": "running",
        "version": app.version,
    }
