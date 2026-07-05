from app.schemas.task_schema import TaskCreate, TaskResponse

class TaskService:
    def __init__(self):
        self.tasks = []
        self.next_id = 1

    def create_task(self, task_data: TaskCreate) -> TaskResponse:
        if not task_data.title.strip():
            raise ValueError("O título da tarefa não pode estar vazio.")
        
        task = TaskResponse(
            id=self.next_id,
            title=task_data.title,
            descripiton=task_data.description,
            status="CRIADA",
        )

        self.tasks.append(task)
        self.next_id += 1

        return task
