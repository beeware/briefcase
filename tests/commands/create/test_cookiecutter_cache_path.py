from pathlib import Path

import pytest

from briefcase.commands.create import cookiecutter_cache_path


@pytest.mark.parametrize(
    "template, cache_dir", [
        # Git/Github URLs
        ('https://github.com/beeware/template.git', 'template'),
        ('https://github.com/beeware/template/', 'template'),
        ('https://github.com/beeware/template', 'template'),
        ('gh:beeware/template', 'template'),
        ('git+ssh://git@github.com/beeware/template.git', 'template'),
        ('git+https://beeware.org/template', 'template'),

        # Paths are valid templates. They're not cached, but this
        # method returns as if they would be, and the "is it a repo"
        # check performed by git will fail instead.
        ('/path/to/template/', 'template'),
        ('/path/to/template', 'template'),
        ('path/to/template/', 'template'),
        ('path/to/template', 'template'),
        ('template/', 'template'),
        ('template', 'template'),

        # Zipfiles are also valid templates. Same rules apply as with paths.
        ('https://example.com/path/to/template.zip', 'template.zip'),
        ('/path/to/template.zip', 'template.zip'),
        ('path/to/template.zip', 'template.zip'),
    ]
)
def test_cookiecutter_cache_path(template, cache_dir):
    "The cookiecutter cache path can be determiend for various template types"
    assert cookiecutter_cache_path(template) == (
        Path.home() / '.cookiecutters' / cache_dir
    )
