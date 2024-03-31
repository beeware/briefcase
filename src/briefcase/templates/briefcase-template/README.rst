Briefcase Bootstrap template
============================

A template for starting a Python app that will be deployed using Briefcase.

Using this template
-------------------

In normal usage, you won't need to reference this template at all - it is used
automatically by Briefcase when you run ``briefcase new``.

If you are developing a modification to this template and want to test it, you
can tell Briefcase to use your own template by passing in the ``-t`` option::

    $ briefcase new -t <path to checkout>

Alternatively, if you want to test this template *without* using Briefcase,
you can use `cookiecutter`_ directly.

1. Install `cookiecutter`_::

    $ pip install cookiecutter

2. Run ``cookiecutter`` on this template::

    $ cookiecutter https://github.com/beeware/briefcase-template

3. Add your code to the project.

.. _cookiecutter: http://github.com/cookiecutter/cookiecutter
.. _briefcase: http://github.com/beeware/briefcase
