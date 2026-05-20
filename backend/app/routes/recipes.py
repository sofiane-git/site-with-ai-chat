from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models import RecipeORM
from app.schemas import Recipe, RecipeCreate

router = APIRouter(prefix="/recipes", tags=["recipes"])


@router.get("", response_model=list[Recipe])
async def get_all_recipes(db: AsyncSession = Depends(get_db)) -> list[RecipeORM]:
    result = await db.execute(select(RecipeORM))
    return result.scalars().all()


@router.get("/{recipe_id}", response_model=Recipe)
async def get_one_recipe(recipe_id: int, db: AsyncSession = Depends(get_db)) -> RecipeORM:
    recipe = await db.get(RecipeORM, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recette introuvable")
    return recipe


@router.post("", response_model=Recipe, status_code=201)
async def post_recipe(data: RecipeCreate, db: AsyncSession = Depends(get_db)) -> RecipeORM:
    recipe = RecipeORM(name=data.name, ingredients=data.ingredients)
    db.add(recipe)
    await db.commit()
    await db.refresh(recipe)
    return recipe


@router.delete("/{recipe_id}", status_code=204)
async def remove_recipe(recipe_id: int, db: AsyncSession = Depends(get_db)) -> None:
    recipe = await db.get(RecipeORM, recipe_id)
    if recipe is None:
        raise HTTPException(status_code=404, detail="Recette introuvable")
    await db.delete(recipe)
    await db.commit()
