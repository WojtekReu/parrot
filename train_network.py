#!/usr/bin/env python
"""
This file needs refactoring
"""

import asyncio
import pickle
from collections import defaultdict

import nltk
from nltk.corpus import wordnet

from wing.crud.word import get_words
from wing.db.session import get_session
from wing.models import *


def split_sentence(sentence: str) -> set:
    result = set()
    for word in sentence.replace(",", "").replace(";", "").split():
        if 2 < len(word):
            result.add(word)
    return result


WORDS_LIMIT = 100


async def async_main():
    synsets_dict = defaultdict(list)
    async for session in get_session():
        for word_lem in await get_words(session, limit=WORDS_LIMIT):
            for synset in wordnet.synsets(word_lem):
                sentences = [synset.definition()]
                sentences.extend(synset.examples())
                synsets_dict[word_lem].append(
                    (
                        sentences,
                        synset.name(),
                        # synset.topic_domains(),
                    )
                )

    return synsets_dict


def word_definition_features(sentence: str, keyword: str):
    features = {}
    for word in sentence.replace(",", "").replace(";", "").split():
        if word != keyword and 2 < len(word) and "'" not in word:
            features[word.lower()] = True
    return features


if __name__ == "__main__":
    synsets_data = asyncio.run(async_main())

    print(f"Synsets len: {len(synsets_data)}")

    accuracy_values = []
    classifiers = defaultdict(list)
    for word_lem, synsets in synsets_data.items():
        if len(synsets) == 1:
            classifiers[word_lem] = synsets[0][1]  # synset_name (str)
        else:
            featuresets = []
            for sentences, synset_name in synsets:
                for sentence in sentences:
                    featuresets.append(
                        (
                            word_definition_features(sentence, word_lem),
                            synset_name,
                        )
                    )
            classifiers[word_lem] = nltk.NaiveBayesClassifier.train(featuresets)

    with open("trained_network_100.pkl", "wb") as f:
        pickle.dump(classifiers, f, -1)

    print("Task completed :)")
