# How-to guides  { #how-to }

How-to guides are recipes that take the user through steps in key subjects. They are more advanced than tutorials and assume a lot more about what the user already knows than tutorials do, and unlike documents in the tutorial they can stand alone.

## Obtaining a Code Signing identity

* [Android](code-signing/android.md) - One way to sign your app where the Google Play Store maintains the authoritative key for your app.
* [macOS](code-signing/macOS.md) - How to generate a macOS code signing identity, which is required to distribute your application.
* [Windows](code-signing/windows.md) - Obtaining a codes signing certificate from a Certificate Authority and installing it in a Windows certificate store.

## Building different types of apps

* [Building your App in CI with GitHub Action](ci.md) - This GitHub Actions workflow provides the basic framework necessary to test, build, and package a Briefcase project in CI for Windows, Linux, macOS, iOS, and Android.
* [Building your Console App with Briefcase](cli-apps.md) - The key differences when creating a console application using Briefcase, as opposed to a GUI-based app.
* [Packaging external apps](external-apps.md) - Learn how Briefcase can be used to package an application that has been constructed using another tool.

## Testing Apps

* [Testing Linux Apps with Docker](x11passthrough.md) - Configure your system to use Docker to build apps for Linux distributions other than the distribution you're currently using.

## Publishing your app

* [Android](publishing/android.md) - Distribute a BeeWare app on the Google Play Store.
* [iOS](publishing/iOS.md) - Publish an iOS app to the Apple App Store.
* [macOS](publishing/macOS.md) - Publish a macOS app to the Apple App Store.

## Contributing to Briefcase

* [Contributing code to Briefcase](contribute/code.md) - The process to follow to contribute to Briefcase source code.
* [Contributing to the documentation](contribute/docs.md) - The process to follow to contribute to Briefcase documentation.

## Internal How-to guides

* [How to cut a Briefcase release](internal/release.md) - The procedure for cutting a new release of Briefcase.

## Upgrading from previous versions

* [Upgrading from Briefcase v0.2](upgrade-from-v0.2.md) - The changes to configuration and processes needed to upgrade from v0.2 to v0.3.
