import truststore


def test_ssl_context(mock_tools):
    """The SSL context is of the expected type."""
    expected_type = truststore.SSLContext

    assert isinstance(mock_tools.file.ssl_context, expected_type)
