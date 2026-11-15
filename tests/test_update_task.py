from fastapi.testclient import TestClient


def test_update_task_completed_to_true(client: TestClient):
    """Testa atualizar o status de conclusão para true."""
    create_res = client.post("/tasks", json={"title": "Tarefa para concluir"})
    task_id = create_res.json()["id"]

    response = client.patch(f"/tasks/{task_id}", json={"completed": True})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["title"] == "Tarefa para concluir"
    assert data["completed"] is True


def test_update_task_completed_to_false(client: TestClient):
    """Testa atualizar o status de conclusão de true para false."""
    create_res = client.post("/tasks", json={"title": "Tarefa para desmarcar"})
    task_id = create_res.json()["id"]

    # Primeiro marca como true
    client.patch(f"/tasks/{task_id}", json={"completed": True})

    # Depois desmarca para false
    response = client.patch(f"/tasks/{task_id}", json={"completed": False})
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == task_id
    assert data["completed"] is False


def test_update_task_non_existent_id(client: TestClient):
    """Testa a atualização de uma tarefa que não existe, devendo retornar 404."""
    response = client.patch("/tasks/99999", json={"completed": True})
    assert response.status_code == 404
    assert response.json()["detail"] == "Tarefa não encontrada"


def test_update_task_invalid_data(client: TestClient):
    """Testa o envio de dados inválidos para o endpoint de atualização."""
    create_res = client.post("/tasks", json={"title": "Tarefa Validação"})
    task_id = create_res.json()["id"]

    # completed não é booleano
    response = client.patch(f"/tasks/{task_id}", json={"completed": "texto_invalido"})
    assert response.status_code == 422

    # corpo vazio sem completed
    response_empty = client.patch(f"/tasks/{task_id}", json={})
    assert response_empty.status_code == 422


def test_update_task_invalid_id_type(client: TestClient):
    """Testa o envio de ID com tipo inválido na URL."""
    response = client.patch("/tasks/invalido", json={"completed": True})
    assert response.status_code == 422


def test_update_task_guarantees_title_not_modified(client: TestClient):
    """Garante que o endpoint PATCH altera apenas completed, mantendo o título intacto."""
    original_title = "Título Imutável"
    create_res = client.post("/tasks", json={"title": original_title})
    task_id = create_res.json()["id"]

    # Tenta enviar novo título junto com completed
    patch_res = client.patch(
        f"/tasks/{task_id}",
        json={"completed": True, "title": "Título Modificado Indevidamente"}
    )
    assert patch_res.status_code == 200
    patch_data = patch_res.json()
    assert patch_data["title"] == original_title
    assert patch_data["completed"] is True

    # Verifica via GET se no banco o título realmente permaneceu inalterado
    get_res = client.get("/tasks")
    tasks = get_res.json()
    assert len(tasks) == 1
    assert tasks[0]["title"] == original_title
    assert tasks[0]["completed"] is True
