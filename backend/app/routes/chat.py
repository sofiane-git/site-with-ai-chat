"""Endpoint de chat — STUB à implémenter par l'étudiant.

Étape 1 : remplacer la réponse 'TODO' par un appel direct à Kimi-K2.6 via
          AzureAIChatCompletionsModel (langchain-azure-ai), sans outils,
          qui renvoie la réponse du modèle.

Étape 2 : transformer ça en agent LangChain avec 3 outils branchés sur app/store.py :
          - list_recipes  → retourne la liste actuelle
          - create_recipe → crée une nouvelle recette
          - delete_recipe → supprime par id
          (voir langchain.agents.create_agent)

Étape 3 (stretch) : mémoire conversationnelle pour suivre une session de chat.
"""

import os

from fastapi import APIRouter
from langchain_azure_ai.chat_models import AzureAIChatCompletionsModel
from pydantic import BaseModel

router = APIRouter(prefix="/chat", tags=["chat"])

llm = AzureAIChatCompletionsModel(
    endpoint=os.environ["AZURE_AI_INFERENCE_ENDPOINT"],
    credential=os.environ["AZURE_AI_INFERENCE_API_KEY"],
    model=os.environ["AZURE_AI_INFERENCE_MODEL"],
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    response = llm.invoke(request.message)
    return ChatResponse(reply=response.content)
