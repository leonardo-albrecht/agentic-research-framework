import os
import json
from groq import Groq

def planejar_pesquisa(pergunta: str) -> list[str]:
    """
    Analisa a pergunta principal do usuário e a divide em 3 a 5 sub-consultas (queries) 
    específicas para busca na internet, estruturadas como um objeto JSON.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Chave de API GROQ_API_KEY não configurada nas variáveis de ambiente.")
        
    client = Groq(api_key=api_key)
    
    prompt = f"""Você é o Planejador da equipe de agentes de pesquisa.
Sua missão é ler a pergunta do usuário e planejar a pesquisa quebrando-a em 3 a 5 tópicos (sub-consultas) específicos e focados para serem pesquisados individualmente na web.

Pergunta original: "{pergunta}"

Responda OBRIGATORIAMENTE com um objeto JSON válido contendo apenas uma chave "sub_queries" que mapeia para uma lista de strings.

Exemplo de formato esperado:
{{
  "sub_queries": [
    "Histórico e fundação da empresa X",
    "Modelo de monetização da empresa X",
    "Principais concorrentes e market share da empresa X"
  ]
}}
"""

    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1,
        response_format={"type": "json_object"}
    )
    
    try:
        dados = json.loads(response.choices[0].message.content)
        queries = dados.get("sub_queries", [])
        if not queries:
            return [pergunta]
        return queries
    except Exception:
        # Fallback caso a decodificação de JSON falhe por algum motivo
        return [pergunta]
