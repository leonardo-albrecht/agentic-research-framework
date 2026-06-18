import os
import uuid
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, FileResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from app.database import create_job, update_job_status, add_job_log, get_job, update_job_sub_queries
from app.agents.planner import planejar_pesquisa
from app.agents.researcher import pesquisar_topico
from app.agents.writer import redigir_relatorio

load_dotenv()

app = FastAPI(
    title="Agentic Research Framework",
    description="Framework multi-agente assíncrono de pesquisa local utilizando SQLite e Groq.",
    version="2.0.0"
)

# Garante que a pasta estática existe
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
os.makedirs(STATIC_DIR, exist_ok=True)

# Monta a rota de arquivos estáticos
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

class ResearchRequest(BaseModel):
    query: str

class ApproveRequest(BaseModel):
    sub_queries: list[str]

class ResearchStatusResponse(BaseModel):
    job_id: str
    query: str
    status: str
    logs: list[str]
    report_content: str | None = None
    sub_queries: list[str] | None = None
    created_at: str

def rodar_planejamento(job_id: str, query: str):
    """
    FASE 1: Executa o agente planejador, salva as sub-queries geradas
    e muda o status do job para AWAITING_APPROVAL.
    """
    try:
        load_dotenv(override=True)
        update_job_status(job_id, "PLANNING")
        add_job_log(job_id, "Iniciando fase de planejamento do escopo da pesquisa...")
        
        sub_queries = planejar_pesquisa(query)
        
        update_job_sub_queries(job_id, sub_queries)
        add_job_log(job_id, f"Planejamento concluído. Sub-consultas sugeridas: {sub_queries}")
        add_job_log(job_id, "Aguardando aprovação ou edição do escopo pelo usuário...")
        
        update_job_status(job_id, "AWAITING_APPROVAL")
    except Exception as e:
        update_job_status(job_id, "FAILED")
        add_job_log(job_id, f"ERRO CRÍTICO NO PLANEJAMENTO: {str(e)}")

def rodar_pesquisa_e_escrita(job_id: str, query: str, sub_queries: list[str]):
    """
    FASE 2: Executa as buscas e leitura da web, depois compila o relatório.
    """
    try:
        load_dotenv(override=True)
        update_job_status(job_id, "RESEARCHING")
        add_job_log(job_id, f"Iniciando investigações para os {len(sub_queries)} tópicos aprovados...")
        
        notas_coletadas = []
        for idx, sq in enumerate(sub_queries, 1):
            add_job_log(job_id, f"Iniciando sub-pesquisa {idx}/{len(sub_queries)}: '{sq}'")
            notas = pesquisar_topico(job_id, sq)
            notas_coletadas.append({"query": sq, "notes": notas})
            add_job_log(job_id, f"Sub-pesquisa {idx} finalizada.")
            
        # FASE 3: Redação do Relatório
        update_job_status(job_id, "WRITING")
        add_job_log(job_id, "Agentes de pesquisa concluíram as investigações. Enviando notas para o Redator...")
        relatorio_markdown = redigir_relatorio(job_id, query, notas_coletadas)
        
        # Conclusão
        update_job_status(job_id, "COMPLETED", report_content=relatorio_markdown)
        add_job_log(job_id, "Processo concluído com sucesso. Relatório disponível para download.")
        
    except Exception as e:
        update_job_status(job_id, "FAILED")
        add_job_log(job_id, f"ERRO CRÍTICO NO PIPELINE: {str(e)}")

@app.get("/", response_class=HTMLResponse)
def index():
    """Rota raiz que serve a página do dashboard frontend."""
    index_html = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(index_html):
        return FileResponse(index_html)
    return HTMLResponse("<h1>Front-end em construção. Acesse /docs para ver a API.</h1>")

@app.post("/api/research")
def iniciar_pesquisa(request: ResearchRequest, background_tasks: BackgroundTasks):
    """Dispara o planejamento inicial em segundo plano, retornando o ID do Job."""
    if not request.query.strip():
        raise HTTPException(status_code=400, detail="A consulta não pode ser vazia.")
        
    job_id = str(uuid.uuid4())
    create_job(job_id, request.query)
    
    # Executa apenas a fase de planejamento em background inicialmente
    background_tasks.add_task(rodar_planejamento, job_id, request.query)
    
    return {"job_id": job_id, "status": "PENDING"}

@app.post("/api/research/{job_id}/approve")
def aprovar_pesquisa(job_id: str, request: ApproveRequest, background_tasks: BackgroundTasks):
    """Aprova e opcionalmente edita a lista de sub-queries para iniciar a pesquisa."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job de pesquisa não encontrado.")
        
    if job["status"] != "AWAITING_APPROVAL":
        raise HTTPException(status_code=400, detail="Este trabalho não está no estado de aprovação.")
        
    if not request.sub_queries:
        raise HTTPException(status_code=400, detail="A lista de sub-consultas aprovadas não pode ser vazia.")
        
    # Salva a lista final/editada de sub-queries no banco de dados
    update_job_sub_queries(job_id, request.sub_queries)
    add_job_log(job_id, f"Escopo de pesquisa aprovado pelo usuário com {len(request.sub_queries)} tópicos.")
    
    # Inicia a pesquisa e escrita em background
    background_tasks.add_task(rodar_pesquisa_e_escrita, job_id, job["query"], request.sub_queries)
    
    return {"status": "RESEARCHING"}

@app.get("/api/research/{job_id}", response_model=ResearchStatusResponse)
def obter_status(job_id: str):
    """Consulta o progresso, logs, sub-queries e resultado final de um Job."""
    job = get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job de pesquisa não encontrado.")
        
    return ResearchStatusResponse(
        job_id=job["id"],
        query=job["query"],
        status=job["status"],
        logs=job["logs"],
        report_content=job["report_content"],
        sub_queries=job.get("sub_queries"),
        created_at=job["created_at"]
    )