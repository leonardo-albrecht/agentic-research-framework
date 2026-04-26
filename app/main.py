from fastapi import FastAPI
from pydantic import BaseModel
from app.agent import executar_agente, SYSTEM_PROMPT
from app.memory import Memory

app = FastAPI(
    title="Agente com Memória",
    description="Agente inteligente com tools e histórico de conversa",
    version="1.0.0"
)

sessoes: dict[str, Memory] = {}

class MensagemRequest(BaseModel):
    sessao_id: str
    mensagem: str

class MensagemResponse(BaseModel):
    resposta: str
    mensagens_no_historico: int

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post("/chat", response_model=MensagemResponse)
def chat(request: MensagemRequest):
    if request.sessao_id not in sessoes:
        sessoes[request.sessao_id] = Memory(system_prompt=SYSTEM_PROMPT)

    memoria = sessoes[request.sessao_id]
    resposta = executar_agente(request.mensagem, memoria)

    return MensagemResponse(
        resposta=resposta,
        mensagens_no_historico=len(memoria.get_historico())
    )

@app.delete("/sessao/{sessao_id}")
def deletar_sessao(sessao_id: str):
    if sessao_id in sessoes:
        del sessoes[sessao_id]
        return {"status": "sessão deletada"}
    return {"status": "sessão não encontrada"}