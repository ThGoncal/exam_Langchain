"""
Chaînes LangChain et agent de chat, assemblés à partir de core/llm.py,
core/schemas.py et prompts/prompts.py.
"""

from langchain.agents import create_agent
from langgraph.checkpoint.memory import InMemorySaver

from llm import get_llm
from schemas import CodeAnalysisResult, GeneratedTestResult, TestExplanationResult
from src.prompts.prompts import (
    CODE_ANALYSIS_PROMPT,
    TEST_GENERATION_PROMPT,
    TEST_EXPLANATION_PROMPT,
    CHAT_SYSTEM_PROMPT,
)


def get_analysis_chain():
    """Chaîne d'analyse de code : prompt -> LLM -> CodeAnalysisResult structuré."""
    llm = get_llm()
    return CODE_ANALYSIS_PROMPT | llm.with_structured_output(CodeAnalysisResult)


def get_test_chain():
    """Chaîne de génération de test unitaire : prompt -> LLM -> GeneratedTestResult."""
    llm = get_llm()
    return TEST_GENERATION_PROMPT | llm.with_structured_output(GeneratedTestResult)


def get_explain_test_chain():
    """Chaîne d'explication du test généré : prompt -> LLM -> TestExplanationResult."""
    llm = get_llm()
    return TEST_EXPLANATION_PROMPT | llm.with_structured_output(TestExplanationResult)


# Checkpointer partagé par l'agent de chat : conserve le contexte de conversation
# en mémoire process, indexé par thread_id (= username), tant que le service tourne.
_checkpointer = InMemorySaver()


def get_chat_agent():
    """
    Agent de chat conversationnel avec mémoire de contexte par thread_id.

    Expose l'interface attendue par les tests :
    .invoke({"messages": [...]}, config={"configurable": {"thread_id": ...}}).
    Le checkpointer étant défini au niveau module (pas recréé ici), le contexte
    de conversation survit d'un appel à l'autre malgré la recréation de l'agent
    à chaque appel de cette factory.
    """
    llm = get_llm()
    return create_agent(
        model=llm,
        tools=[],
        system_prompt=CHAT_SYSTEM_PROMPT,
        checkpointer=_checkpointer,
    )