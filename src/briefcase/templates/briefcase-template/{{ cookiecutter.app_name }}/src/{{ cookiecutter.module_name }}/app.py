"""
{{ cookiecutter.description|escape_toml }}
"""

{% if cookiecutter.app_source %}
{{ cookiecutter.app_source }}
{% else %}

def main():
    # This should start and launch your app!
    pass
{% endif %}
