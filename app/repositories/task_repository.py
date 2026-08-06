from __future__ import annotations

from sqlalchemy import func, or_, select, update
from sqlalchemy.orm import Session, selectinload

from app.core.enums import (
    NotificationType,
    TaskEventType,
    TaskRoleFilter,
    TaskStatus,
)
from app.models.task import Notification, Task, TaskHistory
from app.models.user import User


class TaskRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def create(
        self,
        *,
        title: str,
        description: str | None,
        requester: User,
        assignees: list[User],
    ) -> Task:
        task = Task(
            title=title,
            description=description,
            requester=requester,
            assignees=assignees,
            status=TaskStatus.ASSIGNED,
        )
        self.session.add(task)
        self.session.flush()
        return task

    def get(self, task_id: int) -> Task | None:
        statement = (
            select(Task)
            .where(Task.id == task_id)
            .options(selectinload(Task.assignees))
        )
        return self.session.scalar(statement)

    def list_for_user(
        self,
        user_id: int,
        *,
        status_filter: TaskStatus | None,
        role: TaskRoleFilter,
        limit: int,
        offset: int,
    ) -> tuple[list[Task], int]:
        requested = Task.requester_id == user_id
        assigned = Task.assignees.any(User.id == user_id)

        if role is TaskRoleFilter.REQUESTED:
            participant_filter = requested
        elif role is TaskRoleFilter.ASSIGNED:
            participant_filter = assigned
        else:
            participant_filter = or_(requested, assigned)

        filters = [participant_filter]
        if status_filter is not None:
            filters.append(Task.status == status_filter)

        total_statement = select(func.count(Task.id)).where(*filters)
        total = int(self.session.scalar(total_statement) or 0)

        statement = (
            select(Task)
            .where(*filters)
            .options(selectinload(Task.assignees))
            .order_by(Task.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement)), total

    def change_status(self, task: Task, status: TaskStatus) -> None:
        task.status = status
        self.session.flush()

    def add_history(
        self,
        *,
        task: Task,
        actor_id: int,
        event_type: TaskEventType,
        description: str,
    ) -> TaskHistory:
        event = TaskHistory(
            task_id=task.id,
            actor_id=actor_id,
            event_type=event_type,
            description=description,
        )
        self.session.add(event)
        self.session.flush()
        return event

    def add_notification(
        self,
        *,
        user_id: int,
        task: Task,
        notification_type: NotificationType,
        message: str,
    ) -> Notification:
        notification = Notification(
            user_id=user_id,
            task_id=task.id,
            type=notification_type,
            message=message,
        )
        self.session.add(notification)
        self.session.flush()
        return notification

    def list_history(self, task_id: int) -> list[TaskHistory]:
        statement = (
            select(TaskHistory)
            .where(TaskHistory.task_id == task_id)
            .order_by(TaskHistory.id)
        )
        return list(self.session.scalars(statement))

    def list_notifications(
        self,
        user_id: int,
        *,
        unread_only: bool,
        limit: int,
        offset: int,
    ) -> tuple[list[Notification], int]:
        filters = [Notification.user_id == user_id]
        if unread_only:
            filters.append(Notification.is_read.is_(False))

        total_statement = select(func.count(Notification.id)).where(*filters)
        total = int(self.session.scalar(total_statement) or 0)

        statement = (
            select(Notification)
            .where(*filters)
            .order_by(Notification.id.desc())
            .offset(offset)
            .limit(limit)
        )
        return list(self.session.scalars(statement)), total

    def get_notification_for_user(
        self,
        notification_id: int,
        user_id: int,
    ) -> Notification | None:
        statement = select(Notification).where(
            Notification.id == notification_id,
            Notification.user_id == user_id,
        )
        return self.session.scalar(statement)

    def mark_notification_read(self, notification: Notification) -> None:
        notification.is_read = True
        self.session.flush()

    def mark_all_notifications_read(self, user_id: int) -> int:
        result = self.session.execute(
            update(Notification)
            .where(
                Notification.user_id == user_id,
                Notification.is_read.is_(False),
            )
            .values(is_read=True)
        )
        return int(result.rowcount or 0)
