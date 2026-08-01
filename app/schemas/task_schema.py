from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskStatus(StrEnum):
    ASSIGNED = "ASSIGNED"
    IN_PROGRESS = "IN_PROGRESS"
    IN_REVIEW = "IN_REVIEW"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    APPROVED = "APPROVED"


class TaskEventType(StrEnum):
    TASK_CREATED = "TASK_CREATED"
    TASK_STARTED = "TASK_STARTED"
    TASK_SUBMITTED = "TASK_SUBMITTED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    TASK_APPROVED = "TASK_APPROVED"


class NotificationType(StrEnum):
    TASK_ASSIGNED = "TASK_ASSIGNED"
    TASK_SUBMITTED = "TASK_SUBMITTED"
    CHANGES_REQUESTED = "CHANGES_REQUESTED"
    TASK_APPROVED = "TASK_APPROVED"


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
    requester_id: int = Field(gt=0)
    assignee_ids: list[int] = Field(min_length=1)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("O título da tarefa não pode estar vazio.")
        return normalized

    @field_validator("assignee_ids")
    @classmethod
    def normalize_assignees(cls, value: list[int]) -> list[int]:
        if any(user_id <= 0 for user_id in value):
            raise ValueError("Todos os destinatários devem possuir IDs positivos.")

        unique_ids = list(dict.fromkeys(value))
        if not unique_ids:
            raise ValueError("A tarefa deve possuir pelo menos um destinatário.")
        return unique_ids


class TaskActionRequest(BaseModel):
    actor_id: int = Field(gt=0)


class TaskReviewRequest(TaskActionRequest):
    comment: str | None = Field(default=None, max_length=1000)


class TaskChangesRequest(TaskActionRequest):
    comment: str = Field(min_length=1, max_length=1000)

    @field_validator("comment")
    @classmethod
    def normalize_comment(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("A solicitação de ajustes deve possuir uma observação.")
        return normalized


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    requester_id: int
    assignee_ids: list[int]
    status: TaskStatus


class TaskHistoryEntry(BaseModel):
    id: int
    task_id: int
    actor_id: int
    event_type: TaskEventType
    description: str
    created_at: datetime


class NotificationResponse(BaseModel):
    id: int
    user_id: int
    task_id: int
    type: NotificationType
    message: str
    is_read: bool = False
    created_at: datetime
