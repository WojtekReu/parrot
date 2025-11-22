import logging
from typing import Any

import nltk
import pickle
from wing.definition_feature_functions import word_definition_features
from wing.config import settings

logging.basicConfig(encoding='utf-8', level=logging.INFO)
logger = logging.getLogger(__name__)


class Definitions:
    vocabulary = {}

    def load(self, vocabulary_path):
        try:
            with open(vocabulary_path, "rb") as f:
                self.vocabulary = pickle.load(f)
        except FileNotFoundError:
            logger.warning(f"Vocabulary file not found, skipping.")
            pass

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

    def search_in_nltk(self, word: str) -> dict:
        response = {
            "found": 0,
            "word": word,
            "synsets": []
        }
        for synset in nltk.corpus.wordnet.synsets(word):
            word_dict = {}
            word_dict['name'] = synset.name()
            word_dict['definition'] = synset.definition()
            word_dict['pol'] = ", ".join([l.name() for l in synset.lemmas(lang='pol')])
            response["synsets"].append(word_dict)

        return response

definitions = Definitions()
definitions.load(settings.VOCABULARY_BASE)
