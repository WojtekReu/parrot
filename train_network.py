#!/usr/bin/env python
"""
This script not working properly yet
"""

import asyncio
import logging
import pickle
from collections import defaultdict

import nltk
from nltk.corpus import wordnet
from nltk.classify import accuracy

from wing.config import settings
from wing.crud.word import get_words, get_word_sentences
from wing.db.session import get_session
from wing.definition_feature_functions import word_definition_features
from wing.models import *

logging.basicConfig(encoding="utf-8", level=settings.LOGGING_LEVEL)
logger = logging.getLogger(__name__)

WORDS_LIMIT = 100


async def async_main():
    synsets_dict = defaultdict(list)
    async for session in get_session():
        for word in await get_words(session, limit=WORDS_LIMIT, has_synset=True):
            synset = wordnet.synset(word.synset)
            synset_base = synset.name().split(".")[0]

            sentences = []
            for example in synset.examples():
                sentences.append(example.replace(synset_base, word.lem))

            for sentence in (await get_word_sentences(session, word.id)):
                sentences.append(sentence.sentence)

            synsets_dict[word.lem].append(
                (
                    sentences,
                    synset.name(),
                    word.declination,
                    # synset.topic_domains(),
                )
            )

    return synsets_dict


if __name__ == "__main__":
    synsets_data = asyncio.run(async_main())

    logger.debug(f"Synsets len: {len(synsets_data)}")

    accuracy_values = []
    classifiers = defaultdict(list)
    for word_lem, synsets in synsets_data.items():
        if len(synsets) == 1:
            classifiers[word_lem] = synsets[0][1]  # synset_name (str)
        else:
            featuresets = []
            for sentences, synset_name, declination in synsets:
                for sentence in sentences:
                    featuresets.append(
                        (
                            word_definition_features(sentence, word_lem),
                            synset_name,
                        )
                    )
            half = len(featuresets) // 2
            logger.debug(f"{half = }")
            train_set, test_set = featuresets[half:], featuresets[:half]

            classifier = nltk.NaiveBayesClassifier.train(train_set)

            accuracy_value = accuracy(classifier, test_set)
            accuracy_values.append(accuracy_value)
            logger.debug(f"lem: {word_lem} - {accuracy_value}")
            classifier.show_most_informative_features(9)
            classifiers[word_lem] = classifier

    with open("trained_network_100.pkl", "wb") as f:
        pickle.dump(classifiers, f, -1)

    logger.info("Task completed :) ")
