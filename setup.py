#/usr/bin/env python
import io
import re

from setuptools import setup, find_packages

with io.open('./src/briefcase/__init__.py', encoding='utf8') as version_file:
    version_match = re.search(r"^__version__ = ['\"]([^'\"]*)['\"]", version_file.read(), re.M)
    if version_match:
        version = version_match.group(1)
    else:
        raise RuntimeError("Unable to find version string.")


with io.open('README.rst', encoding='utf8') as readme:
    long_description = readme.read()


setup(
    name='briefcase',
    version=version,
    description='Tools to support converting a Python project into a standalone native application.',
    long_description=long_description,
    author='Russell Keith-Magee',
    author_email='russell@keith-magee.com',
    url='http://pybee.org/briefcase',
    keywords=['app', 'packaging', 'macOS', 'iOS', 'android', 'tvOS', 'mobile', 'windows'],
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    entry_points={
        'distutils.commands': [
            'android = briefcase.android:android',
            'app = briefcase.app:app',  # Don't call directly, but registration required
            'django = briefcase.django:django',
            'ios = briefcase.ios:ios',
            'linux = briefcase.linux:linux',
            'macos = briefcase.macos:macos',
            'tvos = briefcase.tvos:tvos',
            'watchos = briefcase.watchos:watchos',
            'windows = briefcase.windows:windows',
        ]
    },
    python_requires='>=3.4',
    install_requires=[
        'pip >= 18.0',
        'cookiecutter >= 1.0',
        'voc >= 0.1.1',
        'setuptools >= 40.0',
        'requests < 3.0',
        'boto3 >= 1.4.4',
        # urllib3 is required by both requests and boto3. However, they both require
        # different versions. Both versions specify acceptable ranges, but for some
        # reason, pip is unable to resolve an acceptable version.
        # As a workaround, pin a specific urllib3 version. At some point in the future,
        # this will break either requests or boto3 (or possibly both), at which point
        # the requirement can probably be dropped.
        'urllib3<1.24',
    ],
    license='New BSD',
    classifiers=[
        'Development Status :: 4 - Beta',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.4',
        'Programming Language :: Python :: 3.5',
        'Programming Language :: Python :: 3.6',
        'Programming Language :: Python :: 3.7',
        'Programming Language :: Python :: 3 :: Only',
        'Topic :: Software Development',
        'Topic :: Utilities',
    ],
    test_suite='tests',
    package_urls={
        'Funding': 'https://pybee.org/contributing/membership/',
        'Documentation': 'http://briefcase.readthedocs.io/en/latest/',
        'Tracker': 'https://github.com/pybee/briefcase/issues',
        'Source': 'https://github.com/pybee/briefcase',
    },
)
