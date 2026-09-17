# Environment management with uv

Briefcase is able to use [uv](https://docs.astral.sh/uv/) to manage the installation of application requirements.

When `uv` is used to manage your app environment, an official Python or Briefcase-supplied Python support package will be used for your app.

## Prerequisites

Uv environment management can be used for macOS, Windows and iOS apps; and for Linux System apps when Docker is *not* used. An error will be raised if you attempt to use uv as an environment manager on any other platform, or if you attempt to build a Linux System app with Docker.

To use uv as the environment manager in your application, the `uv` binary must be available on your `PATH`. It can be installed using any of the [installation methods described in the uv documentation](https://docs.astral.sh/uv/getting-started/installation/).

## Configuration

To use uv as the environment manager for your app, add `env_manager = "uv"` to your app configuration. This can be done as a global setting (in `[tool.briefcase]` section) or in a per-app setting (in the `[tool.briefcase.app.myapp]` section for `myapp`).

## Specifying requirements

When `uv` is used as an environment manager, requirements are installed using `uv pip install`. The values provided to `requires` and `test_requires` must be in a `pip`-compatible format. The following would be examples of legal specifiers:

- A bare package name:
  ```python
  requires = ["pillow"]
  ```

- A package name with version specifier:
  ```python
  requires = ["pillow==9.1.0"]
  ```

- A package with a platform specifier:
  ```python
  requires = ["pillow==9.1.0; sys_platform == 'darwin'"]
  ```

- A Git repository:
  ```python
  requires = ["git+https://github.com/beeware/briefcase.git"]
  ```

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
