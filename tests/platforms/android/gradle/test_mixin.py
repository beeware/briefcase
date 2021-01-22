from briefcase.platforms.android.gradle import GradleCreateCommand


def test_binary_path(first_app_config, tmp_path):
    command = GradleCreateCommand(base_path=tmp_path)
    binary_path = command.binary_path(first_app_config)

    assert binary_path == (
        tmp_path
        / 'android'
        / 'First App'
        / "app"
        / "build"
        / "outputs"
        / "apk"
        / "debug"
        / "app-debug.apk"
    )


def test_binary_path_with_output_dir(first_app_config, tmp_path):
    output_dir = "output"
    first_app_config.output_dir = output_dir
    command = GradleCreateCommand(base_path=tmp_path)
    binary_path = command.binary_path(first_app_config)

    assert binary_path == (
        tmp_path
        / output_dir
        / 'First App'
        / "app"
        / "build"
        / "outputs"
        / "apk"
        / "debug"
        / "app-debug.apk"
    )


def test_distribution_path(first_app_config, tmp_path):
    command = GradleCreateCommand(base_path=tmp_path)
    distribution_path = command.distribution_path(first_app_config)

    assert distribution_path == (
        tmp_path
        / 'android'
        / 'First App'
        / "app"
        / "build"
        / "outputs"
        / "bundle"
        / "release"
        / "app-release.aab"
    )


def test_distribution_path_with_output_dir(first_app_config, tmp_path):
    output_dir = "output"
    first_app_config.output_dir = output_dir
    command = GradleCreateCommand(base_path=tmp_path)
    distribution_path = command.distribution_path(first_app_config)

    assert distribution_path == (
        tmp_path
        / output_dir
        / 'First App'
        / "app"
        / "build"
        / "outputs"
        / "bundle"
        / "release"
        / "app-release.aab"
    )