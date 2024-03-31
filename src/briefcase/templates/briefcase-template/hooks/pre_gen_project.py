import re
import sys

# The restriction on application naming comes from PEP508
PEP508_NAME_RE = re.compile(r"^([A-Z0-9]|[A-Z0-9][A-Z0-9._-]*[A-Z0-9])$", re.IGNORECASE)

app_name = "{{ cookiecutter.app_name }}"

if not re.match(PEP508_NAME_RE, app_name):
    print("ERROR: `%s` is not a valid Python package name!" % app_name)

    # exits with status 1 to indicate failure
    sys.exit(1)
