import pytest

from ..tools_external import cut_html


def test_cut_html():
    source = 'tender <span class="perf">N</span>'
    result = cut_html(source)
    expected = "tender"
    assert result == expected


def test_cut_html_longer_output():
    source = 'wzywać <span class="perf">[<span class="tempus">perf</span> <span class="perf">wezwać</span>]</span> do składania ofert'
    result = cut_html(source)
    expected = "wzywać do składania ofert"
    assert result == expected


def test_cut_html_strong():
    source = '<strong class=\"headword\">pervade</strong> <span class=\"collocator\">smell, smoke, light</span>'
    result = cut_html(source)
    expected = "pervade"
    assert result == expected
