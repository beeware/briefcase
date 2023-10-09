=======
Windows
=======

Overview
--------

While Windows does not require applications to be code signed, doing so can help
ensure the authenticity and integrity of your application when a user is trying
to install it. This includes preventing Windows from showing warnings to users
that your application is untrusted and may be dangerous.

To code sign your application with Briefcase, you must obtain a code signing
certificate from a Certificate Authority (CA) and install it in a Windows
certificate store.

Obtain a Certificate
--------------------

Microsoft `manages a collection of Certificate Authorities
<https://learn.microsoft.com/en-us/security/trusted-root/release-notes>`__
that are trusted by default in Windows. A code signing certificate from any of
these included entities should be trusted by a modern Windows machine.

Of note, a certificate for code signing is different from a certificate for other
cryptographic purposes. For instance, a certificate used by a website to create
encrypted HTTP connections cannot be used for code signing. Therefore, a request
for a code signing certificate must specifically be for code signing. Certificate
Authorities offering these services will make this clear during the request
process.

Additionally, it is possible to create a code signing certificate directly within
Windows. However, when you create a certificate yourself, it will likely be
considered "self-signed". Using such a certificate to code sign an application
will not imbue it with the trust that a certificate from a Certificate Authority
provides. Therefore, a self-signed certificate should not be used to code sign
applications for distribution.

Install the Certificate
-----------------------

Once a code signing certificate is requested, Certificate Authorities may vary
is how the certificate is actually delivered to you. In general, though, you'll
likely receive an encrypted file containing both the certificate and its private
key. Depending on the exact nature of the file format, Windows provides several
commands to import certificates in to one of its certificate stores.

For instance, this will a import PFX file in to the ``Personal`` certificate
store of ``Current User``:

.. tabs::

  .. group-tab:: CMD

    .. code-block:: doscon

      C:\...>certutil.exe -user -importpfx -p MySecretPassword My .\cert.pfx

  .. group-tab:: PowerShell

    .. code-block:: pwsh-session

      PS C:\...> Import-PfxCertificate -FilePath .\cert.pfx -CertStoreLocation Cert:\CurrentUser\My -Password MySecretPassword

Refer to your Certificate Authority's documentation for specific instructions.

Certificate's SHA-1 Thumbprint
------------------------------

On Windows, :doc:`briefcase package </reference/commands/package>` cannot retrieve the
list of installed code signing certificates automatically. You need to retrieve the
identity manually, and provide the certificates identity as a command line argument.

The certificates installed on the machine are available in the Certificate
Manager. Search for "User Certificates" in the Start Menu to access certificates
for ``Current User`` or search for "Computer Certificates" for certificates for
``Local Machine``. Alternatively, the command ``certmgr.msc`` will open the
manager for ``Current User`` and ``certlm.msc`` for ``Local Machine``.

Once you locate your certificate in the certificate store it was installed in
to, double-click it to access information about it. Near the bottom of the list
on the Details tab, you'll find the ``Thumbprint`` field with the 40 character
SHA-1 hash to use as the ``identity`` in the Briefcase package command.

.. code-block:: doscon

    (venv) C:\...>briefcase package --identity <certificate thumbprint>
