import json
import re

import requests

from wing.logging import write_logs


def cut_html(source: str) -> str:
    """
    Dictionary API return word and some description in 'span' tags. Remove span content. For tag
    'strong' remove tag with attributes but leave his content.
    """
    source = re.sub(r" <span .*>.*</span>", "", source)
    return re.sub(r"<.*?>", "", source)


def translate(api_url: str, headers: dict, log_output) -> list[tuple[str, str]]:
    """
    Translate word using dictionary API
    """
    response = requests.get(
        url=api_url,
        headers=headers,
        verify=False,
    )

    if response.status_code == 204:
        print(f"{api_url = }")
        print("Response status: 204 No content")
        return []

    elif response.status_code == 403:
        print(f"{api_url = }")
        print("Response status: 404 - Forbidden")
        return []

    elif response.status_code == 504:
        print(f"{api_url = }")
        print("Response status: 504 - server has problem. Try later.")
        if log_output and response.text:
            logs = {
                "url": api_url,
                "response": response.text,
            }
            write_logs(logs)
        return []

    elif response.status_code != 200:
        print(f"{api_url = }")
        print(f"Response status: {response.status_code}")
        if log_output and response.text:
            logs = {
                "url": api_url,
                "response": response.text,
            }
            write_logs(logs)
        return []
    try:
        response_json = json.loads(response.content)
        if log_output and response_json:
            write_logs(response_json[0])

    except TypeError:
        print(response.raw)
        raise TypeError(response.raw)

    translations = []
    for row in response_json:
        for hit in row["hits"]:
            for rom in hit["roms"]:
                for arab in rom["arabs"]:
                    for translation in arab["translations"]:
                        source = cut_html(translation["source"])
                        target = cut_html(translation["target"])
                        translations.append((source, target))

    return translations
