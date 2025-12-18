# Writing, running, and testing code

{% extends "contribute/how/write_code.md" %}

{% block front_matter %}

To begin working on code, ensure you have a [development environment](dev_environment.md) set up, and you are [working on a branch](branches.md)

{% endblock %}

{% block testing_additional %}

### Templates used by Briefcase at runtime
Briefcase uses templates at runtime to generate the files and project structure for applications. When a contributor runs commands such as `briefcase new`, `briefcase create`, or `briefcase build`, Briefcase selects and renders one or more templates to produce platform-specific project scaffolding.

These templates are maintained separately from Briefcase’s core code, which allows template development and testing to evolve independently of Briefcase releases.

Broadly, Briefcase works with two categories of templates:

* **Wizard templates**
  These templates are used during `briefcase new` to generate the initial project layout, including files such as `pyproject.toml`, application metadata, and basic source structure.

* **Platform-specific templates**
  These templates are used during `briefcase create` and later stages to generate platform-dependent project files (for example, macOS, Windows, Linux, Android, or iOS). Each platform has its own template repository that defines how the application is structured and built on that platform.

When contributing changes to templates, it is often necessary to test those changes locally before they are merged. The following sections describe how to configure Briefcase to use modified template repositories and branches for testing purposes.

### Testing wizard template changes

Wizard templates are used when creating a new project with `briefcase new`. If you are making changes to a wizard template, it is usually necessary to test those changes locally before submitting them for review.

Briefcase allows contributors to specify a custom wizard template repository and branch when creating a new project. This makes it possible to test template changes without modifying Briefcase’s core code.

To test a modified wizard template:

1. Fork and clone the wizard template repository you are working on.
2. Make your changes in a local branch.
3. Run `briefcase new`, specifying the custom template repository and branch:

```bash
briefcase new --template <template-repository-url> --template-branch <branch-name>

{% endblock %}

{% block end_matter %}

Once you have everything working, you can [submit a pull request](submit_pr.md) with your changes.

{% endblock %}
