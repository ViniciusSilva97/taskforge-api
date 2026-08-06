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

## Estado da versão 0.3

A versão 0.3 adiciona identidade autenticada ao domínio:

- cadastro público em `POST /users/`, agora com senha;
- login em `POST /auth/token`, usando o e-mail no campo `username`;
- usuário autenticado em `GET /auth/me`;
- rotas protegidas por token Bearer;
- solicitante obtido do token, sem `requester_id` no JSON de criação;
- executor/revisor obtido do token, sem `actor_id` nos JSONs;
- listagem de tarefas limitada às tarefas solicitadas ou recebidas pelo usuário;
- consulta de tarefa e histórico restrita aos participantes;
- notificações disponíveis em `GET /tasks/notifications/me`;
- senha armazenada somente como hash Argon2;
- JWT assinado, com expiração configurável.

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
6. Cada usuário consulta somente as próprias notificações.
7. Token ausente, inválido ou expirado retorna `401`.
8. Usuário autenticado sem permissão retorna `403`.
9. Toda transição válida continua gerando histórico e notificações na mesma transação.

## Migração de dados

A migration `20260802_0002` adiciona `password_hash` aos usuários. Usuários criados na v0.2 recebem o valor `!unusable!`, preservando os registros, mas não conseguem autenticar. Como o projeto está em desenvolvimento, recomenda-se recriar esses usuários com senha após a migration ou limpar o volume de testes.

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

Validação da entrega: 11 testes automatizados aprovados; migration validada com `upgrade head` e `downgrade base`.

## Próximas entregas recomendadas

- refresh token e revogação de sessão;
- redefinição segura de senha;
- organizações/workspaces para isolamento entre empresas;
- marcação de notificações como lidas;
- paginação e filtros de tarefas.
