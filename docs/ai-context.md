# Contexto de Continuidade para IA — TaskForge API

## Objetivo do projeto

O TaskForge API é um sistema de tarefas inspirado em Issues e Pull Requests. O produto controla atribuição, execução, entrega, revisão, solicitação de ajustes, aprovação, notificações direcionadas e histórico de eventos.

## Papéis do projeto

- Vinicius atua como analista, testador e responsável pelas decisões de negócio.
- A IA atua como arquiteta e implementadora técnica, mantendo código, testes e documentação.

## Stack aprovada

- Python 3.14+
- FastAPI e Pydantic
- SQLAlchemy 2
- PostgreSQL 17
- Alembic
- uv
- Docker Compose para o banco local
- unittest e FastAPI TestClient

## Estado da versão 0.2

A aplicação deixa de usar armazenamento global em memória e passa a possuir persistência relacional.

Funcionalidades atuais:

- cadastro, listagem e consulta de usuários;
- e-mail de usuário único, normalizado em letras minúsculas;
- criação de tarefa apenas com solicitante e destinatários existentes;
- múltiplos destinatários sem duplicidade;
- workflow `ASSIGNED → IN_PROGRESS → IN_REVIEW`;
- aprovação ou solicitação de ajustes;
- histórico persistido para cada transição;
- notificações persistidas e direcionadas aos envolvidos;
- PostgreSQL no ambiente local via Docker Compose;
- migrations versionadas com Alembic;
- testes isolados em SQLite em memória.

## Arquitetura atual

```text
Router → Service → Repository → SQLAlchemy → Banco de dados
```

- Router: recebe HTTP, resolve dependências e converte erros de domínio em status HTTP.
- Schema: valida contratos de entrada e saída.
- Service: aplica regras de negócio e controla transações.
- Repository: concentra consultas e persistência.
- Model: representa as tabelas e relacionamentos SQLAlchemy.

## Regras de negócio preservadas

1. Toda tarefa possui um solicitante cadastrado.
2. Toda tarefa possui pelo menos um destinatário cadastrado.
3. E-mails de usuários são únicos sem diferenciar maiúsculas de minúsculas.
4. Apenas destinatários podem iniciar ou entregar a tarefa.
5. Apenas o solicitante pode pedir ajustes ou aprovar.
6. A tarefa precisa estar em andamento antes de ser entregue.
7. A tarefa precisa estar em revisão antes de ser aprovada ou devolvida.
8. Solicitar ajustes exige uma observação não vazia.
9. Na criação, somente os destinatários são notificados.
10. Na entrega, somente o solicitante é notificado.
11. Em ajustes ou aprovação, os destinatários são notificados.
12. Toda transição válida gera histórico.

## Como preparar o ambiente local

```powershell
git switch feat/users-postgres-v0.2.0
git pull origin feat/users-postgres-v0.2.0
uv sync
docker compose up -d db
uv run alembic upgrade head
uv run fastapi dev app/main.py
```

Swagger: `http://127.0.0.1:8000/docs`

## Como testar

```powershell
uv run python -m unittest discover -s tests -v
```

Resultado validado nesta etapa: 9 testes executados com sucesso.
A migration também foi validada com upgrade e downgrade em banco SQLite temporário.

## Limitações conhecidas

- Ainda não existe autenticação; `actor_id` continua sendo enviado no payload.
- Não existem senhas, papéis ou permissões globais de usuário.
- Notificações ainda não possuem endpoint para marcação como lidas.
- A API ainda roda localmente fora do Docker; somente o PostgreSQL foi containerizado nesta etapa.
- O arquivo `uv.lock` deve ser atualizado pelo `uv sync` após a inclusão das novas dependências.

## Próxima entrega recomendada

Validar a v0.2 com PostgreSQL real. Depois, implementar autenticação e substituir `actor_id` enviado pelo cliente pela identidade do usuário autenticado.
