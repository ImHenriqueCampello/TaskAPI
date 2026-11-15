from fastapi.testclient import TestClient


def test_list_tasks_empty(client: TestClient):
    """Testa a listagem quando não há nenhuma tarefa cadastrada, devendo retornar lista vazia."""
    response = client.get("/tasks")
    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_multiple(client: TestClient):
    """Testa a listagem com múltiplas tarefas cadastradas."""
    client.post("/tasks", json={"title": "Tarefa 1"})
    client.post("/tasks", json={"title": "Tarefa 2"})
    client.post("/tasks", json={"title": "Tarefa 3"})

    response = client.get("/tasks")
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 3
    assert tasks[0]["title"] == "Tarefa 1"
    assert tasks[1]["title"] == "Tarefa 2"
    assert tasks[2]["title"] == "Tarefa 3"


def test_list_tasks_fields_structure(client: TestClient):
    """Testa a estrutura e tipos dos campos retornados na listagem."""
    client.post("/tasks", json={"title": "Tarefa Estrutura"})
    response = client.get("/tasks")
    assert response.status_code == 200
    tasks = response.json()
    assert len(tasks) == 1
    task = tasks[0]
    assert "id" in task
    assert "title" in task
    assert "completed" in task
    assert isinstance(task["id"], int)
    assert isinstance(task["title"], str)
    assert isinstance(task["completed"], bool)
