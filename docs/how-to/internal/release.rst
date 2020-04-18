==============================
How to cut a Briefcase release
==============================

The release infrastructure for Briefcase is semi-automated, using GitHub
Actions to formally publish releases.

This guide assumes that you have an ``upstream`` remote configured on your
local clone of the Briefcase repository, pointing at the official repository.
If all you have is a checkout of a personal fork of the Briefcase repository,
you can configure that checkout by running::

    $ git remote add upstream https://github.com/beeware/briefcase.git

The procedure for cutting a new release is as follows:

1. Check the contents of the upstream repository's master branch::

    $ git fetch upstream
    $ git checkout --detach upstream/master

   Check that the HEAD of release now matches upstream/master.

2. Make sure the branch is ready for release. Ensure that:

   1. The version number has been bumped.

   2. The release notes are up to date. If they are, the `changes
      <https://github.com/beeware/briefcase/tree/master/changes>`__ directory
      should be empty, except for the ``template.rst`` file.

   These two changes (the version bump and release notes update) should go
   through the normal pull request and review process. They should generally
   comprise the last PR merged before the release occurs.

   If the version number *hasn't* been updated, or ``changes`` directory
   *isn't* empty, you need to create a PR (using the normal development
   process) that contains these changes. Run::

         $ tox -e towncrier -- --draft

   to review the release notes that will be included, and then::

         $ tox -e towncrier

   to generate the updated release notes. Submit the PR; once it's been
   reviewed and merged, you can restart the release process from step 1.

3. Tag the release, and push the tag upstream::

    $ git tag v1.2.3
    $ git push upstream v1.2.3

4. Pushing the tag will start a workflow to create a draft release on GitHub.
   You can `follow the progress of the workflow on GitHub
   <https://github.com/beeware/briefcase/actions?query=workflow%3A%22Create+Release%22>`__;
   once the workflow completes, there should be a new `draft release
   <https://github.com/beeware/briefcase/releases>`__.

5. Edit the GitHub release. Add release notes (you can use the text generated
   by towncrier). Check the pre-release checkbox (if necessary).

6. Double check everything, then click Publish. This will trigger a
   `publication workflow on GitHub
   <https://github.com/beeware/briefcase/actions?query=workflow%3A%22Upload+Python+Package%22>`__.

7. Wait for the `package to appear on PyPI
<https://pypi.org/project/briefcase/>`__.

Congratulations, you've just published a release!

If anything went wrong during steps 3 or 5, you will need to delete the draft
release from GitHub, and push an updated tag. Once the release has successfully
appeared on PyPI, it cannot be changed; if you spot a problem in a published
package, you'll need to tag a completely new release.
