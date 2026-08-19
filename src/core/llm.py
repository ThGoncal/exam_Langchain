"""
Configuration et initialisation du LLM principal de l'assistant.
"""

import os

from dotenv import load_dotenv
from langchain.chat_models import init_chat_model

load_dotenv()


def get_llm():
    """
    Retourne une instance configurée du LLM principal.

    Le format "provider:model" (ex. "groq:llama-3.3-70b-versatile") est géré
    nativement par init_chat_model, qui route vers le bon provider en fonction
    du préfixe. La clé API correspondante (GROQ_API_KEY) est lue automatiquement
    depuis l'environnement par le provider — inutile de la passer à la main.

    Pas d'instanciation au niveau module : on ne crée le LLM qu'au moment où
    une chaîne en a réellement besoin, pour ne pas faire échouer l'import du
    module (et donc la collecte des tests) si la clé API n'est pas encore
    définie dans l'environnement.
    """
    model_name = os.getenv("CHAT_MODEL", "groq:llama-3.3-70b-versatile")
    return init_chat_model(model_name)