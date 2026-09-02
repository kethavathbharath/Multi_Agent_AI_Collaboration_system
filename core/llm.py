from langchain_ollama import ChatOllama

from config.settings import settings


def get_llm():
    """
    Create and return the local Ollama LLM
    used by all agents.
    """

    return ChatOllama(
        model=settings.DEFAULT_MODEL_NAME,
        base_url=settings.OLLAMA_BASE_URL,
        temperature=0.2,
    )