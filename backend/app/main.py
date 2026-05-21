"""Point d'entrée FastAPI — assemble les routes et configure CORS."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import chat, health, recipes

app = FastAPI(title="Carnet de recettes — API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(recipes.router)
app.include_router(chat.router)
