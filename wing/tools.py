
def tag_to_pos(tag: str) -> str:
    """
    Change tag ex. 'VBD' to pos ex. 'v'
    """
    match tag:
        case "NN" | "NNP" | "NNPS" | "NNS":  # nouns
            pos = "n"
        case "VB" | "VBD" | "VBG" | "VBN" | "VBP" | "VBZ":  # verbs
            pos = "v"
        case "JJ" | "JJR" | "JJS":  # adjectives
            pos = "a"
        case "RB" | "RBR" | "RBS":  # adverbs
            pos = "r"
        case _:
            pos = None
    return pos
