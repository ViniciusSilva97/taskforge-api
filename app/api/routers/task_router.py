from collections.abc import Callable

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.database import get_db
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
from app.services.user_service import UserNotFoundError

router = APIRouter(prefix="/tasks", tags=["Tasks"])


@router.post("/", response_model=TaskResponse, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)) -> TaskResponse:
    try:
        return TaskService(db).create_task(payload)
    except UserNotFoundError as error:
        raise _http_exception(error) from error


@router.get("/", response_model=list[TaskResponse])
def list_tasks(db: Session = Depends(get_db)) -> list[TaskResponse]:
    return TaskService(db).list_tasks()


@router.get(
    "/users/{user_id}/notifications",
    response_model=list[NotificationResponse],
)
def list_user_notifications(
    user_id: int,
    db: Session = Depends(get_db),
) -> list[NotificationResponse]:
    try:
        return TaskService(db).list_notifications(user_id)
    except UserNotFoundError as error:
        raise _http_exception(error) from error


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(task_id: int, db: Session = Depends(get_db)) -> TaskResponse:
    try:
        return TaskService(db).get_task(task_id)
    except TaskNotFoundError as error:
        raise _http_exception(error) from error


@router.get("/{task_id}/history", response_model=list[TaskHistoryEntry])
def list_task_history(
    task_id: int,
    db: Session = Depends(get_db),
) -> list[TaskHistoryEntry]:
    try:
        return TaskService(db).list_history(task_id)
    except TaskNotFoundError as error:
        raise _http_exception(error) from error


@router.post("/{task_id}/start", response_model=TaskResponse)
def start_task(
    task_id: int,
    payload: TaskActionRequest,
    db: Session = Depends(get_db),
) -> TaskResponse:
    return _run_action(
        lambda: TaskService(db).start_task(task_id, payload.actor_id)
    )


@router.post("/{task_id}/submit", response_model=TaskResponse)
def submit_task(
    task_id: int,
    payload: TaskActionRequest,
    db: Session = Depends(get_db),
) -> TaskResponse:
    return _run_action(
        lambda: TaskService(db).submit_for_review(task_id, payload.actor_id)
    )


@router.post("/{task_id}/request-changes", response_model=TaskResponse)
def request_task_changes(
    task_id: int,
    payload: TaskChangesRequest,
    db: Session = Depends(get_db),
) -> TaskResponse:
    return _run_action(
        lambda: TaskService(db).request_changes(
            task_id=task_id,
            actor_id=payload.actor_id,
            comment=payload.comment,
        )
    )


@router.post("/{task_id}/approve", response_model=TaskResponse)
def approve_task(
    task_id: int,
    payload: TaskReviewRequest,
    db: Session = Depends(get_db),
) -> TaskResponse:
    return _run_action(
        lambda: TaskService(db).approve_task(
            task_id=task_id,
            actor_id=payload.actor_id,
            comment=payload.comment,
        )
    )


def _run_action(action: Callable[[], TaskResponse]) -> TaskResponse:
    try:
        return action()
    except (
        TaskNotFoundError,
        UserNotFoundError,
        TaskPermissionError,
        InvalidTaskTransitionError,
    ) as error:
        raise _http_exception(error) from error


def _http_exception(error: Exception) -> HTTPException:
    if isinstance(error, (TaskNotFoundError, UserNotFoundError)):
        return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(error))
    if isinstance(error, TaskPermissionError):
        return HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(error))
    return HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(error))
