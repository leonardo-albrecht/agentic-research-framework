import requests
from bs4 import BeautifulSoup
from duckduckgo_search import DDGS

def pesquisar_web(query: str) -> str:
    """
    Realiza uma busca no DuckDuckGo e retorna os principais resultados em formato de texto.
    Uso: pesquisar_web("Slack vs Teams model de negocios")
    """
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=5))
            if not results:
                return "Nenhum resultado encontrado."
            
            formatados = []
            for r in results:
                formatados.append(
                    f"Título: {r.get('title')}\nURL: {r.get('href')}\nResumo: {r.get('body')}\n---"
                )
            return "\n\n".join(formatados)
    except Exception as e:
        return f"Erro ao realizar a busca na web: {str(e)}"

def extrair_conteudo_web(url: str) -> str:
    """
    Acessa uma URL, extrai o texto principal removendo scripts, menus e rodapés,
    e retorna os primeiros 3000 caracteres do conteúdo textual útil.
    Uso: extrair_conteudo_web("https://exemplo.com/artigo")
    """
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        }
        response = requests.get(url, timeout=10, headers=headers)
        if response.status_code != 200:
            return f"Erro ao acessar página: Código HTTP {response.status_code}"
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Remove tags não textuais e elementos comuns de navegação
        for elemento in soup(["script", "style", "noscript", "iframe", "header", "footer", "nav", "aside"]):
            elemento.decompose()
            
        texto = soup.get_text()
        
        # Limpeza de espaços em branco e quebras de linha duplicadas
        linhas = (linha.strip() for linha in texto.splitlines())
        blocos = (bloco.strip() for linha in linhas for bloco in linha.split("  "))
        texto_limpo = "\n".join(bloco for bloco in blocos if bloco)
        
        # Retorna os primeiros 3500 caracteres (suficiente para o agente extrair notas)
        return texto_limpo[:3500]
    except Exception as e:
        return f"Erro ao extrair conteúdo da URL {url}: {str(e)}"

def obter_transcricao_youtube(video_url_ou_id: str) -> str:
    """
    Extrai a transcrição (legendas) de um vídeo do YouTube.
    Uso: obter_transcricao_youtube("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
    """
    import re
    video_id = video_url_ou_id.strip()
    
    # Se for um link completo, extrai o ID
    if "youtube.com" in video_id or "youtu.be" in video_id:
        padrao = r'(?:v=|\/embed\/|\/1/|\/v\/|https:\/\/youtu\.be\/|\/shorts\/)([a-zA-Z0-9_-]{11})'
        match = re.search(padrao, video_id)
        if match:
            video_id = match.group(1)
        else:
            return "Erro: Não foi possível identificar o ID do vídeo a partir da URL fornecida."
            
    if len(video_id) != 11 or not re.match(r'^[a-zA-Z0-9_-]{11}$', video_id):
        return f"Erro: ID de vídeo inválido ({video_id}). O ID deve ter 11 caracteres."
        
    try:
        from youtube_transcript_api import YouTubeTranscriptApi
        
        # Tenta obter transcrição em português primeiro, senão em inglês
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['pt', 'en'])
        except Exception:
            # Caso falhe, tenta obter qualquer uma disponível
            try:
                transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
                transcript_list = transcript_list.find_transcript(['pt', 'en'])
                transcript_list = transcript_list.fetch()
            except Exception:
                # Fallback final: tenta pegar a primeira de qualquer idioma
                transcript_list = YouTubeTranscriptApi.get_transcript(video_id)
            
        textos = [t['text'] for t in transcript_list]
        texto_completo = " ".join(textos)
        
        return f"--- Transcrição do vídeo YouTube (ID: {video_id}) ---\n" + texto_completo[:4000]
    except Exception as e:
        return f"Erro ao extrair transcrição para o vídeo {video_id}: {str(e)}"

# Mapa de ferramentas disponíveis para o agente Researcher
TOOLS = {
    "pesquisar_web": pesquisar_web,
    "extrair_conteudo_web": extrair_conteudo_web,
    "obter_transcricao_youtube": obter_transcricao_youtube,
}

# Definição dos esquemas das ferramentas no formato da API do Groq (Function Calling)
TOOLS_SCHEMA = [
    {
        "type": "function",
        "function": {
            "name": "pesquisar_web",
            "description": "Realiza uma pesquisa por termos na internet e retorna títulos, URLs e pequenos resumos dos resultados.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "O termo de pesquisa a ser buscado."
                    }
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "extrair_conteudo_web",
            "description": "Acessa um website via URL e extrai o texto principal, limpando anúncios e scripts.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "A URL completa do site para extração do conteúdo."
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "obter_transcricao_youtube",
            "description": "Extrai a transcrição textual (legendas) de um vídeo do YouTube a partir de uma URL ou ID do vídeo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "video_url_ou_id": {
                        "type": "string",
                        "description": "A URL completa do vídeo do YouTube ou o ID do vídeo (11 caracteres)."
                    }
                },
                "required": ["video_url_ou_id"]
            }
        }
    }
]