# Building your App in CI with GitHub Actions

This GitHub [Actions](https://docs.github.com/en/actions) workflow provides the basic framework necessary to test, build, and package a Briefcase project in CI for Windows, Linux, macOS, iOS, and Android.

## Target Platforms

The same set of steps are used for each platform via a [matrix strategy](https://docs.github.com/en/actions/writing-workflows/choosing-what-your-workflow-does/running-variations-of-jobs-in-a-workflow). This will create a separate job for each target platform with specific configuration.

These platforms should be updated to match your targets. To remove a platform, delete the entry from `strategy.matrix.target` as well as the corresponding block of configuration under `strategy.matrix.include`.

To add a new targeted platform, add the name of the target to `strategy.matrix.target`. For instance, to target Linux Flatpak, add an entry to `strategy.matrix.target` named `Flatpak` and a configuration to build a Flatpak under `strategy.matrix.include`, for example:

```YAML
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
```

### Target Platform Configuration

These configuration properties can be used to alter behavior of the run for each targeted platform configured in the matrix.

- `target`: Name of the target from `strategy.matrix.target`
- `platform`: Name of the platform to use in `briefcase` commands; if blank, then `target` is used instead
- `output-format`: Name of the platform output format for `briefcase` commands
- `runs-on`: A valid GitHub runner image name for `jobs.<job id>.runs-on`
- `pre-command`: Arbitrary Bash commands to run before the Briefcase commands
- `briefcase-args`: Briefcase arguments to use with all `briefcase` commands
- `briefcase-build-prefix`: Bash commands to prefix to the `briefcase build` command
- `briefcase-build-args`: Briefcase arguments to use with the `briefcase build` command
- `briefcase-run-prefix`: Bash commands to prefix to the `briefcase run` command
- `briefcase-run-args`: Briefcase arguments to use with the `briefcase run` command
- `briefcase-package-prefix`: Bash commands to prefix to the `briefcase package` command
- `briefcase-package-args`: Briefcase arguments to use with the `briefcase package` command

## Workflow File Location

This workflow should be saved in to a file at `.github/workflows/ci.yml` in your GitHub repository. Once it exists on your default branch on GitHub, a run will be triggered in the Actions tab.

## Workflow Steps

- Check out the current GitHub repository
  - This will be the version of your repository that triggered the CI run
  - So, for a pull request (PR), this is the code being submitted in the PR
  - After the PR is merged, this is the code in your default branch
- Install Python 3.12
  - This version of Python should be updated to match the version of Python your app is targeting
- Install the latest version of Briefcase
- Build the test version of the app
- Run the app's test suite
- Package the release version of the app for the platform
- Upload the distributable artefact created for the platform
  - See limitations below for these artefacts
- If an error occurs, the Briefcase log file is uploaded

## Limitations of Uploaded Artefacts

The artefacts produced and uploaded by this workflow will not be signed; therefore, when the app is executed locally, some platforms may show a disconcerting warning about the security of the app or prevent the app from running altogether. See more information about code signing in the [identity guides][obtaining-a-code-signing-identity].

## Workflow File Contents

```YAML
-8<- "how-to/building/workflow.yaml"
```
