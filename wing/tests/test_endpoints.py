from unittest.mock import patch

import pytest

from conftest import BaseTestRouter, DictionaryClientMock

from api.routes.v2 import router as api_router

BOOK_RAW = """As the streets that lead from the Strand to the Embankment are very narrow, it is
better not to walk down them arm-in-arm. If you persist, lawyers’ clerks will have to make flying
leaps into the mud; young lady typists will have to fidget behind you. In the streets of London
where beauty goes unregarded, eccentricity must pay the penalty, and it is better not to be very
tall, to wear a long blue cloak, or to beat the air with your left hand.
One afternoon in the beginning of October when the traffic was becoming brisk a tall man strode
along the edge of the pavement with a lady on his arm. Angry glances struck upon their backs. The
small, agitated figures — for in comparison with this couple most people looked small — decorated
with fountain pens, and burdened with despatch-boxes, had appointments to keep, and drew a weekly
salary, so that there was some reason for the unfriendly stare which was bestowed upon Mr.
Ambrose’s height and upon Mrs. Ambrose’s cloak. But some enchantment had put both man and woman
beyond the reach of malice and unpopularity. In his case one might guess from the moving lips that
it was thought; and in hers from the eyes fixed stonily straight in front of her at a level above
the eyes of most that it was sorrow. It was only by scorning all she met that she kept herself from
tears, and the friction of people brushing past her was evidently painful. After watching the
traffic on the Embankment for a minute or two with a stoical gaze she twitched her husband’s
sleeve, and they crossed between the swift discharge of motor cars. When they were safe on the
further side, she gently withdrew her arm from his, allowing her mouth at the same time to relax,
to tremble; then tears rolled down, and leaning her elbows on the balustrade, she shielded her
face from the curious. Mr. Ambrose attempted consolation; he patted her shoulder; but she showed
no signs of admitting him, and feeling it awkward to stand beside a grief that was greater than
his, he crossed his arms behind him, and took a turn along the pavement.
The embankment juts out in angles here and there, like pulpits; instead of preachers, however,
small boys occupy them, dangling string, dropping pebbles, or launching wads of paper for a cruise.
With their sharp eye for eccentricity, they were inclined to think Mr. Ambrose awful; but the
quickest witted cried "Bluebeard!" as he passed. In case they should proceed to tease his wife, Mr.
Ambrose flourished his stick at them, upon which they decided that he was grotesque merely, and
four instead of one cried "Bluebeard!" in chorus."""


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


async def client_anowak(client):
    await client_logged_in(client, "anowak", "secret")


@pytest.mark.asyncio
class TestBookRouter(BaseTestRouter):
    router = api_router

    async def test_get_root(self, client):
        response = await client.get("/")
        assert response.status_code == 200

    async def test_get_books(self, client):
        response = await client.get("/api/v2/books/public?page=1&size=50")
        assert response.status_code == 200
        books = response.json()
        assert books == {
            "items": [
                {
                    "author": "Virginia Woolf",
                    "id": 1,
                    "is_public": True,
                    "sentences_count": 0,
                    "title": "The Voyage Out",
                    "user_id": 1,
                    "words_count": 0,
                },
                {
                    "author": "Arthur Conan Doyle",
                    "id": 3,
                    "is_public": True,
                    "sentences_count": 0,
                    "title": "The Sign of the Four",
                    "user_id": 2,
                    "words_count": 0,
                },
            ],
            "page": 1,
            "pages": 1,
            "size": 50,
            "total": 2,
        }

    async def test_get_book(self, client):
        await owner(client)
        response = await client.get(f"/api/v2/books/1")
        assert response.status_code == 200
        assert response.json() == {
            "author": "Virginia Woolf",
            "id": 1,
            "is_public": True,
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

    async def test_upload_book(self, client):
        await owner(client)
        response = await client.post(
            "/api/v2/books/upload/1",
            files={"file": ("The_Voyage_Out.txt", BOOK_RAW.encode(), "text/plain")},
        )
        assert response.status_code == 200

        data = response.json()
        assert data == {
            "author": "Virginia Woolf",
            "id": 1,
            "is_public": True,
            "sentences_count": 29,
            "title": "The Voyage Out",
            "user_id": 1,
            "words_count": 201,
        }

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

        await owner(client)
        get_response = await client.get(f"/api/v2/books/1")
        book = get_response.json()
        assert book.get("title") == "The Voyage Out"

    async def test_get_my_reading_books(self, client):
        await owner(client)
        response = await client.get("/api/v2/books/reading")
        assert response.status_code == 200
        data = response.json()
        assert data == [1]

    async def test_set_and_unset_currently_reading_book(self, client):
        await owner(client)
        book_id = 3
        response = await client.post(
            "/api/v2/books/reading",
            json={
                book_id: True,
            },
        )
        assert response.status_code == 204

        response = await client.get("/api/v2/books/reading")
        assert response.json() == [1, book_id]

        response = await client.post(  # unset currently reading book
            "/api/v2/books/reading",
            json={
                book_id: False,
            },
        )
        assert response.status_code == 204

        response = await client.get("/api/v2/books/reading")
        assert response.json() == [1]


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
            "errorMessage": "",
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
class TestFlashcardRouter(BaseTestRouter):
    router = api_router

    async def test_get_flashcard(self, client):
        await owner(client)
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

    async def test_find_flashcards(self, client):
        await owner(client)
        response = await client.get("/api/v2/flashcards/find/ambush")
        assert response.status_code == 200

        data = response.json()
        assert data == [
            {
                "id": 2,
                "keyword": "ambush",
                "translations": ["zasadzka"],
                "user_id": 1,
            }
        ]

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

        response2 = await client.get("/api/v2/books/1/flashcards/1/sentences")
        assert response2.status_code == 200
        data = response2.json()

        assert data == [
            {
                "book_id": 1,
                "id": 1,
                "nr": 1,
                "sentence": "Words of two or three syllables, with the stress distributed "
                "equally between the first syllable and the last.",
            }
        ]

    async def test_flashcard_join_to_words(self, client):
        await owner(client)
        response = await client.post(
            "/api/v2/flashcards/1/words",
            json={
                "disconnect_ids": [],
                "word_ids": [1],
            },
        )
        assert response.status_code == 204

        response2 = await client.get("/api/v2/flashcards/1/words")
        assert response2.status_code == 200
        data = response2.json()

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


@pytest.mark.asyncio
class TestUserRouter(BaseTestRouter):
    router = api_router

    async def test_create_user(self, client):
        response = await client.post(
            "/api/v2/users/",
            json={
                "username": "mkowalski",
                "first_name": "Marian",
                "last_name": "Kowalski",
                "password": "secret-pasword",
                "email": "mkowalski@example.com",
                "is_active": True,
            },
        )
        assert response.status_code == 201

        data = response.json()
        assert data["username"] == "mkowalski"
        assert data["first_name"] == "Marian"
        assert data["last_name"] == "Kowalski"
        assert isinstance(data["id"], int)

    async def test_get_logged_user(self, client):
        await client_anowak(client)
        response = await client.get("/api/v2/users/whoami")
        assert response.status_code == 200

        data = response.json()
        assert data == {
            "id": 2,
            "first_name": None,
            "last_name": None,
            "username": "anowak",
        }

    async def test_search_user(self, client):
        response = await client.post(
            "/api/v2/users/search",
            json={
                "username": "anowak",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data == [
            {
                "id": 2,
                "first_name": None,
                "last_name": None,
                "username": "anowak",
            }
        ]

    async def test_get_user_flashcards(self, client):
        await client_anowak(client)
        response = await client.get("/api/v2/users/flashcards?page=1&size=10")
        assert response.status_code == 200

        data = response.json()
        assert data == {
            "items": [
                {"id": 4, "keyword": "well", "translations": ["studnia"], "user_id": 2},
                {"id": 5, "keyword": "dwarf", "translations": ["krasnal"], "user_id": 2},
            ],
            "page": 1,
            "pages": 1,
            "size": 10,
            "total": 2,
        }

    async def test_get_user_books(self, client):
        await client_anowak(client)
        response = await client.get("/api/v2/users/books?page=1&size=20")
        assert response.status_code == 200

        data = response.json()
        assert data == {
            "items": [
                {
                    "author": "Virginia Woolf",
                    "id": 2,
                    "is_public": False,
                    "sentences_count": 0,
                    "title": "To The Lighthouse",
                    "user_id": 2,
                    "words_count": 0,
                },
                {
                    "author": "Arthur Conan Doyle",
                    "id": 3,
                    "is_public": True,
                    "sentences_count": 0,
                    "title": "The Sign of the Four",
                    "user_id": 2,
                    "words_count": 0,
                },
            ],
            "page": 1,
            "pages": 1,
            "size": 20,
            "total": 2,
        }

    async def test_get_user(self, client):
        response = await client.get("/api/v2/users/1")
        assert response.status_code == 200

        data = response.json()
        assert data == {
            "id": 1,
            "first_name": None,
            "last_name": None,
            "username": "jkowalski",
        }

    async def test_update_user(self, client):
        await client_logged_in(client, "ChangeMe", "old-secret")
        response = await client.put(
            "/api/v2/users/3",
            json={
                "username": "bkupicki",
                "first_name": "Bonifacy",
                "last_name": "Kupicki",
            },
        )
        assert response.status_code == 200

        data = response.json()
        assert data["username"] == "bkupicki"
        assert data["first_name"] == "Bonifacy"
        assert data["last_name"] == "Kupicki"
        assert isinstance(data["id"], int)


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
