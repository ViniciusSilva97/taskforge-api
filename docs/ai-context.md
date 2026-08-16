# Contexto de Continuidade para IA — TaskForge API

## Objetivo do projeto

O TaskForge API é um sistema de tarefas inspirado em Issues e Pull Requests. A aplicação permite cadastro de usuários, autenticação, atribuição, execução, entrega, revisão, solicitação de ajustes, aprovação, notificações e histórico persistente.

## Papéis do projeto

- Vinicius atua como analista, testador e responsável pelas decisões de negócio.
- A IA atua como arquiteta e implementadora técnica, mantendo código, testes e documentação.

## Stack atual

- Python 3.14+
- FastAPI
- Pydantic
- SQLAlchemy 2
- PostgreSQL 17
- Alembic
- OAuth2 Password Bearer
- JWT com PyJWT
- Argon2 com argon2-cffi
- Docker Compose
- uv

## Estado da versão 0.4

A versão 0.4 melhora a consulta e o acompanhamento operacional:

- listagem paginada de tarefas em `GET /tasks/`;
- filtros por status e participação (`all`, `requested` e `assigned`);
- ordenação das tarefas mais recentes primeiro;
- listagem paginada de notificações em `GET /tasks/notifications/me`;
- filtro `unread_only` para notificações não lidas;
- marcação individual em `PATCH /tasks/notifications/{notification_id}/read`;
- marcação em massa em `PATCH /tasks/notifications/read-all`;
- isolamento de notificações pelo usuário autenticado;
- respostas paginadas com `items`, `total`, `limit` e `offset`;
- suíte ampliada para 15 testes automatizados.

## Contratos de consulta

### Tarefas

`GET /tasks/` aceita:

- `status`: `ASSIGNED`, `IN_PROGRESS`, `IN_REVIEW`, `CHANGES_REQUESTED` ou `APPROVED`;
- `role`: `all`, `requested` ou `assigned`;
- `limit`: entre 1 e 100, padrão 20;
- `offset`: inteiro não negativo, padrão 0.

A resposta segue:

```json
{
  "items": [],
  "total": 0,
  "limit": 20,
  "offset": 0
}
```

### Notificações

`GET /tasks/notifications/me` aceita:

- `unread_only`: padrão `false`;
- `limit`: entre 1 e 100, padrão 20;
- `offset`: inteiro não negativo, padrão 0.

Somente o destinatário pode listar ou marcar uma notificação como lida. A tentativa de acessar uma notificação de outro usuário retorna `404`, evitando revelar sua existência.

## Fluxo da tarefa

```text
ASSIGNED
   ↓
IN_PROGRESS
   ↓
IN_REVIEW
   ├──→ APPROVED
   └──→ CHANGES_REQUESTED → IN_PROGRESS
```

## Regras de segurança preservadas

1. A senha nunca aparece nos schemas de resposta.
2. O backend não aceita identidade informada no payload para ações protegidas.
3. Somente destinatários podem iniciar e entregar uma tarefa.
4. Somente o solicitante pode aprovar ou pedir ajustes.
5. Somente participantes podem consultar a tarefa e seu histórico.
6. Cada usuário consulta e altera somente as próprias notificações.
7. Token ausente, inválido ou expirado retorna `401`.
8. Usuário autenticado sem permissão retorna `403`.
9. Toda transição válida continua gerando histórico e notificações na mesma transação.
10. Filtros e paginação são aplicados depois do isolamento por participante.

## Banco de dados

A v0.4 não exige nova migration. O campo `notifications.is_read` já existe desde a migration inicial.

## Variáveis de ambiente

- `DATABASE_URL`
- `JWT_SECRET_KEY` — deve possuir pelo menos 32 bytes e ser trocada fora do desenvolvimento;
- `JWT_ALGORITHM` — padrão `HS256`;
- `ACCESS_TOKEN_EXPIRE_MINUTES` — padrão `60`.

## Como executar

```powershell
uv sync
docker compose up -d db
uv run alembic upgrade head
uv run fastapi dev app/main.py
```

## Como testar

```powershell
uv run python -m unittest discover -s tests -v
```

Meta da entrega: 15 testes automatizados, incluindo paginação, filtros, ciclo de leitura de notificações e isolamento entre usuários.

## Próximas entregas recomendadas

- refresh token e revogação de sessão;
- redefinição segura de senha;
- organizações/workspaces para isolamento entre empresas;
- busca textual de tarefas;
- prioridades, prazos e responsáveis principais.
