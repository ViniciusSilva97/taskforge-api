#Visão do Projeto - TaskForge API

## 1.Objetivo

O **TaskForge API** é uma API para gerenciamento de tarefas com fluxo de atribuição, entrega e revisão.

Diferente de uma lista simples de tarefas, o sistema será inspirado em conceitos do GitHub, com issues, pull requests, revisões, comentários e histórico de alterações.

## 2. Problema 

Empresas e equipes pequenas muitas vezes perdem o controle sobre:
- quem solicitou uma tarefa;
- quem deve executar;
- qual é o prazo;
- se a tarefa foi entregue;
- se precisa de correção;
- quais observações foram feitas;
- qual é o histórico da atividade;

## 3. Solução proposta

Criar um API que permita coontrolar tarefas com um fluco claro:

```text 
CRIADA -> ATRIBUIDA -> EM_ANDAMENTO -> ENTREGUE_PARA_REVISAO -> EM_REVISAO -> APROVADA

EM_REVISAO -> AJUSTES_SOLICITADOS -> EM_ANDAMENTO -> ENTREGUE_PARA_REVISAO
