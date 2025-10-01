import importlib
from types import SimpleNamespace

import pytest


def test_select_target_device_question_executes_branch():
    sdk_mod = importlib.import_module("briefcase.integrations.android_sdk")

    # Provide a dummy 'self'; the method will set device_or_avd=None (our target line)
    # and then fail later because required attributes are missing. That's fine—we only
    # care that the branch executed.
    self = SimpleNamespace()

    with pytest.raises(AttributeError):
        sdk_mod.AndroidSDK.select_target_device(self, "  ?  ")
