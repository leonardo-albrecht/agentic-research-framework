# Agente com Memória

Agente inteligente com memória de conversa e ferramentas reais, exposto via API REST.

## O problema que resolve
LLMs não têm memória nativa — cada chamada começa do zero.
Este agente mantém histórico de conversa por sessão e executa
ações reais no mundo (cotações, data/hora) antes de responder.

## Decisões de engenharia

**Memória por sessão**
Cada sessão tem seu próprio histórico isolado. Múltiplos
usuários simultâneos não interferem entre si.

**ReAct pattern**
O agente entra em loop: raciocina → age (tool) → observa → 
raciocina de novo. Só responde ao usuário quando tem
informação suficiente.

**Tools como dicionário**
O LLM retorna o nome da tool em JSON. O dicionário mapeia
nome → função e executa dinamicamente — sem if/elif por tool.

## Stack
- FastAPI
- Groq (LLaMA 3.3 70B)
- Python

## Como rodar

```bash
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Acesse: http://localhost:8000/docs

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| GET | /health | Status da API |
| POST | /chat | Conversa com memória |
| DELETE | /sessao/{id} | Limpa sessão |

## Exemplo de uso

```json
POST /chat
{
  "sessao_id": "usuario_123",
  "mensagem": "Qual a cotação do dólar agora?"
}

Resposta:
{
  "resposta": "A cotação atual do dólar é R$ 5.01.",
  "mensagens_no_historico": 5
}
```

## Próximos passos
- [ ] Adicionar mais tools (clima, notícias, busca web)
- [ ] Persistência de sessões em banco de dados
- [ ] Autenticação por usuário
- [ ] Deploy com Docker