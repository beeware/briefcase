import subprocess
from pathlib import Path
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.adb import get_devices

DUMMY_SDK_PATH = Path('.')


def devices_result(name):
    """Load `adb devices` output file from the sample directory, and return the content"""
    filename = Path(__file__).parent / 'devices' / '{name}.txt'.format(name=name)
    with filename.open() as f:
        return f.read()


def test_adb_missing():
    "If adb is missing or fails to start, an exception is raised."
    sub = mock.MagicMock()
    sub.check_output.side_effect = subprocess.CalledProcessError(
        cmd=['adb', 'devices'],
        returncode=1
    )

    with pytest.raises(BriefcaseCommandError):
        get_devices(sub=sub, sdk_path=DUMMY_SDK_PATH)


def test_no_devices():
    "If there are no devices available, expect the empty list"
    sub = mock.MagicMock()
    sub.check_output.return_value = devices_result('no-devices')
    devices = get_devices(sub=sub, sdk_path=DUMMY_SDK_PATH)

    assert devices == []


def test_one_device():
    "If there are no devices available, expect the empty list"
    sub = mock.MagicMock()
    sub.check_output.return_value = devices_result('one-device')
    devices = get_devices(sub=sub, sdk_path=DUMMY_SDK_PATH)

    assert devices == ['emulator-5554']
