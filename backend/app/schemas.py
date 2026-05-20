from pydantic import BaseModel


class Recipe(BaseModel):
    id: int
    name: str
    ingredients: list[str]

    model_config = {"from_attributes": True}


class RecipeCreate(BaseModel):
    name: str
    ingredients: list[str]
