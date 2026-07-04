# Requisitos - TaskForge API

## Requisitos funcionais (RF)

### RF001 - Gerenciamento de usuários
- O Sistema deve permitir o cadastro de usuários.

### RF002 - Autenticação 
- O sistema deve permitir que usuários autenticados acessem a API.

### RF003 - Criação de tarefas
- O sistema deve permitir que um usuário crie tarefas.

### RF004 - Atribuição
- O sistema deve permitir atribuir uma tarefa para um ou mais usuários.

### RF005 - Consulta
- O sistema deve permitir listar e consultar tarefas.

### RF006 - Atualização
- O sistema deve permitir atualizar informações de uma tarefa.

### RF007 - Alteração de status
- O sistema deve permitir alterar o status da tarefa de acordo com o fluxo definido

### RF008 - Revisão
- O sistema deve permitir revisar tarefas entregues.

### RF009 - Observações
- Osistema deve permitir registrar observações durante uma revisão.

### RF010 - Histórico
- O sistema deve manter um histórico das alterações realizadas em cada tarefa.

### RF011 - Notificações
- O sistema deve notificar apenas os usuários envolvidos na tarefa.

## Regras de Negócio (RN)

### RN001 
- Toda tarefa deve possuir um criador.

### RN002
- Toda tarefa deve possuir pelo menos um destinatário.

### RN003
- Somente o criador poderá aprovar a entrega da tarefa.

### RN004 
- Uma tarefa entregue deve obrigatoriamente passar por revisão antes de ser considerada concluída.

### RN005
- Caso a revisão solicite ajustes, a tarefa deverá retornar ao responsável pela execução.

### RN006
- Toda alteração relevante deverá ser resgistrada no histórico.

## Requisitos não funcionais (RNF)

### RNF001
- A API deverá seguir o padrão REST

### RNF002
- A autenticação deverá utilizar JWT.

### RNF0003 
- A documentação deverá ser disponibilizada automaticamente pelo FastAPI

### RNF004 
- O banco de dados utilizado será PostgreSQL.

### RNF005
- O projeto deverá utilizar docker para facilitar a execução em diferentes ambientes

### RNF006
- O código deverá seguir boas práticas de organização, legibilidade e documentação

### RNF007
- Os sistemas automatizados deverão ser implementados gradualmente conforme as funcionalidades forem desenvolvidas
