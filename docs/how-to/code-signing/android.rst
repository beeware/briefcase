=======
Android
=======

Overview
--------

Android `requires that all apps be digitally signed with a certificate before
they are installed on a device or updated
<https://developer.android.com/studio/publish/app-signing>`__. Android phones
enforce a policy that updates to an app must come from the same signing key to
validate. This allows the phone to be sure an update is fundamentally the same
app, i.e., has the same author.

This documentation covers one way to sign your app where the Google Play Store
maintains the authoritative key for your app. This approach is called `App
Signing by Google Play
<https://support.google.com/googleplay/android-developer/answer/7384423>`__.

You will need to generate a key on your development workstation to sign an app
package before sending it to the Google Play store. If you use app signing by
Google Play, the key on your workstation is called the upload key.

Generate a key
--------------

You will need to decide where to store the upload key. A good default is to use
one keystore file per app you are creating and to store it in the ``.android``
folder within your home folder. The folder is automatically created by the
Android tools; but if it doesn't exist, create it.

We recommend using a separate keystore file per app. Below, we use the
**upload-key-helloworld.jks** filename. This assumes you are building an app
called "Hello World"; use the (lowercase, no spaces) app name, ``helloworld``
in the filename for the keystore.

Try not to lose this key; make backups if needed. If you do lose this key, you
can `contact Google Play support to reset it
<https://support.google.com/googleplay/android-developer/answer/7384423#reset>`__.
If you choose not to use app signing by Google Play, it is absolutely essential
that you not lose this key. For this reason, we recommend using App Signing by
Google Play.

.. tabs::

  .. group-tab:: macOS

    .. code-block:: bash

      $ mkdir -p ~/.android
      $ ~/Library/Caches/org.beeware.briefcase/tools/java/Contents/Home/bin/keytool -keyalg RSA -deststoretype pkcs12 -genkey -v -storepass android -keystore ~/.android/upload-key-helloworld.jks -keysize 2048 -dname "cn=Upload Key" -alias upload-key -validity 10000

  .. group-tab:: Linux

    .. code-block:: bash

      $ mkdir -p ~/.android
      $ ~/.cache/briefcase/tools/java/bin/keytool -keyalg RSA -deststoretype pkcs12 -genkey -v -storepass android -keystore ~/.android/upload-key-helloworld.jks -keysize 2048 -dname "cn=Upload Key" -alias upload-key -validity 10000

  .. group-tab:: Windows (PowerShell)

    .. code-block:: powershell

      C:\...>If (-Not (Test-Path "$env:HOMEPATH/.android")) { New-Item -Path "$env:HOMEPATH\.android" -ItemType Directory }
      C:\...>& "$env:LOCALAPPDATA\BeeWare\briefcase\Cache\tools\java\bin\keytool.exe" -keyalg RSA -deststoretype pkcs12 -genkey -v -storepass android -keystore "$env:HOMEPATH\.android\upload-key-helloworld.jks" -keysize 2048 -dname "cn=Upload Key" -alias upload-key -validity 10000

  .. group-tab:: Windows (cmd)

    .. code-block:: doscon

      C:\...>IF not exist %HOMEPATH%\.android mkdir %HOMEPATH%\.android
      C:\...>%LOCALAPPDATA%\BeeWare\briefcase\Cache\tools\java\bin\keytool.exe -keyalg RSA -deststoretype pkcs12 -genkey -v -storepass android -keystore %HOMEPATH%\.android\upload-key-helloworld.jks -keysize 2048 -dname "cn=Upload Key" -alias upload-key -validity 10000


This creates a 2048-bit key and stores it in a Java keystore located in the
``.android`` folder within your home folder. Since the key's purpose is to be
used as an upload key for the Google Play store, we call the key "upload-key".

We use a password of ``android``. This is the `default password for common
Android keystores <https://developers.google.com/android/guides/client-auth>`__.
You can change the password if you like. It is more important to limit who
has access to the keystore file than to change the password.

See :doc:`Publishing your app <../publishing/android/>` for instructions
on using this key to upload an app to the Google Play store.
