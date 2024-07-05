#!/usr/bin/env python
"""
Run downloader for nltk and install packages: dolch, punkt, averaged_perceptron_tagger, wordnet.
"""
from wing.config import settings

import nltk

nltk.download("dolch", download_dir=settings.NLTK_DATA_PREFIX)  # Dolch word list
nltk.download("punkt", download_dir=settings.NLTK_DATA_PREFIX)  # Punkt Tokenizer Models
nltk.download(
    "averaged_perceptron_tagger", download_dir=settings.NLTK_DATA_PREFIX
)  # Averaged Perceptron Tagger
nltk.download("wordnet", download_dir=settings.NLTK_DATA_PREFIX)  # A Lexical Database for English
