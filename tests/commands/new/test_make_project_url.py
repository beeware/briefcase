import pytest


@pytest.mark.parametrize(
    'app_name, bundle, candidate',
    [
        ('some-app', 'com.example', 'https://example.com/some-app'),
        ('some_app', 'com.example.more', 'https://more.example.com/some_app'),
        ('myapp', 'com.example', 'https://example.com/myapp'),
    ]
)
def test_make_project_url(new_command, app_name, bundle, candidate):
    "An app name and bundle can be converted into a valid URL."
    url = new_command.make_project_url(bundle, app_name)
    assert url == candidate
    # Double check - the app name passes the validity check.
    assert new_command.is_valid_url(url)
