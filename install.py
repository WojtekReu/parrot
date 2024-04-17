#!/usr/bin/env python
"""
Run downloader for nltk and install packages: dolch, punkt, averaged_perceptron_tagger, wordnet.
"""

import nltk
nltk.download('dolch')
nltk.download('punkt')
nltk.download('averaged_perceptron_tagger')
nltk.download('wordnet')
