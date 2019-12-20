import subprocess
from pathlib import Path
from unittest import mock

import pytest

from briefcase.exceptions import BriefcaseCommandError
from briefcase.integrations.xcode import get_simulators


def simctl_result(name):
    """Load a simctl result file from the sample directory, and return the content"""
    filename = Path(__file__).parent / 'simctl' / '{name}.json'.format(name=name)
    with filename.open() as f:
        return f.read()


def test_simctl_missing():
    "If simctl is missing or fails to start, an exception is raised."
    sub = mock.MagicMock()
    sub.check_output.side_effect = subprocess.CalledProcessError(
        cmd=['xcrun', 'simctl', 'list', '-j'],
        returncode=1
    )

    with pytest.raises(BriefcaseCommandError):
        get_simulators('iOS', sub=sub)


def test_no_runtimes():
    "If there are no runtimes available, no simulators will be found"
    sub = mock.MagicMock()
    sub.check_output.return_value = simctl_result('no-runtimes')

    simulators = get_simulators('iOS', sub=sub)

    assert simulators == {}


def test_single_iOS_runtime():
    "If an iOS version is installed, devices can be found"
    sub = mock.MagicMock()
    sub.check_output.return_value = simctl_result('iOS-13.2-only')

    simulators = get_simulators('iOS', sub=sub)

    assert simulators == {
        '13.2': {
            '20C5B052-F47A-4816-8584-9F1500B50477': 'iPad Pro (9.7-inch)',
            '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D': 'iPhone 11',
            '314E772A-8034-44B4-9B28-3EE80C958F0A': 'iPad Pro (12.9-inch) (3rd generation)',
            '36E4663B-A10F-470F-94E8-05C3DC692AC9': 'iPad Pro (11-inch)',
            '5497F9B2-F4F3-454A-A9DD-993DF44EBB63': 'iPhone 8 Plus',
            '939B1EF6-C25A-4056-B61F-20A2835E89D6': 'iPad (7th generation)',
            '9CFF88F3-489F-444E-8131-FF8731768D31': 'iPhone 11 Pro',
            'B490A004-6B5C-4C2C-BE4D-ACAB5D36C25D': 'iPad Air (3rd generation)',
            'C9A005C8-9468-47C5-8376-68A6E3408209': 'iPhone 8',
            'EEEBA06C-81F9-407C-885A-2261306DB2BE': 'iPhone 11 Pro Max',
        }
    }


def test_watchOS_runtime():
    "Runtimes other than iOS can be requested."
    sub = mock.MagicMock()
    sub.check_output.return_value = simctl_result('iOS-13.2-only')

    simulators = get_simulators('watchOS', sub=sub)

    assert simulators == {
        '6.1': {
            '3EE6E657-9351-406C-9B39-24F0CECCBC74': 'Apple Watch Series 5 - 40mm',
            '3EE83472-A457-4531-A221-67E332359EEC': 'Apple Watch Series 4 - 40mm',
            'ABC5ABF6-C24E-4500-ADDC-A9375FFC36F6': 'Apple Watch Series 5 - 44mm',
            'C240F238-3C85-46F1-AC40-D32C7896D430': 'Apple Watch Series 4 - 44mm',
        }
    }


def test_multiple_iOS_runtime():
    "If multiple iOS versions are installed, this will be reflected in results"
    sub = mock.MagicMock()
    sub.check_output.return_value = simctl_result('multiple-iOS-versions')

    simulators = get_simulators('iOS', sub=sub)

    assert simulators == {
        '13.2': {
            '20C5B052-F47A-4816-8584-9F1500B50477': 'iPad Pro (9.7-inch)',
            '2D3503A3-6EB9-4B37-9B17-C7EFEF2FA32D': 'iPhone 11',
            '314E772A-8034-44B4-9B28-3EE80C958F0A': 'iPad Pro (12.9-inch) (3rd generation)',
            '36E4663B-A10F-470F-94E8-05C3DC692AC9': 'iPad Pro (11-inch)',
            '5497F9B2-F4F3-454A-A9DD-993DF44EBB63': 'iPhone 8 Plus',
            '939B1EF6-C25A-4056-B61F-20A2835E89D6': 'iPad (7th generation)',
            '9CFF88F3-489F-444E-8131-FF8731768D31': 'iPhone 11 Pro',
            'B490A004-6B5C-4C2C-BE4D-ACAB5D36C25D': 'iPad Air (3rd generation)',
            'C9A005C8-9468-47C5-8376-68A6E3408209': 'iPhone 8',
            'EEEBA06C-81F9-407C-885A-2261306DB2BE': 'iPhone 11 Pro Max',
        },
        '10.3': {
            '04D415A8-FBF9-42AD-9F79-0CD452FA09D8': 'iPad Pro (9.7 inch)',
            '0BB80120-FA02-4597-A1BA-DB8CDE4F086D': 'iPhone 5s',
            '1E2A9CEF-AC9B-4CE3-AA66-9EBD785AAF23': 'iPhone 6 Plus',
            '28D58EF9-C079-4809-A9E7-DA0BD7170DA6': 'iPad Air 2',
            '425DE89A-49EA-44B0-9B2E-55BB18D4EF42': 'iPhone SE',
            '6998CA09-44B5-4963-8F80-265412D99683': 'iPhone 7',
            '6CF6870A-A7A6-4A42-8FE7-26FC3E131CDD': 'iPad (5th generation)',
            'A2326477-DD25-4A61-A529-C772E364EDF3': 'iPad Pro (10.5-inch)',
            'B7DEA42B-4740-4542-A1D5-8827546F531B': 'iPhone 7 Plus',
            'BD9BF79E-92E2-444F-8708-4041B7D03681': 'iPad Air',
            'CC954566-F315-4692-A754-DECDF72967CD': 'iPhone 5',
            'D7BBAD14-38FD-48F5-ACFD-B1193F829216': 'iPhone 6',
            'DA9B9F49-A070-4FD7-A6BF-8F49DC72194E': 'iPhone 6s Plus',
            'E582FF8E-A5DC-4985-B6C8-8D6B1795DF62': 'iPad Pro (12.9-inch) (2nd generation)',
            'E956D6AE-29F5-4780-A02A-D3426B7B4018': 'iPad Pro (12.9 inch)',
            'F9A6C462-9A4A-438A-B541-848F0E6DBE5A': 'iPhone 6s'
        }
    }


def test_unknown_runtime():
    "If an unknown runtime is requested, no devices will be found"
    sub = mock.MagicMock()
    sub.check_output.return_value = simctl_result('multiple-iOS-versions')

    simulators = get_simulators('whizzOS', sub=sub)

    assert simulators == {}
