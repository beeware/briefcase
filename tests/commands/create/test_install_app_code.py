import os
import shutil
from unittest import mock

import pytest

import briefcase
from briefcase.commands.create import MissingAppSources

from ...utils import create_file


def assert_dist_info(app_path):
    dist_info_path = app_path / "my_app-1.2.3.dist-info"

    # Confirm the metadata files exist.
    assert (dist_info_path / "INSTALLER").exists()
    assert (dist_info_path / "METADATA").exists()

    with (dist_info_path / "INSTALLER").open(encoding="utf-8") as f:
        assert f.read() == "briefcase\n"

    with (dist_info_path / "METADATA").open(encoding="utf-8") as f:
        assert (
            f.read()
            == f"""Metadata-Version: 2.1
Briefcase-Version: {briefcase.__version__}
Name: my-app
Formal-Name: My App
App-ID: com.example.my-app
Version: 1.2.3
Home-page: https://example.com
Download-URL: https://example.com
Author: First Last
Author-email: first@example.com
Summary: This is a simple app
"""
        )


def test_no_code(
    create_command,
    myapp,
    app_path,
    app_requirements_path_index,
):
    """If an app has no code (?!), install_app_code is mostly a no-op; but
    distinfo is created."""
    # Mock shutil so we can track usage.
    create_command.tools.shutil = mock.MagicMock(spec_set=shutil)
    create_command.tools.os = mock.MagicMock(spec_set=os)

    myapp.sources = None

    create_command.install_app_code(myapp)

    # No request was made to install dependencies
    create_command.tools.shutil.rmtree.assert_called_once_with(app_path)
    create_command.tools.os.mkdir.assert_called_once_with(app_path)
    create_command.tools.shutil.copytree.assert_not_called()
    create_command.tools.shutil.copy.assert_not_called()

    # Metadata has been created
    assert_dist_info(app_path)


def test_empty_code(
    create_command,
    myapp,
    app_path,
    app_requirements_path_index,
):
    """If an app has an empty sources list (?!), install_app_code is mostly a
    no-op; but distinfo is created."""
    # Mock shutil so we can track usage.
    create_command.tools.shutil = mock.MagicMock(spec_set=shutil)
    create_command.tools.os = mock.MagicMock(spec_set=os)

    myapp.sources = []

    create_command.install_app_code(myapp)

    # No request was made to install dependencies
    create_command.tools.shutil.rmtree.assert_called_once_with(app_path)
    create_command.tools.os.mkdir.assert_called_once_with(app_path)
    create_command.tools.shutil.copytree.assert_not_called()
    create_command.tools.shutil.copy.assert_not_called()

    # Metadata has been created
    assert_dist_info(app_path)


def test_source_missing(
    create_command,
    myapp,
    app_path,
    app_requirements_path_index,
):
    """If an app defines sources that are missing, an error is raised."""
    # Set the app definition to point at sources that don't exist
    myapp.sources = ["missing"]

    with pytest.raises(MissingAppSources):
        create_command.install_app_code(myapp)

    # Distinfo won't be created.
    dist_info_path = app_path / "myapp-1.2.3.dist-info"
    assert not dist_info_path.exists()


def test_source_dir(
    create_command,
    myapp,
    tmp_path,
    app_path,
    app_requirements_path_index,
):
    """If an app defines directories of sources, the whole directory is
    copied."""
    # Create the mock sources
    # src /
    #   first /
    #     demo.py
    #   second /
    #     shallow.py
    #     submodule /
    #       deeper.py
    create_file(
        tmp_path / "project" / "src" / "first" / "demo.py",
        "print('hello first')\n",
    )
    create_file(
        tmp_path / "project" / "src" / "second" / "shallow.py",
        "print('hello shallow second')\n",
    )
    create_file(
        tmp_path / "project" / "src" / "second" / "submodule" / "deeper.py",
        "print('hello deep second')\n",
    )

    # Set the app definition, and install sources
    myapp.sources = ["src/first", "src/second"]

    create_command.install_app_code(myapp)

    # All the sources exist.
    assert (app_path / "first").exists()
    assert (app_path / "first" / "demo.py").exists()

    assert (app_path / "second").exists()
    assert (app_path / "second" / "shallow.py").exists()

    assert (app_path / "second" / "submodule").exists()
    assert (app_path / "second" / "submodule" / "deeper.py").exists()

    # Metadata has been created
    assert_dist_info(app_path)


def test_source_file(
    create_command,
    myapp,
    tmp_path,
    app_path,
    app_requirements_path_index,
):
    """If an app defines single file sources, the files are copied."""
    # Create the mock sources
    # src /
    #   demo.py
    # other.py
    create_file(
        tmp_path / "project" / "src" / "demo.py",
        "print('hello first')\n",
    )
    create_file(
        tmp_path / "project" / "other.py",
        "print('hello second')\n",
    )

    # Set the app definition, and install sources
    myapp.sources = ["src/demo.py", "other.py"]

    create_command.install_app_code(myapp)

    # All the sources exist.
    assert (app_path / "demo.py").exists()
    assert (app_path / "other.py").exists()

    # Metadata has been created
    assert_dist_info(app_path)


def test_no_existing_app_folder(
    create_command,
    myapp,
    tmp_path,
    app_path,
    app_requirements_path_index,
):
    """If there's no pre-existing app folder, one is created."""
    # Create the mock sources
    # src /
    #   first /
    #     demo.py
    #   second /
    #     shallow.py
    #     submodule /
    #       deeper.py
    create_file(
        tmp_path / "project" / "src" / "first" / "demo.py",
        "print('hello first')\n",
    )
    create_file(
        tmp_path / "project" / "src" / "second" / "shallow.py",
        "print('hello shallow second')\n",
    )
    create_file(
        tmp_path / "project" / "src" / "second" / "submodule" / "deeper.py",
        "print('hello deep second')\n",
    )

    # Remove the app folder created by the test fixture.
    shutil.rmtree(app_path)

    # Set the app definition, and install sources
    myapp.sources = ["src/first/demo.py", "src/second"]

    create_command.install_app_code(myapp)

    # All the new sources exist, and contain the new content.
    assert (app_path / "demo.py").exists()
    with (app_path / "demo.py").open() as f:
        assert f.read() == "print('hello first')\n"

    assert (app_path / "second").exists()
    assert (app_path / "second" / "shallow.py").exists()
    with (app_path / "second" / "shallow.py").open() as f:
        assert f.read() == "print('hello shallow second')\n"

    assert (app_path / "second" / "submodule").exists()
    assert (app_path / "second" / "submodule" / "deeper.py").exists()
    with (app_path / "second" / "submodule" / "deeper.py").open() as f:
        assert f.read() == "print('hello deep second')\n"

    # The stale/broken modules have been removed.
    assert not (app_path / "stale.py").exists()
    assert not (app_path / "second" / "stale.py").exists()
    assert not (app_path / "second" / "broken").exists()

    # Metadata has been updated.
    assert not (app_path / "my_app-1.2.2.dist-info").exists()
    assert_dist_info(app_path)


def test_replace_sources(
    create_command,
    myapp,
    tmp_path,
    app_path,
    app_requirements_path_index,
):
    """Stale sources and dist-info are removed on installation."""
    # Create the mock sources
    # src /
    #   first /
    #     demo.py
    #   second /
    #     shallow.py
    #     submodule /
    #       deeper.py
    create_file(
        tmp_path / "project" / "src" / "first" / "demo.py",
        "print('hello first')\n",
    )
    create_file(
        tmp_path / "project" / "src" / "second" / "shallow.py",
        "print('hello shallow second')\n",
    )
    create_file(
        tmp_path / "project" / "src" / "second" / "submodule" / "deeper.py",
        "print('hello deep second')\n",
    )

    # Also create some existing sources:
    # path / to / app /
    #   demo.py
    #   stale.py
    #   second /
    #     shallow.py
    #     stale.py
    #     submodule /
    #       deeper.py
    #     broken /
    #       other.py
    #   my_app-1.2.2.dist-info /
    create_file(
        app_path / "src" / "demo.py",
        "print('old hello first')\n",
    )
    create_file(
        app_path / "src" / "stale.py",
        "print('stale hello first')\n",
    )
    create_file(
        app_path / "src" / "second" / "shallow.py",
        "print('old hello shallow second')\n",
    )
    create_file(
        app_path / "src" / "second" / "stale.py",
        "print('hello second stale')\n",
    )
    create_file(
        app_path / "src" / "second" / "submodule" / "deeper.py",
        "print('hello deep second')\n",
    )
    create_file(
        app_path / "src" / "second" / "broken" / "other.py",
        "print('hello second deep broken')\n",
    )

    old_dist_info_dir = app_path / "my_app-1.2.2.dist-info"
    old_dist_info_dir.mkdir()

    # Set the app definition, and install sources
    myapp.sources = ["src/first/demo.py", "src/second"]

    create_command.install_app_code(myapp)

    # All the new sources exist, and contain the new content.
    assert (app_path / "demo.py").exists()
    with (app_path / "demo.py").open() as f:
        assert f.read() == "print('hello first')\n"

    assert (app_path / "second").exists()
    assert (app_path / "second" / "shallow.py").exists()
    with (app_path / "second" / "shallow.py").open() as f:
        assert f.read() == "print('hello shallow second')\n"

    assert (app_path / "second" / "submodule").exists()
    assert (app_path / "second" / "submodule" / "deeper.py").exists()
    with (app_path / "second" / "submodule" / "deeper.py").open() as f:
        assert f.read() == "print('hello deep second')\n"

    # The stale/broken modules have been removed.
    assert not (app_path / "stale.py").exists()
    assert not (app_path / "second" / "stale.py").exists()
    assert not (app_path / "second" / "broken").exists()

    # Metadata has been updated.
    assert not (app_path / "my_app-1.2.2.dist-info").exists()
    assert_dist_info(app_path)


def test_non_latin_metadata(
    create_command,
    myapp,
    app_path,
    app_requirements_path_index,
):
    """If the app metadata contains non-Latin-1 characters, the METADATA file
    is written correctly (Briefcase#767)"""
    myapp.formal_name = "My büggy app"
    myapp.author = "José Weiß-Müller"
    myapp.author_email = "钱华林@中科院.中国"
    myapp.url = "https://xn--7qvx15a.cn"
    myapp.description = "A Møøse once bit my sister..."

    # Mock shutil so we can track usage.
    create_command.tools.shutil = mock.MagicMock(spec_set=shutil)
    create_command.tools.os = mock.MagicMock(spec_set=os)

    myapp.sources = []

    create_command.install_app_code(myapp)

    # No request was made to install dependencies
    create_command.tools.shutil.rmtree.assert_called_once_with(app_path)
    create_command.tools.os.mkdir.assert_called_once_with(app_path)
    create_command.tools.shutil.copytree.assert_not_called()
    create_command.tools.shutil.copy.assert_not_called()

    # The dist-info file was created, and is readable.
    dist_info_path = app_path / "my_app-1.2.3.dist-info"

    # Confirm the metadata files exist.
    assert (dist_info_path / "INSTALLER").exists()
    assert (dist_info_path / "METADATA").exists()

    with (dist_info_path / "INSTALLER").open(encoding="utf-8") as f:
        assert f.read() == "briefcase\n"

    with (dist_info_path / "METADATA").open(encoding="utf-8") as f:
        assert (
            f.read()
            == f"""Metadata-Version: 2.1
Briefcase-Version: {briefcase.__version__}
Name: my-app
Formal-Name: My büggy app
App-ID: com.example.my-app
Version: 1.2.3
Home-page: https://xn--7qvx15a.cn
Download-URL: https://xn--7qvx15a.cn
Author: José Weiß-Müller
Author-email: 钱华林@中科院.中国
Summary: A Møøse once bit my sister...
"""
        )
