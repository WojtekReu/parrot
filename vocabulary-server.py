#!/usr/bin/env python3
"""
Vocabulary server. Load vocabulary from database and listen on specified port.
"""

import json
import logging
import pickle
import selectors
import socket
import types

import nltk.corpus
import typer

from train_network import word_definition_features
from wing.config import settings

logging.basicConfig(encoding='utf-8', level=logging.INFO)
logger = logging.getLogger(__name__)

class Vocabulary:
    classifiers: dict | None = None

    def __init__(self, base_file):
        self.base_file: str = base_file

    def load(self):
        with open(self.base_file, "rb") as f:
            self.classifiers = pickle.load(f)


class Server:
    def __init__(self, host, port, vocabulary):
        self.host: str = host
        self.port: int = port
        self.vocabulary: dict = vocabulary
        self.selector = selectors.DefaultSelector()

    def listen(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as lsock:
            lsock.bind((self.host, self.port))

            lsock.listen()
            logger.info(f"Listening on {self.host}:{self.port}")
            lsock.setblocking(False)
            self.selector.register(lsock, selectors.EVENT_READ, data=None)

            try:
                while True:
                    events = self.selector.select(timeout=None)
                    for key, mask in events:
                        if key.data is None:
                            self.accept_wrapper(key.fileobj)
                        else:
                            self.service_connection(key, mask)
            except KeyboardInterrupt:
                logger.info("Exited on keyboard interrupt")
            finally:
                self.selector.close()

    def accept_wrapper(self, sock):
        conn, addr = sock.accept()  # Should be ready to read
        logger.info(f"Accepted connection from {addr}")
        conn.setblocking(False)
        data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
        events = selectors.EVENT_READ | selectors.EVENT_WRITE
        self.selector.register(conn, events, data=data)

    def service_connection(self, key, mask):
        sock = key.fileobj
        data = key.data
        if mask & selectors.EVENT_READ:
            recv_data = sock.recv(1024)  # Should be ready to read
            if recv_data:
                data.outb += recv_data
            else:
                logger.info(f"Closing connection to {data.addr}")
                self.selector.unregister(sock)
                sock.close()

        if mask & selectors.EVENT_WRITE:
            if data.outb:
                request = json.loads(data.outb.decode())
                logger.info(f"{request = }")
                word = request["word"]
                sentence = request["sentence"]
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
                logger.info(f"{response = }")
                response_str = json.dumps(response)
                data.outb = f"{response_str}\0".encode()
                sent = sock.send(data.outb)  # Should be ready to write
                data.outb = data.outb[sent:]


def main():
    """
    Run server with vocabulary from NLTK
    """
    vc = Vocabulary(settings.VOCABULARY_BASE)
    vc.load()
    server = Server(settings.VOCABULARY_HOST, settings.VOCABULARY_PORT, vc.classifiers)
    server.listen()


if __name__ == "__main__":
    typer.run(main)