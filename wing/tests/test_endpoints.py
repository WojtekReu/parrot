from unittest.mock import patch

import pytest

from conftest import BaseTestRouter, DictionaryClientMock

from api.routes.v2 import router as api_router


async def client_logged_in(client, login, password):
    await client.post(
        "/api/v2/login",
        data=f"grant_type=&username={login}&password={password}&scope=&client_id=",
        headers={
            "Content-Type": "application/x-www-form-urlencoded",
        },
    )


async def guest(client):
    await client_logged_in(client, "akowalski", "secret")


async def owner(client):
    await client_logged_in(client, "jkowalski", "secret")


@pytest.mark.asyncio
class TestBookRouter(BaseTestRouter):
    router = api_router

    async def test_get_root(self, client):
        response = await client.get("/")
        assert response.status_code == 200

    async def test_get_books(self, client):
        response = await client.get("/api/v2/books/all")
        assert response.status_code == 200
        books = response.json()
        assert len(books) == 2
        book = {
            "author": "Virginia Woolf",
            "id": 2,
            "is_public": True,
            "sentences_count": 0,
            "title": "To The Lighthouse",
            "user_id": 1,
            "words_count": 0,
        }
        assert book in books

    async def test_get_book(self, client):
        response = await client.get(f"/api/v2/books/1")
        assert response.status_code == 200
        assert response.json() == {
            "author": "Virginia Woolf",
            "id": 1,
            "is_public": False,
            "sentences_count": 0,
            "title": "The Voyage Out",
            "user_id": 1,
            "words_count": 0,
        }

    async def test_create_book(self, client):
        await owner(client)
        response = await client.post(
            "/api/v2/books/",
            json={
                "author": "Artur Conan Doyle",
                "title": "The Sign of the Four",
            },
        )
        assert response.status_code == 201

        data = response.json()
        assert data["author"] == "Artur Conan Doyle"
        assert isinstance(data["id"], int)

    async def test_update_book(self, client):
        await owner(client)
        response = await client.put(
            f"/api/v2/books/4/update",
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
        await owner(client)
        response0 = await client.post(
            "/api/v2/books/",
            json={
                "author": "Nobody",
                "title": "Book to remove",
            },
        )
        book = response0.json()
        response = await client.delete(f"/api/v2/books/{book['id']}/delete")
        assert response.status_code == 202

        get_response = await client.get(f"/api/v2/books/{book['id']}")
        data = get_response.json()
        assert data["detail"] == "Book not found with the given ID"

    async def test_delete_book_by_guest(self, client):
        await guest(client)
        response = await client.delete(f"/api/v2/books/1/delete")
        assert response.status_code == 401
        assert response.json() == {"detail": "Not authenticated"}

        get_response = await client.get(f"/api/v2/books/1")
        book = get_response.json()
        assert book["id"] == 1


@pytest.mark.asyncio
class TestWordRouter(BaseTestRouter):
    router = api_router

    async def test_get_word(self, client):
        response = await client.get(f"/api/v2/words/1")
        assert response.status_code == 200
        assert response.json() == {
            "id": 1,
            "count": 0,
            "declination": {"NNS": "chapters"},
            "definition": "test definition for chapter",
            "lem": "chapter",
            "pos": "n",
            "synset": None,
        }

    async def test_create_word(self, client):
        await owner(client)
        response = await client.post(
            "/api/v2/words/",
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

    async def test_update_word(self, client):
        await owner(client)
        response = await client.put(
            f"/api/v2/words/3/update",
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
        await owner(client)
        response0 = await client.post(
            "/api/v2/words/",
            json={
                "lem": "attitude",
                "pos": "n",
                "count": "0",
                "declination": {},
                "definition": "",
            },
        )
        word = response0.json()

        response = await client.delete(f"/api/v2/words/{word['id']}/delete")
        assert response.status_code == 202
        assert response.text == "1"

    @patch("wing.crud.word.find_definition")
    async def test_find_definition(self, find_definition_mock, client):
        find_definition_mock.return_value = {
            "found": 1,
            "word": "brooch",
            "synsets": [
                (False, "brooch.n.01", "a decorative pin worn by women"),
                (True, "brooch.v.01", "fasten with or as if with a brooch"),
            ],
            "matched_synset": "brooch.v.01",
        }

        response = await client.get(
            f"/api/v2/words/4/sentences/3/synset",
        )
        result = response.json()

        expected = {
            "synsets": [
                [False, "brooch.n.01", "a decorative pin worn by women"],
                [True, "brooch.v.01", "fasten with or as if with a brooch"],
            ],
            "word": {
                "count": 0,
                "declination": {"NNS": "brooches"},
                "definition": "",
                "id": 4,
                "lem": "brooch",
                "pos": "n",
                "synset": "",
            },
        }

        assert result == expected

    async def test_get_flashcard(self, client):
        response = await client.get("/api/v2/flashcards/1")
        assert response.status_code == 200
        assert response.json() == {
            "id": 1,
            "keyword": "equivocal",
            "translations": ["dwuznaczny"],
            "user_id": 1,
        }

    async def test_create_flashcard(self, client):
        await owner(client)
        response = await client.post(
            "/api/v2/flashcards/",
            json={
                "keyword": "rickety",
                "translations": ["rozklekotany"],
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert data["keyword"] == "rickety"
        assert isinstance(data["id"], int)

    async def test_update_flashcard(self, client):
        await owner(client)
        response = await client.put(
            "/api/v2/flashcards/2/update",
            json={
                "keyword": "repudiate",
                "translations": ["odrzucać"],
                "user_id": 1,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["keyword"] == "repudiate"
        assert data["translations"] == ["odrzucać"]

    async def test_flashcard_join_to_sentences(self, client):
        await owner(client)
        response = await client.post(
            "/api/v2/flashcards/1/sentences",
            json={
                "disconnect_ids": [],
                "sentence_ids": [1],
            },
        )
        assert response.status_code == 204

    async def test_flashcard_get_words(self, client):
        await owner(client)
        response = await client.get(
            "/api/v2/flashcards/1/words",
        )
        assert response.status_code == 200

        data = response.json()
        assert data == [
            {
                "count": 0,
                "declination": {"NNS": "chapters"},
                "definition": "test definition for chapter",
                "id": 1,
                "lem": "chapter",
                "pos": "n",
                "synset": None,
            }
        ]

    async def test_find_words(self, client):
        response = await client.get(
            "/api/v2/words/find/chapter",
        )
        assert response.status_code == 200

        data = response.json()
        assert data == [
            {
                "count": 0,
                "declination": {"NNS": "chapters"},
                "definition": "test definition for chapter",
                "id": 1,
                "lem": "chapter",
                "pos": "n",
                "synset": None,
            }
        ]


@pytest.mark.asyncio
@patch("wing.dictionary.DictionaryClient", new=DictionaryClientMock)
class TestDictionaryRouter(BaseTestRouter):
    router = api_router

    async def test_get_translation(self, client):
        response = await client.get(f"/api/v2/dictionary/find/equivocal")
        assert response.status_code == 200
        assert response.json() == {
            "word": "equivocal",
            "translation": "equivocal /ɪˈkwɪvəkəl/ <Adj>\n  dwuznaczny, niejednoznaczny",
        }


@pytest.mark.asyncio
class TestTranslationRouter(BaseTestRouter):
    router = api_router

    async def test_get_translation_from_sql(self, client):
        response = await client.get(f"/api/v2/translation/find/chapter")
        assert response.status_code == 200
        data = response.json()
        assert data["word"] == "chapter"
        assert data["definition"] == "/ˈʧæptə/ <N>\n  rozdział"
