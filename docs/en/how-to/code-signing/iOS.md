# iOS { #code-signing-ios }

## Overview

To run an app on a physical iPhone or iPad, the app must be signed with a development certificate, and installed with a provisioning profile that authorizes it to run on that device. Briefcase uses Xcode to manage provisioning profiles for you, but you need to set up a development certificate, and prepare your device, before you can deploy to it.

You don't need to be a member of the Apple Developer Program to deploy to your own device; a free Apple ID is sufficient. Apple Developer Program membership is only required to distribute your app through the App Store or TestFlight.

These steps only need to be completed once for each Mac and device that you use.

## Requirements

* A Mac with Xcode installed.
* An iPhone or iPad running iOS or iPadOS 17 or later. Briefcase deploys apps using `devicectl`, which doesn't support earlier versions. This only affects the devices you deploy to during development; it doesn't change the minimum iOS version supported by your app.

## Add your Apple ID to Xcode

Open Xcode, then open Xcode's Settings, and select the *Accounts* tab. Click the `+` button, select *Apple ID*, and sign in.

If you have a free Apple ID, Xcode creates a *Personal Team* for you. If you're a member of one or more Apple Developer Program teams, each of those teams will also be listed.

## Create a development certificate

In the *Accounts* tab, select your Apple ID, select the team you want to use, and click *Manage Certificates...*. Click the `+` button, and select *Apple Development*.

This creates an "Apple Development" certificate, and installs it (with its private key) in your login keychain. You can confirm that the certificate is available by running:

```console
$ security find-identity -v -p codesigning
  1) 38EBD6F8903EC63C238B04C1067833814CE47CA3 "Apple Development: jane@example.com (A1B2C3D4E5)"
     1 valid identities found
```

The 40-character hex string is the identity's fingerprint. You can pass either the fingerprint or the full name of the identity (the part in quotes) to Briefcase using `-i`/`--identity`.

The identifier in parentheses at the end of the name identifies *you*, not your team. Briefcase reads the team from the certificate itself.

## Prepare your device

1. Connect your device to your Mac with a cable, and unlock it. When the device asks if you want to trust the computer, tap *Trust*, and enter your device passcode. After the device has been paired, you can also deploy to it over the local network, as long as the device is on the same network as your Mac.
2. Enable Developer Mode on the device. Open *Settings > Privacy & Security > Developer Mode*, and turn on Developer Mode. The device will restart; when it has restarted, confirm that you want to turn on Developer Mode. If the Developer Mode option isn't visible, open Xcode's *Window > Devices and Simulators* window while the device is connected; this will make the option appear.

You can confirm that the device is ready by running:

```console
$ xcrun devicectl list devices
```

The device should be listed with a state of `available (paired)`.

## Deploy your app

You can now run your app on the device:

```console
$ briefcase run iOS -d
```

Select your device from the list. When you select a physical device, Briefcase will ask you to select a development signing identity, then build the app, install it on the device, and start it.

The first time you run an app signed with a free Apple ID's certificate, iOS won't start the app, and Briefcase will report that the profile "has not been explicitly trusted by the user". To trust your certificate, open *Settings > General > VPN & Device Management* on the device, select your Apple ID under *Developer App*, and tap *Trust*. Then run your app again. You only need to do this once for each certificate.

## Signing behavior

Briefcase uses Xcode's automatic signing. The signing identity you select determines the team that is used; Xcode then creates or updates the provisioning profile for your app and device, registers the device with the team if necessary, and signs the app with that team's development certificate. If you have more than one development certificate for the same team in your keychain, Xcode selects which one is used.

Each app is identified by its bundle identifier (the [`bundle`][] and app name in your `pyproject.toml`). Bundle identifiers must be unique across *all* Apple developer teams, so you can't use a bundle identifier that has been registered by someone else. If Xcode reports that it can't register your bundle identifier, use a bundle based on a domain that you control.

### Free Apple ID limitations

Apps signed with a free Apple ID have some limitations:

* Provisioning profiles expire after 7 days. After that, the app won't start. Running the app again with Briefcase will renew the profile.
* You can only register a small number of new bundle identifiers each week, and only a small number of apps signed with a free Apple ID can be installed on a device at the same time.
* Some capabilities (such as push notifications and iCloud) aren't available.
