from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_root_reports_running_api() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["status"] == "running"


def test_create_and_retrieve_task() -> None:
    create_response = client.post(
        "/tasks/",
        json={
            "title": "  Revisar fluxo de tarefas  ",
            "description": "Validar a primeira entrega da API.",
        },
    )

    assert create_response.status_code == 201
    created_task = create_response.json()
    assert created_task["title"] == "Revisar fluxo de tarefas"
    assert created_task["status"] == "CREATED"

    get_response = client.get(f"/tasks/{created_task['id']}")
    assert get_response.status_code == 200
    assert get_response.json() == created_task


def test_reject_blank_title() -> None:
    response = client.post("/tasks/", json={"title": "   "})

    assert response.status_code == 422


def test_missing_task_returns_404() -> None:
    response = client.get("/tasks/999999")

    assert response.status_code == 404
    assert response.json()["detail"] == "Tarefa 999999 não encontrada."
