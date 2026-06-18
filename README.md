# Agentic Research Framework

Orquestrador de pesquisa multi-agente assíncrono com ferramentas reais e interface interativa.

## O problema que resolve
Pesquisas detalhadas na web tomam muito tempo para abrir guias, filtrar anúncios, ler textos longos e sintetizar as descobertas.
Este framework divide a busca em sub-tópicos, pesquisa de forma autônoma na internet (incluindo transcrições do YouTube) e consolida um relatório executivo final formatado em Markdown com fontes reais.

## Decisões de engenharia

**Orquestração Multi-Agente em Fases**
O fluxo de trabalho é dividido em agentes especializados (Planner, Researcher e Writer) operando de forma assíncrona, o que otimiza o uso de contexto do LLM e garante relatórios de melhor qualidade.

**Human-in-the-Loop (Editor Interativo)**
O pipeline pausa na fase de planejamento, abrindo um editor visual para que o usuário possa refinar, deletar ou adicionar novos tópicos antes que as buscas na internet comecem.

**Hot-Reload de Variáveis (.env)**
O arquivo de configuração `.env` é recarregado a cada nova chamada. Isso permite atualizar ou corrigir sua chave `GROQ_API_KEY` na mesma hora, sem precisar reiniciar o servidor backend.

**Banco de Dados Local (SQLite)**
Os estados dos jobs (fila de tarefas), logs em tempo real do terminal e o conteúdo dos relatórios são mantidos salvos localmente.

## Stack
- FastAPI
- Groq (LLaMA 3.3 70B)
- Python
- SQLite
- Scrapers (BeautifulSoup, DuckDuckGo Search, youtube-transcript-api)

## Como rodar

```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000
```

Acesse a interface no navegador: http://localhost:8000

## Endpoints

| Método | Rota | Descrição |
|--------|------|-----------|
| POST | /api/research | Planeja a pesquisa inicial e retorna o `job_id` |
| POST | /api/research/{job_id}/approve | Aprova e dispara as sub-queries de busca na web |
| GET | /api/research/{job_id} | Consulta logs em tempo real, status e o relatório final |

## Exemplo de uso

```json
POST /api/research
{
  "query": "Evolução do modelo de negócios do Slack nos últimos anos"
}

Resposta:
{
  "job_id": "c22fa968-3469-4100-85e7-4656ab9d9774",
  "status": "PENDING"
}
```

## Próximos passos
- [ ] Integração com banco de dados vetorial para consulta de pesquisas anteriores
- [ ] Botão de download do relatório final em PDF
- [ ] Tradução automática de legendas do YouTube em outros idiomas
- [ ] Containerização da aplicação com Docker
