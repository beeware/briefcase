import pytest

from briefcase.config import is_pep440_canonical_version


@pytest.mark.parametrize(
    'version',
    [
        '0.1',
        '1.2',
        '1.2a3',
        '1.2a13',
        '1.2b4',
        '1.2b14',
        '1.2rc5',
        '1.2rc15',
        '1.2.dev16',
        '1.2.dev6',
        '1.2.post8',
        '1.2.post18',
        '1.2.3',
        '1.0.2a3',
        '1.0.2a13',
        '1.0.2b4',
        '1.0.2b14',
        '1.0.2rc5',
        '1.0.2rc15',
        '1.0.2.dev16',
        '1.0.2.dev6',
        '1.0.2.post7',
        '1.0.2.post17',
        # Date based
        '2019.1',
        '2019.18',
        # Examples
        '1.0.dev456',
        '1.0a1',
        '1.0a2.dev456',
        '1.0a12.dev456',
        '1.0a12',
        '1.0b1.dev456',
        '1.0b2',
        '1.0b2.post345.dev456',
        '1.0b2.post345',
        '1.0rc1.dev456',
        '1.0rc1',
        '1.0',
        '1.0.post456.dev34',
        '1.0.post456',
        '1.1.dev1',
        # Epochs
        '1!2.3',
        '2!1.0a1',
        '31!1.0b2.post345.dev456',
    ]
)
def test_valid_app_version(version):
    assert is_pep440_canonical_version(version)


@pytest.mark.parametrize(
    'version',
    [
        'foobar',  # Really not a version.
        '0xcafe',  # Hex version

        # PEP440 allows for certain variations, but considers them
        # non-canonical. We reject *all* non-canonical.

        # Versions are normalized to lower case
        '1.2RC3',
        '1.2.3.DEV4',

        # Some dashes, underscores and dots are normalized
        '1.0.2.a3',
        '1.0.2-a3',
        '1.0.2_a3',
        '1.0.2.b14',
        '1.0.2-b14',
        '1.0.2_b14',
        '1.0.2.rc15',
        '1.0.2-rc15',
        '1.0.2_rc15',
        '1.0.2dev6',
        '1.0.2post7',
        '1.0.2-dev6',
        '1.0.2_dev6',
        '1.0.2-post7',
        '1.0.2_post7',

        # Other spellings of a/b/rc/pre/post
        '1.0.2alpha7',
        '1.0.2beta7',
        '1.0.2c7',
        '1.0.2preview7',
        '1.0.2r7',
        '1.0.2-7',

        # Local version segments
        '1.0+abc.5',
        '1.0+abc.7',
        '1.0+5',
        '1.0+ubuntu-1',

        # v Prefix,
        'v1.0',
        'v1.2.3.dev4',
    ]
)
def test_invalid_app_version(version):
    assert not is_pep440_canonical_version(version)
