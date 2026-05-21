import json
import logging
from typing import Literal

from fastapi import APIRouter, HTTPException
from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from pydantic import BaseModel
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import RecipeORM
from app.schemas import Recipe

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)

_SYNC_DB_URL = settings.database_url.get_secret_value().replace("+asyncpg", "+psycopg2")
_sync_engine = create_engine(_SYNC_DB_URL)

SYSTEM_PROMPT = (
    "You are a helpful culinary assistant managing a recipe notebook. "
    "You can list existing recipes, add new ones, and delete them by id. "
    "Always confirm what action you took and its result. "
    "For every recipe, determine which country it originates from. "
    "Always include the country of origin in your response when mentioning a recipe — both when listing and when adding. "
    "When adding a recipe, always pass the country of origin to the create_recipe tool. "
    "When adding a recipe, also generate complete pedagogical cooking instructions in French markdown "
    "and pass them as the `instructions` parameter of create_recipe. "
    "The markdown must include: a short cultural context paragraph about the dish's history, "
    "ingredients with exact quantities and selection tips, numbered preparation steps with detailed "
    "technique explanations, grandmother's tips (chef secrets), and estimated preparation and cooking times. "
    "Imagine yourself as an extraordinary chef from that country, dedicated to traditional, "
    "high-quality, and eco-friendly cuisine, who learned everything from his grandmother. "
    "Always speak in French, keep it brief."
)


@tool
def list_recipes() -> str:
    """Return all recipes currently in the notebook."""
    with Session(_sync_engine) as session:
        recipes = session.execute(select(RecipeORM)).scalars().all()
        return json.dumps(
            [Recipe.model_validate(r).model_dump() for r in recipes],
            ensure_ascii=False,
        )


@tool
def create_recipe(name: str, ingredients: list[str], country: str | None = None, instructions: str | None = None) -> str:
    """Add a new recipe to the notebook.

    Args:
        name: Name of the recipe.
        ingredients: List of ingredients.
        country: Country of origin of the recipe.
        instructions: Complete pedagogical cooking instructions in French markdown.
    """
    with Session(_sync_engine) as session:
        recipe = RecipeORM(name=name, ingredients=ingredients, country=country, instructions=instructions)
        session.add(recipe)
        session.commit()
        session.refresh(recipe)
        return json.dumps(Recipe.model_validate(recipe).model_dump(), ensure_ascii=False)


@tool
def delete_recipe(recipe_id: int) -> str:
    """Delete a recipe from the notebook by its id.

    Args:
        recipe_id: The integer id of the recipe to delete.
    """
    with Session(_sync_engine) as session:
        recipe = session.get(RecipeORM, recipe_id)
        if recipe is None:
            return f"No recipe with id {recipe_id}."
        session.delete(recipe)
        session.commit()
        return "Deleted."


_TOOLS = [list_recipes, create_recipe, delete_recipe]

# --- Ollama (toujours disponible) ---
logger.info("🤖 Ollama | model : %s | url : %s", settings.ollama_model, settings.ollama_base_url)
llm_ollama = ChatOllama(
    model=settings.ollama_model,
    base_url=settings.ollama_base_url.get_secret_value(),
    temperature=0.5,
)
agent_ollama = create_agent(llm_ollama, tools=_TOOLS, system_prompt=SYSTEM_PROMPT, checkpointer=InMemorySaver())

# --- Azure AI (optionnel) ---
agent_azure = None
if settings.azure_ai_inference_api_key and settings.azure_ai_inference_endpoint:
    from langchain_azure_ai.chat_models import AzureAIChatCompletionsModel
    llm_azure = AzureAIChatCompletionsModel(
        endpoint=settings.azure_ai_inference_endpoint.get_secret_value(),
        credential=settings.azure_ai_inference_api_key.get_secret_value(),
        model_name=settings.azure_ai_inference_model,
        temperature=0.5,
    )
    agent_azure = create_agent(llm_azure, tools=_TOOLS, system_prompt=SYSTEM_PROMPT, checkpointer=InMemorySaver())
    logger.info("🤖 Azure AI disponible | model : %s", settings.azure_ai_inference_model)
else:
    logger.info("ℹ️  Azure AI non configuré (credentials absents)")


class ChatRequest(BaseModel):
    message: str
    session_id: str = "default"
    provider: Literal["ollama", "azure"] = "ollama"


class ChatResponse(BaseModel):
    reply: str


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    if request.provider == "azure":
        if agent_azure is None:
            raise HTTPException(status_code=400, detail="Azure AI non configuré sur ce serveur")
        agent = agent_azure
    else:
        agent = agent_ollama

    result = agent.invoke(
        {"messages": [HumanMessage(content=request.message)]},
        {"configurable": {"thread_id": request.session_id}},
    )
    return ChatResponse(reply=result["messages"][-1].content)
