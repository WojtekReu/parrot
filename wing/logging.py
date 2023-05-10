import json

from wing.alchemy import API_LOGS_PATH


def write_logs(response_dict: dict):
    with open(API_LOGS_PATH, 'ta') as f:
        f.write(f"{json.dumps(response_dict)}\n")
