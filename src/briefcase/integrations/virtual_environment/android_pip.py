"""Run pip with Android markers for Python versions unsupported by xbuild.

The host Python version matches the app's Python version. Wheel compatibility is
supplied by pip's --platform argument, but pip does not use that argument when
evaluating dependency markers. Match the pre-3.13 Android interpreter's markers for both
direct requirements and wheel metadata.
"""

import sys

from pip._internal.cli.main import main as pip_main
from pip._vendor.packaging import markers


def main():
    """Install requirements using pip and the requested Android ABI's markers."""
    abi = sys.argv[1]
    host_environment = markers.default_environment

    def android_environment():
        return {
            **host_environment(),
            "os_name": "posix",
            "sys_platform": "linux",
            "platform_system": "Linux",
            "platform_release": "",
            "platform_version": "",
            "platform_machine": {
                "arm64-v8a": "aarch64",
                "armeabi-v7a": "armv7l",
                "x86_64": "x86_64",
                "x86": "i686",
            }[abi],
        }

    markers.default_environment = android_environment
    return pip_main(sys.argv[2:])


if __name__ == "__main__":
    sys.exit(main())
