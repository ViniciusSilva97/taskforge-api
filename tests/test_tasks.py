import unittest

from fastapi.testclient import TestClient

from app.main import app


class TaskApiTests(unittest.TestCase):
    def setUp(self) -> None:
        self.client = TestClient(app)

    def test_root_reports_running_api(self) -> None:
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "running")

    def test_create_and_retrieve_task(self) -> None:
        create_response = self.client.post(
            "/tasks/",
            json={
                "title": "  Revisar fluxo de tarefas  ",
                "description": "Validar a primeira entrega da API.",
            },
        )

        self.assertEqual(create_response.status_code, 201)
        created_task = create_response.json()
        self.assertEqual(created_task["title"], "Revisar fluxo de tarefas")
        self.assertEqual(created_task["status"], "CREATED")

        get_response = self.client.get(f"/tasks/{created_task['id']}")
        self.assertEqual(get_response.status_code, 200)
        self.assertEqual(get_response.json(), created_task)

    def test_reject_blank_title(self) -> None:
        response = self.client.post("/tasks/", json={"title": "   "})

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
