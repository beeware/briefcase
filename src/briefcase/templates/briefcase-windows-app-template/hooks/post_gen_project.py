import os
from pathlib import Path


BIN_PATH = Path("src")

# Move the stub for the Python version into the final location
os.rename(BIN_PATH / 'Stub-{{ cookiecutter.python_version|py_tag }}.exe', BIN_PATH / '{{ cookiecutter.formal_name }}.exe')

# Delete all remaining stubs
for stub in BIN_PATH.glob("Stub-*.exe"):
    os.unlink(stub)
