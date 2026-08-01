import unittest

from fastapi.testclient import TestClient

from app.api.routers.task_router import task_service
from app.main import app


class TaskApiTests(unittest.TestCase):
    def setUp(self) -> None:
        task_service.reset()
        self.client = TestClient(app)

    def create_task(self) -> dict:
        response = self.client.post(
            "/tasks/",
            json={
                "title": "  Revisar fluxo de tarefas  ",
                "description": "Validar a entrega da API.",
                "requester_id": 10,
                "assignee_ids": [20, 30, 20],
            },
        )
        self.assertEqual(response.status_code, 201)
        return response.json()

    def test_root_reports_running_api(self) -> None:
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "running")

    def test_create_task_and_notify_only_assignees(self) -> None:
        task = self.create_task()

        self.assertEqual(task["title"], "Revisar fluxo de tarefas")
        self.assertEqual(task["status"], "ASSIGNED")
        self.assertEqual(task["assignee_ids"], [20, 30])

        list_response = self.client.get("/tasks/")
        self.assertEqual(list_response.status_code, 200)
        self.assertEqual(len(list_response.json()), 1)

        requester_notifications = self.client.get(
            "/tasks/users/10/notifications"
        ).json()
        assignee_notifications = self.client.get(
            "/tasks/users/20/notifications"
        ).json()

        self.assertEqual(requester_notifications, [])
        self.assertEqual(len(assignee_notifications), 1)
        self.assertEqual(
            assignee_notifications[0]["type"],
            "TASK_ASSIGNED",
        )

    def test_complete_approval_workflow(self) -> None:
        task = self.create_task()
        task_id = task["id"]

        start = self.client.post(
            f"/tasks/{task_id}/start",
            json={"actor_id": 20},
        )
        self.assertEqual(start.status_code, 200)
        self.assertEqual(start.json()["status"], "IN_PROGRESS")

        submit = self.client.post(
            f"/tasks/{task_id}/submit",
            json={"actor_id": 20},
        )
        self.assertEqual(submit.status_code, 200)
        self.assertEqual(submit.json()["status"], "IN_REVIEW")

        requester_notifications = self.client.get(
            "/tasks/users/10/notifications"
        ).json()
        self.assertEqual(len(requester_notifications), 1)
        self.assertEqual(
            requester_notifications[0]["type"],
            "TASK_SUBMITTED",
        )

        approve = self.client.post(
            f"/tasks/{task_id}/approve",
            json={
                "actor_id": 10,
                "comment": "Entrega validada.",
            },
        )
        self.assertEqual(approve.status_code, 200)
        self.assertEqual(approve.json()["status"], "APPROVED")

        history = self.client.get(f"/tasks/{task_id}/history").json()
        self.assertEqual(
            [event["event_type"] for event in history],
            [
                "TASK_CREATED",
                "TASK_STARTED",
                "TASK_SUBMITTED",
                "TASK_APPROVED",
            ],
        )

        assignee_notifications = self.client.get(
            "/tasks/users/20/notifications"
        ).json()
        self.assertEqual(
            [notification["type"] for notification in assignee_notifications],
            ["TASK_ASSIGNED", "TASK_APPROVED"],
        )

    def test_request_changes_and_restart_work(self) -> None:
        task_id = self.create_task()["id"]

        self.client.post(
            f"/tasks/{task_id}/start",
            json={"actor_id": 30},
        )
        self.client.post(
            f"/tasks/{task_id}/submit",
            json={"actor_id": 30},
        )

        changes = self.client.post(
            f"/tasks/{task_id}/request-changes",
            json={
                "actor_id": 10,
                "comment": "Inclua os cenários de erro.",
            },
        )
        self.assertEqual(changes.status_code, 200)
        self.assertEqual(changes.json()["status"], "CHANGES_REQUESTED")

        restart = self.client.post(
            f"/tasks/{task_id}/start",
            json={"actor_id": 30},
        )
        self.assertEqual(restart.status_code, 200)
        self.assertEqual(restart.json()["status"], "IN_PROGRESS")

        notifications = self.client.get(
            "/tasks/users/30/notifications"
        ).json()
        self.assertEqual(
            [notification["type"] for notification in notifications],
            ["TASK_ASSIGNED", "CHANGES_REQUESTED"],
        )

    def test_non_assignee_cannot_start_task(self) -> None:
        task_id = self.create_task()["id"]

        response = self.client.post(
            f"/tasks/{task_id}/start",
            json={"actor_id": 99},
        )

        self.assertEqual(response.status_code, 403)
        self.assertIn("destinatário", response.json()["detail"])

    def test_requester_cannot_approve_before_review(self) -> None:
        task_id = self.create_task()["id"]

        response = self.client.post(
            f"/tasks/{task_id}/approve",
            json={"actor_id": 10},
        )

        self.assertEqual(response.status_code, 409)
        self.assertIn("ASSIGNED", response.json()["detail"])

    def test_request_changes_requires_observation(self) -> None:
        task_id = self.create_task()["id"]
        self.client.post(
            f"/tasks/{task_id}/start",
            json={"actor_id": 20},
        )
        self.client.post(
            f"/tasks/{task_id}/submit",
            json={"actor_id": 20},
        )

        response = self.client.post(
            f"/tasks/{task_id}/request-changes",
            json={"actor_id": 10, "comment": "   "},
        )

        self.assertEqual(response.status_code, 422)

    def test_reject_blank_title(self) -> None:
        response = self.client.post(
            "/tasks/",
            json={
                "title": "   ",
                "requester_id": 10,
                "assignee_ids": [20],
            },
        )

        self.assertEqual(response.status_code, 422)

    def test_missing_task_returns_404(self) -> None:
        response = self.client.get("/tasks/999999")

        self.assertEqual(response.status_code, 404)
        self.assertEqual(
            response.json()["detail"],
            "Tarefa 999999 não encontrada.",
        )


if __name__ == "__main__":
    unittest.main()
