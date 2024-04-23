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
        response = await client.get(f"/api/v1/book/all")
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
