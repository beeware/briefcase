import tomli_w


def test_template_url(create_command):
    """The template URL is a simple construction of the platform and format."""
    assert (
        create_command.app_template_url
        == "https://github.com/beeware/briefcase-tester-dummy-template.git"
    )


def test_app_path(create_command, myapp):
    bundle_path = create_command.bundle_path(myapp)
    bundle_path.mkdir(parents=True)
    with (bundle_path / "briefcase.toml").open("wb") as f:
        index = {
            "paths": {
                "app_path": "path/to/app",
                "app_packages_path": "path/to/app_packages",
                "support_path": "path/to/support",
            }
        }
        tomli_w.dump(index, f)

    assert create_command.app_path(myapp) == bundle_path / "path" / "to" / "app"

    # Requesting a second time should hit the cache,
    # so the briefcase file won't be needed.
    # Delete it to make sure the cache is used.
    (bundle_path / "briefcase.toml").unlink()
    assert create_command.app_path(myapp) == bundle_path / "path" / "to" / "app"


def test_app_packages_path(create_command, myapp):
    bundle_path = create_command.bundle_path(myapp)
    bundle_path.mkdir(parents=True)
    with (bundle_path / "briefcase.toml").open("wb") as f:
        index = {
            "paths": {
                "app_path": "path/to/app",
                "app_packages_path": "path/to/app_packages",
                "support_path": "path/to/support",
            }
        }
        tomli_w.dump(index, f)

    assert (
        create_command.app_packages_path(myapp)
        == bundle_path / "path" / "to" / "app_packages"
    )

    # Requesting a second time should hit the cache,
    # so the briefcase file won't be needed.
    # Delete it to make sure the cache is used.
    (bundle_path / "briefcase.toml").unlink()
    assert (
        create_command.app_packages_path(myapp)
        == bundle_path / "path" / "to" / "app_packages"
    )


def test_support_path(create_command, myapp):
    bundle_path = create_command.bundle_path(myapp)
    bundle_path.mkdir(parents=True)
    with (bundle_path / "briefcase.toml").open("wb") as f:
        index = {
            "paths": {
                "app_path": "path/to/app",
                "app_packages_path": "path/to/app_packages",
                "support_path": "path/to/support",
            }
        }
        tomli_w.dump(index, f)

    assert create_command.support_path(myapp) == bundle_path / "path" / "to" / "support"

    # Requesting a second time should hit the cache,
    # so the briefcase file won't be needed.
    # Delete it to make sure the cache is used.
    (bundle_path / "briefcase.toml").unlink()
    assert create_command.support_path(myapp) == bundle_path / "path" / "to" / "support"


def test_support_revision(create_command, myapp):
    bundle_path = create_command.bundle_path(myapp)
    bundle_path.mkdir(parents=True)
    with (bundle_path / "briefcase.toml").open("wb") as f:
        index = {
            "paths": {
                "app_path": "path/to/app",
                "app_packages_path": "path/to/app_packages",
                "support_path": "path/to/support",
                "support_revision": 42,
            }
        }
        tomli_w.dump(index, f)

    assert create_command.support_revision(myapp) == 42

    # Requesting a second time should hit the cache,
    # so the briefcase file won't be needed.
    # Delete it to make sure the cache is used.
    (bundle_path / "briefcase.toml").unlink()
    assert create_command.support_revision(myapp) == 42


def test_cleanup_paths(create_command, myapp):
    bundle_path = create_command.bundle_path(myapp)
    bundle_path.mkdir(parents=True)
    with (bundle_path / "briefcase.toml").open("wb") as f:
        index = {
            "paths": {
                "app_path": "path/to/app",
                "cleanup_paths": ["path/to/glob*", "other/path"],
            }
        }
        tomli_w.dump(index, f)

    assert create_command.cleanup_paths(myapp) == ["path/to/glob*", "other/path"]

    # Requesting a second time should hit the cache,
    # so the briefcase file won't be needed.
    # Delete it to make sure the cache is used.
    (bundle_path / "briefcase.toml").unlink()
    assert create_command.cleanup_paths(myapp) == ["path/to/glob*", "other/path"]


def test_support_package_url(create_command):
    # Retrieve the property, retrieving the support package URL.
    url = "https://briefcase-support.s3.amazonaws.com/python/3.X/tester/Python-3.X-tester-support.b52.tar.gz"
    assert create_command.support_package_url(52) == url


def test_no_icon(create_command, myapp):
    """If no icon target is specified, the icon list is empty."""
    bundle_path = create_command.bundle_path(myapp)
    bundle_path.mkdir(parents=True)
    with (bundle_path / "briefcase.toml").open("wb") as f:
        index = {
            "paths": {
                "app_path": "path/to/app",
            }
        }
        tomli_w.dump(index, f)

    assert create_command.icon_targets(myapp) == {}


def test_single_icon(create_command, myapp):
    """If the icon target is specified as a single string, the icon list has
    one unsized entry."""
    bundle_path = create_command.bundle_path(myapp)
    bundle_path.mkdir(parents=True)
    with (bundle_path / "briefcase.toml").open("wb") as f:
        index = {
            "paths": {
                "app_path": "path/to/app",
                "icon": "path/to/icon.png",
            }
        }
        tomli_w.dump(index, f)

    assert create_command.icon_targets(myapp) == {None: "path/to/icon.png"}


def test_multiple_icon(create_command, myapp):
    """If there are multiple icon targets, they're all in the target list."""
    bundle_path = create_command.bundle_path(myapp)
    bundle_path.mkdir(parents=True)
    with (bundle_path / "briefcase.toml").open("wb") as f:
        index = {
            "paths": {
                "app_path": "path/to/app",
                "icon": {
                    "10": "path/to/icon-10.png",
                    "20": "path/to/icon-20.png",
                },
            }
        }
        tomli_w.dump(index, f)

    assert create_command.icon_targets(myapp) == {
        "10": "path/to/icon-10.png",
        "20": "path/to/icon-20.png",
    }


def test_icon_variants(create_command, myapp):
    """If there are icon variants, they are returned."""
    bundle_path = create_command.bundle_path(myapp)
    bundle_path.mkdir(parents=True)
    with (bundle_path / "briefcase.toml").open("wb") as f:
        index = {
            "paths": {
                "app_path": "path/to/app",
                "icon": {
                    "single": "path/to/icon.png",
                    "multi": {
                        "10": "path/to/icon-10.png",
                        "20": "path/to/icon-20.png",
                    },
                },
            }
        }
        tomli_w.dump(index, f)

    assert create_command.icon_targets(myapp) == {
        "single": "path/to/icon.png",
        "multi": {
            "10": "path/to/icon-10.png",
            "20": "path/to/icon-20.png",
        },
    }


def test_no_splash(create_command, myapp):
    """If no splash target is specified, the splash list is empty."""
    bundle_path = create_command.bundle_path(myapp)
    bundle_path.mkdir(parents=True)
    with (bundle_path / "briefcase.toml").open("wb") as f:
        index = {
            "paths": {
                "app_path": "path/to/app",
            }
        }
        tomli_w.dump(index, f)

    assert create_command.splash_image_targets(myapp) == {}


def test_single_splash(create_command, myapp):
    """If the splash target is specified as a single string, the splash list
    has one unsized entry."""
    bundle_path = create_command.bundle_path(myapp)
    bundle_path.mkdir(parents=True)
    with (bundle_path / "briefcase.toml").open("wb") as f:
        index = {
            "paths": {
                "app_path": "path/to/app",
                "splash": "path/to/splash.png",
            }
        }
        tomli_w.dump(index, f)

    assert create_command.splash_image_targets(myapp) == {None: "path/to/splash.png"}


def test_multiple_splash(create_command, myapp):
    """If there are multiple splash targets, they're all in the target list."""
    bundle_path = create_command.bundle_path(myapp)
    bundle_path.mkdir(parents=True)
    with (bundle_path / "briefcase.toml").open("wb") as f:
        index = {
            "paths": {
                "app_path": "path/to/app",
                "splash": {
                    "10x20": "path/to/splash-10.png",
                    "20x30": "path/to/splash-20.png",
                },
            }
        }
        tomli_w.dump(index, f)

    assert create_command.splash_image_targets(myapp) == {
        "10x20": "path/to/splash-10.png",
        "20x30": "path/to/splash-20.png",
    }


def test_no_document_types(create_command, myapp):
    """If no document type targets are specified, the document_type_icons list
    is empty."""
    bundle_path = create_command.bundle_path(myapp)
    bundle_path.mkdir(parents=True)
    with (bundle_path / "briefcase.toml").open("wb") as f:
        index = {
            "paths": {
                "app_path": "path/to/app",
            }
        }
        tomli_w.dump(index, f)

    assert create_command.document_type_icon_targets(myapp) == {}


def test_document_type_single_icon(create_command, myapp):
    """If a doctype icon target is specified as a single string, the
    document_type_icons list has one unsized entry."""
    bundle_path = create_command.bundle_path(myapp)
    bundle_path.mkdir(parents=True)
    with (bundle_path / "briefcase.toml").open("wb") as f:
        index = {
            "paths": {
                "app_path": "path/to/app",
                "document_type_icon": {
                    "mydoc": "path/to/mydoc-icon.png",
                    "other": "path/to/otherdoc-icon.png",
                },
            }
        }
        tomli_w.dump(index, f)

    assert create_command.document_type_icon_targets(myapp) == {
        "mydoc": {
            None: "path/to/mydoc-icon.png",
        },
        "other": {
            None: "path/to/otherdoc-icon.png",
        },
    }


def test_document_type_multiple_icons(create_command, myapp):
    """If there are multiple document_type_icons targets, they're all in the
    target list."""
    bundle_path = create_command.bundle_path(myapp)
    bundle_path.mkdir(parents=True)
    with (bundle_path / "briefcase.toml").open("wb") as f:
        index = {
            "paths": {
                "app_path": "path/to/app",
                "document_type_icon": {
                    "mydoc": "path/to/mydoc-icon.png",
                    "other": {
                        "10": "path/to/otherdoc-icon-10.png",
                        "20": "path/to/otherdoc-icon-20.png",
                    },
                },
            }
        }
        tomli_w.dump(index, f)

    assert create_command.document_type_icon_targets(myapp) == {
        "mydoc": {
            None: "path/to/mydoc-icon.png",
        },
        "other": {
            "10": "path/to/otherdoc-icon-10.png",
            "20": "path/to/otherdoc-icon-20.png",
        },
    }


def test_default_output_format_template_context(default_create_command, myapp):
    """The default output format template context is empty."""
    assert default_create_command.output_format_template_context(myapp) == {}
