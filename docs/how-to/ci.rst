Building your App in CI with GitHub Actions
===========================================

This GitHub `Actions <https://docs.github.com/en/actions>`__ workflow provides
the basic framework necessary to test, build, and package a Briefcase project
in CI for Windows, Linux, macOS, iOS, and Android.

The same set of steps are used for each platform via a `matrix strategy
<https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/running-variations-of-jobs-in-a-workflow>`__.
This will create a separate job for each target platform with specific
configuration.

The workflow steps:

* Check out the current GitHub repository

  * This will be the version of your repository that triggered the CI run
  * So, for a pull request (PR), this is the code being submitted in the PR
  * After the PR is merged, this it is the code in your default branch

* Install Python 3.12
* Install the latest version of Briefcase
* Build the test version of the app
* Run the test suite
* Package the release version of the app for the platform
* Upload the distributable artifact created for the platform
* If an error occurs, the Briefcase log file is uploaded

This workflow should be saved in to a file at ``.github/workflows/ci.yml`` in
your GitHub repository. Once it exists on your default branch on GitHub, a run
will be triggered in the Actions tab.

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
                briefcase-run-prefix: "sudo apt -y install socat && xvfb-run"
                briefcase-args: "--target ubuntu:24.04"

              - target: "Fedora-40"
                platform: "Linux"
                output-format: "system"
                runs-on: "ubuntu-latest"
                briefcase-run-prefix: "sudo apt -y install socat && xvfb-run"
                briefcase-args: "--target fedora:40"

              - target: "iOS"
                output-format: "Xcode"
                runs-on: "macos-latest"
                briefcase-run-args: "--device 'iPhone SE (3rd generation)'"

              - target: "Android"
                output-format: "Gradle"
                runs-on: "ubuntu-latest"
                # Enable KVM permissions for the emulator and use GitHub's preinstalled JDK
                briefcase-run-prefix: >-
                  echo 'KERNEL=="kvm", GROUP="kvm", MODE="0666", OPTIONS+="static_node=kvm"' | sudo tee /etc/udev/rules.d/99-kvm4all.rules
                  && sudo udevadm control --reload-rules
                  && sudo udevadm trigger --name-match=kvm
                  && JAVA_HOME="${JAVA_HOME_17_X64}"
                briefcase-run-args: >-
                  --device '{"avd":"beePhone"}'
                  --Xemulator=-no-window
                  --Xemulator=-no-snapshot
                  --Xemulator=-no-audio
                  --Xemulator=-no-boot-anim
                  --shutdown-on-exit

        steps:
          - name: Checkout
            uses: actions/checkout@v4

          - name: Set up Python
            uses: actions/setup-python@v4
            with:
              python-version: "3.12"

          - name: Install Briefcase
            run: |
              python -m pip install -U pip setuptools wheel
              python -m pip install briefcase

          - name: Build App
            run: |
              briefcase build \
                ${{ matrix.platform || matrix.target }} \
                ${{ matrix.output-format }} \
                --test --no-input \
                ${{ matrix.briefcase-args }}

          - name: Test App
            run: |
              ${{ matrix.briefcase-run-prefix }} \
              briefcase run \
                ${{ matrix.platform || matrix.target }} \
                ${{ matrix.output-format }} \
                --test --no-input \
                ${{ matrix.briefcase-run-args }} \
                ${{ matrix.briefcase-args }}

          - name: Package App
            run: |
              briefcase package \
                ${{ matrix.platform || matrix.target }} \
                ${{ matrix.output-format }} \
                --update --adhoc-sign --no-input \
                ${{ matrix.briefcase-args }}

          - name: Upload App
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
              name: log-${{ matrix.target }}
              path: logs/*
