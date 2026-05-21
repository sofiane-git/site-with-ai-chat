"use client";

import { useCallback, useEffect, useState } from "react";
import { deleteRecipe, listRecipes, Recipe } from "@/lib/api";
import RecipeCard from "@/components/RecipeCard";
import RecipeModal from "@/components/RecipeModal";

export default function RecipeList({ refreshSignal }: { refreshSignal?: number }) {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [error, setError] = useState<string | null>(null);
  const [selectedRecipe, setSelectedRecipe] = useState<Recipe | null>(null);

  const refresh = useCallback(async () => {
    try {
      setRecipes(await listRecipes());
      setError(null);
    } catch (e) {
      setError((e as Error).message);
    }
  }, []);

  useEffect(() => {
    refresh();
  }, [refresh, refreshSignal]);

  async function handleDelete(id: number) {
    try {
      await deleteRecipe(id);
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    }
  }

  return (
    <div className="space-y-4">
      <h2 className="text-xl font-semibold">Mes recettes</h2>
      {error && <p className="text-red-600">{error}</p>}
      {recipes.length === 0 && (
        <p className="text-gray-400 italic text-sm">
          Aucune recette pour l'instant. Demande au chat d'en ajouter une !
        </p>
      )}
      <ul className="space-y-2">
        {recipes.map((r) => (
          <RecipeCard
            key={r.id}
            recipe={r}
            onDelete={handleDelete}
            onClick={setSelectedRecipe}
          />
        ))}
      </ul>
      <RecipeModal recipe={selectedRecipe} onClose={() => setSelectedRecipe(null)} />
    </div>
  );
}
