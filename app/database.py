import sqlite3
import os
import json
from datetime import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "db.sqlite")

def get_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    """Inicializa as tabelas do banco de dados SQLite."""
    with get_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id TEXT PRIMARY KEY,
                query TEXT NOT NULL,
                status TEXT NOT NULL,
                report_content TEXT,
                logs TEXT NOT NULL,
                created_at TEXT NOT NULL
            )
        """)
        # Adiciona a coluna sub_queries caso ela nao exista
        try:
            conn.execute("ALTER TABLE jobs ADD COLUMN sub_queries TEXT")
        except sqlite3.OperationalError:
            pass
        conn.commit()

def create_job(job_id: str, query: str):
    """Cria um novo trabalho de pesquisa com status PENDING."""
    init_db()  # garante que a tabela existe
    agora = datetime.now().isoformat()
    inicial_logs = json.dumps([f"[{datetime.now().strftime('%H:%M:%S')}] Trabalho de pesquisa registrado."])
    with get_connection() as conn:
        conn.execute(
            "INSERT INTO jobs (id, query, status, logs, created_at) VALUES (?, ?, ?, ?, ?)",
            (job_id, query, "PENDING", inicial_logs, agora)
        )
        conn.commit()

def update_job_status(job_id: str, status: str, report_content: str = None):
    """Atualiza o status de um trabalho e opcionalmente insere o relatório final."""
    with get_connection() as conn:
        if report_content is not None:
            conn.execute(
                "UPDATE jobs SET status = ?, report_content = ? WHERE id = ?",
                (status, report_content, job_id)
            )
        else:
            conn.execute(
                "UPDATE jobs SET status = ? WHERE id = ?",
                (status, job_id)
            )
        conn.commit()

def add_job_log(job_id: str, log_message: str):
    """Adiciona uma nova linha de log ao histórico do trabalho."""
    with get_connection() as conn:
        row = conn.execute("SELECT logs FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if row:
            logs = json.loads(row["logs"])
            agora_str = datetime.now().strftime("%H:%M:%S")
            logs.append(f"[{agora_str}] {log_message}")
            conn.execute(
                "UPDATE jobs SET logs = ? WHERE id = ?",
                (json.dumps(logs), job_id)
            )
            conn.commit()

def update_job_sub_queries(job_id: str, sub_queries: list[str]):
    """Atualiza a lista de sub-queries de um trabalho."""
    with get_connection() as conn:
        conn.execute(
            "UPDATE jobs SET sub_queries = ? WHERE id = ?",
            (json.dumps(sub_queries), job_id)
        )
        conn.commit()

def get_job(job_id: str) -> dict:
    """Recupera os detalhes de um trabalho de pesquisa."""
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if row:
            sub_q = None
            if "sub_queries" in row.keys() and row["sub_queries"]:
                try:
                    sub_q = json.loads(row["sub_queries"])
                except Exception:
                    pass
            return {
                "id": row["id"],
                "query": row["query"],
                "status": row["status"],
                "report_content": row["report_content"],
                "logs": json.loads(row["logs"]),
                "sub_queries": sub_q,
                "created_at": row["created_at"]
            }
        return None
