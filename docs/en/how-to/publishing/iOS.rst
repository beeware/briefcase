===
iOS
===

This guide will walk you through the process of publishing an app to the Apple App
Store.

.. admonition: App Stores are a moving target

    The Apple App Store makes frequent changes to the workflows and nomenclature
    associated with publishing apps. As a result, it's very difficult to keep a like
    this one up to date. If you spot any problems, `let us know
    <https://github.com/beeware/briefcase/issues/new?assignees=&labels=bug,documentation,apple&projects=&template=bug_report.yml>`__.

To distribute an app on the iOS App Store, you'll need to :ref:`enroll in the Apple
Developer Program <apple-dev-enroll>`. You don't need to generate any of the
certificates described on that page - you just need an Apple ID registered in the
developer program.

Once you've signed up for an Apple ID account, open the Xcode Settings dialog, and
add your account under the "Accounts" tab.

Open the app in Xcode
=====================

Use Briefcase to open the Xcode project associated with your project.

.. code-block:: console

    (venv) $ briefcase open iOS

Run the app in the simulator
============================

In order to submit your app to the App Store, you will need to provide a range of
screenshots:

* 3-5 screenshots running on a 6.5" iPhone (e.g., iPhone 14 Plus)
* 3-5 screenshots running on a 5.5" iPhone (e.g., iPhone 8 Plus)
* 3-5 screenshots running on an 12.9" iPad Pro (Gen 6; without a physical home button)
* 3-5 screenshots running on an 12.9" iPad Pro (Gen 2; with a physical home button)
* (optionally) 3-5 screenshots running on a 6.7" iPhone (e.g., iPhone 14 Pro Max)

The iOS and iPad simulators have a "Save Screen" button in their title bar; this will
capture screenshots of the necessary size.

You can change simulator device by clicking on the device target int the top bar of the
Xcode window. Click on the device name, and select the device from the list. If the device
you need doesn't exist on this list, click on "Manage Run Destinations" to add a simulator
for that device type.

Produce an App archive
======================

Select the root node of the Xcode project browser (it should be the formal name of your
app), then select the **Signing & Capabilities** tab from configuration options that are
displayed. The "Team" option under "Signing" will be listed as "None"; select the name
of the development team that will sign the app. If there's no team listed, select "Add
an Account", and choose one of the teams that is associated with your Apple ID.

In the top bar of the Xcode window, change the target device from a simulator to "Any
iOS device". Clean the build products folder (select "Clean Build Folder..." from the
Product menu), then build an archive by selecting "Archive" from the Product menu. This
will perform a clean build of your application, build an archive, and open a new window,
called the Organizer. It should list a freshly created archive of your app, with the
current version number.

Select the archive, and click the "Distribute App" on the right side of the Organizer
window. This will display a wizard that will ask details about your app; accept the
default values; once the wizard completes, your app binary has been sent to the App
Store for inclusion in a release.

After a few minutes, you should receive an email notifying you that the binary has been
processed.

Create an App Store entry
=========================

Log into `App Store Connect <https://appstoreconnect.apple.com>`__, click on "My Apps",
then on + to add an app.

Fill out the form for a new app. If you've run the app in Xcode, the Bundle ID for your
app should be listed; select it from the list. You must also create an SKU for your app
- we suggest ``ios-<appname>``, substituting the short app name that you selected when
you initially created your app. So, if you've created an app with a formal name of
"Hello World", with an app name of ``helloworld``, and a bundle of ``org.beeware``, you
should have a Bundle ID of ``org.beeware.helloworld``; we'd suggest an SKU of
``ios-helloworld``.

You'll then be shown another page for app details, including:

* Primary and Secondary Category.
* Screenshots
* Promotional Text
* Description
* Keywords
* Support URL
* Marketing URL
* A URL for your app's privacy policy
* Version number
* The name of the copyright holder

Under the "Build" section, you'll be able to select the archive that you uploaded
through Xcode.

The "App Review Information" section allows you to provide contact details in case Apple
has questions during the review process. If your app requires a login, you *must*
provide a set of credentials so that Apple can log in. You can also provide any
additional notes to assist the reviewer.

Click on "Pricing and Availability" tab on the sidebar, and set up the pricing schedule
and availability for your app.

Then, click on "App Privacy", and click on "Get Started"; this will ask you a series of
questions about the information about users that your app collects.

Once these details have all been provided, click on the "1.0 Prepare for Submission" link
in the sidebar. On the right of the screen, click on "Add for Review"; this will ask some
final questions, and provide one more button "Submit for Review". Click that button, and
you're done!
