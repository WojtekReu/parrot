#!/usr/bin/env python
"""
Create relations between Word and Sentence in db and add Context for Word from book if it exists
in personal library.
"""
import typer

from wing.processing import connect_words_to_sentences, find_books


def main():
    connect_words_to_sentences()
    find_books()


if __name__ == "__main__":
    typer.run(main)
