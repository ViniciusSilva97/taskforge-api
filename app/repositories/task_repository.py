from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.enums import NotificationType, TaskEventType, TaskStatus
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

    def list(self) -> list[Task]:
        statement = select(Task).options(selectinload(Task.assignees)).order_by(Task.id)
        return list(self.session.scalars(statement))

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

    def list_notifications(self, user_id: int) -> list[Notification]:
        statement = (
            select(Notification)
            .where(Notification.user_id == user_id)
            .order_by(Notification.id)
        )
        return list(self.session.scalars(statement))
