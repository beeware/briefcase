# Configuration file for the Sphinx documentation builder.
#
# For the full list of built-in configuration values, see the documentation:
# https://www.sphinx-doc.org/en/master/usage/configuration.html

import os
import sys
from importlib.metadata import version as metadata_version

import beeware_theme

# BeeWare theme override for Furo Sphinx theme to add BeeWare features.
templates_path = []
html_static_path = []
html_css_files = []
html_context = {}
html_theme_options = {}

beeware_theme.init(
    project_name="briefcase",
    templates=templates_path,
    context=html_context,
    static=html_static_path,
    css=html_css_files,
    theme_options=html_theme_options,
)

# If extensions (or modules to document with autodoc) are in another directory,
# add these directories to sys.path here. If the directory is relative to the
# documentation root, use os.path.abspath to make it absolute, like shown here.
sys.path.insert(0, os.path.abspath("../src"))

# -- Project information -----------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#project-information

project = "Briefcase"
copyright = "Russell Keith-Magee"

# The full version, including alpha/beta/rc tags
release = metadata_version("briefcase")
# The short X.Y version
version = ".".join(release.split(".")[:2])

# -- General configuration ---------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#general-configuration

needs_sphinx = "8.2"
extensions = [
    "sphinx.ext.autodoc",
    "sphinx.ext.intersphinx",
    "sphinx_copybutton",
    "sphinx_tabs.tabs",
    "sphinxcontrib.spelling",
]
exclude_patterns = ["_build"]

# API status indicators.
rst_prolog = """
.. role:: full
.. role:: yes
.. role:: ymmv
.. |f| replace:: :full:`●`
.. |y| replace:: :yes:`○`
.. |v| replace:: :ymmv:`△`
"""

# -- Options for HTML output -------------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-html-output

html_theme = "furo"
html_title = f"Briefcase {release}"
html_logo = "_static/images/briefcase.png"
html_static_path.append("_static")

pygments_style = "sphinx"

# -- Options for the Python domain -------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/domains/python.html

add_module_names = False

# -- Options for autodoc extension -------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/autodoc.html#configuration

autoclass_content = "both"

# -- Options for intersphinx extension ---------------------------------------
# https://www.sphinx-doc.org/en/master/usage/extensions/intersphinx.html#configuration

intersphinx_mapping = {
    "python": ("https://docs.python.org/3", None),
}

# -- Options for link checking -----------------------------------------------
# https://www.sphinx-doc.org/en/master/usage/configuration.html#options-for-the-linkcheck-builder

linkcheck_anchors_ignore = [
    # Ignore anchor detection/verification for Apple help links
    # e.g.: https://help.apple.com/xcode/mac/current/#/dev97211aeac
    "^/dev[0-9a-f]{9}$",
]

linkcheck_ignore = [
    r"^./android/gradle.html$",
    r"^./iOS/xcode.html$",
    r"^./linux/appimage.html$",
    r"^./linux/flatpak.html$",
    r"^./linux/system.html$",
    r"^./macOS/app.html$",
    r"^./macOS/xcode.html$",
    r"^./web/static.html$",
    r"^./windows/app.html$",
    r"^./windows/visualstudio.html$",
    r"^https://github.com/beeware/briefcase/issues/\d+$",
    r"^https://github.com/beeware/briefcase/pull/\d+$",
    # Ignore WiX URLs, because they client block RTD's build.
    r"^https://www.firegiant.com/wixtoolset/$",
    # PyGame seems to be having a long-term outage of their homepage.
    r"^https://www.pygame.org/news$",
]

# -- Options for copy button -------------------------------------------------
# https://sphinx-copybutton.readthedocs.io/en/latest/use.html

# virtual env prefix: (venv), (beeware-venv), (testenv)
venv = r"\((?:(?:beeware-)?venv|testvenv)\)"
# macOS and Linux shell prompt: $
shell = r"\$"
# win CMD prompt: C:\>, C:\...>
cmd = r"C:\\>|C:\\\.\.\.>"
# PowerShell prompt: PS C:\>, PS C:\...>
ps = r"PS C:\\>|PS C:\\\.\.\.>"
# zero or one whitespace char
sp = r"\s?"

# optional venv prefix
venv_prefix = rf"(?:{venv})?"
# one of the platforms' shell prompts
shell_prompt = rf"(?:{shell}|{cmd}|{ps})"

copybutton_prompt_text = "|".join(
    [
        # Python REPL
        # r">>>\s?", r"\.\.\.\s?",
        # IPython and Jupyter
        # r"In \[\d*\]:\s?", r" {5,8}:\s?", r" {2,5}\.\.\.:\s?",
        # Shell prompt
        rf"{venv_prefix}{sp}{shell_prompt}{sp}",
    ]
)
copybutton_prompt_is_regexp = True
copybutton_remove_prompts = True
copybutton_only_copy_prompt_lines = True
copybutton_copy_empty_lines = False

# -- Options for spelling ----------------------------------------------------
# https://sphinxcontrib-spelling.readthedocs.io/en/latest/customize.html

# Spelling language.
spelling_lang = "en_US"

# Location of word list.
spelling_word_list_filename = "spelling_wordlist"
