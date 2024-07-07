#!/usr/bin/env python3
"""
This file needs refactoring.
"""

import json
import pickle
import selectors
import socket
import sys
import types

import nltk.corpus

from train_network import word_definition_features

sel = selectors.DefaultSelector()

TRAINED_NETWORK_1 = "trained_network_100.pkl"
TRAINED_NETWORK_2 = "trained_network.pkl"

with open(TRAINED_NETWORK_1, 'rb') as f:
    classifiers = pickle.load(f)

print("Loading completed.")

def accept_wrapper(sock):
    conn, addr = sock.accept()  # Should be ready to read
    # print(f"Accepted connection from {addr}")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b"", outb=b"")
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    sel.register(conn, events, data=data)


def service_connection(key, mask):
    sock = key.fileobj
    data = key.data
    if mask & selectors.EVENT_READ:
        recv_data = sock.recv(1024)  # Should be ready to read
        if recv_data:
            data.outb += recv_data
        else:
            # print(f"Closing connection to {data.addr}")
            sel.unregister(sock)
            sock.close()

    if mask & selectors.EVENT_WRITE:
        if data.outb:
            request = json.loads(data.outb.decode())
            # print(f"{request = }")
            word = request["word"]
            sentence = request["sentence"]
            response = {
                "found": 0,
                "word": word,
                "synsets": [],
            }
            synset_name = ''
            if word in classifiers:
                classifier = classifiers[word]
                if isinstance(classifier, str):
                    synset_name = classifier
                else:
                    synset_name = classifier.classify(word_definition_features(sentence, word))
                response["matched_synset"] = synset_name
                response["found"] = 1
            for synset in nltk.corpus.wordnet.synsets(word):
                response["synsets"].append((
                    synset.name() == synset_name,
                    synset.name(),
                    synset.definition(),
                ))
            print(f"{response = }")
            response_str = json.dumps(response)
            data.outb = f"{response_str}\0".encode()
            # print(f"Echoing {data.outb!r} to {data.addr}")
            sent = sock.send(data.outb)  # Should be ready to write
            data.outb = data.outb[sent:]


if len(sys.argv) != 3:
    print(f"Usage: {sys.argv[0]} <host> <port>")
    sys.exit(1)

host, port = sys.argv[1], int(sys.argv[2])
# lsock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as lsock:
    lsock.bind((host, port))

    lsock.listen()
    print(f"Listening on {(host, port)}")
    lsock.setblocking(False)
    sel.register(lsock, selectors.EVENT_READ, data=None)

    try:
        while True:
            events = sel.select(timeout=None)
            for key, mask in events:
                if key.data is None:
                    accept_wrapper(key.fileobj)
                else:
                    service_connection(key, mask)
    except KeyboardInterrupt:
        print("Caught keyboard interrupt, exiting")
    finally:
        sel.close()

