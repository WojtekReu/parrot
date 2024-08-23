from typing import Any

import nltk
import pickle
from wing.definition_feature_functions import word_definition_features
from wing.config import settings

class Definitions:
    vocabulary = {}

    def load(self, vocabulary_path):
        with open(vocabulary_path, "rb") as f:
            self.vocabulary = pickle.load(f)

    def find_definition(self, word: str, sentence: str) -> dict[str, Any]:
        response = {
            "found": 0,
            "word": word,
            "synsets": [],
        }
        synset_name = ""
        if word in self.vocabulary:
            classifier = self.vocabulary[word]
            if isinstance(classifier, str):
                synset_name = classifier
            else:
                synset_name = classifier.classify(word_definition_features(sentence, word))
            response["matched_synset"] = synset_name
            response["found"] = 1
        for synset in nltk.corpus.wordnet.synsets(word):
            response["synsets"].append(
                (
                    synset.name() == synset_name,
                    synset.name(),
                    synset.definition(),
                )
            )
        return response

definitions = Definitions()
definitions.load(settings.VOCABULARY_BASE)
