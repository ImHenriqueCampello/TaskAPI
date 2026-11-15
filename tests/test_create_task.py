from fastapi.testclient import TestClient


def test_create_valid_task(client: TestClient):
    """Testa a criação de uma tarefa válida com título e status inicial false."""
    response = client.post("/tasks", json={"title": "Estudar Docker"})
    assert response.status_code == 201
    data = response.json()
    assert data["id"] == 1
    assert data["title"] == "Estudar Docker"
    assert data["completed"] is False


def test_create_task_without_title(client: TestClient):
    """Testa a criação de tarefa sem o campo obrigatório title."""
    response = client.post("/tasks", json={})
    assert response.status_code == 422


def test_create_task_empty_title(client: TestClient):
    """Testa a criação de tarefa com título vazio."""
    response = client.post("/tasks", json={"title": ""})
    assert response.status_code == 422


def test_create_task_whitespace_title(client: TestClient):
    """Testa a criação de tarefa com título contendo apenas espaços em branco."""
    response = client.post("/tasks", json={"title": "     "})
    assert response.status_code == 422


def test_create_task_auto_increment_id(client: TestClient):
    """Testa a geração automática e sequencial de IDs para novas tarefas."""
    res1 = client.post("/tasks", json={"title": "Tarefa 1"})
    assert res1.status_code == 201
    assert res1.json()["id"] == 1

    res2 = client.post("/tasks", json={"title": "Tarefa 2"})
    assert res2.status_code == 201
    assert res2.json()["id"] == 2

    res3 = client.post("/tasks", json={"title": "Tarefa 3"})
    assert res3.status_code == 201
    assert res3.json()["id"] == 3


def test_create_task_initial_status_is_false(client: TestClient):
    """Garante que toda nova tarefa inicia com status completed = False."""
    response = client.post("/tasks", json={"title": "Nova Tarefa"})
    assert response.status_code == 201
    assert response.json()["completed"] is False


def test_create_task_ignores_payload_completed(client: TestClient):
    """Garante que o status completed não pode ser definido como True na criação."""
    response = client.post("/tasks", json={"title": "Tarefa com completed", "completed": True})
    assert response.status_code == 201
    assert response.json()["completed"] is False


def test_create_task_strips_surrounding_whitespace(client: TestClient):
    """Testa se espaços nas bordas do título são removidos."""
    response = client.post("/tasks", json={"title": "  Estudar PostgreSQL  "})
    assert response.status_code == 201
    assert response.json()["title"] == "Estudar PostgreSQL"


def test_database_get_db_dependency():
    """Testa a função geradora de sessão get_db de app/database.py."""
    from app.database import get_db
    gen = get_db()
    db = next(gen)
    assert db is not None
    try:
        next(gen)
    except StopIteration:
        pass

