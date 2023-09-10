=======
Android
=======

The Google Play Store is the most widely-used Android app store. This guide
focuses on how to distribute a BeeWare app on the Google Play Store.

.. admonition: App Stores are a moving target

    The Google Play Store makes frequent changes to the workflows and nomenclature
    associated with publishing apps. As a result, it's very difficult to keep a guide
    like this one up to date. If you spot any problems, `let us know
    <https://github.com/beeware/briefcase/issues/new?assignees=&labels=bug,documentation,android&projects=&template=bug_report.yml>`__.

Build the app in release mode
-----------------------------

Use Briefcase to build a release bundle for your application:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      (venv) $ briefcase package android
      [hello-world] Building Android App Bundle and APK in release mode...
      ...
      [hello-world] Packaged dist/Hello World-1.0.0.aab

  .. group-tab:: Linux

    .. code-block:: console

      (venv) $ briefcase package android
      [hello-world] Building Android App Bundle and APK in release mode...
      ...
      [hello-world] Packaged dist/Hello World-1.0.0.aab

  .. group-tab:: Windows

    .. code-block:: doscon

      (venv) C:\...>briefcase package android
      [hello-world] Building Android App Bundle and APK in release mode...
      ...
      [hello-world] Packaged dist\Hello World-1.0.0.aab

This will result in an Android App Bundle file being generated. An `Android App
Bundle <https://developer.android.com/guide/app-bundle>`__ is a publishing
format that includes all your app’s compiled code and resources.

.. admonition:: AAB and APK

    APK (Android Package) files can be directly installed on a device. AAB
    is a newer format that simplifies the process of uploading your app to the
    Play Store, allows Google to manage the signing process, and allows the APK
    that is installed on your end-user's device to be smaller.

Sign the Android App Bundle
---------------------------

.. note::

  Before you sign the APK files, you need to :doc:`create a code signing
  identity. <../code-signing/android>`

The Google Play Store requires that the Android App Bundle is signed
before it is uploaded, using the Java jarsigner tool.

In this example below, we assume your code signing identity is stored
in **upload-key-helloworld.jks** under ``.android`` within your home
folder. We also assume that the app's formal name is Hello World. You
will need to change the path to the AAB file based on your app's formal
name.

.. tabs::

  .. group-tab:: macOS

    .. code-block:: console

      $ ~/Library/Caches/org.beeware.briefcase/tools/java/Contents/Home/bin/jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore ~/.android/upload-key-helloworld.jks "dist/Hello World-1.0.0.aab" upload-key -storepass android
         adding: META-INF/MANIFEST.MF
         adding: META-INF/UPLOAD-K.SF
         adding: META-INF/UPLOAD-K.RSA
        signing: BundleConfig.pb
        signing: BUNDLE-METADATA/com.android.tools.build.libraries/dependencies.pb
        signing: base/assets/python/app/README
      ...
        signing: base/manifest/AndroidManifest.xml
        signing: base/assets.pb
        signing: base/native.pb
        signing: base/resources.pb
      >>> Signer
        X.509, CN=Upload Key
        [trusted certificate]

      jar signed.

      Warning:
      The signer's certificate is self-signed.

  .. group-tab:: Linux

    .. code-block:: console

      $ ~/.cache/briefcase/tools/java/bin/jarsigner -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore ~/.android/upload-key-helloworld.jks "dist/Hello World-1.0.0.aab" upload-key -storepass android
         adding: META-INF/MANIFEST.MF
         adding: META-INF/UPLOAD-K.SF
         adding: META-INF/UPLOAD-K.RSA
        signing: BundleConfig.pb
        signing: BUNDLE-METADATA/com.android.tools.build.libraries/dependencies.pb
        signing: base/assets/python/app/README
      ...
        signing: base/manifest/AndroidManifest.xml
        signing: base/assets.pb
        signing: base/native.pb
        signing: base/resources.pb
      >>> Signer
        X.509, CN=Upload Key
        [trusted certificate]

      jar signed.

      Warning:
      The signer's certificate is self-signed.

  .. group-tab:: Windows (cmd)

    .. code-block:: doscon

      C:\...>%LOCALAPPDATA%\BeeWare\briefcase\Cache\tools\java\bin\jarsigner.exe -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore %HOMEPATH%\.android\upload-key-helloworld.jks "dist\Hello World-1.0.0.aab" upload-key -storepass android
         adding: META-INF/MANIFEST.MF
         adding: META-INF/UPLOAD-K.SF
         adding: META-INF/UPLOAD-K.RSA
        signing: BundleConfig.pb
        signing: BUNDLE-METADATA/com.android.tools.build.libraries/dependencies.pb
        signing: base/assets/python/app/README
      ...
        signing: base/manifest/AndroidManifest.xml
        signing: base/assets.pb
        signing: base/native.pb
        signing: base/resources.pb
      >>> Signer
        X.509, CN=Upload Key
        [trusted certificate]

      jar signed.

      Warning:
      The signer's certificate is self-signed.

  .. group-tab:: Windows (PowerShell)

    .. code-block:: pwsh-session

      PS C:\...> & "$env:LOCALAPPDATA\BeeWare\briefcase\Cache\tools\java\bin\jarsigner.exe" -verbose -sigalg SHA1withRSA -digestalg SHA1 -keystore "$env:HOMEPATH\.android\upload-key-helloworld.jks" "android\gradle\Hello World\app\build\outputs\bundle\release\app-release.aab" upload-key -storepass android
         adding: META-INF/MANIFEST.MF
         adding: META-INF/UPLOAD-K.SF
         adding: META-INF/UPLOAD-K.RSA
        signing: BundleConfig.pb
        signing: BUNDLE-METADATA/com.android.tools.build.libraries/dependencies.pb
        signing: base/assets/python/app/README
      ...
        signing: base/manifest/AndroidManifest.xml
        signing: base/assets.pb
        signing: base/native.pb
        signing: base/resources.pb
      >>> Signer
        X.509, CN=Upload Key
        [trusted certificate]

      jar signed.

      Warning:
      The signer's certificate is self-signed.

You can safely ignore the warning about the signer's certificate being
self-signed. Google will manage the process of signing the app with a verified
certificate when you upload your app for distribution.

Add the app to the Google Play store
------------------------------------

To publish to the Google Play store, you will need a Google Play Developer account,
which costs 25 USD. You will then need to provide information for your app's store
listing including an icon and screenshots, upload the app to Google, and finally roll
the app out to production.

Register for a Google Play Developer account
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Registering for a Google Play Developer account requires a Google Account. You
will need to pay registration fee and accept an agreement in the process.

To check if you already have a Google Play Developer account, you can visit the
`Google Play console. <https://play.google.com/console/about/>`__ If you see a
button to **Publish an Android App on Google Play** or a button to **Create
Application**, you can skip this step.

To create your Google Play developer account, pay the fee, and review the
agreements, `follow Google's documentation.
<https://support.google.com/googleplay/android-developer/answer/6112435?hl=en>`__


Create a listing
~~~~~~~~~~~~~~~~

Visit the `Google Play console. <https://play.google.com/console/about/>`__ and
log in. You will see a button labeled **Create App**; click this button.

Fill out the details for your app. We suggest using your app's formal name (as defined
in ``pyproject.toml`` as the App name; the other details relate to the listing and legal
compliance. At the bottom of of the page, press **Create App**.

This will take you to **Store Listing** section of your app. You will need
to provide a short app description (up to 80 characters) and a full
description (up to 4000 characters). Your app metadata may be helpful here.

You will also need to provide a collection of assets that will be used to
promote your application:

  * **A 512x512px icon.** This will be the icon that appears in the Play Store.
    It should match the icon you set on the application itself.

  * **At least 2 screen screenshots of the app.** Google recommends using a
    screenshot `without framing.
    <https://developer.android.com/distribute/marketing-tools/device-art-generator>`__
    One way to capture such a screenshot is with the Android emulator's
    screenshot functionality (the camera icon on the simulator controls). This
    allows your screenshot to contain just what appears on the screen rather
    than a picture of the virtual device. This will store a file in your
    Desktop folder.

    Screenshots must be at least 320px on their smallest dimension, no larger
    than 3480px on their largest dimension, and can't have an aspect ratio more
    extreme than 2:1. A screenshot from the Android emulator typically fulfills
    these requirements.

  * **A 1024x500px feature graphic.** A feature graphic visually represents the
    purpose of the app or your logo and can optionally include a screenshot of
    the app in use, typically including device framing.

Google Play supports optional graphic assets including promo videos, TV banners,
and 360 degree stereoscopic images. See also `Google's advice on graphic assets.
<https://support.google.com/googleplay/android-developer/answer/9866151>`__

Once you've completed the store listing, you'll need to fill out a range of other
details about your app, including the category where it should appear in the Play Store,
pricing details, details about the app's content and its suitability for children, and
contact details for you as a developer. The navigation pane (typically on the left side
of the screen) contains grayed out check marks covering all the sections with required
details. Visit each of these sections in turn; when you have met the requirements of
each section, the check mark will turn green. Once all the checkmarks are green, you're
ready to release your app.

Create a release
~~~~~~~~~~~~~~~~

In the left navigation bar, select **Production** (in the "Release" grouping), Then
select **Create Release.** If prompted to enable App Signing by Google Play, click
**Continue**.

.. admonition:: Non-production releases

    The Play Store also supports releasing your app for internal, alpha and
    beta testing. Google's documentation `contains more details about creating
    test releases
    <https://support.google.com/googleplay/android-developer/answer/9845334>`__.

In an earlier section of this tutorial, we used ``briefcase publish`` and ``jarsigner``
to create a signed Android App Bundle file. It is stored in the ``dist`` folder of your
project. Upload this file to the Google Play console in the **App Bundles** section,
fill out the **Release notes** section of the app, and click **Next**.

Google will then check that you've filled out all the necessary compliance details for
your app; if there are any missing, you'll be prompted to complete those details.

Once you've completed those details, select **Publishing Overvie** from the navigation
sidebar. You should see "Changes ready to send for review", and a button marked **Send
for review**. Click this button.

The Google Play Store will now review your app. You will be emailed if any updates are
required; otherwise, after a day or two, your app will be rolled out to the Play Store.

Publish an update
-----------------

At some point, you'll want to publish an updated version of your application. Generate a
fresh AAB file, signed with the *same* certificate as your original release. Then log
into the Play Store console, and select your application. Select **Release Management**
in the navigation bar, then **App Releases**.

At this point, the release process is the same as it was for your initial release;
create a release, upload your AAB file, and submit the application for roll out.
