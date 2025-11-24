#!/usr/bin/env python
"""
Run downloader for nltk and install packages: dolch, punkt, averaged_perceptron_tagger, wordnet.
"""
import os

from dotenv import load_dotenv
import nltk

load_dotenv("./.env")

NLTK_DATA_PREFIX = os.environ["NLTK_DATA_PREFIX"]

nltk.download("dolch", download_dir=NLTK_DATA_PREFIX)  # Dolch word list
nltk.download("punkt", download_dir=NLTK_DATA_PREFIX)  # Punkt Tokenizer Models
nltk.download(
    "averaged_perceptron_tagger", download_dir=NLTK_DATA_PREFIX
)  # Averaged Perceptron Tagger
nltk.download("wordnet", download_dir=NLTK_DATA_PREFIX)  # A Lexical Database for English
nltk.download('omw-1.4', download_dir=NLTK_DATA_PREFIX)  # Open Multilingual Wordnet
nltk.download('tagsets', download_dir=NLTK_DATA_PREFIX)
