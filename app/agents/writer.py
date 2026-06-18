import os
from groq import Groq
from app.database import add_job_log

def redigir_relatorio(job_id: str, query_original: str, notas_pesquisa: list[dict]) -> str:
    """
    Lê o histórico de notas de pesquisa de todas as sub-queries e compila
    um relatório executivo final estruturado em Markdown com referências reais.
    """
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise ValueError("Chave de API GROQ_API_KEY não configurada.")
        
    client = Groq(api_key=api_key)
    
    # Agrupa as notas coletadas para passar no contexto do redator
    compilado_notas = ""
    for idx, item in enumerate(notas_pesquisa, 1):
        compilado_notas += f"--- TÓPICO {idx}: {item['query']} ---\n"
        compilado_notas += f"Notas:\n{item['notes']}\n\n"
        
    SYSTEM_PROMPT = """Você é o Redator Técnico da equipe de agentes.
Sua tarefa é ler todas as notas brutas coletadas pelo Pesquisador e transformá-las em um relatório executivo final de altíssimo nível.

Instruções:
1. Comece com um título principal descritivo (# Título).
2. Adicione uma seção de 'Resumo Executivo' contendo as conclusões chave da pesquisa.
3. Desenvolva seções e subseções claras para os diferentes aspectos da pesquisa.
4. Organize dados comparativos em tabelas em Markdown para facilitar a leitura.
5. No fim do documento, crie uma seção '## Referências e Fontes' contendo os links reais encontrados nas notas de pesquisa (nunca invente links que não constavam nas notas).
6. Mantenha um tom profissional, direto e imparcial.
"""

    prompt = f"""Pergunta original do usuário: "{query_original}"

Notas coletadas pelo pesquisador na internet:
{compilado_notas}
"""

    add_job_log(job_id, "Redator iniciou a escrita do relatório em Markdown...")
    
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2
    )
    
    relatorio = response.choices[0].message.content
    add_job_log(job_id, "Relatório executivo finalizado com sucesso.")
    return relatorio
