# Writing, running, and testing code

{% extends "contribute/how/write-code.md" %}

{% block front_matter %}

To begin working on code, ensure you have a [development environment](dev-environment.md) set up, and you are [working on a branch](branches.md)

{% endblock %}

{% block testing_additional %}

### Changing Briefcase templates

Briefcase uses templates at runtime to generate the files and project structure for applications. When a contributor runs commands such as `briefcase new` or `briefcase create`, Briefcase selects and renders one or more templates to produce platform-specific project scaffolding.

These templates are maintained separately from Briefcase's core code, which allows template development and testing to evolve independently of Briefcase releases.

Broadly, Briefcase works with two categories of templates:

* **Wizard templates**
  These templates are used during `briefcase new` to generate the initial project layout, including files such as `pyproject.toml`, application metadata, and basic source structure.

* **Platform-specific templates**
  These templates are used during `briefcase create` and later stages to generate platform-dependent project files (for example, to produce a macOS app or iOS XCode project). Each platform has its own template repository that defines how the application is structured and built on that platform.

When contributing changes to templates, you need to be able to test those changes locally. Briefcase has features to make this testing possible.

#### Testing wizard template changes

Wizard templates are used when creating a new project with `briefcase new`. Briefcase allows a user to specify a custom wizard template repository and branch when creating a new project. This makes it possible to test template changes without modifying Briefcase's core code.

To test a modified wizard template:

1. Fork and clone the wizard template repository you are working on.
2. Make your changes in a local branch.
3. Run `briefcase new`, specifying the custom template repository and branch:

    ```bash
    briefcase new --template ../../../path/to/template-repo-checkout
    ```

    Alternatively, you can push your changes to GitHub, and then point Briefcase at the GitHub repository and branch for your template fork:

     ```bash
     briefcase new --template <template-repository-url> --template-branch <branch-name>
     ```

#### Testing platform template changes

Platform-specific templates are used when deploying a project to a specific platform. This will usually happen when you invoke `briefcase create`, but it can also happen as a result of calling `briefcase build`, `briefcase run`, or `briefcase package` if `briefcase create` hasn't been invoked. These templates define how an application is structured, configured, and built for a specific platform.

Briefcase supports using a local copy of a template using the [`template`][] and [`template_branch`][] options. To test a modified platform template:

1. Fork and clone the platform template repository you are working on.
2. Make your changes in a local branch.
3. Open the project’s `pyproject.toml` file.
4. In the platform-specific configuration section, set the template to use when creating the app. During initial development, it will be easiest to point at a local checkout of the template:

    ```toml
    [tool.briefcase.<platform>]
    template = "../../../path/to/briefcase-<platform>-app-template"
    ```

    However, you can can also push your changes to your GitHub repository, and configure your Briefcase project to point at that repository and branch:

    ```toml
    [tool.briefcase.<platform>]
    template = "https://github.com/your-username/briefcase-<platform>-app-template"
    template_branch = "my-template-changes"
    ```

#### Template changes that require Briefcase changes

In some cases, changes to a template may depend on corresponding changes in Briefcase itself. For example, if you add a new context variable, or modify the behavior of Briefcase to change how a template variable is constructed, you may require both a Briefcase *and* template change.

This situation then causes problems during testing, because Briefcase's tests won't pass with an old template; and tests for the template won't pass with an old version of Briefcase.

To work around this situation, pull requests on Briefcase's template repositories support a syntax for pointing at a specific version of Briefcase. Once you've made changes locally to both Briefcase and the affected template, and you're satisfied that they work, push the changes for both to Briefcase, and open a pull request on each repository.

In the PR description for *Briefcase*, provide details of the template branch that is required for testing. If the template changes are needed for the Briefcase tests to pass, flag this fact in the PR description; this lets reviewers know that the process of merging the PR will be more complicated.

In the PR description for the *template*, include the following two lines (updating as necessary to include your own GitHub username and branch name):
```
briefcase-repo: https://github.com/<github username>/briefcase.git
briefcase-ref: my-template-changes
```
This directs the template tests to use a branch of Briefcase for testing. This should allow the template tests to pass. The person reviewing your PR will review both the Briefcase *and* template changes together. If approved, the template change will be merged, and tests on Briefcase will then be re-run. This provides a final confirmation that the template and Briefcase are compatible.

{% endblock %}

{% block end_matter %}

Once you have everything working, you can [submit a pull request](submit-pr.md) with your changes.

{% endblock %}
