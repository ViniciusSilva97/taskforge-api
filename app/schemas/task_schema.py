from pydantic import BaseModel, Field

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, mas_length=100)
    description: str | Nome = Field(default=None, mas_length=500)

class TaskResponse(BaseModel):
    id: int
    title: str
    descripiton: str | None
    status: str
