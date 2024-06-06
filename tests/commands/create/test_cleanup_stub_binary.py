import pytest

from ...utils import create_file


@pytest.mark.parametrize(
    "unbuilt, built",
    [
        (True, True),
        (True, False),
        (False, True),
        (False, False),
    ],
)
def test_cleanup_stubs(create_command, unbuilt, built, myapp, tmp_path):
    """If an unbuilt stub already exists, it is cleaned up."""

    # Mock a existing stubs
    if unbuilt:
        create_file(
            tmp_path / "base_path/build/my-app/tester/dummy/Stub.bin",
            "Unbuilt stub",
        )
    if built:
        create_file(
            tmp_path / "base_path/build/my-app/tester/dummy/my-app.bin",
            "Built stub",
        )

    # Re-install the support package
    create_command.cleanup_stub_binary(myapp)

    # No matter the starting state, the stubs don't exist after cleanup.
    assert not (tmp_path / "base_path/build/my-app/tester/dummy/Stub.bin").exists()
    assert not (tmp_path / "base_path/build/my-app/tester/dummy/my-app.bin").exists()
