import pytest

from conftest import BaseTestRouter

from api.routes.v1 import router as api_router


@pytest.mark.asyncio
class TestBookRouter(BaseTestRouter):
    router = api_router

    async def test_get_root(self, client):
        response = await client.get("/")
        assert response.status_code == 200

    async def test_get_books(self, book_coroutine, client):
        book = await book_coroutine
        response = await client.get("/api/v1/book/all")
        assert response.status_code == 200
        assert dict(book) in response.json()

    async def test_get_book(self, book_coroutine, client):
        book = await book_coroutine
        response = await client.get(f"/api/v1/book/{book.id}")
        assert response.status_code == 200
        assert response.json() == {
            "author": "Virginia Woolf",
            "id": 2,
            "sentences_count": 0,
            "title": "The Voyage Out",
            "words_count": 0,
        }

    async def test_create_book(self, client):
        response = await client.put(
            "/api/v1/book/",
            json={
                "author": "Artur Conan Doyle",
                "title": "The Sign of the Four",
            },
        )
        assert response.status_code == 201

        data = response.json()
        assert data["author"] == "Artur Conan Doyle"
        assert isinstance(data["id"], int)

    async def test_update_book(self, book_for_modification, client):
        book = await book_for_modification
        response = await client.patch(
            f"/api/v1/book/update/{book.id}",
            json={
                "author": "Ernest Hemingway",
                "title": "The Old Man and the Sea",
            },
        )
        assert response.status_code == 204
        assert response.text == ""

        response = await client.get(f"/api/v1/book/{book.id}")
        updated_book = response.json()

        assert updated_book["author"] == "Ernest Hemingway"
        assert updated_book["title"] == "The Old Man and the Sea"

    async def test_delete_book(self, client):
        put_response = await client.put(
            "/api/v1/book/",
            json={
                "author": "Nobody",
                "title": "Book to remove",
            },
        )
        book = put_response.json()
        response = await client.delete(f"/api/v1/book/delete/{book['id']}")
        assert response.status_code == 202

        get_response = await client.get(f"/api/v1/book/{book['id']}")
        data = get_response.json()
        assert data["detail"] == "Book not found with the given ID"
