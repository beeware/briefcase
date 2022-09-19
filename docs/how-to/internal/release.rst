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

1. Check the contents of the upstream repository's main branch::

    $ git fetch upstream
    $ git checkout --detach upstream/main

   Check that the HEAD of release now matches upstream/main.

2. Ensure that the release notes are up to date. Run::

         $ tox -e towncrier -- --draft

   to review the release notes that will be included, and then::

         $ tox -e towncrier

   to generate the updated release notes.

3. Ensure that there is a version branch for the new Briefcase version
   every template that Briefcase will use at runtime:

   * briefcase-template
   * briefcase-macOS-app-template
   * briefcase-macOS-Xcode-template
   * briefcase-windows-app-template
   * briefcase-windows-VisualStudio-template
   * briefcase-linux-appimage-template
   * briefcase-linux-flatpak-template
   * briefcase-iOS-Xcode-template
   * briefcase-android-gradle-template

4. Tag the release, and push the branch and tag upstream::

    $ git tag v1.2.3
    $ git push upstream main
    $ git push upstream v1.2.3

5. Pushing the tag will start a workflow to create a draft release on GitHub.
   You can `follow the progress of the workflow on GitHub
   <https://github.com/beeware/briefcase/actions?query=workflow%3A%22Create+Release%22>`__;
   once the workflow completes, there should be a new `draft release
   <https://github.com/beeware/briefcase/releases>`__.

6. Log into ReadTheDocs, visit the `Versions tab
   <https://readthedocs.org/projects/briefcase/versions/>`__, and activate the
   new version. Ensure that the build completes; if there's a problem, you
   may need to correct the build configuration, roll back and re-tag the release.

7. Edit the GitHub release. Add release notes (you can use the text generated
   by towncrier). Check the pre-release checkbox (if necessary).

8. Double check everything, then click Publish. This will trigger a
   `publication workflow on GitHub
   <https://github.com/beeware/briefcase/actions?query=workflow%3A%22Upload+Python+Package%22>`__.

9. Wait for the `package to appear on PyPI
<https://pypi.org/project/briefcase/>`__.

Congratulations, you've just published a release!

If anything went wrong during steps 4-6, you will need to delete the draft
release from GitHub, and push an updated tag. Once the release has successfully
appeared on PyPI, it cannot be changed; if you spot a problem in a published
package, you'll need to tag a completely new release.
