==============================
How to cut a Briefcase release
==============================

The release infrastructure for Briefcase is semi-automated, using Github
Actions to formally publish releases.

This guide assumes that you have an ``upstream`` remote configured on your
local clone of the Briefcase repository, pointing at the official repository.
It also assumes that you have a local ``release`` branch that tracks
``upstream/master``.

You should have a checkout of a personal fork of the Briefcase repository; to
configure this fork for a release, run::

    $ git remote add upstream git@github.com:beeware/briefcase.git
    $ git clone upstream/master release

The procedure for cutting a new release is as follows:

1. Refresh your release branch::

    $ git checkout release
    $ git fetch upstream
    $ git pull

   Check that the HEAD of release now matches upstream/master.

2. Tag the release, and push the tag upstream::

    $ git tag v1.2.3
    $ git push upstream --tags

3. Pushing the tag will start a workflow to create a draft release on Github.
   You can `follow the progress of the workflow on Github
   <https://github.com/beeware/briefcase/actions?query=workflow%3A%22Create+Release%22>`__;
   once the workflow completes, there should be a new `draft release
   <https://github.com/beeware/briefcase/releases>`__.

4. Edit the Github release. Add release notes, and check the pre-release
   checkbox (if necessary).

5. Double check everything, then click Publish. This will trigger a
   `publication workflow on Github
   <https://github.com/beeware/briefcase/actions?query=workflow%3A%22Upload+Python+Package%22>`__.

6. Wait for the `package to appear on PyPI
<https://pypi.org/project/briefcase/>`__.

Congratulations, you've just published a release!

If anything went wrong during steps 3 or 5, you will need to delete the draft
release from Github, and push an updated tag. Once the release has successfully
appeared on PyPI, it cannot be changed; if you spot a problem in a published
package, you'll need to tag a completely new release.
