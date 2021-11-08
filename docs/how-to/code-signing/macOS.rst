=====
macOS
=====

Overview
--------

Getting the code signing identity for macOS will require four main steps, which you will be guided through in this tutorial:

1. Enrolling in the Apple Developer program

2. Generating a Certificate Signing Request on Keychain Access

3. Creating a Developer ID Application Certificate

4. Accessing the details of the Certificate on your Terminal


Enrolling in the Apple Developer program
----------------------------------------

You can enrol to the Apple Developer program either as an individual, or as an organization. In both cases, you'll have to follow the instructions on the `Apple Developer website <https://developer.apple.com/programs/enroll/>`__. 

Once you click "Start Enrollment Now" at the bottom of the page, you can either sign in with your existing Apple ID or alternatively, create a new one:

.. image:: AppleID.png
   :width: 300

As part of the registration procedure, you'll have to pay a **$99 fee**, which will be charged on an annual basis. **Note**: If you're registering as a non-profit organization, an educational institution or a government entity, you may be eligible for a fee waiver, which you can read more about `here <https://developer.apple.com/support/membership-fee-waiver/>`__. 


Generating a certificate request on Keychain Access
---------------------------------------------------

Now that you're set up with an Apple Developer ID, it's time to create a certificate *request*, which you'll then use to generate a valid Developer ID certificate. 

First, open the Keychain Access application on your Mac. At the top left of your screen, click ``Keychain Access`` > ``Certificate Assistant`` > ``Request a Certificate From a Certificate Authority``:

.. image:: Keychain_request1.png
   :width: 500

A Certificate Assistant window should open up, looking similar to this one:

.. image:: Keychain_request2.png
   :width: 500

* In the field ``User Email Address``, type the email address associated with your Apple Developer Account (e.g. ``jane@example.com``).
* ``Common Name`` should refer to the name with which you registered to the Apple Developer program (e.g. ``Jane Doe``).
* The field ``CA Email Address`` can be left empty.
* Make sure that you choose ``Saved to Disk`` in the ``Request is`` field.
* Click "Continue", and save save your Certificate Signing Request somewhere on your local machine. The saved certificate request should be of the format ``example.certSigningRequest``.

As documented by `Apple <https://help.apple.com/xcode/mac/current/#/dev97211aeac>`__, this procedure creates not only the file you have just saved, but also a private key in your Keychain, which will establish the validity of your actual Developer ID Application certificate later on. 


Creating a Developer ID Application Certificate
-----------------------------------------------

Once you have saved the certificate request, head to the `Apple Developer website <https://developer.apple.com/account>`__ and click "Certificates, Identifiers and Profiles":

.. image:: Certificates_Identifiers_Profiles.png
   :width: 500

When you land in the Certificates section, click the "+" symbol to create a new certificate:

.. image:: Create_certificate.png
   :width: 500

In the next page, you'll have to choose the type of certificate you want to generate. In the Software section, choose the very last option of **"Developer ID Application"**. **It's very important you choose the right type of certificate**:

.. image:: Choose_developerID_application.png
   :width: 500

**Note**: If you've been registered as an organization, there's a chance that the option of the Developer ID Application is unavailable because you're not assigned the role of the `Account Holder <https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution>`__. You can access and change these roles using `App Store Connect <https://appstoreconnect.apple.com/access/users>`__.  

Then click "Continue". In the next window, click "Choose file" and upload the Certificate Signing Request you have just generated on your Keychain:

.. image:: Upload_certificate_request.png
   :width: 500

Once you click "Continue", Apple will generate your Developer ID Application Certificate. Click the "Download" button and save the certificate on your local machine:

.. image:: Download_certificate.png
   :width: 500

Once you download the certificate, double-click on it to install it on your Keychain. 

Then go to back to your Keychain Access application, and open the window ``My Certificates``. You should see a certificate that reads "Developer ID Application...". 

Click on the certificate and make sure you see a note that reads ``This certificate is valid``. **Note**: In the example below, certificate details have been erased:

.. image:: Valid_certificate.png
   :width: 500

Congratulations! You've just successfully installed the Developer ID Application certificate.


Accessing the details of the Certificate on your Terminal
----------------------------------------------------------------

Finally, open your Terminal. You'll have to run a command that will fetch detailed information about all valid certificates for code signing on your local machine, including the Developer ID Application Certificate you have just created:

.. tabs::

  .. group-tab:: macOS

    .. code-block:: bash

      $ security find-identity -p basic -v


The important part of the output is the following:: 

    <Certificate ID> "Developer ID Application: <Name> (<Team ID>)"

e.g::
    
    A1B2C3D4E5F6G7H8I9J10K11L12M13N14O15P16R "Developer ID Application: Jane Doe (ABCD123456)"

You'll need to keep note of two things:

  1. **Certificate ID**: This should be a 40-unit string, which in the example is: ``A1B2C3D4E5F6G7H8I9J10K11L12M13N14O15P16R``

  2. **Team ID**: Will usually be a 10-unit string. Here, it's: ``ABCD123456``. 


Next steps
----------
Certificates of this type are quite precious, and you should make sure to keep them safe. A single Developer ID Application Certificate can be used to `sign and notarize multiple applications <https://developer.apple.com/forums/thread/657993>`__, which is why only a `very limited number of them <https://help.apple.com/xcode/mac/current/#/dev3a05256b8>`__ can be created on a particular Developer Account. You should consider making a back up copy, which will require you to export the certificate together with the associated private key from the Keychain. The procedure for doing so is `documented <https://support.apple.com/guide/keychain-access/import-and-export-keychain-items-kyca35961/mac>`__ by Apple.

Now it's time to start using the Developer ID Application Certificate to sign and notarize your application!