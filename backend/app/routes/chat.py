import json
import logging

from fastapi import APIRouter
from langchain.agents import create_agent
from langchain_ollama import ChatOllama
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from pydantic import BaseModel
from sqlalchemy import create_engine, select
from sqlalchemy.orm import Session

from app.config import settings
from app.models import RecipeORM
from app.schemas import Recipe

router = APIRouter(prefix="/chat", tags=["chat"])
logger = logging.getLogger(__name__)

_SYNC_DB_URL = settings.database_url.get_secret_value().replace("+asyncpg", "+psycopg2")

logger.info("🤖 LLM service : Ollama | model : %s | url : %s", settings.ollama_model, settings.ollama_base_url)

llm = ChatOllama(
    model=settings.ollama_model,
    base_url=settings.ollama_base_url.get_secret_value(),
    temperature=0.5,
)

_sync_engine = create_engine(_SYNC_DB_URL)

SYSTEM_PROMPT = (
    "You are a helpful culinary assistant managing a recipe notebook. "
    "You can list existing recipes, add new ones, and delete them by id. "
    "Always confirm what action you took and its result. "
    "For every recipe, determine which country it originates from. "
    "Always include the country of origin in your response when mentioning a recipe — both when listing and when adding. "
    "When adding a recipe, always pass the country of origin to the create_recipe tool. "
    "Imagine yourself as an extraordinary chef from that country, dedicated to traditional, high-quality, and eco-friendly cuisine, who learned everything from his grandmother. "
    "Always speak in French."
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
def create_recipe(name: str, ingredients: list[str], country: str | None = None) -> str:
    """Add a new recipe to the notebook.

    Args:
        name: Name of the recipe.
        ingredients: List of ingredients.
        country: Country of origin of the recipe.
    """
    with Session(_sync_engine) as session:
        recipe = RecipeORM(name=name, ingredients=ingredients, country=country)
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

