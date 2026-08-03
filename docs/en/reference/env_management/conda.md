# Environment management with Conda

Briefcase is able to use [Conda](https://conda.io) to provide Python, and manage the installation of application requirements.

## Prerequisites

Briefcase requires the use of Conda 26.5 or higher.

## Configuration

To use Conda as the environment manager for your app, add `env_manager = "conda"` to your app configuration. This can be done as a global setting (in `[tool.briefcase]` section) or in a per-app setting (in the `[tool.briefcase.app.myapp]` section for `myapp`).

The Conda environments that are created by Briefcase are installed using the `rattler` resolver.

## Specifying requirements

When `conda` is used as an environment manager, the values provided to `requires` and `test_requires` must be in Conda-compatible format. The following would be examples of legal specifiers:

- Bare package name:
  ```python
  requires = ["pillow"]
  ```

- Fuzzy version match
  ```python
  requires = ["pillow=9.1"]
  ```

- Channel-qualified install
  ```python
  requires = ["conda-forge::pillow"]
  ```

Conda cannot install packages stored as local source references. If your requirements reference a local path, Briefcase will use `pip` to install that requirement (and its dependencies) into your Conda environment. The following are examples of paths that would be installed with `pip`:

- A local directory:
  ```python
  requires = [
      "../mysrc/myapp",
      "./local/otherapp",
      "/usr/local/fullapp",
  ]
  ```
  When in development mode, a reference to a local directory will be installed editable. Any changes made to the code in the original location will be picked up automatically the next time you start your application in development mode. When generating a final application, editable mode will *not* be used.

- Local wheel file:
  ```python
  requires = [
      "../mysrc/myapp-1.2.3.py3-none-any.whl",
      "./local/otherapp-1.2.3.py3-none-any.whl",
      "/usr/local/fullapp-1.2.3.py3-none-any.whl",
  ]
  ```
