const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export type Recipe = {
  id: number;
  name: string;
  ingredients: string[];
  country: string | null;
  instructions: string | null;
};

const COUNTRY_FLAGS: Record<string, string> = {
  'france': '🇫🇷',
  'italie': '🇮🇹', 'italy': '🇮🇹',
  'espagne': '🇪🇸', 'spain': '🇪🇸',
  'japon': '🇯🇵', 'japan': '🇯🇵',
  'chine': '🇨🇳', 'china': '🇨🇳',
  'inde': '🇮🇳', 'india': '🇮🇳',
  'maroc': '🇲🇦', 'morocco': '🇲🇦',
  'mexique': '🇲🇽', 'mexico': '🇲🇽',
  'thaïlande': '🇹🇭', 'thailande': '🇹🇭', 'thailand': '🇹🇭',
  'grèce': '🇬🇷', 'grece': '🇬🇷', 'greece': '🇬🇷',
  'liban': '🇱🇧', 'lebanon': '🇱🇧',
  'turquie': '🇹🇷', 'turkey': '🇹🇷',
  'vietnam': '🇻🇳',
  'allemagne': '🇩🇪', 'germany': '🇩🇪',
  'portugal': '🇵🇹',
  'brésil': '🇧🇷', 'bresil': '🇧🇷', 'brazil': '🇧🇷',
  'argentine': '🇦🇷', 'argentina': '🇦🇷',
  'pérou': '🇵🇪', 'peru': '🇵🇪',
  'états-unis': '🇺🇸', 'etats-unis': '🇺🇸', 'usa': '🇺🇸', 'amérique': '🇺🇸',
  'corée': '🇰🇷', 'coree': '🇰🇷', 'korea': '🇰🇷', 'corée du sud': '🇰🇷',
  'égypte': '🇪🇬', 'egypte': '🇪🇬', 'egypt': '🇪🇬',
  'tunisie': '🇹🇳', 'tunisia': '🇹🇳',
  'algérie': '🇩🇿', 'algerie': '🇩🇿', 'algeria': '🇩🇿',
  'sénégal': '🇸🇳', 'senegal': '🇸🇳',
  'belgique': '🇧🇪', 'belgium': '🇧🇪',
  'royaume-uni': '🇬🇧', 'angleterre': '🇬🇧', 'england': '🇬🇧', 'uk': '🇬🇧',
  'russie': '🇷🇺', 'russia': '🇷🇺',
  'indonésie': '🇮🇩', 'indonesie': '🇮🇩', 'indonesia': '🇮🇩',
  'cambodge': '🇰🇭', 'cambodia': '🇰🇭',
  'éthiopie': '🇪🇹', 'ethiopie': '🇪🇹', 'ethiopia': '🇪🇹',
  'nigeria': '🇳🇬',
  'suède': '🇸🇪', 'suede': '🇸🇪', 'sweden': '🇸🇪',
  'norvège': '🇳🇴', 'norvege': '🇳🇴', 'norway': '🇳🇴',
  'danemark': '🇩🇰', 'denmark': '🇩🇰',
  'pays-bas': '🇳🇱', 'netherlands': '🇳🇱', 'hollande': '🇳🇱',
  'suisse': '🇨🇭', 'switzerland': '🇨🇭',
  'pologne': '🇵🇱', 'poland': '🇵🇱',
  'philippines': '🇵🇭',
  'malaisie': '🇲🇾', 'malaysia': '🇲🇾',
  'singapour': '🇸🇬', 'singapore': '🇸🇬',
  'pakistan': '🇵🇰',
  'iran': '🇮🇷',
  'chili': '🇨🇱', 'chile': '🇨🇱',
  'colombie': '🇨🇴', 'colombia': '🇨🇴',
  'canada': '🇨🇦',
  'australie': '🇦🇺', 'australia': '🇦🇺',
};

export function countryToEmoji(country: string | null): string {
  if (!country) return '🌍';
  return COUNTRY_FLAGS[country.toLowerCase().trim()] ?? '🌍';
}

export async function listRecipes(): Promise<Recipe[]> {
  const res = await fetch(`${API_URL}/recipes`, { cache: "no-store" });
  if (!res.ok) throw new Error("Échec liste recettes");
  return res.json();
}

export async function createRecipe(name: string, ingredients: string[]): Promise<Recipe> {
  const res = await fetch(`${API_URL}/recipes`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name, ingredients }),
  });
  if (!res.ok) throw new Error("Échec création recette");
  return res.json();
}

export async function deleteRecipe(id: number): Promise<void> {
  const res = await fetch(`${API_URL}/recipes/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error("Échec suppression");
}

export type LLMProvider = "ollama" | "azure";

export async function sendChat(message: string, provider: LLMProvider = "ollama"): Promise<{ reply: string }> {
  const res = await fetch(`${API_URL}/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, provider }),
  });
  if (!res.ok) throw new Error("Échec chat");
  return res.json();
}

export type ProvidersHealth = { ollama: boolean; azure: boolean };

export async function getProvidersHealth(): Promise<ProvidersHealth> {
  const res = await fetch(`${API_URL}/health/providers`);
  if (!res.ok) throw new Error("Échec health check");
  return res.json();
}
