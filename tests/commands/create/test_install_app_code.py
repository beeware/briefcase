from unittest import mock

import pytest

from briefcase.commands.create import MissingAppSources


def assert_dist_info(app_path):
    dist_info_path = app_path / 'my_app-1.2.3.dist-info'

    # Confirm the metadata files exist.
    assert (dist_info_path / 'INSTALLER').exists()
    assert (dist_info_path / 'METADATA').exists()

    with (dist_info_path / 'INSTALLER').open() as f:
        assert f.read() == 'briefcase\n'

    with (dist_info_path / 'METADATA').open() as f:
        assert f.read() == """Metadata-Version: 2.1
Name: my-app
Formal-Name: My App
App-ID: com.example.my-app
Version: 1.2.3
Summary: This is a simple app
"""


def test_no_code(create_command, myapp, app_path):
    "If an app has no code (?!), install_app_code is mostly a no-op; but distinfo is created"
    # Mock shutil so we can track usage.
    create_command.shutil = mock.MagicMock()

    myapp.sources = None

    create_command.install_app_code(myapp)

    # No request was made to install dependencies
    create_command.shutil.rmtree.assert_not_called()
    create_command.shutil.copytree.assert_not_called()
    create_command.shutil.copy.assert_not_called()

    # Metadata has been created
    assert_dist_info(app_path)


def test_empty_code(create_command, myapp, app_path):
    "If an app has an empty sources list (?!), install_app_code is mostly a no-op; but distinfo is created"
    # Mock shutil so we can track usage.
    create_command.shutil = mock.MagicMock()

    myapp.sources = []

    create_command.install_app_code(myapp)

    # No request was made to install dependencies
    create_command.shutil.rmtree.assert_not_called()
    create_command.shutil.copytree.assert_not_called()
    create_command.shutil.copy.assert_not_called()

    # Metadata has been created
    assert_dist_info(app_path)


def test_source_missing(create_command, myapp, app_path):
    "If an app defines sources that are missing, an error is raised"
    # Set the app definition to point at sources that don't exsit
    myapp.sources = ['missing']

    with pytest.raises(MissingAppSources):
        create_command.install_app_code(myapp)

    # Distinfo won't be created.
    dist_info_path = app_path / 'myapp-1.2.3.dist-info'
    assert not dist_info_path.exists()


def test_source_dir(create_command, myapp, tmp_path, app_path):
    "If an app defines directories of sources, the whole directory is copied."
    # Create the mock sources
    # src /
    #   first /
    #     demo.py
    #   second /
    #     shallow.py
    #     submodule /
    #       deeper.py
    first_src = tmp_path / 'src' / 'first' / 'demo.py'
    first_src.parent.mkdir(parents=True)
    with (first_src).open('w') as f:
        f.write("print('hello first')\n")

    second_shallow_src = tmp_path / 'src' / 'second' / 'shallow.py'
    second_deep_src = tmp_path / 'src' / 'second' / 'submodule' / 'deeper.py'
    second_deep_src.parent.mkdir(parents=True)
    with (second_shallow_src).open('w') as f:
        f.write("print('hello shallow second')\n")
    with (second_deep_src).open('w') as f:
        f.write("print('hello deep second')\n")

    # Set the app definition, and install sources
    myapp.sources = ['src/first', 'src/second']

    create_command.install_app_code(myapp)

    # All the sources exist.
    assert (app_path / 'first').exists()
    assert (app_path / 'first' / 'demo.py').exists()

    assert (app_path / 'second').exists()
    assert (app_path / 'second' / 'shallow.py').exists()

    assert (app_path / 'second' / 'submodule').exists()
    assert (app_path / 'second' / 'submodule' / 'deeper.py').exists()

    # Metadata has been created
    assert_dist_info(app_path)


def test_source_file(create_command, myapp, tmp_path, app_path):
    "If an app defines single file sources, the files are copied."
    # Create the mock sources
    # src /
    #   first /
    #     demo.py
    #   other.py
    first_src = tmp_path / 'src' / 'first' / 'demo.py'
    first_src.parent.mkdir(parents=True)
    with (first_src).open('w') as f:
        f.write("print('hello first')\n")

    second_src = tmp_path / 'src' / 'other.py'
    with (second_src).open('w') as f:
        f.write("print('hello second')\n")

    # Set the app definition, and install sources
    myapp.sources = ['src/first/demo.py', 'src/other.py']

    create_command.install_app_code(myapp)

    # All the sources exist.
    assert (app_path / 'demo.py').exists()
    assert (app_path / 'other.py').exists()

    # Metadata has been created
    assert_dist_info(app_path)


def test_replace_sources(create_command, myapp, tmp_path, app_path):
    "If an app defines directories of sources, the whole directory is copied."
    # Create the mock sources
    # src /
    #   first /
    #     demo.py
    #   second /
    #     shallow.py
    #     submodule /
    #       deeper.py
    first_src = tmp_path / 'src' / 'first' / 'demo.py'
    first_src.parent.mkdir(parents=True)
    with (first_src).open('w') as f:
        f.write("print('hello first')\n")

    second_shallow_src = tmp_path / 'src' / 'second' / 'shallow.py'
    second_deep_src = tmp_path / 'src' / 'second' / 'submodule' / 'deeper.py'
    second_deep_src.parent.mkdir(parents=True)
    with (second_shallow_src).open('w') as f:
        f.write("print('hello shallow second')\n")
    with (second_deep_src).open('w') as f:
        f.write("print('hello deep second')\n")

    # Also create some existing sources:
    # path / to / app /
    #   demo.py
    #   second /
    #     shallow.py
    #     stale.py
    #     submodule /
    #       deeper.py
    #     broken /
    #       other.py

    old_first_src = app_path / 'demo.py'
    with (old_first_src).open('w') as f:
        f.write("print('old hello first')\n")

    old_second_shallow_src = app_path / 'src' / 'second' / 'shallow.py'
    old_second_stale_src = app_path / 'src' / 'second' / 'stale.py'
    old_second_deep_src = app_path / 'src' / 'second' / 'submodule' / 'deeper.py'
    old_second_broken_src = app_path / 'src' / 'second' / 'broken' / 'other.py'
    old_second_deep_src.parent.mkdir(parents=True)
    old_second_broken_src.parent.mkdir(parents=True)
    with (old_second_shallow_src).open('w') as f:
        f.write("print('old hello shallow second')\n")
    with (old_second_stale_src).open('w') as f:
        f.write("print('hello second stale')\n")
    with (old_second_deep_src).open('w') as f:
        f.write("print('old hello deep second')\n")
    with (old_second_broken_src).open('w') as f:
        f.write("print('hello second deep broken')\n")

    # Set the app definition, and install sources
    myapp.sources = ['src/first/demo.py', 'src/second']

    create_command.install_app_code(myapp)

    # All the new sources exist, and contain the new content.
    assert (app_path / 'demo.py').exists()
    with (app_path / 'demo.py').open() as f:
        assert f.read() == "print('hello first')\n"

    assert (app_path / 'second').exists()
    assert (app_path / 'second' / 'shallow.py').exists()
    with (app_path / 'second' / 'shallow.py').open() as f:
        assert f.read() == "print('hello shallow second')\n"

    assert (app_path / 'second' / 'submodule').exists()
    assert (app_path / 'second' / 'submodule' / 'deeper.py').exists()
    with (app_path / 'second' / 'submodule' / 'deeper.py').open() as f:
        assert f.read() == "print('hello deep second')\n"

    # The stale/broken modules have been removed.
    assert not (app_path / 'second' / 'stale.py').exists()
    assert not (app_path / 'second' / 'broken').exists()

    # Metadata has been created
    assert_dist_info(app_path)
