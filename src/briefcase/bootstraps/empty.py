from __future__ import annotations

from briefcase.bootstraps.base import BaseGuiBootstrap


class EmptyBootstrap(BaseGuiBootstrap):
    def app_source(self):
        return """\

def main():
    # Your app logic goes here
    print("Hello, World.")
"""

    def app_start_source(self):
        return """\
from {{ cookiecutter.module_name }}.app import main

if __name__ == "__main__":
    main()
"""

    def pyproject_table_briefcase_app_extra_content(self):
        return """
requires = [
    # Add your cross-platform app requirements here
]
test_requires = [
    # Add your cross-platform test requirements here
]
"""

    def pyproject_table_macOS(self):
        return """\
universal_build = true
requires = [
    # Add your macOS-specific app requirements here
]
"""

    def pyproject_table_linux(self):
        return """\
requires = [
    # Add your Linux-specific app requirements here
]
"""

    def pyproject_table_linux_system_debian(self):
        return """\
system_requires = [
    # Add any system packages needed at build the app here
]

system_runtime_requires = [
    # Add any system packages needed at runtime here
]
"""

    def pyproject_table_linux_system_rhel(self):
        return """\
system_requires = [
    # Add any system packages needed at build the app here
]

system_runtime_requires = [
    # Add any system packages needed at runtime here
]
"""

    def pyproject_table_linux_system_suse(self):
        return """\
system_requires = [
    # Add any system packages needed at build the app here
]

system_runtime_requires = [
    # Add any system packages needed at runtime here
]
"""

    def pyproject_table_linux_system_arch(self):
        return """\
system_requires = [
    # Add any system packages needed at build the app here
]

system_runtime_requires = [
    # Add any system packages needed at runtime here
]
"""

    def pyproject_table_linux_flatpak(self):
        return """\
flatpak_runtime = "org.freedesktop.Platform"
flatpak_runtime_version = "24.08"
flatpak_sdk = "org.freedesktop.Sdk"
"""

    def pyproject_table_windows(self):
        return """\
requires = [
    # Add your Windows-specific app requirements here
]
"""

    def pyproject_table_iOS(self):
        return """\
requires = [
    # Add your iOS-specific app requirements here
]
"""

    def pyproject_table_android(self):
        return """\
requires = [
    # Add your Android-specific app requirements here
]
"""

    def pyproject_table_web(self):
        return """\
requires = [
    # Add your web-specific app requirements here
]
"""
