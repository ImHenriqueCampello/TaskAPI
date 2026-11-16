# To-Do API - Gerenciamento de Tarefas

API REST para criar, listar e atualizar a conclusão de tarefas, desenvolvida para a disciplina de **Gerência de Configuração e Evolução de Software**.

Imagem no Docker Hub: [joaolucenalima/taskapi](https://hub.docker.com/r/joaolucenalima/taskapi).

## Tecnologias

Python, FastAPI, PostgreSQL, SQLAlchemy, Docker Compose, Jenkins, Pytest e pytest-cov.

## Preparação

Pré-requisitos: Git, Docker e Docker Compose. Para executar o Pytest, instale também Python 3.12. Os comandos abaixo usam um terminal Bash ou Zsh.

```bash
git clone https://github.com/ImHenriqueCampello/TaskAPI.git
cd TaskAPI
cp .env.example .env
```

Se já tiver o repositório, abra um terminal na pasta do projeto. Copie o `.env.example` apenas se ainda não houver um `.env`.

No `.env`, ajuste a conexão do banco de testes para a porta **5433**:

```env
TEST_DATABASE_URL=postgresql://postgres:postgres@localhost:5433/tasks_test
```

Se alterou o usuário ou a senha do PostgreSQL, ajuste também as credenciais dessa URL. Escolha o fluxo abaixo conforme a atividade.

## Testes

Crie e ative o ambiente virtual e instale as dependências:

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

Suba somente o banco de testes e execute o Pytest:

```bash
docker compose -f docker-compose.dev.yml up -d --wait postgres-test
python -m pytest --cov=app --cov=scripts --cov-report=term-missing --cov-fail-under=90
```

O serviço cria o banco temporário `tasks_test`, separado do banco da aplicação. As fixtures limpam as tarefas e reiniciam a sequência de IDs entre os testes. O Pytest inicia a API internamente pelo `TestClient`, sem precisar de um servidor separado, e exige cobertura mínima de **90%**.

### Cenários cobertos pelos testes

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

## Dev

Suba a API e o banco da aplicação pelo Docker:

```bash
docker compose -f docker-compose.dev.yml up -d --build --wait api postgres
```

Esse comando inicia somente a API na porta 8000 e o PostgreSQL da aplicação na porta 5432. Os dados da aplicação ficam em um volume persistente.

Acesse a documentação interativa em [Swagger UI](http://localhost:8000/docs).

## Jenkins

Para executar o pipeline, o `docker-compose.yml` sobe quatro serviços:

| Serviço | Origem | Função |
|---------|--------|--------|
| `jenkins` | Dockerfile local em `jenkins/` | Executar o pipeline |
| `api` | Imagem do Docker Hub | Disponibilizar a API |
| `postgres` | `postgres:16-alpine` | Armazenar os dados |
| `adminer` | Imagem do Adminer | Consultar o banco pelo navegador |

Antes de iniciar a stack completa, pare o Compose de desenvolvimento conforme o primeiro comando abaixo para liberar a porta 8000.

Use o `.env` criado anteriormente e configure:

| Variáveis | Finalidade |
|-----------|------------|
| `JENKINS_ADMIN_ID`, `JENKINS_ADMIN_PASSWORD` | Acesso ao Jenkins |
| `GIT_REPO_URL` | Repositório utilizado pelo job |
| `DOCKERHUB_REPO`, `DOCKERHUB_USERNAME`, `DOCKERHUB_TOKEN` | Repositório e credenciais para publicação |
| `NOTIFY_EMAIL` | Destinatário(s) das notificações |
| `SMTP_HOST`, `SMTP_PORT`, `SMTP_USER`, `SMTP_PASSWORD`, `SMTP_FROM` | Configuração do envio de e-mail |
| `DOCKER_GID` | Grupo de acesso ao Docker; no Linux, use o resultado de `stat -c %g /var/run/docker.sock` |

```bash
docker compose -f docker-compose.dev.yml down
docker compose up -d --build
```

- [Jenkins](http://localhost:8080): acesso com as credenciais do `.env`; job `taskapi` criado automaticamente.
- [API / Swagger UI](http://localhost:8000/docs).
- [Adminer](http://localhost:8081): selecione PostgreSQL, servidor `postgres` e credenciais do banco no `.env`.

Os serviços se comunicam pelo nome na rede do Compose. Os volumes `postgres_data` e `jenkins_home` preservam os dados do banco e do Jenkins. O Compose configura o banco de testes do pipeline em `postgres:5432/tasks_test`, independentemente da URL local usada nos testes.

### Pipeline

O Jenkins é configurado como código por `jenkins/casc.yaml`. O `Jenkinsfile` executa:

1. Checkout do repositório.
2. Instalação das dependências em ambiente virtual.
3. Validação com `compileall`.
4. Testes com cobertura mínima de 90% e geração de relatórios JUnit e cobertura XML/HTML.
5. Build da imagem Docker e do pacote `dist/taskapi-<build>-<commit>.tar.gz`.
6. Publicação no Docker Hub somente na branch `main`, com tags `latest` e `<build>-<commit>`.
7. Tentativa de notificação por e-mail após a execução, tanto em sucesso quanto em falha. Falhas no envio não reprovam o build.

Os arquivos de `dist/` e `reports/` são arquivados como artefatos de cada build.

## Endpoints

| Método | Rota | Finalidade | Status HTTP |
|--------|------|------------|-------------|
| POST | `/tasks` | Criar tarefa com título obrigatório e `completed = false` | 201; 422 para dados inválidos |
| GET | `/tasks` | Listar tarefas por ID; retorna `[]` se não houver tarefas | 200 |
| PATCH | `/tasks/{id}` | Atualizar somente `completed` | 200; 404 se inexistente; 422 para dados inválidos |

O título é salvo sem espaços nas bordas e não pode ser vazio. O PATCH recebe o campo `completed` e preserva o título.

Exemplo de criação:

```bash
curl -X POST http://localhost:8000/tasks \
  -H "Content-Type: application/json" \
  -d '{"title": "Estudar Docker"}'
```

Consulte os corpos de requisição e resposta e experimente os três endpoints no [Swagger UI](http://localhost:8000/docs).

## Uso de Inteligência Artificial

No desenvolvimento deste projeto, foram utilizadas ferramentas de Inteligência Artificial como suporte:

- **ChatGPT**: Utilizado para *brainstorming* e concepção inicial das ideias do projeto.
- **Gemini 3.8 Flash**: Utilizado como assistente no desenvolvimento da API, configuração dos testes e documentação.
- **Codex**: Implementação do processo do Jenkins e configuração dos arquivos do Docker.
- **Claude**: Implementação do envio de e-mail e integração do Docker Compose.
