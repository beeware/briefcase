=======
Android
=======

Overview
--------

The Google Play Store is the most widely-used Android app store. This guide
focuses on how to distribute a BeeWare app there.

Build the app in release mode
-----------------------------

Run this command.

.. tabs::

  .. group-tab:: macOS

    .. code-block:: bash

      $ (venv) briefcase package android

  .. group-tab:: Linux

    .. code-block:: bash

      $ (venv) briefcase package android

  .. group-tab:: Windows

    .. code-block:: bash

      C:\...> (venv) briefcase package android

This will result in an Android App Bundle file being generated. An `Android App Bundle
<https://developer.android.com/guide/app-bundle>`__ is a publishing format that
includes all your app’s compiled code and resources, and defers APK generation and
signing to Google.

Sign the Android App Bundle
---------------------------

.. admonition:: Create code signing identity

  Before you sign the APK files, you need to :doc:`create a code signing
  identity. <../code-signing/android>`

The Google Play Store requires that the Android App Bundle is signed
before it is uploaded. Since you already have a code signing identity,
we run the Java jarsigner tool to sign the AAB file.

In this example below, we assume your code signing identity is stored
in **upload-key-helloworld.jks** under ``.android`` within your home
folder.

.. tabs::

  .. group-tab:: macOS

    .. code-block:: bash

      $ ~/.briefcase/tools/java/Contents/Home/bin/jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore ~/.android/upload-key-helloworld.jks android/*/app/build/outputs/bundle/release/app-release.aab upload-key -storepass android

  .. group-tab:: Linux

    .. code-block:: bash

      $ ~/.briefcase/tools/java/bin/jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore ~/.android/upload-key-helloworld.jks android/*/app/build/outputs/bundle/release/app-release.aab upload-key -storepass android

  .. group-tab:: Windows

    On Windows, you must specify the full path to the AAB file. We assume below
    that the app's formal name is Hello World. You will need to change the path
    to the AAB file based on your app's formal name.

    .. code-block:: doscon

      C:\...> %HOMEPATH%\.briefcase\tools\java\bin\jarsigner.exe -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore %HOMEPATH%\.android\upload-key-helloworld.jks "android\Hello World\app\build\outputs\bundle\release\app-release.aab" upload-key -storepass android

Add the app to the Google Play store
------------------------------------

To publish to the Google Play store, you will need a Google Play
Developer account. Creating a Google Play developer account costs about
$25 USD. You will then need to provide information for your app's store
listing including an icon and screenshots, upload the app to Google, and
finally roll the app out to production.

The Google Play Store allows you to distribute your app for free to users,
to charge for it, and/or to require in-app payments to unlock app features.
The BeeWare tools do not currently provide particular support for using Play
Store in-app payments, but it should be possible with substantial work.

Register for a Google Play Developer account and pay the registration fee
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Registering for a Google Play Developer account requires a Google Account.
You will need to pay registration fee and accept an agreement in the
process.

To check if you already have a Google Play Developer account, you can visit
the `Google Play console. <https://play.google.com/apps/publish/>`__ If you
see a button to **Publish an Android App on Google Play** or a button to
**Create Application**, you can skip this step.

To create your Google Play developer account, pay the fee, and review the
agreements, `follow Google's documentation.
<https://support.google.com/googleplay/android-developer/answer/6112435?hl=en>`__


Create a listing
++++++++++++++++

Visit the `Google Play console. <https://play.google.com/apps/publish/>`__
You will see a button labeled **Publish an Android App on Google Play** or
a button to **Create Application**. Click it.

Once you've done that, click **Create Application**. Choose a language and
write a brief app title, up to 50 characters. We suggest making this the
same as your app's Formal Name in its ``pyproject.toml``.

This will take you to **Store Listing** section of your app. You will need
to provide a short app description (up to 80 characters) and a full
description (up to 4000 characters).

You will need to upload an icon of size 512x512. For briefcase apps, an icon
is typically specified in
your app's ``pyproject.toml`` file. Look for a line starting with ``icon =``.

You will need at least two screenshots of the app. Google recommends
using a screenshot `without framing.
<https://developer.android.com/distribute/marketing-tools/device-art-generator>`__
One way to capture such a screenshot is with the Android emulator's screenshot
functionality, notated by a camera icon. This allows your screenshot to contain
just what appears on the screen rather than a picture of the virtual device.
This will store a file in your Desktop folder.

You will need a feature graphic. A feature graphic visually represents the
purpose of the app or your logo and can optionally include a screenshot of
the app in use, typically including device framing.

Google Play supports optional graphic assets including promo videos, TV banners,
and 360 degree stereoscopic images. See also `Google's advice on graphic assets.
<https://support.google.com/googleplay/android-developer/answer/1078870>`__

The Google Play Store will require a variety of other information, including
an app category and your assessment of the likelihood that children will want
to use the app, an email address where users can contact you. This email
address is publicly displayed.

Create a release and uploading your signed Android App Bundle
+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

To create a release, visit your app in the `Google Play console
<https://play.google.com/apps/publish/>`__. If you have multiple apps, ensure
the correct app is selected, usually in a drop-down at the top of the screen.

Click **App releases** in the navigation (typically on the left). Click **Manage**
within the **Production track.** In this section, click **Create Release.**

If prompted to enable App Signing by Google Play, click **Continue**.

In an earlier section of this tutorial, we used ``briefcase publish`` and
``jarsigner`` to create a signed Android App Bundle file. It is stored at
``android/*/app/build/outputs/bundle/release/app-release.aab`` (where ``*``
refers to your app's formal name). Upload this file to the Google Play
console within **Browse Files** under **Android App Bundles and APKs to add.**

You will need to write release notes for the app in the **What's new in this
release?** section. If this is your first upload of the app, write the words,
"Initial upload."

Click **Review** to see your answers. You can expect to be prompted to answer
a variety of content questions from the Google Play Store about the
absence/presence of advertising, the appropriateness of your app for different
age groups, and any embedded commercial aspects.

Once you have answered those questions, you can click **Start Rollout To Production.**

The Google Play Store may at this point pause roll-out while they review your app.
They will email updates to you. Once review is complete, you can log in to the
Play Store publishing console and click **Start Rollout To Production** again.
