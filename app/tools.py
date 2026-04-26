import requests
from datetime import datetime

def buscar_cotacao_dolar() -> str:
    """Busca a cotação atual do dólar em reais."""
    try:
        response = requests.get(
            "https://api.exchangerate-api.com/v4/latest/USD",
            timeout=5
        )
        data = response.json()
        valor = data["rates"]["BRL"]
        return f"Cotação atual: R$ {valor:.2f}"
    except Exception as e:
        return f"Erro ao buscar cotação: {str(e)}"

def buscar_data_hora() -> str:
    """Retorna a data e hora atual."""
    agora = datetime.now()
    return agora.strftime("Data: %d/%m/%Y | Hora: %H:%M")

# Mapa de ferramentas disponíveis pro agente
TOOLS = {
    "buscar_cotacao_dolar": buscar_cotacao_dolar,
    "buscar_data_hora": buscar_data_hora,
}