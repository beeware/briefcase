{% if cookiecutter.test_framework == 'pytest' -%}

def test_first():
    """An initial test for the app."""
    assert 1 + 1 == 2
{% elif cookiecutter.test_framework == "unittest" %}
import unittest


class {{ cookiecutter.class_name }}Tests(unittest.TestCase):
    def test_first(self):
        """An initial test for the app."""
        self.assertEqual(1 + 1, 2)
{% endif %}