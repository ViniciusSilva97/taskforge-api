# Contexto de Continuidade para IA — TaskForge API

## Objetivo do projeto

O TaskForge API é um sistema de tarefas com fluxo inspirado em GitHub Issues e Pull Requests. O produto deverá permitir atribuição, entrega, revisão, solicitação de ajustes, aprovação, notificações direcionadas e histórico de eventos.

## Papéis do projeto

- Vinicius atua como analista, testador e responsável pelas decisões de negócio.
- A IA atua como arquiteta e implementadora técnica, mantendo código, testes e documentação.

## Stack aprovada

- Python 3.14+
- FastAPI
- Pydantic
- uv
- PostgreSQL, SQLAlchemy e Alembic em etapas futuras
- Docker em etapa futura

## Estado atual

A versão 0.1 implementa uma API mínima com armazenamento temporário em memória:

- verificação de saúde em `GET /`;
- criação de tarefa em `POST /tasks/`;
- listagem em `GET /tasks/`;
- busca por identificador em `GET /tasks/{task_id}`;
- validação e normalização do título;
- status inicial `CREATED`;
- resposta 404 para tarefa inexistente;
- testes de comportamento com `unittest` e `TestClient`.

## Decisões que devem ser preservadas

1. Router recebe HTTP, mas não concentra regra de negócio.
2. Schema valida e normaliza o contrato de entrada e saída.
3. Service concentra o comportamento da aplicação.
4. Persistência em memória é temporária e será substituída por repository + PostgreSQL.
5. Somente usuários envolvidos deverão receber notificações.
6. A entrega deverá passar por revisão antes da conclusão.
7. Ajustes solicitados devem devolver a tarefa ao responsável.
8. Mudanças importantes deverão gerar histórico.

## Limitações conhecidas

- Não há usuários ou autenticação.
- Não há banco de dados; os dados são perdidos ao reiniciar a aplicação.
- Não há atribuição, entrega, revisão, notificações ou histórico.
- O serviço é instanciado globalmente no router, adequado apenas para esta etapa inicial.

## Como executar

```powershell
uv sync
uv run fastapi dev app/main.py
```

## Como testar

```powershell
uv run python -m unittest discover -s tests -v
```

## Próxima entrega recomendada

Introduzir a entidade de usuário e modelar criador e destinatários da tarefa antes de implementar o fluxo de entrega e revisão.
