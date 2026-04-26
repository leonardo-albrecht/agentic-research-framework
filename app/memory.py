class Memory:
    """
    Gerencia o histórico de conversa do agente.
    Cada mensagem é um dict com role e content.
    """
    def __init__(self, system_prompt: str):
        self.messages = [
            {"role": "system", "content": system_prompt}
        ]

    def adicionar_mensagem(self, role: str, content: str):
        self.messages.append({"role": role, "content": content})

    def get_historico(self) -> list:
        return self.messages

    def resumo(self) -> str:
        total = len(self.messages) - 1  # desconta system prompt
        return f"{total} mensagens no histórico"