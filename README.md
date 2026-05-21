# Site with AI chat

Mini-application "Carnet de recettes" :
- **Backend** FastAPI (Python) avec une API REST pour gérer des recettes
- **Frontend** Next.js 15 (TypeScript) qui consomme l'API
- **Chat IA** : un endpoint `/chat` côté backend que **vous devez implémenter** (LangChain + Azure AI Inference, déploiement **Kimi-K2.6**)

Les consignes pédagogiques détaillées te sont remises séparément par ton formateur.

## Prérequis

- Docker et Docker Compose installés
- Un accès au déploiement Azure AI Foundry (endpoint + clé + nom du modèle), fourni par votre formateur

## Lancement

```bash
# 1. Configurer les variables Azure
cp .env.example .env
# édite .env et renseigne les trois variables AZURE_*
# (endpoint et clé visibles dans Azure AI Foundry → ton projet → Models + endpoints → Kimi-K2.6)

# 2. Démarrer
make up
# (équivalent à : docker compose up --build)
```

Ouvre ensuite :
- Backend (Swagger UI) : <http://localhost:8000/docs>
- Frontend : <http://localhost:3000>

## Vérification rapide

```bash
curl http://localhost:8000/health
# {"status":"ok"}

curl http://localhost:8000/recipes
# Renvoie la liste des recettes pré-remplies

curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Bonjour"}'
# {"reply":"TODO: implémenter le chat. ..."}
```

Le frontend affiche les recettes à gauche et un panneau de chat à droite. Le chat répond actuellement avec un placeholder — **votre travail est d'y brancher un vrai agent LangChain**.

## Structure

```
.
├── docker-compose.yml       # Orchestration backend + frontend
├── Makefile                 # Raccourcis make up/down/logs/test
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml
│   ├── app/
│   │   ├── main.py          # FastAPI app + CORS
│   │   ├── store.py         # CRUD recettes en mémoire
│   │   └── routes/
│   │       ├── health.py
│   │       ├── recipes.py   # ✅ déjà implémenté
│   │       └── chat.py      # ⚠️  STUB — à implémenter
│   └── tests/test_recipes.py
└── frontend/
    ├── Dockerfile
    ├── package.json
    ├── app/                 # Pages Next.js (App Router)
    ├── components/          # RecipeList, ChatPanel
    └── lib/api.ts           # Client REST typé
```

## Comment fonctionne le chat

### Vue d'ensemble

Quand tu envoies un message dans le chat, voici ce qui se passe de bout en bout :

```
Navigateur (ChatPanel.tsx)
  │  POST /chat  {"message": "Ajoute une quiche lorraine"}
  ▼
FastAPI  (routes/chat.py)
  │  agent.invoke(HumanMessage(...))
  ▼
Agent LangChain
  │  Le LLM lit le message et décide quel outil appeler
  │  → appelle create_recipe("quiche lorraine", ["oeufs", "lardons", ...])
  ▼
Tool  (fonction Python @tool)
  │  INSERT INTO recipes ...  (via SQLAlchemy + psycopg2)
  ▼
PostgreSQL
  │  retourne la ligne insérée
  ▼
Tool  → renvoie le JSON de la recette au LLM
  ▼
LLM  → formule une réponse en français
  ▼
FastAPI  → {"reply": "J'ai ajouté la quiche lorraine !"}
  ▼
ChatPanel.tsx  → affiche la réponse + déclenche le rechargement de RecipeList
```

### Le rôle de l'agent

L'agent est créé avec `create_agent(llm, tools=[...], system_prompt=...)` (LangChain).
Ce n'est **pas** un simple appel LLM — c'est une boucle de raisonnement :

1. Le LLM reçoit le message de l'utilisateur et la liste des outils disponibles (avec leur description).
2. Il décide s'il doit appeler un outil ou répondre directement.
3. Si un outil est appelé, son résultat est renvoyé au LLM.
4. Le LLM peut enchaîner plusieurs appels d'outils avant de formuler la réponse finale.

Le `system_prompt` définit la personnalité de l'agent : assistant culinaire qui répond toujours en français avec un ton chaleureux, et confirme systématiquement chaque action effectuée.

Le modèle LLM est servi par **Azure AI** (`AzureAIChatCompletionsModel` de `langchain-azure-ai`), configuré via les variables `AZURE_AI_INFERENCE_ENDPOINT`, `AZURE_AI_INFERENCE_API_KEY` et `AZURE_AI_INFERENCE_MODEL` dans `.env`.

### Le rôle de chaque outil

| Outil | Ce qu'il fait | SQL exécuté |
|-------|--------------|-------------|
| `list_recipes()` | Retourne toutes les recettes au format JSON | `SELECT * FROM recipes` |
| `create_recipe(name, ingredients)` | Ajoute une recette et retourne la ligne créée | `INSERT INTO recipes ...` |
| `delete_recipe(recipe_id)` | Supprime une recette par son id | `DELETE FROM recipes WHERE id = ?` |

Chaque outil est une fonction Python décorée `@tool`. LangChain lit la **docstring** et les **annotations de types** pour construire la description envoyée au LLM — c'est ce qui permet au modèle de choisir le bon outil et de passer les bons arguments.

> **Nota :** le chat utilise une connexion **synchrone** (`psycopg2`) alors que le reste du backend est async (`asyncpg`). C'est un contournement car LangChain ne supporte pas facilement l'async ici — d'où la ligne `DATABASE_URL.replace("+asyncpg", "+psycopg2")`.

### Flux de données complet (exemple)

```
Utilisateur : "Quelles recettes j'ai ?"

  1. ChatPanel envoie  POST /chat {"message": "Quelles recettes j'ai ?"}
  2. FastAPI passe le message à l'agent LangChain
  3. Le LLM choisit d'appeler  list_recipes()
  4. list_recipes() exécute  SELECT * FROM recipes  → JSON
  5. Le LLM reçoit le JSON et rédige une réponse en français
  6. FastAPI retourne  {"reply": "Voici vos recettes : …"}
  7. ChatPanel affiche la réponse (pas de mutation → RecipeList ne se recharge pas)
```

```
Utilisateur : "Supprime la recette numéro 3"

  1. → POST /chat {"message": "Supprime la recette numéro 3"}
  2. Le LLM appelle  delete_recipe(recipe_id=3)
  3. delete_recipe() exécute  DELETE FROM recipes WHERE id = 3
  4. Le LLM confirme la suppression en français
  5. ChatPanel reçoit la réponse → appelle onMutation() → RecipeList se recharge
```

---

## Comment fonctionne le chat — v2

> **Ce qui a changé** : bascule sur Ollama, centralisation de la config, ajout des champs `country` et `instructions`.

### Vue d'ensemble

Le flux reste identique, mais le LLM est maintenant servi par **Ollama** (en local) et l'agent transmet deux informations supplémentaires lors de la création d'une recette :

```
Navigateur (ChatPanel.tsx)
  │  POST /chat  {"message": "Ajoute une quiche lorraine"}
  ▼
FastAPI  (routes/chat.py)
  │  agent.invoke(HumanMessage(...))
  ▼
Agent LangChain
  │  Le LLM lit le message et décide quel outil appeler
  │  → appelle create_recipe("quiche lorraine", ["oeufs", ...], country="France", instructions="# Quiche…")
  ▼
Tool  (fonction Python @tool)
  │  INSERT INTO recipes ...  (via SQLAlchemy + psycopg2)
  ▼
PostgreSQL
  │  retourne la ligne insérée (avec country + instructions)
  ▼
Tool  → renvoie le JSON de la recette au LLM
  ▼
LLM  → formule une réponse en français, mentionne le pays d'origine
  ▼
FastAPI  → {"reply": "J'ai ajouté la quiche lorraine, spécialité de France !"}
  ▼
ChatPanel.tsx  → affiche la réponse + déclenche le rechargement de RecipeList
```

### Le rôle de l'agent

Même mécanique de boucle de raisonnement LangChain. Deux évolutions :

**Nouveau fournisseur LLM — Ollama**
```python
from langchain_ollama import ChatOllama
llm = ChatOllama(model=settings.ollama_model, base_url=settings.ollama_base_url, temperature=0.5)
```
Ollama tourne en local (ou sur une machine dédiée). Les variables `OLLAMA_BASE_URL` et `OLLAMA_MODEL` dans `.env` remplacent les variables Azure.

**Config centralisée — `app/config.py`**
Les `os.environ["..."]` éparpillés dans chaque fichier sont remplacés par un objet `settings` (Pydantic Settings), qui lit le `.env` automatiquement et valide les types au démarrage :
```python
from app.config import settings
settings.ollama_model          # → "ministral-3:14b"
settings.database_url.get_secret_value()  # → masqué dans les logs
```

**System prompt enrichi** : le LLM incarne désormais un chef formé par sa grand-mère, identifie le pays d'origine de chaque recette, et génère une fiche pédagogique complète (contexte culturel, quantités, étapes numérotées, astuces de chef) à chaque ajout.

### Le rôle de chaque outil

| Outil | Ce qu'il fait | SQL exécuté |
|-------|--------------|-------------|
| `list_recipes()` | Retourne toutes les recettes au format JSON | `SELECT * FROM recipes` |
| `create_recipe(name, ingredients, country, instructions)` | Ajoute une recette avec pays et fiche pédagogique | `INSERT INTO recipes ...` |
| `delete_recipe(recipe_id)` | Supprime une recette par son id | `DELETE FROM recipes WHERE id = ?` |

`country` et `instructions` sont tous deux optionnels (`str | None`). Le LLM est instruit dans le system prompt de toujours les renseigner — c'est lui qui détermine le pays et rédige la fiche.

> **Nota (inchangé) :** le chat utilise une connexion **synchrone** (`psycopg2`) alors que le reste du backend est async (`asyncpg`), d'où `DATABASE_URL.replace("+asyncpg", "+psycopg2")`.

### Flux de données complet (exemple)

```
Utilisateur : "Quelles recettes j'ai ?"

  1. ChatPanel envoie  POST /chat {"message": "Quelles recettes j'ai ?"}
  2. FastAPI passe le message à l'agent LangChain
  3. Le LLM choisit d'appeler  list_recipes()
  4. list_recipes() exécute  SELECT * FROM recipes  → JSON (avec country + instructions)
  5. Le LLM reçoit le JSON et liste les recettes avec leur pays d'origine
  6. FastAPI retourne  {"reply": "Voici vos recettes : …"}
  7. ChatPanel affiche la réponse (pas de mutation → RecipeList ne se recharge pas)
```

```
Utilisateur : "Ajoute un tiramisu"

  1. → POST /chat {"message": "Ajoute un tiramisu"}
  2. Le LLM appelle  create_recipe("tiramisu", [...], country="Italie", instructions="# Tiramisu\n…")
  3. create_recipe() exécute  INSERT INTO recipes (name, ingredients, country, instructions)
  4. Le LLM confirme l'ajout en mentionnant l'Italie
  5. ChatPanel reçoit la réponse → appelle onMutation() → RecipeList se recharge
```

---

## Comment fonctionne le chat — v3

> **Ce qui a changé** : sélecteur de provider LLM (Ollama / Azure) avec persistance localStorage, indicateurs de disponibilité en temps réel, carte de recette cliquable, modal pédagogique avec Markdown.

### Nouveautés frontend

**Sélecteur de provider dans `ChatPanel`**

Un toggle Ollama / Azure apparaît en haut du panneau. Le choix est persisté dans `localStorage` (`llm_provider`) et relu au montage. Le provider sélectionné est désormais transmis dans chaque requête :

```typescript
// lib/api.ts
export type LLMProvider = "ollama" | "azure";
sendChat(message, provider)  // body: { message, provider }
```

Chaque bouton affiche un point coloré indiquant la disponibilité du provider, interrogée au chargement via un nouvel endpoint :

```typescript
// GET /health/providers → { ollama: boolean, azure: boolean }
getProvidersHealth()
// vert = disponible · rouge = indisponible · gris = en cours de vérification
```

**`RecipeCard` — nouveau composant**

Remplace l'ancienne liste `<li>` brute. Chaque carte affiche le drapeau du pays, le nom et un aperçu des 3 premiers ingrédients. Un clic ouvre la modal ; le bouton ✕ supprime sans l'ouvrir (`e.stopPropagation()`).

**`RecipeModal` — nouveau composant**

Modal plein écran fermable via `Escape` ou clic extérieur. Affiche :
- En-tête sticky : drapeau + nom + pays + `#id`
- Ingrédients en liste à puces
- Instructions rendues en Markdown via `react-markdown`

**`countryToEmoji` — helper dans `lib/api.ts`**

Convertit le nom du pays (français ou anglais) en emoji drapeau via une table de 50+ correspondances. Retourne `🌍` par défaut.

**`RecipeList`**

Le formulaire d'ajout manuel a été supprimé — l'ajout se fait uniquement via le chat. Un message d'état vide guide l'utilisateur quand le carnet est vide.

## Commandes utiles

| Commande     | Effet                                            |
|--------------|--------------------------------------------------|
| `make up`    | Build + démarre tout (logs en avant-plan)        |
| `make down`  | Arrête les services                              |
| `make logs`  | Logs en continu                                  |
| `make test`  | Lance les tests pytest du backend                |
| `make clean` | Down + supprime les volumes                      |

## Ressources

- [FastAPI — premiers pas](https://fastapi.tiangolo.com/tutorial/first-steps/)
- [LangChain — `create_agent`](https://docs.langchain.com/oss/python/langchain/agents)
- [`langchain-azure-ai` — chat models](https://python.langchain.com/docs/integrations/chat/azure_ai/)
- [Azure AI Foundry — Inference API](https://learn.microsoft.com/azure/ai-foundry/model-inference/)
- [Next.js App Router](https://nextjs.org/docs/app)
