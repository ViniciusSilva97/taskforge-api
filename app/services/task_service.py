from sqlalchemy.orm import Session

from app.core.enums import NotificationType, TaskEventType, TaskStatus
from app.models.task import Task
from app.models.user import User
from app.repositories.task_repository import TaskRepository
from app.repositories.user_repository import UserRepository
from app.schemas.task_schema import (
    NotificationResponse,
    TaskCreate,
    TaskHistoryEntry,
    TaskResponse,
)
from app.services.user_service import UserNotFoundError


class TaskNotFoundError(LookupError):
    pass


class TaskPermissionError(PermissionError):
    pass


class InvalidTaskTransitionError(ValueError):
    pass


class TaskService:
    def __init__(self, session: Session) -> None:
        self.session = session
        self.tasks = TaskRepository(session)
        self.users = UserRepository(session)

    def create_task(self, task_data: TaskCreate) -> TaskResponse:
        requester = self._get_user(task_data.requester_id)
        assignees = [self._get_user(user_id) for user_id in task_data.assignee_ids]

        task = self.tasks.create(
            title=task_data.title,
            description=task_data.description,
            requester=requester,
            assignees=assignees,
        )
        self._record_history(
            task=task,
            actor_id=requester.id,
            event_type=TaskEventType.TASK_CREATED,
            description="Tarefa criada e atribuída aos destinatários.",
        )
        self._notify_users(
            user_ids=[user.id for user in assignees],
            task=task,
            notification_type=NotificationType.TASK_ASSIGNED,
            message=f"Você recebeu a tarefa: {task.title}",
        )
        self.session.commit()
        return self._to_response(task)

    def list_tasks(self) -> list[TaskResponse]:
        return [self._to_response(task) for task in self.tasks.list()]

    def get_task(self, task_id: int) -> TaskResponse:
        return self._to_response(self._get_task(task_id))

    def start_task(self, task_id: int, actor_id: int) -> TaskResponse:
        task = self._get_task(task_id)
        self._require_assignee(task, actor_id)
        self._require_status(
            task,
            {TaskStatus.ASSIGNED, TaskStatus.CHANGES_REQUESTED},
            "iniciar",
        )
        self.tasks.change_status(task, TaskStatus.IN_PROGRESS)
        self._record_history(
            task=task,
            actor_id=actor_id,
            event_type=TaskEventType.TASK_STARTED,
            description="Execução da tarefa iniciada.",
        )
        self.session.commit()
        return self._to_response(task)

    def submit_for_review(self, task_id: int, actor_id: int) -> TaskResponse:
        task = self._get_task(task_id)
        self._require_assignee(task, actor_id)
        self._require_status(task, {TaskStatus.IN_PROGRESS}, "enviar para revisão")
        self.tasks.change_status(task, TaskStatus.IN_REVIEW)
        self._record_history(
            task=task,
            actor_id=actor_id,
            event_type=TaskEventType.TASK_SUBMITTED,
            description="Tarefa entregue para revisão.",
        )
        self._notify_users(
            user_ids=[task.requester_id],
            task=task,
            notification_type=NotificationType.TASK_SUBMITTED,
            message=f"A tarefa '{task.title}' foi entregue para revisão.",
        )
        self.session.commit()
        return self._to_response(task)

    def request_changes(
        self,
        task_id: int,
        actor_id: int,
        comment: str,
    ) -> TaskResponse:
        task = self._get_task(task_id)
        self._require_requester(task, actor_id)
        self._require_status(task, {TaskStatus.IN_REVIEW}, "solicitar ajustes")
        self.tasks.change_status(task, TaskStatus.CHANGES_REQUESTED)
        self._record_history(
            task=task,
            actor_id=actor_id,
            event_type=TaskEventType.CHANGES_REQUESTED,
            description=f"Ajustes solicitados: {comment}",
        )
        self._notify_users(
            user_ids=self._assignee_ids(task),
            task=task,
            notification_type=NotificationType.CHANGES_REQUESTED,
            message=f"Foram solicitados ajustes na tarefa '{task.title}': {comment}",
        )
        self.session.commit()
        return self._to_response(task)

    def approve_task(
        self,
        task_id: int,
        actor_id: int,
        comment: str | None = None,
    ) -> TaskResponse:
        task = self._get_task(task_id)
        self._require_requester(task, actor_id)
        self._require_status(task, {TaskStatus.IN_REVIEW}, "aprovar")
        self.tasks.change_status(task, TaskStatus.APPROVED)

        description = "Tarefa revisada e aprovada."
        if comment and comment.strip():
            description = f"{description} Observação: {comment.strip()}"
        self._record_history(
            task=task,
            actor_id=actor_id,
            event_type=TaskEventType.TASK_APPROVED,
            description=description,
        )
        self._notify_users(
            user_ids=self._assignee_ids(task),
            task=task,
            notification_type=NotificationType.TASK_APPROVED,
            message=f"A tarefa '{task.title}' foi aprovada.",
        )
        self.session.commit()
        return self._to_response(task)

    def list_history(self, task_id: int) -> list[TaskHistoryEntry]:
        self._get_task(task_id)
        return [
            TaskHistoryEntry.model_validate(event)
            for event in self.tasks.list_history(task_id)
        ]

    def list_notifications(self, user_id: int) -> list[NotificationResponse]:
        self._get_user(user_id)
        return [
            NotificationResponse.model_validate(notification)
            for notification in self.tasks.list_notifications(user_id)
        ]

    def _get_user(self, user_id: int) -> User:
        user = self.users.get(user_id)
        if user is None:
            raise UserNotFoundError(f"Usuário {user_id} não encontrado.")
        return user

    def _get_task(self, task_id: int) -> Task:
        task = self.tasks.get(task_id)
        if task is None:
            raise TaskNotFoundError(f"Tarefa {task_id} não encontrada.")
        return task

    def _assignee_ids(self, task: Task) -> list[int]:
        return [user.id for user in task.assignees]

    def _to_response(self, task: Task) -> TaskResponse:
        return TaskResponse(
            id=task.id,
            title=task.title,
            description=task.description,
            requester_id=task.requester_id,
            assignee_ids=self._assignee_ids(task),
            status=task.status,
            created_at=task.created_at,
            updated_at=task.updated_at,
        )

    def _require_assignee(self, task: Task, actor_id: int) -> None:
        if actor_id not in self._assignee_ids(task):
            raise TaskPermissionError(
                "Somente um destinatário da tarefa pode executar esta ação."
            )

    def _require_requester(self, task: Task, actor_id: int) -> None:
        if actor_id != task.requester_id:
            raise TaskPermissionError(
                "Somente quem solicitou a tarefa pode executar esta ação."
            )

    def _require_status(
        self,
        task: Task,
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
        *,
        task: Task,
        actor_id: int,
        event_type: TaskEventType,
        description: str,
    ) -> None:
        self.tasks.add_history(
            task=task,
            actor_id=actor_id,
            event_type=event_type,
            description=description,
        )

    def _notify_users(
        self,
        *,
        user_ids: list[int],
        task: Task,
        notification_type: NotificationType,
        message: str,
    ) -> None:
        for user_id in user_ids:
            self.tasks.add_notification(
                user_id=user_id,
                task=task,
                notification_type=notification_type,
                message=message,
            )
