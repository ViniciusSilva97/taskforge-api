# Contexto de Continuidade para IA — TaskForge API

## Objetivo do projeto

O TaskForge API é um sistema de tarefas com fluxo inspirado em GitHub Issues e Pull Requests. O produto permite atribuição, execução, entrega, revisão, solicitação de ajustes, aprovação, notificações direcionadas e histórico de eventos.

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

A versão em desenvolvimento utiliza armazenamento temporário em memória e implementa:

- verificação de saúde em `GET /`;
- criação e atribuição de tarefa em `POST /tasks/`;
- listagem em `GET /tasks/`;
- busca em `GET /tasks/{task_id}`;
- início da execução em `POST /tasks/{task_id}/start`;
- entrega para revisão em `POST /tasks/{task_id}/submit`;
- solicitação de ajustes em `POST /tasks/{task_id}/request-changes`;
- aprovação em `POST /tasks/{task_id}/approve`;
- histórico em `GET /tasks/{task_id}/history`;
- notificações por usuário em `GET /tasks/users/{user_id}/notifications`;
- validação de títulos, IDs e observações de correção;
- testes automatizados cobrindo o fluxo principal e cenários de erro.

## Estados atuais da tarefa

```text
ASSIGNED
   ↓
IN_PROGRESS
   ↓
IN_REVIEW
   ├──→ APPROVED
   └──→ CHANGES_REQUESTED → IN_PROGRESS
```

## Regras de negócio preservadas

1. Toda tarefa possui um solicitante (`requester_id`).
2. Toda tarefa possui um ou mais destinatários (`assignee_ids`).
3. IDs repetidos de destinatários são removidos durante a validação.
4. Apenas destinatários podem iniciar ou entregar a tarefa.
5. Apenas o solicitante pode pedir ajustes ou aprovar.
6. A tarefa precisa estar em andamento antes de ser entregue.
7. A tarefa precisa estar em revisão antes de ser aprovada ou devolvida.
8. Solicitar ajustes exige uma observação não vazia.
9. Quando criada, somente os destinatários são notificados.
10. Quando entregue, somente o solicitante é notificado.
11. Quando ajustes são solicitados ou a entrega é aprovada, os destinatários são notificados.
12. Toda transição válida gera histórico.
13. Router trata HTTP, schema valida contratos e service concentra regras de negócio.

## Respostas HTTP relevantes

- `201`: tarefa criada;
- `403`: usuário sem permissão para a ação;
- `404`: tarefa inexistente;
- `409`: transição incompatível com o estado atual;
- `422`: payload inválido.

## Limitações conhecidas

- Os usuários são representados apenas por IDs; ainda não existe cadastro ou autenticação.
- Não há banco de dados; os dados são perdidos ao reiniciar a aplicação.
- Notificações são apenas registros internos, sem e-mail, push ou WebSocket.
- O serviço é instanciado globalmente no router, adequado somente ao protótipo em memória.
- Ainda não há marcação de notificação como lida.

## Como executar

```powershell
uv sync
uv run fastapi dev app/main.py
```

## Como testar

```powershell
uv run python -m unittest discover -s tests -v
```

Resultado validado nesta etapa: 9 testes executados com sucesso.

## Próxima entrega recomendada

Concluir a validação manual deste workflow e, depois, introduzir PostgreSQL com SQLAlchemy e Alembic. A persistência deverá preservar as mesmas regras públicas do service e os contratos atuais da API.
