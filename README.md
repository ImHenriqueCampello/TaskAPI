# To-Do API - Gerenciamento de Tarefas

API REST simples, robusta e eficiente para gerenciamento de tarefas (To-Do API), desenvolvida para a disciplina de **Gerência de Configuração e Evolução de Software**.

Nesta etapa do projeto, o foco foi desenvolver exclusivamente:
- A aplicação FastAPI e seus três endpoints fundamentais.
- A persistência de dados utilizando PostgreSQL definitivo e SQLAlchemy.
- A orquestração do banco de dados PostgreSQL via Docker Compose.
- A suíte completa de testes automatizados com Pytest utilizando um banco de testes isolado (`tasks_test`).
- Cobertura de testes superior a 90% (atingindo **100% de cobertura** do código da aplicação).

---

## 🛠️ Tecnologias Utilizadas

- **[Python](https://www.python.org/)**: Linguagem de programação principal.
- **[FastAPI](https://fastapi.tiangolo.com/)**: Framework web moderno, assíncrono e de alto desempenho.
- **[PostgreSQL](https://www.postgresql.org/)**: Banco de dados relacional oficial.
- **[SQLAlchemy](https://www.sqlalchemy.org/)**: ORM para comunicação e modelagem de banco de dados.
- **[Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/)**: Containerização e isolamento do PostgreSQL.
- **[Pytest](https://docs.pytest.org/)**: Framework para testes automatizados.
- **[pytest-cov](https://pytest-cov.readthedocs.io/)**: Ferramenta de análise e relatório de cobertura de código.

---

## 📁 Estrutura do Projeto

```
TaskAPI/
│
├── app/
│   ├── __init__.py
│   ├── main.py          # Ponto de entrada FastAPI e ciclo de vida
│   ├── database.py      # Configuração do SQLAlchemy e conexão com PostgreSQL
│   ├── models.py        # Modelos ORM (SQLAlchemy) e esquemas de validação (Pydantic)
│   └── routes.py        # Definição e lógica dos três endpoints da API
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py          # Fixtures do Pytest, isolamento e limpeza de banco
│   ├── test_create_task.py  # Testes de criação e validação de tarefas
│   ├── test_list_tasks.py   # Testes de listagem de tarefas
│   └── test_update_task.py  # Testes de atualização de status (PATCH)
│
├── docker-compose.yml   # Definição do serviço PostgreSQL em container
├── requirements.txt     # Dependências da aplicação
├── .env                 # Variáveis de ambiente locais (não versionado)
├── .env.example         # Modelo de configuração de variáveis de ambiente
├── .gitignore           # Regras de exclusão do controle de versão
└── README.md            # Documentação completa do projeto
```

---

## ⚙️ Configuração e Instalação

### 1. Clonar ou Acessar o Repositório

```bash
cd "/home/rick/Documents/IdeaProjects/PyCharm Projects/TaskAPI"
```

### 2. Configurar o Ambiente Virtual (venv)

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Instalar as Dependências

```bash
pip install -r requirements.txt
```

### 4. Configurar as Variáveis de Ambiente

Copie o arquivo de exemplo `.env.example` para `.env`:

```bash
cp .env.example .env
```

Conteúdo padrão do arquivo `.env`:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=tasks
POSTGRES_HOST=localhost
POSTGRES_PORT=5432

DATABASE_URL=postgresql://postgres:postgres@localhost:5432/tasks
TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5432/tasks_test
```

---

## 🐳 Inicialização do Banco de Dados (Docker Compose)

O PostgreSQL é executado em container com porta 5432 exposta, volume nomeado para persistência e verificação de integridade (*healthcheck*).

### Subir o container PostgreSQL

```bash
docker compose up -d
```

Verifique se o container está rodando e saudável:

```bash
docker compose ps
```

### Criar o banco de dados de testes (`tasks_test`)

Para garantir que os testes não afetem a base de dados de desenvolvimento, crie a base separada:

```bash
docker compose exec postgres psql -U postgres -c "CREATE DATABASE tasks_test;"
```

> **Nota:** As fixtures do Pytest também realizam a verificação e criação automática do banco `tasks_test` caso ele ainda não tenha sido criado manualmente.

---

## 🚀 Executando a API

Com o banco de dados em execução e o ambiente virtual ativado:

```bash
uvicorn app.main:app --reload --port 8000
```

A API estará acessível em: `http://localhost:8000`  
Documentação interativa Swagger UI: `http://localhost:8000/docs`

---

## 📡 Endpoints da API

A API possui estritamente três endpoints, conforme especificado:

### 1. Criar tarefa
- **Método**: `POST /tasks`
- **Status HTTP**: `201 Created`
- **Regras**: Título obrigatório, não vazio e não composto apenas de espaços. A tarefa sempre inicia com `completed = false`.
- **Exemplo de Requisição**:
  ```bash
  curl -X POST http://localhost:8000/tasks \
    -H "Content-Type: application/json" \
    -d '{"title": "Estudar Docker"}'
  ```
- **Resposta**:
  ```json
  {
    "id": 1,
    "title": "Estudar Docker",
    "completed": false
  }
  ```

---

### 2. Listar tarefas
- **Método**: `GET /tasks`
- **Status HTTP**: `200 OK`
- **Regras**: Retorna a lista de todas as tarefas cadastradas ordenadas por ID. Se não houver tarefas, retorna `[]`.
- **Exemplo de Requisição**:
  ```bash
  curl -X GET http://localhost:8000/tasks
  ```
- **Resposta**:
  ```json
  [
    {
      "id": 1,
      "title": "Estudar Docker",
      "completed": false
    }
  ]
  ```

---

### 3. Atualizar conclusão da tarefa
- **Método**: `PATCH /tasks/{id}`
- **Status HTTP**: `200 OK` (se encontrada) ou `404 Not Found` (se não existir)
- **Regras**: Altera estritamente o campo `completed` (`true` ou `false`). Não permite modificar título ou outros campos.
- **Exemplo de Requisição**:
  ```bash
  curl -X PATCH http://localhost:8000/tasks/1 \
    -H "Content-Type: application/json" \
    -d '{"completed": true}'
  ```
- **Resposta**:
  ```json
  {
    "id": 1,
    "title": "Estudar Docker",
    "completed": true
  }
  ```

---

## 🧪 Testes Automatizados e Cobertura

Os testes utilizam exclusivamente PostgreSQL através da base `tasks_test`. Cada teste é isolado por fixtures que limpam e resetam as sequências (`TRUNCATE TABLE tasks RESTART IDENTITY CASCADE`).

### Executar a suíte de testes

```bash
pytest -v
```

### Executar com relatório de cobertura

```bash
pytest --cov=app --cov-report=term-missing
```

### Validar cobertura mínima de 90% (critério de aprovação)

```bash
pytest --cov=app --cov-report=term-missing --cov-fail-under=90
```

---

## 📋 Cenários Cobertos pelos Testes

- [x] Criação de tarefa válida com ID sequencial e status inicial `completed = false`.
- [x] Criação de tarefa sem título (validação HTTP 422).
- [x] Criação de tarefa com título vazio `""` (validação HTTP 422).
- [x] Criação de tarefa com título contendo apenas espaços em branco `"   "` (validação HTTP 422).
- [x] Remoção automática de espaços excessivos nas bordas do título (*trim*).
- [x] Geração automática e sequencial de IDs.
- [x] Garantia de que envio de `completed = true` no POST é ignorado (sempre inicia `false`).
- [x] Listagem sem tarefas cadastradas retornando lista vazia `[]` com HTTP 200.
- [x] Listagem com múltiplas tarefas mantendo consistência e ordenação.
- [x] Validação estrutural de tipos e propriedades no retorno da listagem.
- [x] Atualização de `completed` para `true` com retorno HTTP 200.
- [x] Atualização de `completed` para `false` com retorno HTTP 200.
- [x] Tentativa de atualização de tarefa inexistente retornando HTTP 404 e mensagem `"Tarefa não encontrada"`.
- [x] Envio de dados inválidos (tipo não booleano ou corpo vazio) retornando HTTP 422.
- [x] Envio de ID inválido no caminho retornando HTTP 422.
- [x] Garantia de que envio de novos títulos no endpoint PATCH não altera o título original.
- [x] Teste de ciclo de vida e injeção do gerador de sessões do banco de dados (`get_db`).

