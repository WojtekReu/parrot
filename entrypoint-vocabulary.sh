#!/bin/sh
echo "Wait 8 seconds for the database creation to complete."
sleep 8

if [ ! -f trained_network_100.pkl ]; then
    echo "Creating file trained_network_100.pkl for vocabulary server"
    python3 train_network.py
fi

echo "Starting vocabulary server"
python3 vocabulary-server.py 0.0.0.0 65432
