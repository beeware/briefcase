``--file-digest <digest>``
~~~~~~~~~~~~~~~~~~~~~~~~~~

The digest algorithm to use for code signing files in the project. Defaults to
``sha256``.

``--use-local-machine-stores``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

By default, the certificate for code signing is assumed to be in the Current
User's certificate stores. Use this flag to indicate the certificate is in the
Local Machine's certificate stores.

``--cert-store <store>``
~~~~~~~~~~~~~~~~~~~~~~~~

The internal Windows name for the certificate store containing the certificate
for code signing. Defaults to ``My``.

Common Stores:

+--------------------------------------------+------------------+
| Personal                                   | My               |
+--------------------------------------------+------------------+
| Intermediate Certification Authorities     | CA               |
+--------------------------------------------+------------------+
| Third-Party Root Certification Authorities | AuthRoot         |
+--------------------------------------------+------------------+
| Trusted People                             | TrustedPeople    |
+--------------------------------------------+------------------+
| Trusted Publishers                         | TrustedPublisher |
+--------------------------------------------+------------------+
| Trusted Root Certification Authorities     | Root             |
+--------------------------------------------+------------------+

``--timestamp-url <url>``
~~~~~~~~~~~~~~~~~~~~~~~~~

The URL of the Timestamp Authority server to timestamp the code signing.
Defaults to ``http://timestamp.digicert.com``.

``--timestamp-digest <url>``
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The digest algorithm to request the Timestamp Authority server uses for the
timestamp for code signing. Defaults to ``sha256``.
