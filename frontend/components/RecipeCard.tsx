"use client";

import { Recipe, countryToEmoji } from "@/lib/api";

interface RecipeCardProps {
  recipe: Recipe;
  onDelete: (id: number) => void;
  onClick: (recipe: Recipe) => void;
}

export default function RecipeCard({ recipe, onDelete, onClick }: RecipeCardProps) {
  const preview = recipe.ingredients.slice(0, 3);
  const hasMore = recipe.ingredients.length > 3;

  return (
    <li
      className="border rounded-lg p-4 cursor-pointer hover:bg-gray-50 transition-colors relative"
      onClick={() => onClick(recipe)}
    >
      <button
        onClick={(e) => { e.stopPropagation(); onDelete(recipe.id); }}
        className="absolute top-3 right-3 text-gray-300 hover:text-red-500 text-lg leading-none"
        aria-label="Supprimer la recette"
      >
        ✕
      </button>
      <div className="pr-6">
        {recipe.country && (
          <div className="text-sm text-gray-400 mb-1">
            {countryToEmoji(recipe.country)} {recipe.country}
          </div>
        )}
        <div className="font-semibold text-gray-900">{recipe.name}</div>
        <div className="text-sm text-gray-500 mt-1">
          {preview.join(", ")}{hasMore ? "…" : ""}
        </div>
      </div>
    </li>
  );
}
