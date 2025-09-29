import pytest

from briefcase.commands.config import validate_key
from briefcase.exceptions import BriefcaseConfigError


@pytest.mark.parametrize("bad", ["not-an-email", "user@", "@host", "a@b", "a@@b.com"])
def test_author_email_invalid_rejected(bad):
    with pytest.raises(BriefcaseConfigError):
        validate_key("author.email", bad)
