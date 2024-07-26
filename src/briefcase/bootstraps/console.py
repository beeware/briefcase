from briefcase.bootstraps.base import BaseGuiBootstrap


class ConsoleBootstrap(BaseGuiBootstrap):
    display_name_annotation = "does not support iOS/Android/Web deployment"

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
console_app = true
requires = [
]
test_requires = [
{% if cookiecutter.test_framework == "pytest" %}
    "pytest",
{% endif %}
]
"""

    def pyproject_table_macOS(self):
        return """\
universal_build = true
requires = [
]
"""

    def pyproject_table_linux(self):
        return """\
requires = [
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
flatpak_runtime_version = "23.08"
flatpak_sdk = "org.freedesktop.Sdk"
"""

    def pyproject_table_windows(self):
        return """\
requires = [
]
"""

    def pyproject_table_iOS(self):
        return """\
supported = false
"""

    def pyproject_table_android(self):
        return """\
supported = false
"""

    def pyproject_table_web(self):
        return """\
supported = false
"""
