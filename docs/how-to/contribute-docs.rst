Contributing to the documentation
=================================

Here are some tips for working on this documentation. You're welcome to add
more and help us out!

First of all, you should check the `Restructured Text (reST) and Sphinx
CheatSheet <http://thomas-cokelaer.info/tutorials/sphinx/rest_syntax.html>`_ to
learn how to write your .rst file.

Create a .rst file
---------------------

Look at the structure and choose the best category to put your .rst file. Make
sure that it is referenced in the index of the corresponding category, so it
will show on in the documentation. If you have no idea how to do this, study
the other index files for clues.


Build documentation locally
---------------------------

Go to the documentation folder::

    $ cd docs

Install Sphinx with the helpers and extensions we use::

    $ pip install -r requirements_rtd.txt

Create the static files: ::

    $ make html

Check for any errors and,if possible, fix them.
The output of the file should be in the ``_build/html`` folder.
Open the file you changed in the browser.
