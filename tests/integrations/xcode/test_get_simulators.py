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
        'iOS 13.2': {
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
        'watchOS 6.1': {
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
        'iOS 13.2': {
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
        'iOS 10.3': {
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


def test_alternate_format():
    "The alternate format for device versions can be parsed"
    sub = mock.MagicMock()
    sub.check_output.return_value = simctl_result('alternate-format')

    simulators = get_simulators('iOS', sub=sub)

    assert simulators == {
        'iOS 12.0': {
            '00751854-B15C-4C77-ACF7-2657CEF7DB58': 'iPhone 7',
            '109F9913-9D7C-4170-974D-49DD6ED30AFE': 'iPhone XR',
            '184397FC-2FBD-4342-9B93-C3B9710C86CD': 'iPhone 6s Plus',
            '2C44F495-398B-4613-B798-D8DE8E3A1845': 'iPhone XS',
            '354F7547-6A8B-4191-9A89-5EB707D6A1F0': 'iPhone 8',
            '3A6C95FA-E3E9-4698-8E51-7EC60C4A642E': 'iPad Pro (10.5-inch)',
            '485AA24A-BABF-4635-B849-8EE7BA10F259': 'iPad (5th generation)',
            '497C2D40-6AA3-4485-B9DA-0C9615511854': 'iPad Air 2',
            '54CD64AE-49FE-47D1-AF3A-8E7F02909E25': 'iPhone 6s',
            '5773DBDD-EA60-4E53-8A96-57BD6C644DD5': 'iPad Pro (9.7-inch)',
            '85A06C2A-ACDF-4A19-8C90-386DCF887670': 'iPhone XS Max',
            '921C8E93-702E-47AB-A233-88982C2BBD95': 'iPhone 6',
            '9F055949-5DF2-40D8-A955-A8517F213E24': 'iPhone 8 Plus',
            'A1970E36-8906-48FF-8B3C-819A0A88D9D6': 'iPhone 6 Plus',
            'A604E87D-B2BF-4190-B974-C29FC40A6F15': 'iPhone 7 Plus',
            'AAF12280-0DC2-472F-87C5-2F141A6F0C55': 'iPad Pro (12.9-inch) (2nd generation)',
            'AC8D34EB-F42D-4518-A09C-3C3AD7FCAC8C': 'iPhone SE',
            'C4DE0942-3A85-4091-98CC-C4A90E2D07C3': 'iPhone X',
            'C8E5AD6A-B7EB-480F-89E8-341FD45AAFFC': 'iPad Air',
            'D675DECD-F18D-4950-A72C-22D2F3D39FFC': 'iPad Pro (12.9-inch)',
            'DCBB1DBB-D3AF-4A65-AC35-A367B0E5BB8A': 'iPad (6th generation)',
            'E98A6654-E843-43A5-8BD8-5D4C891EBA15': 'iPhone 5s'},
        'iOS 12.1': {
            '01A9DC6A-58D3-4D7D-AC98-9F0689990DC6': 'iPhone 8 Plus',
            '04325672-C35F-4E5E-BD08-EAC478B7165C': 'iPhone XS',
            '28F0335D-1B4D-4493-A5C5-4E86E2916178': 'iPhone 6',
            '28F16D36-8878-489F-A8CF-33E7037D252B': 'iPad Pro (9.7-inch)',
            '512E11C5-5654-4F10-98D7-F75C50DF5DB7': 'iPad Pro (12.9-inch) (3rd generation)',
            '53D7FAF6-83D7-415D-A3B4-20A9D8C37C44': 'iPhone 5s',
            '5EF8EAA5-9D63-4F53-8896-57F9D59DECF9': 'iPhone 6s',
            '61D96B3A-3747-41AC-92F7-2177E467A196': 'iPad Pro (10.5-inch)',
            '64467336-1571-403C-9225-77133D27E525': 'iPhone 7',
            '64B63780-6911-4459-8024-F97A2DA5E36D': 'iPhone 7 Plus',
            '765EA3E6-5E8E-4792-BD8B-AEDC20FFAFDB': 'iPad (6th generation)',
            '91F106B8-5928-45F4-B840-25F5496680BF': 'iPhone X',
            '93F5DA98-21F3-4923-A403-B8433558CAFA': 'iPhone 8',
            '95ACBE11-CB06-4EBB-9AC9-CCEE2AEB6901': 'iPhone XR',
            '9E20D123-3F2B-4203-8B4C-78EFF946E303': 'iPhone 6s Plus',
            'A5298485-C7DB-4D00-9B6D-1AC436BD3B1A': 'iPad (5th generation)',
            'A8296054-BDAF-4EBF-A964-CFF0A528ED9C': 'iPad Pro (12.9-inch)',
            'C07C5003-9728-4184-B030-063074C4972F': 'iPhone SE',
            'CC3A7ECB-1BB2-4B77-9473-9ACCC06FC002': 'iPhone XS Max',
            'D637BC6D-A53F-4E78-BDA7-FA0D59303350': 'iPad Pro (11-inch)',
            'DC08D810-B9AD-4423-972E-3EE8949BC1F2': 'iPad Air',
            'DEE6AF0E-596D-4713-8B57-8C77D45EED80': 'iPad Air 2',
            'F022D86A-E404-46C0-98B2-9AB63AD7008B': 'iPad Pro (12.9-inch) (2nd generation)',
            'F7EF0E11-864C-42A2-8D80-4DBE78AFD86B': 'iPhone 6 Plus'
        }
    }
