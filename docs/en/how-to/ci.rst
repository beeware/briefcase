Building your App in CI with GitHub Actions
===========================================

This GitHub `Actions <https://docs.github.com/en/actions>`__ workflow provides
the basic framework necessary to test, build, and package a Briefcase project
in CI for Windows, Linux, macOS, iOS, and Android.

Target Platforms
----------------

The same set of steps are used for each platform via a `matrix strategy
<https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/running-variations-of-jobs-in-a-workflow>`__.
This will create a separate job for each target platform with specific
configuration.

These platforms should be updated to match your targets. To remove a platform,
delete the entry from ``strategy.matrix.target`` as well as the corresponding
block of configuration under ``strategy.matrix.include``.

To add a new targeted platform, add the name of the target to
``strategy.matrix.target``. For instance, to target Linux Flatpak, add an entry
to ``strategy.matrix.target`` named ``Flatpak`` and a configuration to build a
Flatpak under ``strategy.matrix.include``, for example:

.. code-block:: YAML

  strategy:
    matrix:
      target: [ "Windows", "macOS", "iOS", "Android", "Flatpak" ]
      include:
        - target: "Flatpak"
          platform: "Linux"
          output-format: "Flatpak"
          runs-on: "ubuntu-latest"
          pre-command: "sudo apt update && sudo apt -y install flatpak flatpak-builder"
          briefcase-run-prefix: "xvfb-run"

Target Platform Configuration
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

These configuration properties can be used to alter behavior of the run for
each targeted platform configured in the matrix.

* ``target``: Name of the target from ``strategy.matrix.target``
* ``platform``: Name of the platform to use in ``briefcase`` commands; if
  blank, then ``target`` is used instead
* ``output-format``: Name of the platform output format for ``briefcase``
  commands
* ``runs-on``: A valid GitHub runner image name for ``jobs.<job id>.runs-on``
* ``pre-command``: Arbitrary Bash commands to run before the Briefcase commands
* ``briefcase-args``: Briefcase arguments to use with all ``briefcase`` commands
* ``briefcase-build-prefix``: Bash commands to prefix to the ``briefcase build``
  command
* ``briefcase-build-args``: Briefcase arguments to use with the ``briefcase
  build`` command
* ``briefcase-run-prefix``: Bash commands to prefix to the ``briefcase run``
  command
* ``briefcase-run-args``: Briefcase arguments to use with the ``briefcase
  run`` command
* ``briefcase-package-prefix``: Bash commands to prefix to the ``briefcase
  package`` command
* ``briefcase-package-args``: Briefcase arguments to use with the ``briefcase
  package`` command

Workflow File Location
----------------------

This workflow should be saved in to a file at ``.github/workflows/ci.yml`` in
your GitHub repository. Once it exists on your default branch on GitHub, a run
will be triggered in the Actions tab.

Workflow Steps
--------------

* Check out the current GitHub repository

  * This will be the version of your repository that triggered the CI run
  * So, for a pull request (PR), this is the code being submitted in the PR
  * After the PR is merged, this is the code in your default branch

* Install Python 3.12

  * This version of Python should be updated to match the version of Python
    your app is targeting

* Install the latest version of Briefcase
* Build the test version of the app
* Run the app's test suite
* Package the release version of the app for the platform
* Upload the distributable artefact created for the platform

  * See limitations below for these artefacts

* If an error occurs, the Briefcase log file is uploaded

Limitations of Uploaded Artefacts
----------------------------------

The artefacts produced and uploaded by this workflow will not be signed;
therefore, when the app is executed locally, some platforms may show a
disconcerting warning about the security of the app or prevent the app from
running altogether. See more information about code signing in the `identity
guides <../how-to/code-signing/>`_.

Workflow File Contents
----------------------

.. code-block:: YAML

    name: CI
    on:
      pull_request:
      push:
        branches:
          - main  # update to match the default branch for your repo

    # Cancel active CI runs for a PR before starting another run
    concurrency:
      group: ${{ github.workflow}}-${{ github.ref }}
      cancel-in-progress: ${{ github.event_name == 'pull_request' }}

    env:
      FORCE_COLOR: "1"

    defaults:
      run:
        shell: bash

    jobs:
      ci:
        name: Test and Package
        runs-on: ${{ matrix.runs-on }}
        strategy:
          fail-fast: false
          matrix:
            target: [ "Windows", "macOS", "Ubuntu-24.04", "Fedora-40", "iOS", "Android"]
            include:
              - target: "Windows"
                output-format: "app"
                runs-on: "windows-latest"

              - target: "macOS"
                output-format: "app"
                runs-on: "macos-latest"

              - target: "Ubuntu-24.04"
                platform: "Linux"
                output-format: "system"
                runs-on: "ubuntu-latest"
                pre-command: "sudo apt -y install socat"
                briefcase-run-prefix: "xvfb-run"
                briefcase-args: "--target ubuntu:24.04"

              - target: "Fedora-40"
                platform: "Linux"
                output-format: "system"
                runs-on: "ubuntu-latest"
                pre-command: "sudo apt -y install socat"
                briefcase-run-prefix: "xvfb-run"
                briefcase-args: "--target fedora:40"

              - target: "iOS"
                output-format: "Xcode"
                runs-on: "macos-latest"
                briefcase-run-args: "--device 'iPhone SE (3rd generation)'"

              - target: "Android"
                output-format: "Gradle"
                runs-on: "ubuntu-latest"
                pre-command: |
                  # Enable KVM permissions for the emulator
                  echo 'KERNEL=="kvm", GROUP="kvm", MODE="0666", OPTIONS+="static_node=kvm"' \
                    | sudo tee /etc/udev/rules.d/99-kvm4all.rules
                  sudo udevadm control --reload-rules
                  sudo udevadm trigger --name-match=kvm
                briefcase-run-args: >-
                  --device '{"avd":"beePhone"}'
                  --shutdown-on-exit
                  --Xemulator=-no-window
                  --Xemulator=-no-snapshot
                  --Xemulator=-no-audio
                  --Xemulator=-no-boot-anim

        steps:
          - name: Checkout
            uses: actions/checkout@v4

          - name: Setup Python
            uses: actions/setup-python@v4
            with:
              python-version: "3.12"  # update with your targeted Python version

          - name: Install Briefcase
            run: |
              python -m pip install -U pip setuptools wheel
              python -m pip install briefcase

          - name: Setup Environment
            run: |
              # Use GitHub's preinstalled JDK 17 for Android builds
              echo JAVA_HOME="${JAVA_HOME_17_X64:-$JAVA_HOME_17_arm64}" | tee -a ${GITHUB_ENV}
              ${{ matrix.pre-command }}

          - name: Build App
            run: |
              ${{ matrix.briefcase-build-prefix }} \
              briefcase build \
                ${{ matrix.platform || matrix.target }} \
                ${{ matrix.output-format }} \
                --test --no-input --log \
                ${{ matrix.briefcase-args }} \
                ${{ matrix.briefcase-build-args }}

          - name: Test App
            run: |
              ${{ matrix.briefcase-run-prefix }} \
              briefcase run \
                ${{ matrix.platform || matrix.target }} \
                ${{ matrix.output-format }} \
                --test --no-input --log \
                ${{ matrix.briefcase-args }} \
                ${{ matrix.briefcase-run-args }}

          - name: Package App
            run: |
              ${{ matrix.briefcase-package-prefix }} \
              briefcase package \
                ${{ matrix.platform || matrix.target }} \
                ${{ matrix.output-format }} \
                --update --adhoc-sign --no-input --log \
                ${{ matrix.briefcase-args }} \
                ${{ matrix.briefcase-package-args }}

          - name: Upload App
            # Briefcase cannot create iOS artefacts; instead, apps
            # must be packaged and published for iOS through Xcode.
            if: matrix.target != 'iOS'
            uses: actions/upload-artifact@v4
            with:
              name: App-${{ matrix.target }}
              path: dist
              if-no-files-found: error

          - name: Upload Log
            if: failure()
            uses: actions/upload-artifact@v4
            with:
              name: Log-Failure-${{ matrix.target }}
              path: logs/*
