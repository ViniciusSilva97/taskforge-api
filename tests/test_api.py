import os
import unittest

os.environ["DATABASE_URL"] = "sqlite+pysqlite://"

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.database import get_db
from app.main import app
from app.models import Base

engine = create_engine(
    "sqlite+pysqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


def override_get_db():
    with TestingSessionLocal() as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


class TaskForgeApiTests(unittest.TestCase):
    def setUp(self) -> None:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        self.client = TestClient(app)
        self.requester = self.create_user("Ana Solicitante", "ana@example.com")
        self.assignee = self.create_user("Bruno Executor", "bruno@example.com")
        self.second_assignee = self.create_user("Carla Executor", "carla@example.com")

    def create_user(self, name: str, email: str) -> dict:
        response = self.client.post("/users/", json={"name": name, "email": email})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def create_task(self) -> dict:
        response = self.client.post(
            "/tasks/",
            json={
                "title": "  Revisar fluxo de tarefas  ",
                "description": "Validar a entrega persistida.",
                "requester_id": self.requester["id"],
                "assignee_ids": [
                    self.assignee["id"],
                    self.second_assignee["id"],
                    self.assignee["id"],
                ],
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_root_reports_version_020(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["version"], "0.2.0")

    def test_create_list_and_get_users(self) -> None:
        users = self.client.get("/users/")
        self.assertEqual(users.status_code, 200)
        self.assertEqual(len(users.json()), 3)

        user = self.client.get(f"/users/{self.requester['id']}")
        self.assertEqual(user.status_code, 200)
        self.assertEqual(user.json()["email"], "ana@example.com")

    def test_duplicate_email_returns_conflict(self) -> None:
        response = self.client.post(
            "/users/",
            json={"name": "Outra Ana", "email": "ANA@example.com"},
        )
        self.assertEqual(response.status_code, 409)

    def test_task_requires_existing_users(self) -> None:
        response = self.client.post(
            "/tasks/",
            json={
                "title": "Tarefa inválida",
                "requester_id": 999,
                "assignee_ids": [self.assignee["id"]],
            },
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("Usuário 999", response.json()["detail"])

    def test_create_task_persists_and_notifies_assignees(self) -> None:
        task = self.create_task()
        self.assertEqual(task["status"], "ASSIGNED")
        self.assertEqual(
            task["assignee_ids"],
            [self.assignee["id"], self.second_assignee["id"]],
        )

        stored = self.client.get(f"/tasks/{task['id']}")
        self.assertEqual(stored.status_code, 200)
        self.assertEqual(stored.json()["id"], task["id"])

        requester_notifications = self.client.get(
            f"/tasks/users/{self.requester['id']}/notifications"
        ).json()
        assignee_notifications = self.client.get(
            f"/tasks/users/{self.assignee['id']}/notifications"
        ).json()
        self.assertEqual(requester_notifications, [])
        self.assertEqual(assignee_notifications[0]["type"], "TASK_ASSIGNED")

    def test_complete_approval_workflow_persists_history(self) -> None:
        task = self.create_task()
        task_id = task["id"]

        start = self.client.post(
            f"/tasks/{task_id}/start",
            json={"actor_id": self.assignee["id"]},
        )
        self.assertEqual(start.status_code, 200)
        self.assertEqual(start.json()["status"], "IN_PROGRESS")

        submit = self.client.post(
            f"/tasks/{task_id}/submit",
            json={"actor_id": self.assignee["id"]},
        )
        self.assertEqual(submit.status_code, 200)
        self.assertEqual(submit.json()["status"], "IN_REVIEW")

        approve = self.client.post(
            f"/tasks/{task_id}/approve",
            json={"actor_id": self.requester["id"], "comment": "Aprovado."},
        )
        self.assertEqual(approve.status_code, 200)
        self.assertEqual(approve.json()["status"], "APPROVED")

        history = self.client.get(f"/tasks/{task_id}/history").json()
        self.assertEqual(
            [event["event_type"] for event in history],
            ["TASK_CREATED", "TASK_STARTED", "TASK_SUBMITTED", "TASK_APPROVED"],
        )

    def test_request_changes_returns_task_to_work(self) -> None:
        task_id = self.create_task()["id"]
        actor_id = self.second_assignee["id"]
        self.client.post(f"/tasks/{task_id}/start", json={"actor_id": actor_id})
        self.client.post(f"/tasks/{task_id}/submit", json={"actor_id": actor_id})

        changes = self.client.post(
            f"/tasks/{task_id}/request-changes",
            json={
                "actor_id": self.requester["id"],
                "comment": "Inclua os cenários de erro.",
            },
        )
        self.assertEqual(changes.status_code, 200)
        self.assertEqual(changes.json()["status"], "CHANGES_REQUESTED")

        restart = self.client.post(
            f"/tasks/{task_id}/start",
            json={"actor_id": actor_id},
        )
        self.assertEqual(restart.status_code, 200)
        self.assertEqual(restart.json()["status"], "IN_PROGRESS")

    def test_non_assignee_cannot_start(self) -> None:
        outsider = self.create_user("Diego Externo", "diego@example.com")
        task_id = self.create_task()["id"]
        response = self.client.post(
            f"/tasks/{task_id}/start",
            json={"actor_id": outsider["id"]},
        )
        self.assertEqual(response.status_code, 403)

    def test_notification_endpoint_requires_existing_user(self) -> None:
        response = self.client.get("/tasks/users/999/notifications")
        self.assertEqual(response.status_code, 404)


if __name__ == "__main__":
    unittest.main()
