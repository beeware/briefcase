.. Notes about this file:
    The writing style may not match other BeeWare docs. I intend to revise it.
    This file is a stub. Feedback very welcome, though.

=======
Android
=======

Overview
--------

The Google Play Store is the most widely-used Android app store. This guide
focuses on how to distribute a BeeWare app there.

Build the app in release mode
-----------------------------

Run this command::

  briefcase publish android

This will result in four APK files being generated. Each file corresponds
to a different type of CPU that may be in an Android device, known as an
Android ABI.

.. TODO list:
    - Adjust cookiecutter to make per-ABI APKs, per https://dev.to/sys1yagi/enable-split-apk-only-when-release-build-1ij
    - Use Windows/Mac/Linux tabs for the above.
    - Test it.


Sign the APK files
------------------

.. admonition:: Create code signing identity

  Before you sign the APK files, you need to :doc:`create a code signing
  identity<../code-signing/android>`.

Since you already have a code signing identity, we run the two Android SDK
commands required to sign the APK files. First, we ensure the APK files are
aligned to 32-bit boundaries, per the Android requirements.

::

  $ zipalign -p 4 -f filename.apk

Next, we sign the actual package files.

::

  $ apksigner sign --ks my-release-key.jks my-app-unsigned-aligned.apk

.. TODO list:
    - Use Windows/Mac/Linux tabs for the above.
    - Make sure we specify a path that finds these programs.
    - Test it.
    - Decide with Russell where we want to store these keys.

Adding the app to the Google Play store
---------------------------------------

Adding the app requires a few steps. You need to have a Google Account and
create a listing for your app. You will need to choose your app's signing
configuration in the store. Finally, you will create a new release of the app,
at which point you will upload the APK files that comprise your app.

Creating a listing
++++++++++++++++++

To distribute your app on the Google Play Store, you need to visit
https://play.google.com/apps/publish/ and create an account.

Once you've done that, click **Create Application**. Choose a language and
write a brief app title, up to 50 characters. This should probably be the
same as your app's Formal Name in the BeeWare ecosystem.

This will take you to **Store Listing** section of your app. You will need to
answer a variety of questions. Take your time to answer them well.

You will need to upload an icon. For briefcase apps, an icon is typically specified in
your app's ``pyproject.toml`` file. Look for a line starting with ``icon = ``.
The Google Play Store will require a variety of other information, including at least
one screenshot of your app and your assessment of likelihood that children will want
to use the app.

Configure app signing
+++++++++++++++++++++

Click **App Signing** in the left navigation. The Google Play Store offers an app signing
feature where they maintain the signing key for your app. For simplicity, you will
click **Opt Out** to opt out of that feature.

.. admonition:: Letting Google manage and protect your app signing key

  The Google Play store's feature to manage app signing keys offers a way to
  protect your app if your signing key is ever lost or compromised. You can read
  more about it in `Google's documentation. <https://support.google.com/googleplay/android-developer/answer/7384423?hl=en>`_
  For simplicity, this documentation relies on you to manage and protect your
  app's signing key.

  You can enable this feature later if you are willing to give Google the private
  key corresponding to this app.

Creating a release and uploading APK files
++++++++++++++++++++++++++++++++++++++++++

To create a release, click **Release management** in the navigation.
Choose **App releases.**  **Production**, click the button labeled
**Manage.** In this section, click **Create Release.**

If prompted to enable Google's hosted app signing, click **Opt Out**. You may have
to click **I'm Sure, Opt Out** for now. If you do prefer to set up Google's hosted
app signing, you may configure that, but it is beyond the scope of this document.

Scroll to **Android App Bundles and APKs to add** and click **Browse Files.** This will
allow you to choose the four APK files under the TODO directory.

Scroll to **What's new in this release?**. If this is your first upload of the app,
write the words, "Initial upload."

Finally, click **Review.**

This will prompt a variety of questions from the Google Play Store about the content
of your app, including the absence/presence of advertising, its appropriateness for
different age groups, and any embedded commercial aspects.

Once you have answered those questions, you can click **Start Rollout To Production.**

The Google Play Store may at this point pause roll-out while they review your app.
They will email updates to you. Once review is complete, you can log in to the
Play Store publishing console and click **Start Rollout To Production** again.
