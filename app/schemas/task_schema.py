from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class TaskStatus(StrEnum):
    CREATED = "CREATED"


class TaskCreate(BaseModel):
    title: str = Field(min_length=1, max_length=100)
    description: str | None = Field(default=None, max_length=500)

    @field_validator("title")
    @classmethod
    def normalize_title(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("O título da tarefa não pode estar vazio.")
        return normalized


class TaskResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    description: str | None
    status: TaskStatus
