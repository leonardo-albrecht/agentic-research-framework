import os
import json
from groq import Groq
from app.tools import TOOLS, TOOLS_SCHEMA
from app.database import add_job_log

def pesquisar_topico(job_id: str, sub_query: str) -> str:
    """
    Executa um agente de pesquisa autônomo focado em resolver uma sub-consulta específica.
    Usa function calling nativo (ferramentas de busca e scraper) com controle de loops.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Chave de API GROQ_API_KEY não configurada.")
        
    client = Groq(api_key=api_key)
    
    SYSTEM_PROMPT = """Você é o Agente Pesquisador encarregado de coletar dados concretos na internet.
Sua missão é investigar o tópico solicitado usando as ferramentas disponíveis (pesquisar_web e extrair_conteudo_web) para fundamentar suas notas de pesquisa.

Diretrizes:
1. Sempre use `pesquisar_web` para encontrar links relevantes sobre o tópico.
2. Identifique os melhores links do resultado e use `extrair_conteudo_web` neles para ler o texto principal.
3. Colete dados reais (números, estatísticas, fatos históricos, fontes). Não invente nada.
4. Quando tiver coletado informações suficientes, escreva um resumo consolidado de fatos estruturados e sempre liste as URLs das fontes consultadas no final.
"""

    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": f"Investigue e colete notas detalhadas sobre: {sub_query}"}
    ]
    
    add_job_log(job_id, f"Pesquisador iniciou investigação de: '{sub_query}'")
    
    max_turnos = 5
    for turno in range(max_turnos):
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            tools=TOOLS_SCHEMA,
            tool_choice="auto",
            temperature=0.1
        )
        
        response_message = response.choices[0].message
        tool_calls = response_message.tool_calls
        
        if tool_calls:
            # Groq exige persistir a resposta com os tool_calls antes das respostas das ferramentas
            messages.append(response_message)
            
            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                
                add_job_log(job_id, f"Ativando tool: {tool_name}({list(tool_args.values())[0]})")
                
                # Executa a tool de forma dinâmica
                if tool_name in TOOLS:
                    try:
                        resultado = TOOLS[tool_name](**tool_args)
                    except Exception as e:
                        resultado = f"Erro ao executar a ferramenta: {str(e)}"
                else:
                    resultado = f"Erro: ferramenta '{tool_name}' desconhecida."
                
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "name": tool_name,
                    "content": resultado
                })
        else:
            # Se não há chamadas de ferramenta, temos o resumo das notas do pesquisador
            add_job_log(job_id, f"Notas coletadas para: '{sub_query}'")
            return response_message.content
            
    add_job_log(job_id, f"Aviso: Máximo de turnos alcançado na pesquisa de: '{sub_query}'")
    
    # Fallback para retornar a última resposta gerada
    for msg in reversed(messages):
        if msg.get("role") == "assistant" and msg.get("content"):
            return msg.get("content")
            
    return "Falha ao consolidar notas sobre o tópico."
