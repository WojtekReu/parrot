from nltk.tokenize import word_tokenize

def neighbour_words(tokens, keyword, space=3):
    features = {}
    try:
        index = tokens.index(keyword)
    except ValueError:
        # TODO: check also for declination and other lemmas with declination
        raise ValueError(f"No {keyword} in tokens: {tokens}")

    for i in range(1, space + 1):
        before = index - i
        after = index + i
        if 0 <= before:
            features[f"before_{i}"] = tokens[before]
        if after < len(tokens):
            features[f"after_{i}"] = tokens[after]

    return features


def word_definition_features(sentence: str, keyword: str):
    tokens = word_tokenize(sentence)
    features = neighbour_words(tokens, keyword, space=5)

    return features
