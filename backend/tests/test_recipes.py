from httpx import AsyncClient


async def test_health(client: AsyncClient) -> None:
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_list_recipes_empty(client: AsyncClient) -> None:
    response = await client.get("/recipes")
    assert response.status_code == 200
    assert response.json() == []


async def test_create_recipe(client: AsyncClient) -> None:
    response = await client.post(
        "/recipes", json={"name": "Tarte aux pommes", "ingredients": ["pommes", "sucre"]}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Tarte aux pommes"
    assert data["ingredients"] == ["pommes", "sucre"]
    assert isinstance(data["id"], int)


async def test_get_recipe(client: AsyncClient) -> None:
    created = await client.post(
        "/recipes", json={"name": "Quiche", "ingredients": ["œufs", "lardons"]}
    )
    recipe_id = created.json()["id"]

    response = await client.get(f"/recipes/{recipe_id}")
    assert response.status_code == 200
    assert response.json()["name"] == "Quiche"


async def test_create_and_delete_recipe(client: AsyncClient) -> None:
    create = await client.post("/recipes", json={"name": "Test", "ingredients": ["a", "b"]})
    assert create.status_code == 201
    recipe_id = create.json()["id"]

    deleted = await client.delete(f"/recipes/{recipe_id}")
    assert deleted.status_code == 204

    not_found = await client.get(f"/recipes/{recipe_id}")
    assert not_found.status_code == 404


async def test_get_unknown_recipe_returns_404(client: AsyncClient) -> None:
    response = await client.get("/recipes/99999")
    assert response.status_code == 404


async def test_delete_unknown_recipe_returns_404(client: AsyncClient) -> None:
    response = await client.delete("/recipes/99999")
    assert response.status_code == 404


async def test_chat_responds(client: AsyncClient) -> None:
    response = await client.post("/chat", json={"message": "Bonjour"})
    assert response.status_code == 200
    assert "reply" in response.json()


async def test_create_recipe_with_country_and_instructions(client: AsyncClient) -> None:
    response = await client.post(
        "/recipes",
        json={
            "name": "Ratatouille",
            "ingredients": ["courgettes", "aubergines", "tomates"],
            "country": "France",
            "instructions": "## Préparation\n\n1. Couper les légumes en rondelles.",
        },
    )
    assert response.status_code == 201
    data = response.json()
    assert data["country"] == "France"
    assert data["instructions"] is not None
    assert "Préparation" in data["instructions"]


async def test_create_recipe_country_and_instructions_default_to_null(client: AsyncClient) -> None:
    response = await client.post(
        "/recipes", json={"name": "Simple", "ingredients": ["sel"]}
    )
    assert response.status_code == 201
    data = response.json()
    assert data["country"] is None
    assert data["instructions"] is None


async def test_list_recipes_includes_country_and_instructions(client: AsyncClient) -> None:
    await client.post(
        "/recipes",
        json={
            "name": "Paella",
            "ingredients": ["riz", "safran"],
            "country": "Espagne",
            "instructions": "## Étapes\n\n1. Faire revenir.",
        },
    )
    response = await client.get("/recipes")
    assert response.status_code == 200
    recipes = response.json()
    assert len(recipes) == 1
    assert recipes[0]["country"] == "Espagne"
    assert recipes[0]["instructions"] is not None
