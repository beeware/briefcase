from briefcase.commands.run import LogFilter


def test_custom_filter():
    "The user can specify a custom failure filter"
    custom_func = LogFilter.test_filter("WIBBLE")

    recent = [
        "rootdir: /Users/rkm/beeware/briefcase, configfile: pyproject.toml",
        "plugins: cov-3.0.0",
        "collecting ... collected 0 items",
        "",
        "============================ no tests ran in 0.01s =============================",
    ]

    assert not custom_func("\n".join(recent))

    # Add an extra line that *will* match the filter
    recent.append("I will now say the magic word, which is WIBBLE, so we match")
    assert custom_func("\n".join(recent))
