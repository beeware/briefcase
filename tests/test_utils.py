import json
from importlib import metadata

import pytest

from briefcase.utils import _is_editable_pep610


class DummyDist:
    def __init__(self, direct_url):
        self._direct_url = direct_url

    def read_text(self, name):
        return self._direct_url if name == "direct_url.json" else None


@pytest.mark.parametrize(
    "direct_url,is_editable",
    [
        (json.dumps({"dir_info": {"editable": True}}), True),  # editable
        (json.dumps({"dir_info": {"editable": False}}), False),  # not editable
        (json.dumps({}), False),  # missing dir_info
        (None, False),  # missing direct_url.json
        ("not-json", False),  # invalid JSON
    ],
)
def test_is_editable_pep610(monkeypatch, direct_url, is_editable):
    monkeypatch.setattr(metadata, "distribution", lambda name: DummyDist(direct_url))
    assert _is_editable_pep610("briefcase") is is_editable


def test_is_editable_pep610_package_not_found(monkeypatch):
    def raise_not_found(name):
        raise metadata.PackageNotFoundError

    monkeypatch.setattr(metadata, "distribution", raise_not_found)
    with pytest.raises(metadata.PackageNotFoundError):
        _is_editable_pep610("briefcase")
