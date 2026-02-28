import os
import shutil
from unittest import mock

import pytest

import briefcase
from briefcase.exceptions import MissingAppSources

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
    """If an app has no code (?!), install_app_code is mostly a no-op; but distinfo is
    created."""
    # Mock shutil so we can track usage.
    create_command.tools.shutil = mock.MagicMock(spec_set=shutil)
    create_command.tools.os = mock.MagicMock(spec_set=os)

    myapp.sources = None

    create_command.install_app_code(myapp)

    # No request was made to install requirements
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
    """If an app has an empty sources list (?!), install_app_code is mostly a no-op; but
    distinfo is created."""
    # Mock shutil so we can track usage.
    create_command.tools.shutil = mock.MagicMock(spec_set=shutil)
    create_command.tools.os = mock.MagicMock(spec_set=os)

    myapp.sources = []

    create_command.install_app_code(myapp)

    # No request was made to install requirements
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
    """If an app defines directories of sources, the whole directory is copied."""
    # Create the mock sources
    # src /
    #   first /
    #     demo.py
    #   second /
    #     shallow.py
    #     submodule /
    #       deeper.py
    create_file(
        tmp_path / "base_path/src/first/demo.py",
        "print('hello first')\n",
    )
    create_file(
        tmp_path / "base_path/src/second/shallow.py",
        "print('hello shallow second')\n",
    )
    create_file(
        tmp_path / "base_path/src/second/submodule/deeper.py",
        "print('hello deep second')\n",
    )

    # Set the app definition, and install sources
    myapp.sources = ["src/first", "src/second"]

    create_command.install_app_code(myapp)

    # All the sources exist.
    assert (app_path / "first").exists()
    assert (app_path / "first/demo.py").exists()

    assert (app_path / "second").exists()
    assert (app_path / "second/shallow.py").exists()

    assert (app_path / "second/submodule").exists()
    assert (app_path / "second/submodule/deeper.py").exists()

    # Metadata has been created
    assert_dist_info(app_path)

    # Original app definitions haven't changed
    assert myapp.sources == ["src/first", "src/second"]
    assert myapp.test_sources is None


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
        tmp_path / "base_path/src/demo.py",
        "print('hello first')\n",
    )
    create_file(
        tmp_path / "base_path/other.py",
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

    # Original app definitions haven't changed
    assert myapp.sources == ["src/demo.py", "other.py"]
    assert myapp.test_sources is None


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
        tmp_path / "base_path/src/first/demo.py",
        "print('hello first')\n",
    )
    create_file(
        tmp_path / "base_path/src/second/shallow.py",
        "print('hello shallow second')\n",
    )
    create_file(
        tmp_path / "base_path/src/second/submodule/deeper.py",
        "print('hello deep second')\n",
    )

    # Remove the app folder created by the test fixture.
    shutil.rmtree(app_path)

    # Set the app definition, and install sources
    myapp.sources = ["src/first/demo.py", "src/second"]

    create_command.install_app_code(myapp)

    # All the new sources exist, and contain the new content.
    assert (app_path / "demo.py").exists()
    with (app_path / "demo.py").open(encoding="utf-8") as f:
        assert f.read() == "print('hello first')\n"

    assert (app_path / "second").exists()
    assert (app_path / "second/shallow.py").exists()
    with (app_path / "second/shallow.py").open(encoding="utf-8") as f:
        assert f.read() == "print('hello shallow second')\n"

    assert (app_path / "second/submodule").exists()
    assert (app_path / "second/submodule/deeper.py").exists()
    with (app_path / "second/submodule/deeper.py").open(encoding="utf-8") as f:
        assert f.read() == "print('hello deep second')\n"

    # The stale/broken modules have been removed.
    assert not (app_path / "stale.py").exists()
    assert not (app_path / "second/stale.py").exists()
    assert not (app_path / "second/broken").exists()

    # Metadata has been updated.
    assert not (app_path / "my_app-1.2.2.dist-info").exists()
    assert_dist_info(app_path)

    # Original app definitions haven't changed
    assert myapp.sources == ["src/first/demo.py", "src/second"]
    assert myapp.test_sources is None


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
        tmp_path / "base_path/src/first/demo.py",
        "print('hello first')\n",
    )
    create_file(
        tmp_path / "base_path/src/second/shallow.py",
        "print('hello shallow second')\n",
    )
    create_file(
        tmp_path / "base_path/src/second/submodule/deeper.py",
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
        app_path / "src/demo.py",
        "print('old hello first')\n",
    )
    create_file(
        app_path / "src/stale.py",
        "print('stale hello first')\n",
    )
    create_file(
        app_path / "src/second/shallow.py",
        "print('old hello shallow second')\n",
    )
    create_file(
        app_path / "src/second/stale.py",
        "print('hello second stale')\n",
    )
    create_file(
        app_path / "src/second/submodule/deeper.py",
        "print('hello deep second')\n",
    )
    create_file(
        app_path / "src/second/broken/other.py",
        "print('hello second deep broken')\n",
    )

    old_dist_info_dir = app_path / "my_app-1.2.2.dist-info"
    old_dist_info_dir.mkdir()

    # Set the app definition, and install sources
    myapp.sources = ["src/first/demo.py", "src/second"]

    create_command.install_app_code(myapp)

    # All the new sources exist, and contain the new content.
    assert (app_path / "demo.py").exists()
    with (app_path / "demo.py").open(encoding="utf-8") as f:
        assert f.read() == "print('hello first')\n"

    assert (app_path / "second").exists()
    assert (app_path / "second/shallow.py").exists()
    with (app_path / "second/shallow.py").open(encoding="utf-8") as f:
        assert f.read() == "print('hello shallow second')\n"

    assert (app_path / "second/submodule").exists()
    assert (app_path / "second/submodule/deeper.py").exists()
    with (app_path / "second/submodule/deeper.py").open(encoding="utf-8") as f:
        assert f.read() == "print('hello deep second')\n"

    # The stale/broken modules have been removed.
    assert not (app_path / "stale.py").exists()
    assert not (app_path / "second/stale.py").exists()
    assert not (app_path / "second/broken").exists()

    # Metadata has been updated.
    assert not (app_path / "my_app-1.2.2.dist-info").exists()
    assert_dist_info(app_path)

    # Original app definitions haven't changed
    assert myapp.sources == ["src/first/demo.py", "src/second"]
    assert myapp.test_sources is None


def test_non_latin_metadata(
    create_command,
    myapp,
    app_path,
    app_requirements_path_index,
):
    """If the app metadata contains non-Latin-1 characters, the METADATA file is written
    correctly (Briefcase#767)"""
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

    # No request was made to install requirements
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


def test_test_sources(
    create_command,
    myapp,
    tmp_path,
    app_path,
    app_requirements_path_index,
):
    """If an app defines test code, but we're not in test mode, it isn't copied."""
    # Create the mock sources
    # src /
    #   first /
    #     demo.py
    #   second /
    #     shallow.py
    # tests /
    #   first.py
    #   deep /
    #     test_case.py
    # othertests/
    #   tests_more.py
    #   special /
    #     test_weird.py
    create_file(
        tmp_path / "base_path/src/first/demo.py",
        "print('hello first')\n",
    )
    create_file(
        tmp_path / "base_path/src/second/shallow.py",
        "print('hello shallow second')\n",
    )
    create_file(
        tmp_path / "base_path/tests/first.py",
        "print('hello first test suite')\n",
    )
    create_file(
        tmp_path / "base_path/tests/deep/test_case.py",
        "print('hello test case')\n",
    )
    create_file(
        tmp_path / "base_path/othertests/test_more.py",
        "print('hello more tests')\n",
    )
    create_file(
        tmp_path / "base_path/othertests/special/test_weird.py",
        "print('hello weird tests')\n",
    )

    # Set the app definition, and install sources
    myapp.sources = ["src/first", "src/second"]
    myapp.test_sources = ["tests", "othertests"]

    create_command.install_app_code(myapp)

    # App sources exist.
    assert (app_path / "first").exists()
    assert (app_path / "first/demo.py").exists()

    assert (app_path / "second").exists()
    assert (app_path / "second/shallow.py").exists()

    # Test sources do not exist
    assert not (app_path / "tests").exists()
    assert not (app_path / "othertests").exists()

    # Metadata has been created
    assert_dist_info(app_path)

    # Original app definitions haven't changed
    assert myapp.sources == ["src/first", "src/second"]
    assert myapp.test_sources == ["tests", "othertests"]


def test_test_sources_test_mode(
    create_command,
    myapp,
    tmp_path,
    app_path,
    app_requirements_path_index,
):
    """If an app defines test code, and we're in test mode, test sources are copied."""
    # Create the mock sources
    # src /
    #   first /
    #     demo.py
    #   second /
    #     shallow.py
    # tests /
    #   first.py
    #   deep /
    #     test_case.py
    # othertests/
    #   tests_more.py
    #   special /
    #     test_weird.py
    create_file(
        tmp_path / "base_path/src/first/demo.py",
        "print('hello first')\n",
    )
    create_file(
        tmp_path / "base_path/src/second/shallow.py",
        "print('hello shallow second')\n",
    )
    create_file(
        tmp_path / "base_path/tests/first.py",
        "print('hello first test suite')\n",
    )
    create_file(
        tmp_path / "base_path/tests/deep/test_case.py",
        "print('hello test case')\n",
    )
    create_file(
        tmp_path / "base_path/othertests/test_more.py",
        "print('hello more tests')\n",
    )
    create_file(
        tmp_path / "base_path/othertests/special/test_weird.py",
        "print('hello weird tests')\n",
    )

    # Set the app definition, and install sources
    myapp.sources = ["src/first", "src/second"]
    myapp.test_sources = ["tests", "othertests"]
    myapp.test_mode = True

    create_command.install_app_code(myapp)

    # App sources exist.
    assert (app_path / "first").exists()
    assert (app_path / "first/demo.py").exists()

    assert (app_path / "second").exists()
    assert (app_path / "second/shallow.py").exists()

    # Test sources exist
    assert (app_path / "tests/first.py").exists()
    assert (app_path / "tests/deep/test_case.py").exists()

    assert (app_path / "othertests/test_more.py").exists()
    assert (app_path / "othertests/special/test_weird.py").exists()

    # Metadata has been created
    assert_dist_info(app_path)

    # Original app definitions haven't changed
    assert myapp.sources == ["src/first", "src/second"]
    assert myapp.test_sources == ["tests", "othertests"]


def test_only_test_sources_test_mode(
    create_command,
    myapp,
    tmp_path,
    app_path,
    app_requirements_path_index,
):
    """If an app only defines test code, and we're in test mode, test sources are
    copied."""
    # Create the mock sources
    # tests /
    #   first.py
    #   deep /
    #     test_case.py
    # othertests/
    #   tests_more.py
    #   special /
    #     test_weird.py
    create_file(
        tmp_path / "base_path/src/first/demo.py",
        "print('hello first')\n",
    )
    create_file(
        tmp_path / "base_path/src/second/shallow.py",
        "print('hello shallow second')\n",
    )
    create_file(
        tmp_path / "base_path/tests/first.py",
        "print('hello first test suite')\n",
    )
    create_file(
        tmp_path / "base_path/tests/deep/test_case.py",
        "print('hello test case')\n",
    )
    create_file(
        tmp_path / "base_path/othertests/test_more.py",
        "print('hello more tests')\n",
    )
    create_file(
        tmp_path / "base_path/othertests/special/test_weird.py",
        "print('hello weird tests')\n",
    )

    # Set the app definition, and install sources
    myapp.sources = None
    myapp.test_sources = ["tests", "othertests"]
    myapp.test_mode = True

    create_command.install_app_code(myapp)

    # App sources do not exist.
    assert not (app_path / "first").exists()
    assert not (app_path / "second").exists()

    # Test sources exist
    assert (app_path / "tests/first.py").exists()
    assert (app_path / "tests/deep/test_case.py").exists()

    assert (app_path / "othertests/test_more.py").exists()
    assert (app_path / "othertests/special/test_weird.py").exists()

    # Metadata has been created
    assert_dist_info(app_path)

    # Original app definitions haven't changed
    assert myapp.sources is None
    assert myapp.test_sources == ["tests", "othertests"]


def test_source_dir_merge_and_file_overwrite(
    create_command,
    myapp,
    tmp_path,
    app_path,
    app_requirements_path_index,
):
    """If multiple sources define directories or files with the same name, directories
    are merged and files are overwritten, with later files overwriting earlier ones."""
    # Create the mock sources with two source directories and two test directories
    # top.py
    # test_top.py
    # lib /
    #   a.py
    #   b.py
    # srcdir /
    #   lib /
    #     b.py  (different content)
    #     c.py
    #   top.py (different content)
    # tests /
    #   test_a.py
    #   test_b.py
    # testdir /
    #   tests /
    #     test_b.py  (different content)
    #     test_c.py
    #   test_top.py (different content)
    create_file(
        tmp_path / "base_path/top.py",
        "# top\n",
    )
    create_file(
        tmp_path / "base_path/test_top.py",
        "# test_top\n",
    )
    create_file(
        tmp_path / "base_path/lib/a.py",
        "# a from lib\n",
    )
    create_file(
        tmp_path / "base_path/lib/b.py",
        "# b from lib\n",
    )
    create_file(
        tmp_path / "base_path/srcdir/lib/b.py",
        "# b from srcdir\n",
    )
    create_file(
        tmp_path / "base_path/srcdir/lib/c.py",
        "# c from srcdir\n",
    )
    create_file(
        tmp_path / "base_path/srcdir/top.py",
        "# top from srcdir\n",
    )
    create_file(
        tmp_path / "base_path/tests/test_a.py",
        "# test_a from tests\n",
    )
    create_file(
        tmp_path / "base_path/tests/test_b.py",
        "# test_b from tests\n",
    )
    create_file(
        tmp_path / "base_path/testdir/tests/test_b.py",
        "# test_b from testdir\n",
    )
    create_file(
        tmp_path / "base_path/testdir/tests/test_c.py",
        "# test_c from testdir\n",
    )
    create_file(
        tmp_path / "base_path/testdir/test_top.py",
        "# test_top from testdir\n",
    )

    # Set the app definition with two sources and two test sources, and two top-level
    # files with the same name
    myapp.sources = ["lib", "srcdir/lib", "top.py", "srcdir/top.py"]
    myapp.test_sources = [
        "tests",
        "testdir/tests",
        "test_top.py",
        "testdir/test_top.py",
    ]
    myapp.test_mode = True

    create_command.install_app_code(myapp)

    # The lib directory exists
    assert (app_path / "lib").exists()

    # a.py from lib (not overwritten)
    assert (app_path / "lib/a.py").exists()
    with (app_path / "lib/a.py").open(encoding="utf-8") as f:
        assert f.read() == "# a from lib\n"

    # b.py from srcdir (overwrote lib)
    assert (app_path / "lib/b.py").exists()
    with (app_path / "lib/b.py").open(encoding="utf-8") as f:
        assert f.read() == "# b from srcdir\n"

    # c.py from srcdir
    assert (app_path / "lib/c.py").exists()
    with (app_path / "lib/c.py").open(encoding="utf-8") as f:
        assert f.read() == "# c from srcdir\n"

    # top.py from srcdir (overwrites file from root)
    assert (app_path / "top.py").exists()
    with (app_path / "top.py").open(encoding="utf-8") as f:
        assert f.read() == "# top from srcdir\n"

    # The tests directory exists
    assert (app_path / "tests").exists()

    # test_a.py from tests (not overwritten)
    assert (app_path / "tests/test_a.py").exists()
    with (app_path / "tests/test_a.py").open(encoding="utf-8") as f:
        assert f.read() == "# test_a from tests\n"

    # test_b.py from testdir (overwrote tests)
    assert (app_path / "tests/test_b.py").exists()
    with (app_path / "tests/test_b.py").open(encoding="utf-8") as f:
        assert f.read() == "# test_b from testdir\n"

    # test_c.py from testdir
    assert (app_path / "tests/test_c.py").exists()
    with (app_path / "tests/test_c.py").open(encoding="utf-8") as f:
        assert f.read() == "# test_c from testdir\n"

    # test_top.py from testdir (overwrites file from root)
    assert (app_path / "test_top.py").exists()
    with (app_path / "test_top.py").open(encoding="utf-8") as f:
        assert f.read() == "# test_top from testdir\n"

    # Metadata has been created
    assert_dist_info(app_path)

    # Original app definitions haven't changed
    assert myapp.sources == ["lib", "srcdir/lib", "top.py", "srcdir/top.py"]
    assert myapp.test_sources == [
        "tests",
        "testdir/tests",
        "test_top.py",
        "testdir/test_top.py",
    ]


def test_dist_info_with_missing_optional_fields(
    create_command,
    myapp,
    app_path,
    app_requirements_path_index,
):
    """Dist-info is created correctly when optional app fields are set to None."""

    myapp.url = None
    myapp.author = None
    myapp.author_email = None

    # Mock shutil so we can track usage.
    create_command.tools.shutil = mock.MagicMock(spec_set=shutil)
    create_command.tools.os = mock.MagicMock(spec_set=os)

    myapp.sources = None

    create_command.install_app_code(myapp)

    # No request was made to install requirements
    create_command.tools.shutil.rmtree.assert_called_once_with(app_path)
    create_command.tools.os.mkdir.assert_called_once_with(app_path)
    create_command.tools.shutil.copytree.assert_not_called()
    create_command.tools.shutil.copy.assert_not_called()

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
Download-URL:\x20
Summary: This is a simple app
"""
        )
