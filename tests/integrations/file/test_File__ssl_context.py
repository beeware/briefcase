import sys

if sys.version_info >= (3, 10):  # pragma: no-cover-if-lt-py310
    import truststore
else:  # pragma: no-cover-if-gte-py310
    # truststore is only available for python 3.10+
    truststore = None


def test_ssl_context(mock_tools):
    """The SSL context is of the expected type."""
    if sys.version_info >= (3, 10):
        expected_type = truststore.SSLContext
    else:
        expected_type = bool

    assert isinstance(mock_tools.file.ssl_context, expected_type)
