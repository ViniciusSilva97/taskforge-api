from collections.abc import Callable

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.task_schema import (
    NotificationResponse,
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
def create_task(
    payload: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    try:
        return TaskService(db).create_task(payload, current_user.id)
    except UserNotFoundError as error:
        raise _http_exception(error) from error


@router.get("/", response_model=list[TaskResponse])
def list_tasks(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TaskResponse]:
    return TaskService(db).list_tasks(current_user.id)


@router.get("/notifications/me", response_model=list[NotificationResponse])
def list_my_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[NotificationResponse]:
    return TaskService(db).list_notifications(current_user.id)


@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    return _run_action(
        lambda: TaskService(db).get_task(task_id, current_user.id)
    )


@router.get("/{task_id}/history", response_model=list[TaskHistoryEntry])
def list_task_history(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[TaskHistoryEntry]:
    try:
        return TaskService(db).list_history(task_id, current_user.id)
    except (TaskNotFoundError, TaskPermissionError) as error:
        raise _http_exception(error) from error


@router.post("/{task_id}/start", response_model=TaskResponse)
def start_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    return _run_action(
        lambda: TaskService(db).start_task(task_id, current_user.id)
    )


@router.post("/{task_id}/submit", response_model=TaskResponse)
def submit_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    return _run_action(
        lambda: TaskService(db).submit_for_review(task_id, current_user.id)
    )


@router.post("/{task_id}/request-changes", response_model=TaskResponse)
def request_task_changes(
    task_id: int,
    payload: TaskChangesRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    return _run_action(
        lambda: TaskService(db).request_changes(
            task_id=task_id,
            actor_id=current_user.id,
            comment=payload.comment,
        )
    )


@router.post("/{task_id}/approve", response_model=TaskResponse)
def approve_task(
    task_id: int,
    payload: TaskReviewRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskResponse:
    return _run_action(
        lambda: TaskService(db).approve_task(
            task_id=task_id,
            actor_id=current_user.id,
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
