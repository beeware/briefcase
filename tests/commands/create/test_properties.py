import pytest
import toml
from botocore.stub import Stubber

from briefcase.commands.create import NoSupportPackage


def test_template_url(create_command):
    "The template URL is a simple construction of the platform and format"
    assert create_command.template_url == 'https://github.com/beeware/briefcase-tester-dummy-template.git'


def test_app_path(create_command, myapp, tmp_path):
    bundle_path = create_command.bundle_path(myapp, tmp_path)
    bundle_path.mkdir(parents=True)
    with open(bundle_path / 'briefcase.toml', 'w') as f:
        index = {
            'paths': {
                'app_path': 'path/to/app',
                'app_packages_path': 'path/to/app_packages',
                'support_path': 'path/to/support',
            }
        }
        toml.dump(index, f)

    assert create_command.app_path(myapp, tmp_path) == bundle_path / 'path' / 'to' / 'app'

    # Requesting a second time should hit the cache,
    # so the briefcase file won't be needed.
    # Delete it to make sure the cache is used.
    (bundle_path / 'briefcase.toml').unlink()
    assert create_command.app_path(myapp, tmp_path) == bundle_path / 'path' / 'to' / 'app'


def test_app_packages_path(create_command, myapp, tmp_path):
    bundle_path = create_command.bundle_path(myapp, tmp_path)
    bundle_path.mkdir(parents=True)
    with open(bundle_path / 'briefcase.toml', 'w') as f:
        index = {
            'paths': {
                'app_path': 'path/to/app',
                'app_packages_path': 'path/to/app_packages',
                'support_path': 'path/to/support',
            }
        }
        toml.dump(index, f)

    assert create_command.app_packages_path(myapp, tmp_path) == bundle_path / 'path' / 'to' / 'app_packages'

    # Requesting a second time should hit the cache,
    # so the briefcase file won't be needed.
    # Delete it to make sure the cache is used.
    (bundle_path / 'briefcase.toml').unlink()
    assert create_command.app_packages_path(myapp, tmp_path) == bundle_path / 'path' / 'to' / 'app_packages'


def test_support_path(create_command, myapp, tmp_path):
    bundle_path = create_command.bundle_path(myapp, tmp_path)
    bundle_path.mkdir(parents=True)
    with open(bundle_path / 'briefcase.toml', 'w') as f:
        index = {
            'paths': {
                'app_path': 'path/to/app',
                'app_packages_path': 'path/to/app_packages',
                'support_path': 'path/to/support',
            }
        }
        toml.dump(index, f)

    assert create_command.support_path(myapp, tmp_path) == bundle_path / 'path' / 'to' / 'support'

    # Requesting a second time should hit the cache,
    # so the briefcase file won't be needed.
    # Delete it to make sure the cache is used.
    (bundle_path / 'briefcase.toml').unlink()
    assert create_command.support_path(myapp, tmp_path) == bundle_path / 'path' / 'to' / 'support'


def test_support_package_url_single_match(create_command):
    # Prime the s3 client, and wrap it in a stubber.
    s3 = create_command._anonymous_s3_client('us-west-2')
    stub_s3 = Stubber(s3)

    # Add the expected request/responses from S3
    stub_s3.add_response(
        method='list_objects_v2',
        expected_params={
            'Bucket': 'briefcase-support',
            'Prefix': 'python/3.X/tester/'
        },
        service_response={
            'Contents': [
                {'Key': 'python/3.X/tester/Python-3.X-tester-support.b1.tar.gz'}
            ],
            'KeyCount': 1,
        }
    )

    # We've set up all the expected S3 responses, so activate the stub
    stub_s3.activate()

    # Retrieve the property, retrieving the support package URL.
    assert create_command.support_package_url == 'https://briefcase-support.s3-us-west-2.amazonaws.com/python/3.X/tester/Python-3.X-tester-support.b1.tar.gz'

    # Check the S3 calls have been exhausted
    stub_s3.assert_no_pending_responses()


def test_support_package_url_multiple_match(create_command):
    "If there are multiple candidate support packages, the highest build number wins"
    # Prime the s3 client, and wrap it in a stubber.
    s3 = create_command._anonymous_s3_client('us-west-2')
    stub_s3 = Stubber(s3)

    # Add the expected request/responses from S3
    stub_s3.add_response(
        method='list_objects_v2',
        expected_params={
            'Bucket': 'briefcase-support',
            'Prefix': 'python/3.X/tester/'
        },
        service_response={
            'Contents': [
                {'Key': 'python/3.X/tester/Python-3.X-tester-support.b11.tar.gz'},
                {'Key': 'python/3.X/tester/Python-3.X-tester-support.b8.tar.gz'},
                {'Key': 'python/3.X/tester/Python-3.X-tester-support.b9.tar.gz'},
                {'Key': 'python/3.X/tester/Python-3.X-tester-support.b10.tar.gz'},
            ],
            'KeyCount': 4,
        }
    )

    # We've set up all the expected S3 responses, so activate the stub
    stub_s3.activate()

    # Retrieve the property, retrieving the support package URL.
    assert create_command.support_package_url == 'https://briefcase-support.s3-us-west-2.amazonaws.com/python/3.X/tester/Python-3.X-tester-support.b11.tar.gz'

    # Check the S3 calls have been exhausted
    stub_s3.assert_no_pending_responses()


def test_support_package_url_no_match(create_command):
    "If there is no plausible candidate support package, raise an error"
    # Prime the s3 client, and wrap it in a stubber.
    s3 = create_command._anonymous_s3_client('us-west-2')
    stub_s3 = Stubber(s3)

    # Add the expected request/responses from S3
    stub_s3.add_response(
        method='list_objects_v2',
        expected_params={
            'Bucket': 'briefcase-support',
            'Prefix': 'python/3.X/tester/'
        },
        service_response={
            'KeyCount': 0,
        }
    )

    # We've set up all the expected S3 responses, so activate the stub
    stub_s3.activate()

    # Retrieve the property, retrieving the support package URL.
    with pytest.raises(NoSupportPackage):
        create_command.support_package_url

    # Check the S3 calls have been exhausted
    stub_s3.assert_no_pending_responses()
