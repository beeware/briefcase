.. Notes about this file:
    The writing style may not match other BeeWare docs. I intend to revise it.
    This file is a stub.

=======
Android
=======

Overview
--------

Android devices require signed apps. The Play store requires signed apps. This doc is about
how to sign your app. It only really matters when it's time to ship the app
to the Play Store.

The signing key is used to indicate to Android phones that the app is still controlled by
you as you ship updates. This documentation covers one way to sign your app,
where you retain full control over the signing key. There's another way, where you still
sign the app this way, but the Google Play Store removes that signature and signs it with
its own key. That can have its advantages, but is out of scope for this documentation.

Generate a key
--------------

Run this command::

  $ keytool -genkey -v -keystore my-release-key.jks -keyalg RSA -keysize 2048 -validity 10000 -alias my-alias

.. TODO list:
    - Use Windows/Mac/Linux tabs for the above.
    - Add $JAVA_HOME.
    - Test it.
    - Decide with Russell where we want to store these keys.

.. admonition:: Don't lose the key!

  If you lose this key, you won't be able to distribute updates to the app. Keep it safe;
  make a backup; do what you have to do.
