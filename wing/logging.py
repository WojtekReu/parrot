import json

from wing.config import settings


def write_logs(response_dict: dict):
    with open(settings.API_LOGS_PATH, 'ta') as f:
        f.write(f"{json.dumps(response_dict)}\n")
