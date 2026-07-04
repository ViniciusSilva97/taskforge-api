# Modelagem do Domínio - TaskForge API

## 1. Objetivo

Este documento descreve os principais conceitos do domínio do TaskForge API e como eles se relacionam .

O objetivo é entender o negócio antes de definir o banco de dados, endpoints ou código.

---

## 2. Entidades Principais

### Usuário

Representa uma pessoa que utiliza o sistema.

Um usuário pode:

- criar tarefas;
- receber tarefas;
- entregar tarefas;
- revisar tarefas;
- recebr notificações

---

### Tarefas 
Representa uma atividade que precisa ser executada.

Uma tarefa possui:
- título 
- descrição;
- criador;
- destinatário;
- status;
- prioridade;
- prazo;
- data de criação;
- data de atualização.

---

### Revisão
Representa a análise de uma tarefa entregue.

Uma revisão possui:
- Tarefa;
- revisor;
- decisão;
- observação;
- data da revisão.

Decisões possíveis;

- aprovada;
- ajustes solicitados.

---
### Notificações
Representa uma aviso enviado para usuários envolvidos na tarefa.

Uma notificação possui:
- usuários destinatário;
- tarefa realcionada;
- mensagem;
- tipo;
- status de leitura;
- data de criação.

---

### Histórico
Representa o registro de eventos importantes da tarefa.

Exeplos:
- tarefa criada;
- tarefa atribuída;
- status alterado;
- tarefa entregue;
- revisão criada;
- ajustes solicitados;
- tarefa aprovada.

---
## 3. Relacionamentos

```text
Usuário cria muitas tarefas
Usuário pode receber muitas tarefas
Tarefa pode ter muitos destinatários
Tarefa podeter muitas revisões
Tarefa pode ter muitsa notificações
Tarefa pode ter muitos registros de histórico
```
### Status da tarefa
```
CRIADA
ATRIBUIDA
EM_ANDAMENTO
ENTREGUE_PARA_REVISAO
EM_REVISAO
AJUSTES_SOLICITADOS
APROVADA
CANCELADA
```

### Fluxo principal
```
CRIADA -> ATRIBUIDA -> EM_ANDAMENTO -> ENTREGUE_PARA_REVISAO -> EM_REVISAO -> APROVADA
```

### 6. Fluxo com correção
```
EM_REVISAO -> AJUSTES_SOLICITADOS -> EM_ANDAMENTO -> ENTREGUE_PARA_REVISAO