from typing import Coroutine

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from wing.crud.book import create_book, get_book
from wing.crud.sentence import create_sentence, count_sentences_for_book
from wing.crud.word import count_words_for_book
from wing.models.book import BookCreate
from wing.models.sentence import SentenceCreate
from wing.processing import load_sentences, save_prepared_words

BOOK_RAW1 = """
CHAPTER I
Mr. Jones, of the Manor Farm, had locked the hen-houses for the night, but was too drunk to remember to shut the popholes. With the ring of light from his lantern dancing from side to side, he lurched across the yard, kicked off his boots at the back door, drew himself a last glass of beer from the barrel in the scullery, and made his way up to bed, where Mrs. Jones was already snoring.
As soon as the light in the bedroom went out there was a stirring and a fluttering all through the farm buildings. Word had gone round during the day that old Major, the prize Middle White boar, had had a strange dream on the previous night and wished to communicate it to the other animals. It had been agreed that they should all meet in the big barn as soon as Mr. Jones was safely out of the way. Old Major (so he was always called, though the name under which he had been exhibited was Willingdon Beauty) was so highly regarded on the farm that everyone was quite ready to lose an hour's sleep in order to hear what he had to say.
At one end of the big barn, on a sort of raised platform, Major was already ensconced on his bed of straw, under a lantern which hung from a beam. He was twelve years old and had lately grown rather stout, but he was still a majestic-looking pig, with a wise and benevolent appearance in spite of the fact that his tushes had never been cut. Before long the other animals began to arrive and make themselves comfortable after their different fashions. First came the three dogs, Bluebell, Jessie, and Pincher, and then the pigs, who settled down in the straw immediately in front of the platform. The hens perched themselves on the window-sills, the pigeons fluttered up to the rafters, the sheep and cows lay down behind the pigs and began to chew the cud. The two cart-horses, Boxer and Clover, came in together, walking very slowly and setting down their vast hairy hoofs with great care lest there should be some small animal concealed in the straw. Clover was a stout motherly mare approaching middle life, who had never quite got her figure back after her fourth foal. Boxer was an enormous beast, nearly eighteen hands high, and as strong as any two ordinary horses put together. A white stripe down his nose gave him a somewhat stupid appearance, and in fact he was not of first-rate intelligence, but he was universally respected for his steadiness of character and tremendous powers of work. After the horses came Muriel, the white goat, and Benjamin, the donkey. Benjamin was the oldest animal on the farm, and the worst tempered. He seldom talked, and when he did, it was usually to make some cynical remark—for instance, he would say that God had given him a tail to keep the flies off, but that he would sooner have had no tail and no flies. Alone among the animals on the farm he never laughed. If asked why, he would say that he saw nothing to laugh at. Nevertheless, without openly admitting it, he was devoted to Boxer; the two of them usually spent their Sundays together in the small paddock beyond the orchard, grazing side by side and never speaking.
"""


@pytest.mark.asyncio
async def test_load_sentences(session: AsyncSession):
    book = await get_book(session, 3)
    pos_collections = await load_sentences(session, BOOK_RAW1, book.id)
    assert len(pos_collections) == 4
    assert len(pos_collections[0]) == 105
    assert len(pos_collections[0]["animal"]["sentence_ids"]) == 5
    del pos_collections[0]["animal"]["sentence_ids"]
    assert pos_collections[0]["animal"] == {
        "count": 5,
        "declination": {"NNS": "animals"},
        "flashcard_ids": set(),
        "lem": "animal",
        "pos": "n",
    }


PREPARED_WORDS = {
    "animal": {
        "count": 5,
        "declination": {"NNS": "animals"},
        "flashcard_ids": set(),
        "lem": "animal",
        "pos": "n",
        "sentence_ids": {17, 19, 4, 9, 12},
    },
    "give": {
        "count": 2,
        "declination": {"VBD": "gave", "VBN": "given"},
        "flashcard_ids": set(),
        "lem": "give",
        "pos": "v",
        "sentence_ids": {18, 15},
    },
    "seldom": {
        "count": 1,
        "declination": {},
        "flashcard_ids": set(),
        "lem": "seldom",
        "pos": "r",
        "sentence_ids": {18},
    },
    "benevolent": {
        "count": 1,
        "declination": {},
        "flashcard_ids": set(),
        "lem": "benevolent",
        "pos": "a",
        "sentence_ids": {8},
    },
}


@pytest.mark.asyncio
async def test_save_prepared_words(session: AsyncSession):
    book = await get_book(session, 3)
    for lem, values in PREPARED_WORDS.items():
        sentence = await create_sentence(
            session,
            SentenceCreate(
                nr=1,
                book_id=book.id,
                sentence="This is the test example sentence.",
            ),
        )
        values["sentence_ids"] = {sentence.id}

    await save_prepared_words(session, PREPARED_WORDS)
    assert True


@pytest.mark.asyncio
async def test_count_sentences_and_words(session: AsyncSession):
    book = await create_book(session, BookCreate(
        title="Animal Farm",
        author="Eric Arthur Blair",
    ))
    pos_collections = await load_sentences(session, BOOK_RAW1, book.id)
    for dest in pos_collections:
        await save_prepared_words(session, dest)

    sentences_count = await count_sentences_for_book(session, book.id)
    words_count = await count_words_for_book(session, book.id)

    assert sentences_count == 21
    assert words_count == 226
