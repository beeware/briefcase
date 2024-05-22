===
Security Tips
===

This guide will walk you through some key security considerations for publishing your
first app.
.. admonition: This is a draft.

    This documentation is currently an incomplete draft, and should not be relied on
    for completeness, grammar, or accuracy..

*  Keeping Your Personal Information Private
*  Protecting Your Signing Keys
*  Protecting Your Credentials
*
*
*
*
*
*
*

Keeping Your Personal Information Private
=====================
.. admonition: This is a draft.

    This admonition will be removed when content has been drafted and reviewed.
* The information you provide about yourself in your `pyproject.toml` file will be visible
to your users and the general public.
* Don’t use an important email for publishing
* The name you publish under will be public, and you may or may not be able to
fully remove/change it later
* Something about judicious use of path names wrt “The packages (and other various source code
    and data-defining attributes) in setup.py have been replaced with a single sources key. The
    paths specified in sources will be copied in their entirety into the packaged application.”
* You may wish to  open the Android bundle file with an unarchiving program, open the `resources.pb`` file,
and confirm that the bundle name appearing in the first line is the one you intend to make public. If it's not, you
can update the bundle name in `pyproject.toml`.

Protecting Your Signing Keys
============================

.. admonition: This is a draft.

    This admonition will be removed when content has been drafted and reviewed.

* Add your keystore (as generated in https://briefcase.readthedocs.io/en/stable/how-to/code-signing/android.html)
    to your gitignore before generating the signing key, so you don’t accidentally disclose
* It is more important to protect the file than to change the password, but you should still change the password
        * Some jurisdictions have compliance requirements wrt use of default passwords that you may run afoul of
        * Post-SHAttered this is very iumportant tbh.
* Signing Certificates are intended to be used for multiple applications. However, keep in mind that users may be
able to associate your apps with each other using the signing key. This is totally fine for almost everyone, but
may be worth considering if you work on any apps of sensitive nature.


Protecting Your Credentials
======================

.. admonition: This is a draft.

    This admonition will be removed when content has been drafted and reviewed.

    * iOS publishing requires a set of credentials for your app if your app requires login; these should be unique
    credentials to an account used only for this purpose, and it's especially important to use a randomly-generated
    password and/or unpredictable username for this account because everyone familiar with app store policies will
    know there is one, and you won't be logging into it regularly which makes it especially vulnerable to ATO.
