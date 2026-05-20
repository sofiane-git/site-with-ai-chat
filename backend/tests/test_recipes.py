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


async def test_chat_stub_responds(client: AsyncClient) -> None:
    response = await client.post("/chat", json={"message": "Bonjour"})
    assert response.status_code == 200
    assert "TODO" in response.json()["reply"]
