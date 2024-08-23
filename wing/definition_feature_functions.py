
def word_definition_features(sentence: str, keyword: str):
    features = {}
    for word in sentence.replace(",", "").replace(";", "").split():
        if word != keyword and 2 < len(word) and "'" not in word:
            features[word.lower()] = True
    return features
