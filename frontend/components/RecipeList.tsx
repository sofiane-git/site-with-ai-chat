"use client";

import { useCallback, useEffect, useState } from "react";
import { createRecipe, deleteRecipe, listRecipes, Recipe } from "@/lib/api";
import RecipeCard from "@/components/RecipeCard";
import RecipeModal from "@/components/RecipeModal";

export default function RecipeList({ refreshSignal }: { refreshSignal?: number }) {
  const [recipes, setRecipes] = useState<Recipe[]>([]);
  const [name, setName] = useState("");
  const [ingredients, setIngredients] = useState("");
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

  async function handleAdd(e: React.FormEvent) {
    e.preventDefault();
    if (!name.trim()) return;
    try {
      await createRecipe(
        name,
        ingredients.split(",").map((s) => s.trim()).filter(Boolean),
      );
      setName("");
      setIngredients("");
      await refresh();
    } catch (e) {
      setError((e as Error).message);
    }
  }

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
      <form onSubmit={handleAdd} className="border p-3 rounded space-y-2">
        <input
          className="border p-2 w-full rounded"
          placeholder="Nom de la recette"
          value={name}
          onChange={(e) => setName(e.target.value)}
        />
        <input
          className="border p-2 w-full rounded"
          placeholder="Ingrédients (séparés par des virgules)"
          value={ingredients}
          onChange={(e) => setIngredients(e.target.value)}
        />
        <button type="submit" className="bg-blue-600 text-white px-4 py-2 rounded">
          Ajouter
        </button>
      </form>
      <RecipeModal recipe={selectedRecipe} onClose={() => setSelectedRecipe(null)} />
    </div>
  );
}
