from briefcase.config import merge_pep621_config


def test_empty():
    "Merging a PEP621 config with no interesting keys causes no changes"
    briefcase_config = {"key": "value"}

    merge_pep621_config(briefcase_config, {"other": "thingy"})

    assert briefcase_config == {"key": "value"}


def test_base_keys():
    "If the PEP621 config provides keys, they are added"
    briefcase_config = {"key": "value"}

    merge_pep621_config(
        briefcase_config,
        {
            "description": "It's cool",
            "version": "1.2.3",
            "urls": {"Homepage": "https://example.com"},
            "license": {"text": "BSD License"},
        },
    )

    assert briefcase_config == {
        "key": "value",
        "description": "It's cool",
        "version": "1.2.3",
        "license": "BSD License",
        "url": "https://example.com",
    }


def test_base_keys_override():
    "If the PEP621 config provides keys, they are added"
    briefcase_config = {
        "key": "value",
        "description": "Good code I promise",
        "version": "2.3.4",
        "url": "https://beeware.org",
        "license": "BSD License",
    }

    merge_pep621_config(
        briefcase_config,
        {
            "description": "It's cool",
            "version": "1.2.3",
            "urls": {"Homepage": "https://example.com"},
            "license": {"text": "GPL3"},
        },
    )

    assert briefcase_config == {
        "key": "value",
        "description": "Good code I promise",
        "version": "2.3.4",
        "license": "BSD License",
        "url": "https://beeware.org",
    }


def test_missing_subkeys():
    "If a subkey is missing, the value is ignored"
    briefcase_config = {"key": "value"}

    merge_pep621_config(
        briefcase_config,
        {
            "urls": {"Sponsorship": "https://example.com"},
            "license": {"file": "license.txt"},
        },
    )

    assert briefcase_config == {
        "key": "value",
    }


def test_empty_authors():
    "If the author list is empty, no author is recorded"
    briefcase_config = {"key": "value"}

    merge_pep621_config(
        briefcase_config,
        {"authors": []},
    )

    assert briefcase_config == {
        "key": "value",
    }


def test_single_author():
    "If there is a single author, their details are recorded"
    briefcase_config = {"key": "value"}

    merge_pep621_config(
        briefcase_config,
        {
            "authors": [
                {
                    "name": "Jane Developer",
                    "email": "jane@example.com",
                }
            ]
        },
    )

    assert briefcase_config == {
        "key": "value",
        "author": "Jane Developer",
        "author_email": "jane@example.com",
    }


def test_multiple_authors():
    "If there are multiple authors, the first author is recorded"
    briefcase_config = {"key": "value"}

    merge_pep621_config(
        briefcase_config,
        {
            "authors": [
                {
                    "name": "Jane Developer",
                    "email": "jane@example.com",
                },
                {
                    "name": "John Assistant",
                    "email": "john@somewhere.com",
                },
            ]
        },
    )

    assert briefcase_config == {
        "key": "value",
        "author": "Jane Developer",
        "author_email": "jane@example.com",
    }


def test_mising_author_name():
    "If the author is missing name, only the author email is captured"
    briefcase_config = {"key": "value"}

    merge_pep621_config(
        briefcase_config,
        {
            "authors": [
                {
                    "email": "jane@example.com",
                }
            ]
        },
    )

    assert briefcase_config == {
        "key": "value",
        "author_email": "jane@example.com",
    }


def test_missing_author_email():
    "If the author email is missing, the name is still recorded"
    briefcase_config = {"key": "value"}

    merge_pep621_config(
        briefcase_config,
        {
            "authors": [
                {
                    "name": "Jane Developer",
                }
            ]
        },
    )

    assert briefcase_config == {
        "key": "value",
        "author": "Jane Developer",
    }


def test_existing_author_name():
    "If the author is defined in the global config, the PEP621 value is ignored"
    briefcase_config = {"key": "value", "author": "Grace Hopper"}

    merge_pep621_config(
        briefcase_config,
        {
            "authors": [
                {
                    "name": "Jane Developer",
                    "email": "jane@example.com",
                }
            ]
        },
    )

    assert briefcase_config == {
        "key": "value",
        "author": "Grace Hopper",
        "author_email": "jane@example.com",
    }


def test_existing_author_email():
    "If the author email is missing, the name is still recorded"
    briefcase_config = {"key": "value", "author_email": "grace@hopper.org"}

    merge_pep621_config(
        briefcase_config,
        {
            "authors": [
                {
                    "name": "Jane Developer",
                    "email": "jane@example.com",
                }
            ]
        },
    )

    assert briefcase_config == {
        "key": "value",
        "author": "Jane Developer",
        "author_email": "grace@hopper.org",
    }


def test_no_dependencies():
    "If there are no global dependencies, requires are used as is."
    briefcase_config = {"key": "value", "requires": ["first", "second"]}

    merge_pep621_config(
        briefcase_config,
        {},
    )

    assert briefcase_config == {
        "key": "value",
        "requires": ["first", "second"],
    }


def test_dependencies_without_requires():
    "If the global config doesn't specify requirements, dependencies are used as is"
    briefcase_config = {"key": "value"}

    merge_pep621_config(
        briefcase_config,
        {"dependencies": ["dep1", "dep2"]},
    )

    assert briefcase_config == {
        "key": "value",
        "requires": ["dep1", "dep2"],
    }


def test_dependencies_with_requires():
    "If the global config specify requirements, requires augments dependencies"
    briefcase_config = {"key": "value", "requires": ["first", "second"]}

    merge_pep621_config(
        briefcase_config,
        {"dependencies": ["dep1", "dep2"]},
    )

    assert briefcase_config == {
        "key": "value",
        "requires": ["dep1", "dep2", "first", "second"],
    }


def test_no_test_dependencies():
    "If the global config doesn't specify test dependencies, test_requires are used as is"
    briefcase_config = {"key": "value", "test_requires": ["first", "second"]}

    merge_pep621_config(
        briefcase_config,
        {},
    )

    assert briefcase_config == {
        "key": "value",
        "test_requires": ["first", "second"],
    }


def test_optional_non_test_dependencies():
    "If the global config has non-test optional requirements, requires is used as-is"
    briefcase_config = {"key": "value", "requires": ["first", "second"]}

    merge_pep621_config(
        briefcase_config,
        {"optional-dependencies": {"other": ["dep1", "dep2"]}},
    )

    assert briefcase_config == {
        "key": "value",
        "requires": ["first", "second"],
    }


def test_test_dependencies_without_requires():
    "If the global config doesn't specify test requirements, test dependencies are used as is"
    briefcase_config = {"key": "value"}

    merge_pep621_config(
        briefcase_config,
        {"optional-dependencies": {"test": ["dep1", "dep2"]}},
    )

    assert briefcase_config == {
        "key": "value",
        "test_requires": ["dep1", "dep2"],
    }


def test_test_dependencies_with_requires():
    "If the global config specify requirements, requires augments dependencies"
    briefcase_config = {"key": "value", "test_requires": ["first", "second"]}

    merge_pep621_config(
        briefcase_config,
        {"optional-dependencies": {"test": ["dep1", "dep2"]}},
    )

    assert briefcase_config == {
        "key": "value",
        "test_requires": ["dep1", "dep2", "first", "second"],
    }
