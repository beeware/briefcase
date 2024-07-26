import pytest

from briefcase.config import (
    validate_document_description,
    validate_document_ext,
    validate_document_icon,
    validate_document_url,
)
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
        {
            "icon": "icon 2",
            "description": "this is a descrpition",
            "url": "http://testurl.com",
            "extension": "png",
        },
    ],
)
@pytest.mark.parametrize(
    "validation",
    [
        validate_document_icon,
        validate_document_description,
        validate_document_url,
        validate_document_ext,
    ],
)
def test_validations(validation, valid_document):
    # Success does not raise an exception
    validation("ext", valid_document)


def test_validate_document_missing_field(valid_document):
    del valid_document["icon"]
    # Failure raises an exception
    with pytest.raises(
        BriefcaseConfigError, match=r"Document type .* does not define an icon."
    ):
        validate_document_icon("ext", valid_document)


@pytest.mark.parametrize("invalid_icon", (1, None, False, True))
def test_validate_document_invalid_icon(invalid_icon, valid_document):
    valid_document["icon"] = invalid_icon
    # Failure raises an exception
    with pytest.raises(
        BriefcaseConfigError,
        match=r"The icon definition associated with document type .* is not a string.",
    ):
        validate_document_icon("ext", valid_document)


def test_validate_document_missing_description(valid_document):
    del valid_document["description"]
    # Failure raises an exception
    with pytest.raises(
        BriefcaseConfigError, match=r"Document type .* does not provide a description."
    ):
        validate_document_description("ext", valid_document)


@pytest.mark.parametrize("invalid_description", (1, None, False, True))
def test_validate_document_invalid_description(invalid_description, valid_document):
    valid_document["description"] = invalid_description
    # Failure raises an exception
    with pytest.raises(
        BriefcaseConfigError,
        match=r"The description associated with document type .* is not a string.",
    ):
        validate_document_description("ext", valid_document)


def test_validate_document_missing_url(valid_document):
    del valid_document["url"]
    # Failure raises an exception
    with pytest.raises(
        BriefcaseConfigError, match=r"Document type .* does not provide a URL."
    ):
        validate_document_url("ext", valid_document)


@pytest.mark.parametrize("invalid_url", (False, None, "test.com", "fake"))
def test_validate_document_invalid_url(invalid_url, valid_document):
    valid_document["url"] = invalid_url
    # Failure raises an exception
    with pytest.raises(
        BriefcaseConfigError,
        match=r"The URL associated with document type .* is invalid: Not a valid URL!",
    ):
        validate_document_url("ext", valid_document)


def test_validate_document_missing_extension(valid_document):
    del valid_document["extension"]
    # Failure raises an exception
    with pytest.raises(
        BriefcaseConfigError, match=r"Document type .* does not provide an extension."
    ):
        validate_document_ext("ext", valid_document)


@pytest.mark.parametrize("invalid_extension", (1, "..", ".-.", False, None))
def test_validate_document_invalid_extension(invalid_extension, valid_document):
    valid_document["extension"] = invalid_extension
    # Failure raises an exception
    with pytest.raises(
        BriefcaseConfigError,
        match=r"The extension provided for document type .* is not alphanumeric.",
    ):
        validate_document_ext("ext", valid_document)
