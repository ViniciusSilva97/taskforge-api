# Modelagem do banco de dados - TaskForge API

## 1. Objetivo

Este documento descreve a primeira versão da estrutura de dados do TaskForge API.

A modelagem ainda pode evoluir conforme o projeto avançar.

---

## 2. Tabelas iniciais

### users 
Representa os usuários do sistema 

|Campo|Tipo|Observação|
|---|---|---|
|id|UUID|Identificador único|
|name|VARCHAR|Nome do usuário|
|email|VARCHAR|E-mail único|
|password_hash|VARCHAR|senha criptografada|
|created_at|TIMESTAMP|Data de criação|
|update_at|TIMESTAMP|Data de atualização|

---

### tasks

Representa as tarefas.
|Campo|Tipo|Observação|
|---|---|---|
|id|UUID|identificador único|
|title|VARCHAR|Título da tarefa|
|description|TEXT|Descrição|
|creator_id|UUID|Usuário que criou|
|status|VARCHAR|Status atual|
|priority|VARCHAR|Prioridade|
|due_date|DATE|Prazo|
|created_at|TIMESTAMP|Data de criação|
|updated_at|TIMESTAMP|Data de atualização|

---

### task_assignees

Relaciona tarefas e destinatários.

|Campo|Tipo|Observação|
|---|---|---|
|task_id|UUID|Tarefa|
|user_id|UUID|Usuário destinatário|

---

### task_reviews

Representa revisões das tarefas.
|Campo|Tipo|Observação|
|---|---|---|
|id|UUID|Identificador único|
|task_id|UUID|Tarefa revisada|
|reviewer_id|UUID|Usuário revisor|
|decision|VARCHAR|APPROVED ou CHANGES_REQUESTED|
|comment|TEXT|Observação da revisão|
|created_at|TIMESTAMP|Data da revisão|

---

### notifications

Representa notificações enviadas aos usuários.
|Campo|Tipo|Observação|
|---|---|---|
|id|UUID|Identificador único|
|user_id|UUID|usuário notificado|
|task_id|UUID|Tarefa relacionada|
|message|TEXT|Mensagem|
|type|VARCHAR|Tipo da notificação|
|read_at|TIMESTAMP|Data de leitura|
|created_at|TIMESTAMP|Data de criação|

---
### task_history

Registra eventos importantes da tarefa
|Campo|Tipo|Observação|
|---|---|---|
|id|UUID|Identificador único|
|task_id|UUID|Tarefa|
|actor_id|UUID|Usuário que realizou a ação|
|event_type|VARCHAR|Tipo do envento|
|description|TEXT|Descrição do evento|
|created_at|TIMESTAMP|Data do evento|

---
## 3. Relacionamentos
```text
users 1:N tasks
users N:N tasks através de task_assignees
tasks 1:N task_reviews
tasks 1:N notifications
tasks 1:N task_history
```


