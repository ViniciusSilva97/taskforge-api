from app.schemas.task_schema import TaskCreate, TaskResponse, TaskStatus


class TaskNotFoundError(LookupError):
    """Raised when a task cannot be found by its identifier."""


class TaskService:
    """Applies task business rules using temporary in-memory storage."""

    def __init__(self) -> None:
        self._tasks: list[TaskResponse] = []
        self._next_id = 1

    def create_task(self, task_data: TaskCreate) -> TaskResponse:
        task = TaskResponse(
            id=self._next_id,
            title=task_data.title,
            description=task_data.description,
            status=TaskStatus.CREATED,
        )

        self._tasks.append(task)
        self._next_id += 1
        return task

    def list_tasks(self) -> list[TaskResponse]:
        return list(self._tasks)

    def get_task(self, task_id: int) -> TaskResponse:
        for task in self._tasks:
            if task.id == task_id:
                return task
        raise TaskNotFoundError(f"Tarefa {task_id} não encontrada.")
