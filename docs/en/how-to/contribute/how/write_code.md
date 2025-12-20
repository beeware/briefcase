# Writing, running, and testing code

{% extends "contribute/how/write_code.md" %}

{% block front_matter %}

To begin working on code, ensure you have a [development environment](dev_environment.md) set up, and you are [working on a branch](branches.md)

{% endblock %}

{% block testing_additional %}

### Templates used by Briefcase at runtime
Briefcase uses templates at runtime to generate the files and project structure for applications. When a contributor runs commands such as `briefcase new`, `briefcase create`, or `briefcase build`, Briefcase selects and renders one or more templates to produce platform-specific project scaffolding.

These templates are maintained separately from Briefcase's core code, which allows template development and testing to evolve independently of Briefcase releases.

Broadly, Briefcase works with two categories of templates:

* **Wizard templates**
  These templates are used during `briefcase new` to generate the initial project layout, including files such as `pyproject.toml`, application metadata, and basic source structure.

* **Platform-specific templates**
  These templates are used during `briefcase create` and later stages to generate platform-dependent project files (for example, macOS, Windows, Linux, Android, or iOS). Each platform has its own template repository that defines how the application is structured and built on that platform.

When contributing changes to templates, it is often necessary to test those changes locally before they are merged. The following sections describe how to configure Briefcase to use modified template repositories and branches for testing purposes.

### Testing wizard template changes

Wizard templates are used when creating a new project with `briefcase new`. If you are making changes to a wizard template, it is usually necessary to test those changes locally before submitting them for review.

Briefcase allows contributors to specify a custom wizard template repository and branch when creating a new project. This makes it possible to test template changes without modifying Briefcase's core code.

To test a modified wizard template:

1. Fork and clone the wizard template repository you are working on.
2. Make your changes in a local branch.
3. Run `briefcase new`, specifying the custom template repository and branch:

```bash
briefcase new \
  --template <template-repository-url> \
  --template-branch <branch-name>
```

### Testing platform template changes

Platform-specific templates are used after a project has been created, during commands such as `briefcase create`, `briefcase build`, `briefcase run`, and `briefcase package`. These templates define how an application is structured, configured, and built for a specific platform (such as macOS, Windows, Linux, Android, or iOS).

When modifying a platform template, contributors typically need to test those changes against a local project without modifying Briefcase's core code.

Briefcase supports this by allowing projects to explicitly specify which platform template repository and branch should be used.

The `template` configuration option specifies the Git repository containing the platform template.
The `template_branch` configuration option specifies the branch of that repository that Briefcase should use when rendering the template.

To test a modified platform template:

1. Fork and clone the platform template repository you are working on.
2. Make your changes in a local branch.
3. Open the project’s `pyproject.toml` file.
4. In the platform-specific configuration section, set the template repository and branch. For example:

```toml
[tool.briefcase.<platform>]
template = "https://github.com/your-username/briefcase-<platform>-app-template"
template_branch = "my-template-changes"
```

### When template changes also require Briefcase changes

In some cases, changes to a template may depend on corresponding changes in Briefcase's core code. This can occur when a template requires new context variables, additional configuration options, or updated behavior that is not yet supported by the current version of Briefcase.

For testing purposes, Briefcase provides mechanisms to point a project at a modified version of the Briefcase codebase (for example, by specifying an alternate Briefcase repository and reference). This allows contributors to validate template changes that depend on unreleased Briefcase functionality before those changes are merged.

When this happens, template changes cannot be tested in isolation. Instead, both the template and the Briefcase code need to be tested together to ensure they work correctly.

A common approach in these situations is to:

1. Create a branch containing the required changes in the Briefcase repository.
2. Create a corresponding branch in the template repository that depends on those changes.
3. Configure the test project to use both the modified Briefcase code and the modified template when testing.

When submitting pull requests, it is important to clearly link the related Briefcase and template changes so reviewers understand the dependency between them. This helps ensure that the changes are reviewed and merged in the correct order.

Once the necessary support is available in Briefcase itself, the template changes can be tested independently using the standard template configuration options described above.

{% endblock %}

{% block end_matter %}

Once you have everything working, you can [submit a pull request](submit_pr.md) with your changes.

{% endblock %}
