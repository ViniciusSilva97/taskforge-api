import os
import unittest

os.environ["DATABASE_URL"] = "sqlite+pysqlite://"
os.environ["JWT_SECRET_KEY"] = "test-secret-key-with-at-least-32-bytes"
os.environ["ACCESS_TOKEN_EXPIRE_MINUTES"] = "60"

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
    password = "SenhaForte123"

    def setUp(self) -> None:
        Base.metadata.drop_all(bind=engine)
        Base.metadata.create_all(bind=engine)
        self.client = TestClient(app)
        self.requester = self.create_user("Ana Solicitante", "ana@example.com")
        self.assignee = self.create_user("Bruno Executor", "bruno@example.com")
        self.second_assignee = self.create_user("Carla Executor", "carla@example.com")
        self.outsider = self.create_user("Diego Externo", "diego@example.com")
        self.requester_headers = self.login("ana@example.com")
        self.assignee_headers = self.login("bruno@example.com")
        self.second_assignee_headers = self.login("carla@example.com")
        self.outsider_headers = self.login("diego@example.com")

    def create_user(self, name: str, email: str) -> dict:
        response = self.client.post(
            "/users/",
            json={
                "name": name,
                "email": email,
                "password": self.password,
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def login(self, email: str, password: str | None = None) -> dict[str, str]:
        response = self.client.post(
            "/auth/token",
            data={
                "username": email,
                "password": password or self.password,
            },
        )
        self.assertEqual(response.status_code, 200, response.text)
        token = response.json()["access_token"]
        return {"Authorization": f"Bearer {token}"}

    def create_task(self) -> dict:
        response = self.client.post(
            "/tasks/",
            headers=self.requester_headers,
            json={
                "title": "  Revisar fluxo de tarefas  ",
                "description": "Validar a entrega autenticada.",
                "assignee_ids": [
                    self.assignee["id"],
                    self.second_assignee["id"],
                    self.assignee["id"],
                ],
            },
        )
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_root_reports_version_030(self) -> None:
        response = self.client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["version"], "0.3.0")

    def test_login_and_current_user(self) -> None:
        response = self.client.get("/auth/me", headers=self.requester_headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["email"], "ana@example.com")

    def test_invalid_credentials_return_unauthorized(self) -> None:
        response = self.client.post(
            "/auth/token",
            data={
                "username": "ana@example.com",
                "password": "senha-errada",
            },
        )
        self.assertEqual(response.status_code, 401)

    def test_protected_endpoint_requires_token(self) -> None:
        response = self.client.get("/tasks/")
        self.assertEqual(response.status_code, 401)

    def test_duplicate_email_returns_conflict(self) -> None:
        response = self.client.post(
            "/users/",
            json={
                "name": "Outra Ana",
                "email": "ANA@example.com",
                "password": self.password,
            },
        )
        self.assertEqual(response.status_code, 409)

    def test_task_uses_authenticated_requester_and_filters_visibility(self) -> None:
        task = self.create_task()
        self.assertEqual(task["requester_id"], self.requester["id"])
        self.assertEqual(
            task["assignee_ids"],
            [self.assignee["id"], self.second_assignee["id"]],
        )
        requester_tasks = self.client.get(
            "/tasks/",
            headers=self.requester_headers,
        ).json()
        outsider_tasks = self.client.get(
            "/tasks/",
            headers=self.outsider_headers,
        ).json()
        self.assertEqual(len(requester_tasks), 1)
        self.assertEqual(outsider_tasks, [])

    def test_task_requires_existing_assignees(self) -> None:
        response = self.client.post(
            "/tasks/",
            headers=self.requester_headers,
            json={"title": "Tarefa inválida", "assignee_ids": [999]},
        )
        self.assertEqual(response.status_code, 404)
        self.assertIn("Usuário 999", response.json()["detail"])

    def test_complete_authenticated_approval_workflow(self) -> None:
        task_id = self.create_task()["id"]
        start = self.client.post(
            f"/tasks/{task_id}/start",
            headers=self.assignee_headers,
        )
        self.assertEqual(start.status_code, 200)
        self.assertEqual(start.json()["status"], "IN_PROGRESS")

        submit = self.client.post(
            f"/tasks/{task_id}/submit",
            headers=self.assignee_headers,
        )
        self.assertEqual(submit.status_code, 200)
        self.assertEqual(submit.json()["status"], "IN_REVIEW")

        approve = self.client.post(
            f"/tasks/{task_id}/approve",
            headers=self.requester_headers,
            json={"comment": "Aprovado."},
        )
        self.assertEqual(approve.status_code, 200)
        self.assertEqual(approve.json()["status"], "APPROVED")

        history = self.client.get(
            f"/tasks/{task_id}/history",
            headers=self.requester_headers,
        ).json()
        self.assertEqual(
            [event["event_type"] for event in history],
            [
                "TASK_CREATED",
                "TASK_STARTED",
                "TASK_SUBMITTED",
                "TASK_APPROVED",
            ],
        )
        self.assertEqual(history[1]["actor_id"], self.assignee["id"])

    def test_request_changes_returns_task_to_work(self) -> None:
        task_id = self.create_task()["id"]
        self.client.post(
            f"/tasks/{task_id}/start",
            headers=self.second_assignee_headers,
        )
        self.client.post(
            f"/tasks/{task_id}/submit",
            headers=self.second_assignee_headers,
        )
        changes = self.client.post(
            f"/tasks/{task_id}/request-changes",
            headers=self.requester_headers,
            json={"comment": "Inclua os cenários de erro."},
        )
        self.assertEqual(changes.status_code, 200)
        self.assertEqual(changes.json()["status"], "CHANGES_REQUESTED")

        restart = self.client.post(
            f"/tasks/{task_id}/start",
            headers=self.second_assignee_headers,
        )
        self.assertEqual(restart.status_code, 200)
        self.assertEqual(restart.json()["status"], "IN_PROGRESS")

    def test_outsider_cannot_access_or_start_task(self) -> None:
        task_id = self.create_task()["id"]
        get_response = self.client.get(
            f"/tasks/{task_id}",
            headers=self.outsider_headers,
        )
        start_response = self.client.post(
            f"/tasks/{task_id}/start",
            headers=self.outsider_headers,
        )
        self.assertEqual(get_response.status_code, 403)
        self.assertEqual(start_response.status_code, 403)

    def test_notifications_are_bound_to_authenticated_user(self) -> None:
        self.create_task()
        requester_notifications = self.client.get(
            "/tasks/notifications/me",
            headers=self.requester_headers,
        ).json()
        assignee_notifications = self.client.get(
            "/tasks/notifications/me",
            headers=self.assignee_headers,
        ).json()
        self.assertEqual(requester_notifications, [])
        self.assertEqual(
            assignee_notifications[0]["type"],
            "TASK_ASSIGNED",
        )


if __name__ == "__main__":
    unittest.main()
