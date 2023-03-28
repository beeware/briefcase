import subprocess
import platform

import pytest

from .conftest import CREATE_NEW_PROCESS_GROUP, CREATE_NO_WINDOW


@pytest.mark.skipif(platform.system() != "Windows", reason="requires Windows")
def test_creationflag_constants():
    assert subprocess.CREATE_NEW_PROCESS_GROUP == CREATE_NEW_PROCESS_GROUP
    assert subprocess.CREATE_NO_WINDOW == CREATE_NO_WINDOW
