import pytest

import json

from ..tools_external import translate
from unittest.mock import patch

json_out = (
    {
        "lang": "en",
        "hits": [
            {
                "roms": [
                    {
                        "arabs": [
                            {
                                "translations": [
                                    {
                                        "source": '<strong class="headword">post</strong>',
                                        "target": 'poczta <span class="genus"><acronym title="feminine">f</acronym></span>',
                                    },
                                    {
                                        "source": '<strong class="headword">post</strong>',
                                        "target": 'korespondencja <span class="genus"><acronym title="feminine">f</acronym></span>',
                                    },
                                ]
                            }
                        ]
                    }
                ]
            }
        ],
    },
)


def test_word_post():
    with patch("requests.get") as mock_request:
        mock_request.return_value.status_code = 200
        mock_request.return_value.raw = "raw_response_test"
        mock_request.return_value.json.return_value = json_out
        mock_request.return_value.content = json.dumps(json_out)

        result = translate("some_url", {}, False)
        expected = ("post", "poczta")

        assert expected in result
