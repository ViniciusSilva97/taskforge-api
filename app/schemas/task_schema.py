from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.core.enums import NotificationType, TaskEventType, TaskStatus


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)
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
        return list(dict.fromkeys(value))


class TaskReviewRequest(BaseModel):
    comment: str | None = Field(default=None, max_length=1000)


class TaskChangesRequest(BaseModel):
    comment: str = Field(min_length=1, max_length=1000)

    @field_validator("comment")
    @classmethod
    def normalize_comment(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("A solicitação de ajustes deve possuir uma observação.")
        return normalized


class TaskResponse(BaseModel):
    id: int
    title: str
    description: str | None
    requester_id: int
    assignee_ids: list[int]
    status: TaskStatus
    created_at: datetime
    updated_at: datetime


class TaskHistoryEntry(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    task_id: int
    actor_id: int
    event_type: TaskEventType
    description: str
    created_at: datetime


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    user_id: int
    task_id: int
    type: NotificationType
    message: str
    is_read: bool
    created_at: datetime
