# Briefcase Debugger Support
This package contains the debugger support package for the `pdb` and `debugpy` debuggers.

It starts the remote debugger automatically at startup through an .pth file, if a `BRIEFCASE_DEBUGGER` environment variable is set.

## Installation
Normally you do not need to install this package manually, because it is done automatically by briefcase using the `--debug=pdb` or `--debug=debugpy` option.
