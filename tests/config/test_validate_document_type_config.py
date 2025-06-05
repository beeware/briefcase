import sys

import pytest

from briefcase.config import validate_document_type_config
from briefcase.exceptions import BriefcaseConfigError


@pytest.fixture
def valid_document():
    return {
        "icon": "icon",
        "description": "description",
        "url": "https://testurl.com",
        "extension": "ext",
    }


@pytest.mark.parametrize(
    "valid_document",
    [
        {
            "icon": "icon",
            "description": "description",
            "url": "https://testurl.com",
            "extension": "ext",
        },
        # Extension doesn't need to match document type
        {
            "icon": "icon 2",
            "description": "this is a descrpition",
            "url": "http://testurl.com",
            "extension": "png",
        },
    ],
)
def test_document_type_config(valid_document):
    """Valid document types don't raise an exception when validated."""
    validate_document_type_config("ext", valid_document)


def test_validate_document_missing_field(valid_document):
    """If a document type is missing an icon, an exception is raised."""
    del valid_document["icon"]
    # Failure raises an exception
    with pytest.raises(
        BriefcaseConfigError, match=r"Document type .* does not define an icon."
    ):
        validate_document_type_config("ext", valid_document)


@pytest.mark.parametrize(
    "invalid_icon",
    [
        1,
        None,
        False,
        True,
    ],
)
def test_validate_document_invalid_icon(invalid_icon, valid_document):
    """Invalid icon values raise an error when validating document types."""
    valid_document["icon"] = invalid_icon
    # Failure raises an exception
    with pytest.raises(
        BriefcaseConfigError,
        match=r"The icon definition associated with document type .* is not a string.",
    ):
        validate_document_type_config("ext", valid_document)


def test_validate_document_missing_description(valid_document):
    """If a document type is missing a description, an exception is raised."""
    del valid_document["description"]
    # Failure raises an exception
    with pytest.raises(
        BriefcaseConfigError, match=r"Document type .* does not provide a description."
    ):
        validate_document_type_config("ext", valid_document)


@pytest.mark.parametrize(
    "invalid_description",
    [
        1,
        None,
        False,
        True,
    ],
)
def test_validate_document_invalid_description(invalid_description, valid_document):
    """Invalid description values raise an error when validating document types."""

    valid_document["description"] = invalid_description
    # Failure raises an exception
    with pytest.raises(
        BriefcaseConfigError,
        match=r"The description associated with document type .* is not a string.",
    ):
        validate_document_type_config("ext", valid_document)


def test_validate_document_missing_url(valid_document):
    """If a document type is missing a URL, an exception is raised."""

    del valid_document["url"]
    # Failure raises an exception
    with pytest.raises(
        BriefcaseConfigError, match=r"Document type .* does not provide a URL."
    ):
        validate_document_type_config("ext", valid_document)


@pytest.mark.parametrize(
    "invalid_url",
    [
        False,
        None,
        "test.com",
        "fake",
    ],
)
def test_validate_document_invalid_url(invalid_url, valid_document):
    """Invalid URL values raise an error when validating document types."""

    valid_document["url"] = invalid_url
    # Failure raises an exception
    with pytest.raises(
        BriefcaseConfigError,
        match=r"The URL associated with document type .* is invalid: Not a valid URL!",
    ):
        validate_document_type_config("ext", valid_document)


def test_validate_document_missing_extension(valid_document):
    """If a document type is missing an extension, an exception is raised."""

    del valid_document["extension"]
    # Failure raises an exception
    with pytest.raises(
        BriefcaseConfigError, match=r"Document type .* does not provide an extension."
    ):
        validate_document_type_config("ext", valid_document)


@pytest.mark.parametrize(
    "invalid_extension",
    [
        1,
        "..",
        ".-.",
        False,
        None,
    ],
)
def test_validate_document_invalid_extension(invalid_extension, valid_document):
    """Invalid extension values raise an error when validating document types."""
    valid_document["extension"] = invalid_extension
    # Failure raises an exception
    with pytest.raises(
        BriefcaseConfigError,
        match=r"The extension provided for document type .* is not alphanumeric.",
    ):
        validate_document_type_config("ext", valid_document)


@pytest.mark.skipif(sys.platform != "darwin", reason="Test runs only on macOS")
def test_document_type_macOS_config_with_mimetype_single(valid_document):
    """Valid document types don't raise an exception when validated.

    application/pdf is the only valid MIME type for PDF files.
    """
    valid_document["mime_type"] = "application/pdf"
    validate_document_type_config("ext", valid_document)
    assert "LSItemContentTypes" in valid_document["macOS"].keys()
    assert valid_document["macOS"]["LSItemContentTypes"] == ["com.adobe.pdf"]
    assert valid_document["macOS"]["is_core_type"] is True
    assert valid_document["macOS"]["LSHandlerRank"] == "Alternate"
    assert "UTTypeConformsTo" not in valid_document["macOS"].keys()


@pytest.mark.skipif(sys.platform != "darwin", reason="Test runs only on macOS")
def test_document_type_macOS_config_with_mimetype_list(valid_document):
    """Valid document types don't raise an exception when validated.

    text/vcard is _not_ the only valid MIME type for vCard files, others are
    text/directory and text/x-vcard so a list if MIME types is returned
    internally but should still resolve to public.vcard
    """
    valid_document["mime_type"] = "text/vcard"
    validate_document_type_config("ext", valid_document)
    assert "LSItemContentTypes" in valid_document["macOS"].keys()
    assert valid_document["macOS"]["LSItemContentTypes"] == ["public.vcard"]
    assert valid_document["macOS"]["is_core_type"] is True
    assert valid_document["macOS"]["LSHandlerRank"] == "Alternate"
    assert "UTTypeConformsTo" not in valid_document["macOS"].keys()


@pytest.mark.skipif(sys.platform != "darwin", reason="Test runs only on macOS")
def test_document_type_macOS_config_with_unknown_mimetype(valid_document):
    """Valid document types don't raise an exception when validated.

    Here, a MIME type is provided that is not known to be valid for any file.
    That means that LSItemContentTypes should _not_ be set.
    """
    valid_document["mime_type"] = "custom/mytype"
    validate_document_type_config("ext", valid_document)
    assert "LSItemContentTypes" not in valid_document["macOS"].keys()
    assert valid_document["macOS"]["is_core_type"] is False
    assert valid_document["macOS"]["LSHandlerRank"] == "Owner"
    # default to a 'normal' document type
    assert valid_document["macOS"]["UTTypeConformsTo"] == [
        "public.data",
        "public.content",
    ]


@pytest.mark.skipif(sys.platform != "darwin", reason="Test runs only on macOS")
def test_document_type_macOS_config_with_list_of_content_types(valid_document):
    """Multiple content types are not allowed.

    If a document type has multiple content types, an exception is raised.
    """
    valid_document.setdefault("macOS", {})["LSItemContentTypes"] = [
        "com.adobe.pdf",
        "public.vcard",
    ]
    with pytest.raises(
        BriefcaseConfigError,
        match="Document type 'ext' has multiple content types.",
    ):
        validate_document_type_config("ext", valid_document)


@pytest.mark.skipif(sys.platform != "darwin", reason="Test runs only on macOS")
@pytest.mark.parametrize(
    "ls_item_content_types",
    ["com.adobe.pdf", ["com.adobe.pdf"]],
)
def test_document_type_macOS_config_with_list_of_single_content_type(
    valid_document, ls_item_content_types
):
    """Single content type is allowed, even if a list is provided.

    If a document type has a single content type, it is converted to a string.
    """
    valid_document.setdefault("macOS", {})["LSItemContentTypes"] = ls_item_content_types
    validate_document_type_config("ext", valid_document)
    assert valid_document["macOS"]["LSItemContentTypes"] == ["com.adobe.pdf"]
    assert valid_document["macOS"]["is_core_type"] is True
    assert valid_document["macOS"]["LSHandlerRank"] == "Alternate"
    assert "UTTypeConformsTo" not in valid_document["macOS"].keys()
