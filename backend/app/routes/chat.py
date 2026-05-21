import json
import logging
import os

from fastapi import APIRouter
from langchain.agents import create_agent
# from langchain_azure_ai.chat_models import AzureAIChatCompletionsModel
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from pydantic import BaseModel
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.models import RecipeORM
from app.schemas import Recipe

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)

# ENDPOINT = os.environ["AZURE_AI_INFERENCE_ENDPOINT"]
# API_KEY = os.environ["AZURE_AI_INFERENCE_API_KEY"]
# MODEL = os.environ.get("AZURE_AI_INFERENCE_MODEL", "Mistral-Large-3")
_SYNC_DB_URL = os.environ["DATABASE_URL"].replace("+asyncpg", "+psycopg2")

OLLAMA_BASE_URL = os.environ.get("OLLAMA_BASE_URL")
OLLAMA_MODEL = os.environ.get("OLLAMA_MODEL")

logger.info("🤖 LLM service : Ollama | model : %s | url : %s", OLLAMA_MODEL, OLLAMA_BASE_URL)

llm = ChatOllama(
    model=OLLAMA_MODEL,
    base_url=OLLAMA_BASE_URL,
    temperature=0,
)

_sync_engine = create_engine(_SYNC_DB_URL)

SYSTEM_PROMPT = (
    "You are a helpful culinary assistant managing a recipe notebook. "
    "You can list existing recipes, add new ones, and delete them by id. "
    "Always confirm what action you took and its result."
    "Always speak in French, with a friendly and engaging tone."
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
def create_recipe(name: str, ingredients: list[str]) -> str:
    """Add a new recipe to the notebook.

    Args:
        name: Name of the recipe.
        ingredients: List of ingredients.
    """
    with Session(_sync_engine) as session:
        recipe = RecipeORM(name=name, ingredients=ingredients)
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


agent = create_agent(
    llm,
    tools=[list_recipes, create_recipe, delete_recipe],
    system_prompt=SYSTEM_PROMPT,
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    result = agent.invoke(
        {"messages": [HumanMessage(content=request.message)]},
        {"configurable": {"thread_id": request.message}},
    )
    reply = result["messages"][-1].content
    # messages = [
    #     ChatMessage(role="control", content="thinking"),
    #     HumanMessage(content=request.message),
    # ]

    # response = llm.invoke(messages)
    return ChatResponse(reply=reply)
    # return ChatResponse(reply=response.content)

