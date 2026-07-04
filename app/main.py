from fastapi import FastAPI


app = FastAPI (
    title = "TaskForge API",
    vesion = "0.1.0",
    description = "API para gerenciamento de tarefas com fluxo de revisão"
)

@app.get("/")
async def root():
    return{
        "message": "Welcome to TaskForge API",
        "status":"Runing",
    }