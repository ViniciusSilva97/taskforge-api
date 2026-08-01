from fastapi import APIRouter, HTTPException, status

from app.schemas.task_schema import (
    NotificationResponse,
    TaskActionRequest,
    TaskChangesRequest,
    TaskCreate,
    TaskHistoryEntry,
    TaskResponse,
    TaskReviewRequest,
)
from app.services.task_service import (
    InvalidTaskTransitionError,
    TaskNotFoundError,
    TaskPermissionError,
    TaskService,
)

router = APIRouter(prefix="/tasks", tags=["Tasks"])
task_service = TaskService()


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
async def create_task(task_data: TaskCreate) -> TaskResponse:
    return task_service.create_task(task_data)


@router.get("/", response_model=list[TaskResponse])
async def list_tasks() -> list[TaskResponse]:
    return task_service.list_tasks()


@router.get(
    "/users/{user_id}/notifications",
    response_model=list[NotificationResponse],
)
async def list_user_notifications(user_id: int) -> list[NotificationResponse]:
    return task_service.list_notifications(user_id)


@router.get("/{task_id}", response_model=TaskResponse)
async def get_task(task_id: int) -> TaskResponse:
    try:
        return task_service.get_task(task_id)
    except TaskNotFoundError as error:
        raise _http_exception(error) from error


@router.get("/{task_id}/history", response_model=list[TaskHistoryEntry])
async def list_task_history(task_id: int) -> list[TaskHistoryEntry]:
    try:
        return task_service.list_history(task_id)
    except TaskNotFoundError as error:
        raise _http_exception(error) from error


@router.post("/{task_id}/start", response_model=TaskResponse)
async def start_task(task_id: int, payload: TaskActionRequest) -> TaskResponse:
    try:
        return task_service.start_task(task_id, payload.actor_id)
    except (TaskNotFoundError, TaskPermissionError, InvalidTaskTransitionError) as error:
        raise _http_exception(error) from error


@router.post("/{task_id}/submit", response_model=TaskResponse)
async def submit_task(task_id: int, payload: TaskActionRequest) -> TaskResponse:
    try:
        return task_service.submit_for_review(task_id, payload.actor_id)
    except (TaskNotFoundError, TaskPermissionError, InvalidTaskTransitionError) as error:
        raise _http_exception(error) from error


@router.post("/{task_id}/request-changes", response_model=TaskResponse)
async def request_task_changes(
    task_id: int,
    payload: TaskChangesRequest,
) -> TaskResponse:
    try:
        return task_service.request_changes(
            task_id=task_id,
            actor_id=payload.actor_id,
            comment=payload.comment,
        )
    except (TaskNotFoundError, TaskPermissionError, InvalidTaskTransitionError) as error:
        raise _http_exception(error) from error


@router.post("/{task_id}/approve", response_model=TaskResponse)
async def approve_task(
    task_id: int,
    payload: TaskReviewRequest,
) -> TaskResponse:
    try:
        return task_service.approve_task(
            task_id=task_id,
            actor_id=payload.actor_id,
            comment=payload.comment,
        )
    except (TaskNotFoundError, TaskPermissionError, InvalidTaskTransitionError) as error:
        raise _http_exception(error) from error


def _http_exception(error: Exception) -> HTTPException:
    if isinstance(error, TaskNotFoundError):
        return HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(error),
        )
    if isinstance(error, TaskPermissionError):
        return HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=str(error),
        )
    return HTTPException(
        status_code=status.HTTP_409_CONFLICT,
        detail=str(error),
    )
