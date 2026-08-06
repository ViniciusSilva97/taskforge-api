from collections.abc import Callable
from typing import TypeVar

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.dependencies.auth import get_current_user
from app.core.database import get_db
from app.core.enums import TaskRoleFilter, TaskStatus
from app.models.user import User
from app.schemas.task_schema import (
    NotificationPage,
    NotificationReadAllResponse,
    NotificationResponse,
    TaskChangesRequest,
    TaskCreate,
    TaskHistoryEntry,
    TaskPage,
    TaskResponse,
    TaskReviewRequest,
)
from app.services.task_service import (
    InvalidTaskTransitionError,
    NotificationNotFoundError,
    TaskNotFoundError,
    TaskPermissionError,
    TaskService,
)
from app.services.user_service import UserNotFoundError

router = APIRouter(prefix="/tasks", tags=["Tasks"])
ResponseT = TypeVar("ResponseT")


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


@router.get("/", response_model=TaskPage)
def list_tasks(
    status_filter: TaskStatus | None = Query(default=None, alias="status"),
    role: TaskRoleFilter = Query(default=TaskRoleFilter.ALL),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> TaskPage:
    return TaskService(db).list_tasks(
        current_user.id,
        status_filter=status_filter,
        role=role,
        limit=limit,
        offset=offset,
    )


@router.get("/notifications/me", response_model=NotificationPage)
def list_my_notifications(
    unread_only: bool = Query(default=False),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationPage:
    return TaskService(db).list_notifications(
        current_user.id,
        unread_only=unread_only,
        limit=limit,
        offset=offset,
    )


@router.patch(
    "/notifications/read-all",
    response_model=NotificationReadAllResponse,
)
def mark_all_notifications_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationReadAllResponse:
    return TaskService(db).mark_all_notifications_read(current_user.id)


@router.patch(
    "/notifications/{notification_id}/read",
    response_model=NotificationResponse,
)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationResponse:
    return _run_action(
        lambda: TaskService(db).mark_notification_read(
            notification_id,
            current_user.id,
        )
    )


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


def _run_action(action: Callable[[], ResponseT]) -> ResponseT:
    try:
        return action()
    except (
        TaskNotFoundError,
        NotificationNotFoundError,
        UserNotFoundError,
        TaskPermissionError,
        InvalidTaskTransitionError,
    ) as error:
        raise _http_exception(error) from error


def _http_exception(error: Exception) -> HTTPException:
    if isinstance(
        error,
        (TaskNotFoundError, NotificationNotFoundError, UserNotFoundError),
    ):
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
