from pathlib import Path

from .....utils import create_file


def test_clean_dist_folder_removes_signature(package_command, first_app, tmp_path):
    """Cleaning the dist folder also removes the signature file."""
    first_app.packaging_format = "pkg"
    package_command.tools[first_app].app_context.check_output.return_value = "wonky"

    dist_path = tmp_path / "base_path/dist/first-app-0.0.1-1-wonky.pkg.tar.zst"
    create_file(dist_path, "package content")
    create_file(Path(f"{dist_path}.sig"), "signature")

    package_command.clean_dist_folder(first_app)

    assert not dist_path.exists()
    assert not Path(f"{dist_path}.sig").exists()


def test_clean_dist_folder_no_signature(package_command, first_app, tmp_path):
    """Cleaning the dist folder when no signature exists is a no-op."""
    first_app.packaging_format = "pkg"
    package_command.tools[first_app].app_context.check_output.return_value = "wonky"

    dist_path = tmp_path / "base_path/dist/first-app-0.0.1-1-wonky.pkg.tar.zst"
    create_file(dist_path, "package content")

    package_command.clean_dist_folder(first_app)

    assert not dist_path.exists()
