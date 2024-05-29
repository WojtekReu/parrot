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
        response = await client.post(
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
        response = await client.put(
            f"/api/v1/book/update/{book.id}",
            json={
                "author": "Ernest Hemingway",
                "title": "The Old Man and the Sea",
            },
        )
        assert response.status_code == 200
        updated_book = response.json()

        assert updated_book["author"] == "Ernest Hemingway"
        assert updated_book["title"] == "The Old Man and the Sea"

    async def test_delete_book(self, client):
        response0 = await client.post(
            "/api/v1/book/",
            json={
                "author": "Nobody",
                "title": "Book to remove",
            },
        )
        book = response0.json()
        response = await client.delete(f"/api/v1/book/delete/{book['id']}")
        assert response.status_code == 202

        get_response = await client.get(f"/api/v1/book/{book['id']}")
        data = get_response.json()
        assert data["detail"] == "Book not found with the given ID"


@pytest.mark.asyncio
class TestWordRouter(BaseTestRouter):
    router = api_router

    async def test_get_word(self, word_coroutine, client):
        word = await word_coroutine
        response = await client.get(f"/api/v1/word/{word.id}")
        assert response.status_code == 200
        assert response.json() == {
            "id": 3,
            "count": 0,
            "declination": {},
            "definition": "test definition",
            "lem": "test",
            "pos": "n",
        }
        response.json()

    async def test_create_word(self, client):
        response = await client.post(
            "/api/v1/word/",
            json={
                "lem": "tack",
                "pos": "v",
                "declination": {"VBN": "tacked"},
                "definition": "fasten with tacks",
                "count": 1,
            },
        )
        assert response.status_code == 201

        data = response.json()
        assert data["lem"] == "tack"
        assert isinstance(data["id"], int)

    async def test_update_word(self, word_for_update, client):
        word = await word_for_update
        response = await client.put(
            f"/api/v1/word/update/{word.id}",
            json={
                "definition": "part of book",
                "count": 8,
            },
        )
        assert response.status_code == 200

        updated_word = response.json()
        assert updated_word["definition"] == "part of book"
        assert updated_word["count"] == 8

    async def test_delete_word(self, client):
        response0 = await client.post(
            "/api/v1/word/",
            json={
                "lem": "attitude",
                "pos": "n",
                "count": "0",
                "declination": {},
                "definition": "",
            },
        )
        word = response0.json()

        response = await client.delete(f"/api/v1/word/delete/{word['id']}")
        assert response.status_code == 202
        assert response.text == "1"
