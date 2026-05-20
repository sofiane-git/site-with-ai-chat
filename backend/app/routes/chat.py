import json
import os

from fastapi import APIRouter
from langchain.agents import create_agent
from langchain_azure_ai.chat_models import AzureAIChatCompletionsModel
from langchain_core.messages import HumanMessage
from langchain_core.tools import tool
from langgraph.checkpoint.memory import InMemorySaver
from pydantic import BaseModel

from app.store import RecipeCreate
from app.store import create_recipe as store_create_recipe
from app.store import delete_recipe as store_delete_recipe
from app.store import list_recipes as store_list_recipes

router = APIRouter(prefix="/chat", tags=["chat"])

ENDPOINT = os.environ["AZURE_AI_INFERENCE_ENDPOINT"]
API_KEY = os.environ["AZURE_AI_INFERENCE_API_KEY"]
MODEL = os.environ.get("AZURE_AI_INFERENCE_MODEL", "Mistral-Large-3")

llm = AzureAIChatCompletionsModel(
    endpoint=ENDPOINT,
    credential=API_KEY,
    model=MODEL,
)

SYSTEM_PROMPT = (
    "You are a helpful culinary assistant managing a recipe notebook. "
    "You can list existing recipes, add new ones, and delete them by id. "
    "Always confirm what action you took and its result."
    "Always speak in French, with a friendly and engaging tone."
)


@tool
def list_recipes() -> str:
    """Return all recipes currently in the notebook."""
    recipes = store_list_recipes()
    return json.dumps([r.model_dump() for r in recipes], ensure_ascii=False)


@tool
def create_recipe(name: str, ingredients: list[str]) -> str:
    """Add a new recipe to the notebook.

    Args:
        name: Name of the recipe.
        ingredients: List of ingredients.
    """
    recipe = store_create_recipe(RecipeCreate(name=name, ingredients=ingredients))
    return json.dumps(recipe.model_dump(), ensure_ascii=False)


@tool
def delete_recipe(recipe_id: int) -> str:
    """Delete a recipe from the notebook by its id.

    Args:
        recipe_id: The integer id of the recipe to delete.
    """
    success = store_delete_recipe(recipe_id)
    return "Deleted." if success else f"No recipe with id {recipe_id}."


agent = create_agent(
    llm,
    tools=[list_recipes, create_recipe, delete_recipe],
    system_prompt=SYSTEM_PROMPT,
    # checkpointer=InMemorySaver(),
)


class ChatRequest(BaseModel):
    message: str


class ChatResponse(BaseModel):
    reply: str


@router.post("", response_model=ChatResponse)
def chat(request: ChatRequest) -> ChatResponse:
    result = agent.invoke({"messages": [HumanMessage(content=request.message)]}, {"configurable": {"thread_id": "1"}})
    reply = result["messages"][-1].content
    return ChatResponse(reply=reply)
