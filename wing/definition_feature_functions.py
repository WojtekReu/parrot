from nltk.tokenize import word_tokenize

from wing.models.word import WordBase


def neighbour_words(tokens: list, word: WordBase, space=3):
    features = {}
    keyword = word.lem
    tokens_lower = [t.lower() for t in tokens]
    try:
        index = tokens_lower.index(keyword)
    except ValueError:
        index = None
        for keyword in word.declination.values():
            try:
                index = tokens_lower.index(keyword)
                break
            except ValueError:
                pass
        if not index:
            raise ValueError(f"No {keyword} in tokens: {tokens}")

    for i in range(1, space + 1):
        before = index - i
        after = index + i
        if 0 <= before:
            features[f"before_{i}"] = tokens[before]
        if after < len(tokens):
            features[f"after_{i}"] = tokens[after]

    return features


def word_definition_features(sentence: str, keyword: WordBase):
    tokens = word_tokenize(sentence)
    features = neighbour_words(tokens, keyword, space=5)

    return features
