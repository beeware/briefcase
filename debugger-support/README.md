# Briefcase Debugger Support
[![Python Versions](https://img.shields.io/pypi/pyversions/briefcase-debugger.svg)](https://pypi.python.org/pypi/briefcase-debugger)
[![PyPI Version](https://img.shields.io/pypi/v/briefcase-debugger.svg)](https://pypi.python.org/pypi/briefcase-debugger)
[![Maturity](https://img.shields.io/pypi/status/briefcase-debugger.svg)](https://pypi.python.org/pypi/briefcase-debugger)
[![BSD License](https://img.shields.io/pypi/l/briefcase-debugger.svg)](https://github.com/beeware/briefcase/blob/main/debugger-support/LICENSE)
[![Build Status](https://github.com/beeware/briefcase/workflows/CI/badge.svg?branch=main)](https://github.com/beeware/briefcase/actions)
[![Discord server](https://img.shields.io/discord/836455665257021440?label=Discord%20Chat&logo=discord&style=plastic)](https://beeware.org/bee/chat/)

This package contains the debugger support package for the `pdb` and `debugpy` debuggers.

It starts the remote debugger automatically at startup through an .pth file, if a `BRIEFCASE_DEBUGGER` environment variable is set.

## Installation
As an end-user, you won't normally need to install this package. It will be installed automatically by Briefcase if you specify the `--debug=pdb` or `--debug=debugpy` option when running your application.

## Financial support

The BeeWare project would not be possible without the generous support
of our financial members:

[![Anaconda logo](https://beeware.org/community/members/anaconda/anaconda-large.png)](https://anaconda.com/)

Anaconda Inc. - Advancing AI through open source.

Plus individual contributions from [users like
you](https://beeware.org/community/members/). If you find Briefcase, or
other BeeWare tools useful, please consider becoming a financial member.

## Documentation

Documentation for Briefcase can be found on [Read The
Docs](https://briefcase.readthedocs.io).

## Community

Briefcase is part of the [BeeWare suite](https://beeware.org). You can
talk to the community through:

- [@beeware@fosstodon.org on Mastodon](https://fosstodon.org/@beeware)
- [Discord](https://beeware.org/bee/chat/)
- The Briefcase [GitHub Discussions
  forum](https://github.com/beeware/briefcase/discussions)

We foster a welcoming and respectful community as described in our
[BeeWare Community Code of
Conduct](https://beeware.org/community/behavior/).

## Contributing

If you experience problems with Briefcase, [log them on
GitHub](https://github.com/beeware/briefcase/issues).

If you'd like to contribute to Briefcase development, our [contribution
guide](https://briefcase.readthedocs.io/en/latest/how-to/contribute/index.html)
details how to set up a development environment, and other requirements
we have as part of our contribution process.
