from groq import Groq
from app.memory import Memory
from app.tools import TOOLS
from dotenv import load_dotenv
import os
import json

load_dotenv()

client = Groq(api_key=os.getenv("GROQ_API_KEY"))

SYSTEM_PROMPT = """Você é um agente de pesquisa inteligente.

Você tem acesso às seguintes ferramentas:
- buscar_cotacao_dolar: busca a cotação atual do dólar
- buscar_data_hora: retorna a data e hora atual

Quando precisar usar uma ferramenta, responda APENAS com JSON neste formato:
{"tool": "nome_da_ferramenta"}

Quando tiver a informação necessária para responder, responda normalmente em português.
Nunca invente informações — use as ferramentas quando precisar de dados reais."""

def executar_agente(pergunta: str, memoria: Memory) -> str:
    memoria.adicionar_mensagem("user", pergunta)

    while True:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=memoria.get_historico(),
            temperature=0.1
        )

        resposta = response.choices[0].message.content

        # verifica se o agente quer usar uma tool
        try:
            dados = json.loads(resposta)
            nome_tool = dados.get("tool")

            if nome_tool and nome_tool in TOOLS:
                print(f"[agente usando tool: {nome_tool}]")
                resultado = TOOLS[nome_tool]()
                memoria.adicionar_mensagem("assistant", resposta)
                memoria.adicionar_mensagem("user", f"Resultado da tool: {resultado}")
                continue  # volta pro loop pra processar o resultado

        except json.JSONDecodeError:
            pass  # não é JSON, é resposta final

        # resposta final
        memoria.adicionar_mensagem("assistant", resposta)
        return resposta