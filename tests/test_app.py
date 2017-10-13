import unittest
import os
from distutils.dist import Distribution
from briefcase.dummy import dummy
from briefcase.app import DevRequirementsDontExists
from unittest.mock import patch
from unittest.mock import Mock
from unittest.mock import mock_open


class TestDevMode(unittest.TestCase):
    def setUp(self):
        self.app = dummy(Distribution())
        self.app.finalize_options()

    def test_parse_options(self):
        options_data = (
            'toga-core /Users/rkm/code/toga/src/core/toga\n'
            'toga-cocoa /Users/rkm/code/toga/src/cocoa/toga_cocoa\n'
            'colosseum /Users/rkm/code/colosseum/colosseum\n'
        )

        expected = {
            'toga-core': '/Users/rkm/code/toga/src/core/toga',
            'toga-cocoa': '/Users/rkm/code/toga/src/cocoa/toga_cocoa',
            'colosseum': '/Users/rkm/code/colosseum/colosseum'
        }

        self.app.dev = 'requirements.dev'
        with patch('builtins.open', mock_open(read_data=options_data)) as m:
            result = self.app.parse_dev_options()
        self.assertEqual(expected, result)

    def test_raise_exception_when_dev_req_dont_exists(self):
        self.app.dev = 'invalid_file_name.dev'

        with patch('briefcase.app.os.path.isfile', return_value = False):
            self.assertRaises(
                DevRequirementsDontExists,
                self.app.finalize_options
            )

    @patch('briefcase.app.pip.main')
    def test_override_dependencies_with_requirements_file(self, mocked_main):
        parsed = {
            'dummy': '/Users/rkm/code/toga/src/core/dummy',
        }
        self.app.app_requires = ['dummy']
        self.app.dev = 'requirements.dev'

        with patch.object(self.app, 'parse_dev_options', return_value = parsed):
            with patch('briefcase.app.os.path.isfile', return_value = True):
                self.app.finalize_options()

        arguments = [
            'install',
            '--upgrade',
            '--force-reinstall',
            '--target=%s' % self.app.app_packages_dir,
        ] + ['/Users/rkm/code/toga/src/core/dummy']

        self.app.install_platform_requirements()
        mocked_main.assert_called_once_with(arguments)

    @patch('briefcase.app.pip.main')
    def test_override_dependencies_and_append_missing(self, mocked_main):
        parsed = {
            'dummy': '/Users/rkm/code/toga/src/core/dummy',
            'eummy': '/Users/rkm/code/toga/src/core/eummy',
        }
        self.app.app_requires = ['dummy']
        self.app.dev = 'requirements.dev'

        with patch.object(self.app, 'parse_dev_options', return_value = parsed):
            with patch('briefcase.app.os.path.isfile', return_value = True):
                self.app.finalize_options()

        arguments = [
            'install',
            '--upgrade',
            '--force-reinstall',
            '--target=%s' % self.app.app_packages_dir,
        ] + ['/Users/rkm/code/toga/src/core/dummy',
             '/Users/rkm/code/toga/src/core/eummy']

        self.app.install_platform_requirements()
        mocked_main.assert_called_once_with(arguments)

    @patch('briefcase.app.pip.main')
    def test_dont_override_dependencies_when_dev_requirements_is_None(self, mocked_main):
        self.app.app_requires = ['dummy']
        self.app.finalize_options()

        arguments = [
            'install',
            '--upgrade',
            '--force-reinstall',
            '--target=%s' % self.app.app_packages_dir,
        ] + ['dummy']

        self.app.install_platform_requirements()
        mocked_main.assert_called_once_with(arguments)


if __name__ == '__main__':
    unittest.main()
