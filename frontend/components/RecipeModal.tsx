"use client";

import { useEffect } from "react";
import ReactMarkdown from "react-markdown";
import { Recipe, countryToEmoji } from "@/lib/api";

interface RecipeModalProps {
  recipe: Recipe | null;
  onClose: () => void;
}

export default function RecipeModal({ recipe, onClose }: RecipeModalProps) {
  useEffect(() => {
    const handler = (e: KeyboardEvent) => { if (e.key === "Escape") onClose(); };
    document.addEventListener("keydown", handler);
    return () => document.removeEventListener("keydown", handler);
  }, [onClose]);

  if (!recipe) return null;

  return (
    <div
      className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      onClick={onClose}
    >
      <div
        className="bg-white rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="sticky top-0 bg-white border-b px-6 py-4 flex justify-between items-start">
          <div>
            <h2 className="text-xl font-bold text-gray-900">
              {countryToEmoji(recipe.country)} {recipe.name}
            </h2>
            {recipe.country && (
              <p className="text-sm text-gray-500 mt-0.5">{recipe.country}</p>
            )}
            <p className="text-xs text-gray-400 mt-0.5">#{recipe.id}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 text-2xl font-light ml-4 leading-none"
            aria-label="Fermer"
          >
            ✕
          </button>
        </div>

        <div className="px-6 py-5 space-y-6">
          <section>
            <h3 className="font-semibold text-gray-800 mb-2">Ingrédients</h3>
            <ul className="list-disc list-inside space-y-1 text-gray-700 text-sm">
              {recipe.ingredients.map((ing, i) => (
                <li key={i}>{ing}</li>
              ))}
            </ul>
          </section>

          {recipe.instructions ? (
            <section>
              <h3 className="font-semibold text-gray-800 mb-2">Instructions</h3>
              <div className="prose prose-sm max-w-none text-gray-700">
                <ReactMarkdown>{recipe.instructions}</ReactMarkdown>
              </div>
            </section>
          ) : (
            <p className="text-sm text-gray-400 italic">
              Aucune instruction disponible pour cette recette.
            </p>
          )}
        </div>
      </div>
    </div>
  );
}
