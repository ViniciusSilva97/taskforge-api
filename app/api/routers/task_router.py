from fastapi import APIRouter, HTTPException, status

from app.schemas.task_schema import TaskCreate, TaskResponse
from app.services.task_service import TaskNotFoundError, TaskService

router = APIRouter(prefix="/tasks", tags=["Tasks"])
task_service = TaskService()


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task_data: TaskCreate) -> TaskResponse:
    return task_service.create_task(task_data)


@router.get("/", response_model=list[TaskResponse])
async def list_tasks() -> list[TaskResponse]:
    return task_service.list_tasks()


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int) -> TaskResponse:
    try:
        return task_service.get_task(task_id)
    except TaskNotFoundError as error:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        ) from error
