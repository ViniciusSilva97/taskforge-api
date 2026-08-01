from datetime import UTC, datetime

from app.schemas.task_schema import (
    NotificationResponse,
    NotificationType,
    TaskCreate,
    TaskEventType,
    TaskHistoryEntry,
    TaskResponse,
    TaskStatus,
)


class TaskNotFoundError(LookupError):
    """Raised when a task cannot be found by its identifier."""


class TaskPermissionError(PermissionError):
    """Raised when a user is not allowed to execute a task action."""


class InvalidTaskTransitionError(ValueError):
    """Raised when the requested workflow transition is not allowed."""


class TaskService:
    """Applies task workflow rules using temporary in-memory storage."""

    def __init__(self) -> None:
        self.reset()

    def reset(self) -> None:
        self._tasks: dict[int, TaskResponse] = {}
        self._history: dict[int, list[TaskHistoryEntry]] = {}
        self._notifications: list[NotificationResponse] = []
        self._next_task_id = 1
        self._next_history_id = 1
        self._next_notification_id = 1

    def create_task(self, task_data: TaskCreate) -> TaskResponse:
        task = TaskResponse(
            id=self._next_task_id,
            title=task_data.title,
            description=task_data.description,
            requester_id=task_data.requester_id,
            assignee_ids=task_data.assignee_ids,
            status=TaskStatus.ASSIGNED,
        )
        self._tasks[task.id] = task
        self._history[task.id] = []
        self._next_task_id += 1

        self._record_history(
            task=task,
            actor_id=task.requester_id,
            event_type=TaskEventType.TASK_CREATED,
            description="Tarefa criada e atribuída aos destinatários.",
        )
        self._notify_users(
            user_ids=task.assignee_ids,
            task=task,
            notification_type=NotificationType.TASK_ASSIGNED,
            message=f"Você recebeu a tarefa: {task.title}",
        )
        return task

    def list_tasks(self) -> list[TaskResponse]:
        return list(self._tasks.values())

    def get_task(self, task_id: int) -> TaskResponse:
        try:
            return self._tasks[task_id]
        except KeyError as error:
            raise TaskNotFoundError(f"Tarefa {task_id} não encontrada.") from error

    def start_task(self, task_id: int, actor_id: int) -> TaskResponse:
        task = self.get_task(task_id)
        self._require_assignee(task, actor_id)
        self._require_status(
            task,
            {TaskStatus.ASSIGNED, TaskStatus.CHANGES_REQUESTED},
            "iniciar",
        )

        updated = self._change_status(task, TaskStatus.IN_PROGRESS)
        self._record_history(
            task=updated,
            actor_id=actor_id,
            event_type=TaskEventType.TASK_STARTED,
            description="Execução da tarefa iniciada.",
        )
        return updated

    def submit_for_review(self, task_id: int, actor_id: int) -> TaskResponse:
        task = self.get_task(task_id)
        self._require_assignee(task, actor_id)
        self._require_status(task, {TaskStatus.IN_PROGRESS}, "enviar para revisão")

        updated = self._change_status(task, TaskStatus.IN_REVIEW)
        self._record_history(
            task=updated,
            actor_id=actor_id,
            event_type=TaskEventType.TASK_SUBMITTED,
            description="Tarefa entregue para revisão.",
        )
        self._notify_users(
            user_ids=[updated.requester_id],
            task=updated,
            notification_type=NotificationType.TASK_SUBMITTED,
            message=f"A tarefa '{updated.title}' foi entregue para revisão.",
        )
        return updated

    def request_changes(
        self,
        task_id: int,
        actor_id: int,
        comment: str,
    ) -> TaskResponse:
        task = self.get_task(task_id)
        self._require_requester(task, actor_id)
        self._require_status(task, {TaskStatus.IN_REVIEW}, "solicitar ajustes")

        updated = self._change_status(task, TaskStatus.CHANGES_REQUESTED)
        self._record_history(
            task=updated,
            actor_id=actor_id,
            event_type=TaskEventType.CHANGES_REQUESTED,
            description=f"Ajustes solicitados: {comment}",
        )
        self._notify_users(
            user_ids=updated.assignee_ids,
            task=updated,
            notification_type=NotificationType.CHANGES_REQUESTED,
            message=f"Foram solicitados ajustes na tarefa '{updated.title}': {comment}",
        )
        return updated

    def approve_task(
        self,
        task_id: int,
        actor_id: int,
        comment: str | None = None,
    ) -> TaskResponse:
        task = self.get_task(task_id)
        self._require_requester(task, actor_id)
        self._require_status(task, {TaskStatus.IN_REVIEW}, "aprovar")

        updated = self._change_status(task, TaskStatus.APPROVED)
        description = "Tarefa revisada e aprovada."
        if comment:
            description = f"{description} Observação: {comment.strip()}"

        self._record_history(
            task=updated,
            actor_id=actor_id,
            event_type=TaskEventType.TASK_APPROVED,
            description=description,
        )
        self._notify_users(
            user_ids=updated.assignee_ids,
            task=updated,
            notification_type=NotificationType.TASK_APPROVED,
            message=f"A tarefa '{updated.title}' foi aprovada.",
        )
        return updated

    def list_history(self, task_id: int) -> list[TaskHistoryEntry]:
        self.get_task(task_id)
        return list(self._history[task_id])

    def list_notifications(self, user_id: int) -> list[NotificationResponse]:
        return [
            notification
            for notification in self._notifications
            if notification.user_id == user_id
        ]

    def _change_status(
        self,
        task: TaskResponse,
        new_status: TaskStatus,
    ) -> TaskResponse:
        updated = task.model_copy(update={"status": new_status})
        self._tasks[task.id] = updated
        return updated

    def _require_assignee(self, task: TaskResponse, actor_id: int) -> None:
        if actor_id not in task.assignee_ids:
            raise TaskPermissionError(
                "Somente um destinatário da tarefa pode executar esta ação."
            )

    def _require_requester(self, task: TaskResponse, actor_id: int) -> None:
        if actor_id != task.requester_id:
            raise TaskPermissionError(
                "Somente quem solicitou a tarefa pode executar esta ação."
            )

    def _require_status(
        self,
        task: TaskResponse,
        allowed_statuses: set[TaskStatus],
        action: str,
    ) -> None:
        if task.status not in allowed_statuses:
            allowed = ", ".join(sorted(status.value for status in allowed_statuses))
            raise InvalidTaskTransitionError(
                f"Não é possível {action} uma tarefa no status {task.status.value}. "
                f"Status permitidos: {allowed}."
            )

    def _record_history(
        self,
        task: TaskResponse,
        actor_id: int,
        event_type: TaskEventType,
        description: str,
    ) -> None:
        event = TaskHistoryEntry(
            id=self._next_history_id,
            task_id=task.id,
            actor_id=actor_id,
            event_type=event_type,
            description=description,
            created_at=datetime.now(UTC),
        )
        self._history[task.id].append(event)
        self._next_history_id += 1

    def _notify_users(
        self,
        user_ids: list[int],
        task: TaskResponse,
        notification_type: NotificationType,
        message: str,
    ) -> None:
        for user_id in user_ids:
            notification = NotificationResponse(
                id=self._next_notification_id,
                user_id=user_id,
                task_id=task.id,
                type=notification_type,
                message=message,
                created_at=datetime.now(UTC),
            )
            self._notifications.append(notification)
            self._next_notification_id += 1
