{% if cookiecutter.app_start_source %}
{{ cookiecutter.app_start_source }}
{% else %}
from {{ cookiecutter.module_name }}.app import main


if __name__ == "__main__":
    main()
{% endif %}
