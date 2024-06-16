import pytest

from briefcase.config import (
    validate_document_description,
    validate_document_ext,
    validate_document_icon,
    validate_document_url,
)
from briefcase.exceptions import BriefcaseConfigError


@pytest.mark.parametrize(
    "validation",
    [
        validate_document_icon,
        validate_document_description,
        validate_document_url,
        validate_document_ext,
    ],
)
def test_validations(validation):
    valid_document = {
        "icon": "icon",
        "description": "description",
        "url": "https://testurl.com",
        "extension": "ext",
    }
    # Success does not raise an exception
    validation("ext", valid_document)


def test_validate_document_missing_field():
    invalid_document = {
        "description": "description",
        "url": "https://testurl.com",
        "extension": "ext",
    }
    # Failure raises an exception
    with pytest.raises(BriefcaseConfigError):
        validate_document_icon("ext", invalid_document)


def test_validate_document_invalid_icon():
    invalid_document = {
        "icon": 1,
        "description": "description",
        "url": "https://testurl.com",
        "extension": "ext",
    }
    # Failure raises an exception
    with pytest.raises(BriefcaseConfigError):
        validate_document_icon("ext", invalid_document)


def test_validate_document_missing_description():
    invalid_document = {
        "icon": "icon",
        "url": "https://testurl.com",
        "extension": "ext",
    }
    # Failure raises an exception
    with pytest.raises(BriefcaseConfigError):
        validate_document_description("ext", invalid_document)


def test_validate_document_invalid_description():
    invalid_document = {
        "icon": "icon",
        "description": 37,
        "url": "https://testurl.com",
        "extension": "ext",
    }
    # Failure raises an exception
    with pytest.raises(BriefcaseConfigError):
        validate_document_description("ext", invalid_document)


def test_validate_document_missing_url():
    invalid_document = {
        "icon": "icon",
        "description": "description",
        "extension": "ext",
    }
    # Failure raises an exception
    with pytest.raises(BriefcaseConfigError):
        validate_document_url("ext", invalid_document)


def test_validate_document_invalid_url():
    invalid_document = {
        "icon": "icon",
        "description": "description",
        "url": "testurl.com",
        "extension": "ext",
    }
    # Failure raises an exception
    with pytest.raises(BriefcaseConfigError):
        validate_document_url("ext", invalid_document)


def test_validate_document_missing_extension():
    invalid_document = {
        "icon": "icon",
        "description": "description",
        "url": "https://testurl.com",
    }
    # Failure raises an exception
    with pytest.raises(BriefcaseConfigError):
        validate_document_ext("ext", invalid_document)


def test_validate_document_invalid_extension():
    invalid_document_ext = {"extension": ".-."}
    # Failure raises an exception
    with pytest.raises(BriefcaseConfigError):
        validate_document_ext("ext", invalid_document_ext)
