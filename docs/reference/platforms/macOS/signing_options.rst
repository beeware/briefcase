``--installer-identity <identity>``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

This option is only used when creating a ``.pkg`` installer.

The :doc:`code signing identity </how-to/code-signing/macOS>` to use when signing the
installer package. This is a *different* signing identity to the one used to sign the
app, but it must be from the same team as the app signing identity.

``--no-sign-installer``
~~~~~~~~~~~~~~~~~~~~~~~

This option is only used when creating a ``.pkg`` installer.

Do not sign the installer. This option can be useful during development and testing.
However, care should be taken using this option for release artefacts, as it may not be
possible to distribute an unsigned installer to others.

``--no-notarize``
~~~~~~~~~~~~~~~~~

Do not submit the application for notarization. By default, apps will be
submitted for notarization unless they have been signed with an ad-hoc
signing identity.
