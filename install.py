#!/usr/bin/env python
"""
Run downloader for nltk and install packages: dolch, punkt, averaged_perceptron_tagger, wordnet.
"""

import nltk
nltk.download('dolch')  # Dolch word list
nltk.download('punkt')  # Punkt Tokenizer Models
nltk.download('averaged_perceptron_tagger')  # Averaged Perceptron Tagger
nltk.download('wordnet')  # A Lexical Database for English
