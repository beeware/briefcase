# Contributing code to Briefcase  { #contribute }

Is there a feature you'd like to see in Briefcase? Have you found a bug that you'd like to fix? Or are you just looking for a challenge to exercise your Python skills? Here's how to get involved!

## Prerequisites  { #dev-environment-prereqs }

You'll need to install the following prerequisites.

/// tab | macOS

Briefcase requires installing Python 3.10+. You will also need a method for managing virtual environments (such as `venv`).

///

/// tab | Linux

Briefcase requires installing Python 3.10+. You will also need a method for managing virtual environments (such as `venv`).

///

/// tab | Windows

Briefcase requires installing Python 3.10+. You will also need a method for managing virtual environments (such as `venv`).

///

## <nospell>tl;dr</nospell> - Dev Quick-Setup { #dev-environment-tldr }

Set up the dev environment by running:

/// tab | macOS

```console
$ git clone https://github.com/beeware/briefcase.git
$ cd briefcase
$ python3 -m venv .venv
$ . .venv/bin/activate
(.venv) $ python -m pip install -Ue . --group dev
(.venv) $ pre-commit install
```

///

/// tab | Linux

```console
$ git clone https://github.com/beeware/briefcase.git
$ cd briefcase
$ python3 -m venv .venv
$ . .venv/bin/activate
(.venv) $ python -m pip install -Ue . --group dev
(.venv) $ pre-commit install
```

///

/// tab | Windows

```doscon
C:\...>git clone https://github.com/beeware/briefcase.git
C:\...>cd briefcase
C:\...>py -m venv .venv
C:\...>.venv\Scripts\activate
(.venv) C:\...>python -m pip install -Ue . --group dev
(.venv) C:\...>pre-commit install
```

///

Invoke checks and tests by running:

/// tab | macOS

```console
(.venv) $ tox
```

///

/// tab | Linux

```console
(.venv) $ tox
```

///

/// tab | Windows

```doscon
(.venv) C:\...>tox
```

///

## Set up your development environment  { #setup-dev-environment }

The recommended way of setting up your development environment for Briefcase is to use a [virtual environment](https://docs.python.org/3/library/venv.html), and then install the development version of Briefcase and its dependencies.

First, ensure that you have Python 3 and pip installed. To do this, run:

/// tab | macOS

```console
$ python --version
$ python -m pip --version
```

///

/// tab | Linux

```console
$ python --version
$ python -m pip --version
```

///

/// tab | Windows

```doscon
C:\...>python --version
C:\...>python -m pip --version
```

///

### Clone the Briefcase repository

Next, go to the [Briefcase page on GitHub](https://github.com/beeware/briefcase), and, if you haven't already, [fork the repository](https://github.com/beeware/briefcase/fork) into your own account. Next, click on the "<> Code" button on your fork. If you have the GitHub desktop application installed on your computer, you can select "Open with GitHub Desktop"; otherwise, copy the HTTPS URL provided, and use it to clone the repository to your computer using the command line:

/// tab | macOS

Fork the Briefcase repository, and then:

```console
$ git clone https://github.com/<your username>/briefcase.git
```

(substituting your GitHub username)

///

/// tab | Linux

Fork the Briefcase repository, and then:

```console
$ git clone https://github.com/<your username>/briefcase.git
```

(substituting your GitHub username)

///

/// tab | Windows

Fork the Briefcase repository, and then:

```doscon
C:\...>git clone https://github.com/<your username>/briefcase.git
```

(substituting your GitHub username)

///

### Create a virtual environment

To set up a virtual environment, run:

/// tab | macOS

```console
$ cd briefcase
$ python3 -m venv .venv
$ source .venv/bin/activate
```

///

/// tab | Linux

```console
$ cd briefcase
$ python3 -m venv .venv
$ source .venv/bin/activate
```

///

/// tab | Windows

```doscon
C:\...>cd briefcase
C:\...>python -m venv .venv
C:\...>.venv\Scripts\activate
```

///

Your prompt should now have a `(.venv)` prefix in front of it.

### Install Briefcase

Now that you have the source code, you can do an [editable install](https://setuptools.pypa.io/en/latest/userguide/development_mode.html) of Briefcase into your development environment. Run the following command:

/// tab | macOS

```console
(.venv) $ python -m pip install -Ue . --group dev
```

///

/// tab | Linux

```console
(.venv) $ python -m pip install -Ue . --group dev
```

///

/// tab | Windows

```doscon
(.venv) C:\...>python -m pip install -Ue . --group dev
```

///

### Enable pre-commit

Briefcase uses a tool called [pre-commit](https://pre-commit.com) to identify simple issues and standardize code formatting. It does this by installing a git hook that automatically runs a series of code linters prior to finalizing any git commit. To enable pre-commit, run:

/// tab | macOS

```console
(.venv) $ pre-commit install
pre-commit installed at .git/hooks/pre-commit
```

///

/// tab | Linux

```console
(.venv) $ pre-commit install
pre-commit installed at .git/hooks/pre-commit
```

///

/// tab | Windows

```doscon
(.venv) C:\...>pre-commit install
pre-commit installed at .git/hooks/pre-commit
```

///

Now you are ready to start hacking on Briefcase!

## What should I do?

Depending on your level of expertise, or areas of interest, there are a number of ways you can contribute to Briefcase's code.

### Fix a bug

Briefcase's issue tracker logs the list of [known issues](https://github.com/beeware/briefcase/issues?q=is%3Aopen+is%3Aissue+label%3Abug). Any of these issues are candidates to be worked on. This list can be filtered by platform, so you can focus on issues that affect the platforms you're able to test on. There's also a filter for [good first issues](https://github.com/beeware/briefcase/issues?q=is%3Aopen+is%3Aissue+label%3A%22good+first+issue%22) . These have been identified as problems that have a known cause, and we believe the fix *should* be relatively simple (although we might be wrong in our analysis).

We don't have any formal process of "claiming" or "assigning" issues; if you're interested in a ticket, leave a comment that says you're working on it. If there's an existing comment that says someone is working on the issue, and that comment is recent, then leave a comment asking if they're still working on the issue. If you don't get a response in a day or two, you can assume the issue is available. If the most recent comment is more than a few weeks old, it's probably safe to assume that the issue is still available to be worked on.

If an issue is particularly old (more than 6 months), it's entirely possible that the issue has been resolved, so the first step is to verify that you can reproduce the problem. Use the information provided in the bug report to try and reproduce the problem. If you can't reproduce the problem, report what you have found as a comment on the ticket, and pick another ticket.

If a bug report has no comments from anyone other than the original reporter, the issue needs to be triaged. Triaging a bug involves taking the information provided by the reporter, and trying to reproduce it. Again, if you can't reproduce the problem, report what you have found as a comment on the ticket, and pick another ticket.

If you can reproduce the problem - try to fix it! Work out what combination of code is implementing the feature, and see if you can work out what isn't working correctly.

If you're able to fix the problem, you'll need to [add tests][run-test-suite] to verify that the problem has been fixed (and to prevent the issue from occurring again in future).

Even if you can't fix the problem, reporting anything you discover as a comment on the ticket is worthwhile. If you can find the source of the problem, but not the fix, that knowledge will often be enough for someone who knows more about a platform to solve the problem. Even a good reproduction case (a sample app that does nothing but reproduce the problem) can be a huge help.

### Contribute improvements to documentation

We've got a [separate contribution guide][contribute-docs] for documentation contributions. This covers how to set up your development environment to build Briefcase's documentation, and separate ideas for what to work on.

### Add a new feature

Can you think of a feature that Briefcase should have? Propose a new API or feature, and provide a sample implementation. If you don't have any ideas of your own, the Briefcase issue tracker has some [existing feature suggestions](https://github.com/beeware/briefcase/issues?q=is%3Aopen+is%3Aissue+label%3Aenhancement) that you could try to implement.

Again, you'll need to add unit tests for any new features you add.

### Implement an entirely new platform backend

Briefcase currently has support for 6 platforms, with multiple formats on some backends - but there's room for more! In particular, we'd be interested in seeing a [Snap backend](https://github.com/beeware/briefcase/issues/358) to support Ubuntu's packaging format, or support for Apple's [tvOS](https://github.com/beeware/briefcase/issues/4), [watchOS](https://github.com/beeware/briefcase/issues/5), and [visionOS](https://github.com/beeware/briefcase/issues/2253) platforms.

## Running tests and coverage  { #run-test-suite }

Briefcase uses [`tox`](https://tox.wiki/en/latest/) to manage the testing process and [`pytest`](https://docs.pytest.org/en/latest) for its own test suite.

The default `tox` command includes running:

- pre-commit hooks
- `towncrier` release note check
- documentation linting
- test suite for available Python versions
- code coverage reporting

This is essentially what is run by CI when you submit a pull request.

To run the full test suite, run:

/// tab | macOS

```console
(.venv) $ tox
```

///

/// tab | Linux

```console
(.venv) $ tox
```

///

/// tab | Windows

```doscon
(.venv) C:\...>tox
```

///

The full test suite can take a while to run. You can speed it up considerably by running `tox` in parallel, by running `tox p` (or `tox run-parallel`). When you run the test suite in parallel, you'll get less feedback on the progress of the test suite as it runs, but you'll still get a summary of any problems found at the end of the test run. You should get some output indicating that tests have been run. You may see `SKIPPED` tests, but shouldn't ever get any `FAIL` or `ERROR` test results. We run our full test suite before merging every patch. If that process discovers any problems, we don't merge the patch. If you do find a test error or failure, either there's something odd in your test environment, or you've found an edge case that we haven't seen before - either way, let us know!

As with the full test suite, and the core, this should report [100% test coverage][code-coverage].

## Running test variations

### Run tests for multiple versions of Python

By default, many of the `tox` commands will attempt to run the test suite multiple times, once for each Python version supported by Briefcase. To do this, though, each of the Python versions must be installed on your machine and available to `tox`'s Python [discovery](https://virtualenv.pypa.io/en/latest/user_guide.html#python-discovery) process. In general, if a version of Python is available via `PATH`, then `tox` should be able to find and use it.

### Run only the test suite

If you're rapidly iterating on a new feature, you don't need to run the full test suite; you can run *just* the unit tests. To do this, run:

/// tab | macOS

```console
(.venv) $ tox -e py
```

///

/// tab | Linux

```console
(.venv) $ tox -e py
```

///

/// tab | Windows

```doscon
(.venv) C:\...>tox -e py
```

///

### Run a subset of tests  { #test-subset }

By default, `tox` will run all tests in the unit test suite. When you're developing your new test, it may be helpful to run *just* that one test. To do this, you can pass in [any `pytest` specifier](https://docs.pytest.org/en/latest/how-to/usage.html#specifying-which-tests-to-run) as an argument to `tox`. These test paths are relative to the `briefcase` directory. For example, to run only the tests in a single file, run:

/// tab | macOS

```console
(.venv) $ tox -e py -- tests/path_to_test_file/test_some_test.py
```

///

/// tab | Linux

```console
(.venv) $ tox -e py -- tests/path_to_test_file/test_some_test.py
```

///

/// tab | Windows

```doscon
(.venv) C:\...>tox -e py -- tests/path_to_test_file/test_some_test.py
```

///

You'll still get a coverage report when running a part of the test suite -but the coverage results will only report the lines of code that were executed by the specific tests you ran.

### Run the test suite for a specific Python version  { #test-py-version }

By default `tox -e py` will run using whatever interpreter resolves as `python3` on your machine. If you have multiple Python versions installed, and want to test a specific Python version from the versions you have installed, you can specify a specific Python version to use. For example, to run the test suite on Python 3.10, run:

/// tab | macOS

```console
(.venv) $ tox -e py310
```

///

/// tab | Linux

```console
(.venv) $ tox -e py310
```

///

/// tab | Windows

```doscon
(.venv) C:\...>tox -e py310
```

///

A [subset of tests][test-subset] can be run by adding `--` and a test specification to the command line.

### Run the test suite without coverage (fast)

By default, `tox` will run the `pytest` suite in single threaded mode. You can speed up the execution of the test suite by running the test suite in parallel. This mode does not produce coverage files due to complexities in capturing coverage within spawned processes. To run a single python version in "fast" mode, run:

/// tab | macOS

```console
(.venv) $ tox -e py-fast
```

///

/// tab | Linux

```console
(.venv) $ tox -e py-fast
```

///

/// tab | Windows

```doscon
(.venv) C:\...>tox -e py-fast
```

///

A [subset of tests][test-subset] can be run by adding `--` and a test specification to the command line; a [specific Python version][test-py-version] can be used by adding the version to the test target (e.g., `py310-fast` to run fast on Python 3.10).

## Code coverage

Briefcase maintains 100% branch coverage in its codebase. When you add or modify code in the project, you must add test code to ensure coverage of any changes you make.

However, Briefcase targets multiple platforms, as well as multiple versions of Python, so full coverage cannot be verified on a single platform and Python version. To accommodate this, several conditional coverage rules are defined in the `tool.coverage.coverage_conditional_plugin.rules` section of `pyproject.toml` (e.g., `no-cover-if-is-windows` can be used to flag a block of code that won't be executed when running the test suite on Windows). These rules are used to identify sections of code that are only covered on particular platforms or Python versions.

Of note, coverage reporting across Python versions can be a bit quirky. For instance, if coverage files are produced using one version of Python but coverage reporting is done on another, the report may include false positives for missed branches. Because of this, coverage reporting should always use the oldest version Python used to produce the coverage files.

### Understanding coverage results

At the end of the coverage test output there should be a report of the coverage data that was gathered:

```console
Name    Stmts   Miss Branch BrPart   Cover   Missing
----------------------------------------------------
TOTAL    7540      0   1040      0  100.0%
```

This tells us that the test suite has executed every possible branching path in the `briefcase` code. This isn't a 100% guarantee that there are no bugs, but it does mean that we're exercising every line of code in the codebase.

If you make changes to the codebase, it's possible you'll introduce a gap in this coverage. When this happens, the coverage report will tell you which lines aren't being executed. For example, lets say we made a change to `briefcase/integrations/file.py`, adding some new logic. The coverage report might look something like:

```console
Name                                 Stmts   Miss Branch BrPart  Cover   Missing
--------------------------------------------------------------------------------
src/briefcase/integrations/file.py     111      1     26      0  98.1%   170, 302-307
--------------------------------------------------------------------------------
TOTAL                                 7540      1   1726      0  99.9%
```

This tells us that line 170, and lines 302-307 are not being executed by the test suite. You'll need to add new tests (or modify an existing test) to restore this coverage.

### Coverage report for host platform and Python version

You can generate a coverage report for your platform and version of Python. For example, to run the test suite and generate a coverage report on Python 3.11, run:

/// tab | macOS

```console
(.venv) $ tox -m test311
```

///

/// tab | Linux

```console
(.venv) $ tox -m test311
```

///

/// tab | Windows

```doscon
(.venv) C:\...>tox -m test311
```

///

### Coverage report for host platform

If all supported versions of Python are available to `tox`, then coverage for the host platform can be reported by running:

/// tab | macOS

```console
(.venv) $ tox p -m test-platform
```

///

/// tab | Linux

```console
(.venv) $ tox p -m test-platform
```

///

/// tab | Windows

```doscon
(.venv) C:\...>tox p -m test-platform
```

///

### Coverage reporting in HTML

A HTML coverage report can be generated by appending `-html` to any of the coverage `tox` environment names, for instance:

/// tab | macOS

```console
(.venv) $ tox -e coverage-platform-html
```

///

/// tab | Linux

```console
(.venv) $ tox -e coverage-platform-html
```

///

/// tab | Windows

```doscon
(.venv) C:\...>tox -e coverage-platform-html
```

///

## Submitting a pull request  { #pr-housekeeping }

Before you submit a pull request, there's a few bits of housekeeping to do.

### Submit from a feature branch, not your `main` branch

Before you start working on your change, make sure you've created a branch. By default, when you clone your repository fork, you'll be checked out on your `main` branch. This is a direct copy of Briefcase's `main` branch.

While you *can* submit a pull request from your `main` branch, it's preferable if you *don't* do this. If you submit a pull request that is *almost* right, the core team member who reviews your pull request may be able to make the necessary changes, rather than giving feedback asking for a minor change. However, if you submit your pull request from your `main` branch, reviewers are prevented from making modifications.

Instead, you should make your changes on a *feature branch*. A feature branch has a simple name to identify the change that you've made. For example, if you've found a bug in Briefcase's binary signing on Windows, you might create a feature branch `fix-windows-signing`. If your bug relates to a specific issue that has been reported, it's also common to reference that issue number in the branch name (e.g., `fix-1234`).

To create a `fix-windows-signing` feature branch, run:

/// tab | macOS

```console
(.venv) $ git switch -c fix-windows-signing
```

///

/// tab | Linux

```console
(.venv) $ git switch -c fix-windows-signing
```

///

/// tab | Windows

```doscon
(.venv) C:\...>git switch -c fix-windows-signing
```

///

Commit your changes to this branch, then push to GitHub and create a pull request.

### Working with pre-commit

When you commit any change, pre-commit will run automatically. If there are any issues found with the commit, this will cause your commit to fail. Where possible, pre-commit will make the changes needed to correct the problems it has found:

/// tab | macOS

```console
(.venv) $ git add some/interesting_file.py
(.venv) $ git commit -m "Minor change"
check toml...............................................................Passed
check yaml...............................................................Passed
check for case conflicts.................................................Passed
check docstring is first.................................................Passed
fix end of files.........................................................Passed
trim trailing whitespace.................................................Passed
ruff format..............................................................Failed
- hook id: ruff-format
- files were modified by this hook

1 file reformatted, 488 files left unchanged

ruff check...............................................................Passed
codespell................................................................Passed
```

///

/// tab | Linux

```console
(.venv) $ git add some/interesting_file.py
(.venv) $ git commit -m "Minor change"
check toml...............................................................Passed
check yaml...............................................................Passed
check for case conflicts.................................................Passed
check docstring is first.................................................Passed
fix end of files.........................................................Passed
trim trailing whitespace.................................................Passed
ruff format..............................................................Failed
- hook id: ruff-format
- files were modified by this hook

1 file reformatted, 488 files left unchanged

ruff check...............................................................Passed
codespell................................................................Passed
```

///

/// tab | Windows

```doscon
(.venv) C:\...>git add some/interesting_file.py
(.venv) C:\...>git commit -m "Minor change"
check toml...............................................................Passed
check yaml...............................................................Passed
check for case conflicts.................................................Passed
check docstring is first.................................................Passed
fix end of files.........................................................Passed
trim trailing whitespace.................................................Passed
ruff format..............................................................Failed
- hook id: ruff-format
- files were modified by this hook

1 file reformatted, 488 files left unchanged

ruff check...............................................................Passed
codespell................................................................Passed
```

///

You can then re-add any files that were modified as a result of the pre-commit checks, and re-commit the change.

/// tab | macOS

```console
(.venv) $ git add some/interesting_file.py
(.venv) $ git commit -m "Minor change"
check toml...............................................................Passed
check yaml...............................................................Passed
check for case conflicts.................................................Passed
check docstring is first.................................................Passed
fix end of files.........................................................Passed
trim trailing whitespace.................................................Passed
ruff format..............................................................Passed
ruff check...............................................................Passed
codespell................................................................Passed
[bugfix e3e0f73] Minor change
1 file changed, 4 insertions(+), 2 deletions(-)
```

///

/// tab | Linux

```console
(.venv) $ git add some/interesting_file.py
(.venv) $ git commit -m "Minor change"
check toml...............................................................Passed
check yaml...............................................................Passed
check for case conflicts.................................................Passed
check docstring is first.................................................Passed
fix end of files.........................................................Passed
trim trailing whitespace.................................................Passed
ruff format..............................................................Passed
ruff check...............................................................Passed
codespell................................................................Passed
[bugfix e3e0f73] Minor change
1 file changed, 4 insertions(+), 2 deletions(-)
```

///

/// tab | Windows

```doscon
(.venv) C:\...>git add some\interesting_file.py
(.venv) C:\...>git commit -m "Minor change"
check toml...............................................................Passed
check yaml...............................................................Passed
check for case conflicts.................................................Passed
check docstring is first.................................................Passed
fix end of files.........................................................Passed
trim trailing whitespace.................................................Passed
ruff format..............................................................Passed
ruff check...............................................................Passed
codespell................................................................Passed
```

///

Once everything passes, you're ready for the next steps.

### Add change information for release notes

When you submit this change as a pull request, you need to add a *change note*. Briefcase uses [`towncrier`](https://pypi.org/project/towncrier/) to automate building the release notes for each release. Every pull request must include at least one file in the `changes/` directory that provides a short description of the change implemented by the pull request.

The change note should be in Markdown format, in a file that has name of the format `<id>.<fragment type>.md`. If the change you are proposing will fix a bug or implement a feature for which there is an existing issue number, the ID will be the number of that ticket. If the change has no corresponding issue, the PR number can be used as the ID. You won't know this PR number until you push the pull request, so the first CI pass will fail the `towncrier` check; add the change note and push a PR update and CI should then pass.

There are five allowed fragment types:

- `feature`: The PR adds a new behavior or capability that wasn't previously possible (e.g., adding support for a new packaging format, or a new feature in an existing packaging format);
- `bugfix`: The PR fixes a bug in the existing implementation;
- `doc`: The PR is an significant improvement to documentation;
- `removal`; The PR represents a backwards incompatible change in the Briefcase API; or
- `misc`; A minor or administrative change (e.g., fixing a typo, a minor language clarification, or updating a dependency version) that doesn't need to be announced in the release notes.

This description in the change note should be a high level summary of the change from the perspective of the user, not a deep technical description or implementation detail. It is distinct from a commit message - a commit message describes what has been done so that future developers can follow the reasoning for a change; the change note is a "user facing" description. For example, if you fix a bug related to project naming, the commit message might read:

> Disallow project names that begin with a number.

The corresponding change note would read something like:

> Project names can no longer begin with a number.

Some PRs will introduce multiple features and fix multiple bugs, or introduce multiple backwards incompatible changes. In that case, the PR may have multiple change note files. If you need to associate two fragment types with the same ID, you can append a numerical suffix. For example, if PR 789 added a feature described by ticket 123, closed a bug described by ticket 234, and also made two backwards incompatible changes, you might have 4 change note files:

- `123.feature.md`
- `234.bugfix.md`
- `789.removal.1.md`
- `789.removal.2.md`

For more information about `towncrier` and fragment types see [News Fragments](https://towncrier.readthedocs.io/en/stable/tutorial.html#creating-news-fragments). You can also see existing examples of news fragments in the `changes` directory of the Briefcase repository. If this folder is empty, it's likely because Briefcase has recently published a new release; change note files are deleted and combined to update the [release notes][release-history] with each release. You can look at that file to see the style of comment that is required; you can look at [recently merged PRs](https://github.com/beeware/briefcase/pulls?q=is%3Apr+is%3Amerged) to see how to format your change notes.

### It's not just about coverage!

Although we have full test coverage, the task isn't *just* about maintaining the numerical coverage value. Part of the task is to audit the code as you go. You could write a comprehensive set of tests for a concrete life jacket... but a concrete life jacket would still be useless for the purpose it was intended!

As you develop tests and improve coverage, you should be checking that the core module is internally **consistent** as well. If you notice any method names that aren't internally consistent (e.g., something called `on_select` in one module, but called `on_selected` in another), or where the data isn't being handled consistently, flag it and bring it to our attention by raising a ticket. Or, if you're confident that you know what needs to be done, create a pull request that fixes the problem you've found.

### Waiting for feedback

Once you've written your code, test, and change note, you can submit your changes as a pull request. One of the core team will review your work, and give feedback. If any changes are requested, you can make those changes, and update your pull request; eventually, the pull request will be accepted and merged. Congratulations, you're a contributor to Briefcase!

## What next?

Rinse and repeat! If you've improved coverage by one line, go back and do it again for *another* coverage line! If you've implemented a new feature, implement *another* feature!

Most importantly - have fun!
