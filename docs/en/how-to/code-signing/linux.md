# Linux { #code-signing-linux }

## Overview

Linux system packages (`.deb`, `.rpm` and `.pkg.tar.zst`) can be signed using a [GNU Privacy Guard](https://gnupg.org/) (GPG) key. Unlike macOS and Windows, there is no central authority that issues signing certificates for Linux. A GPG signature does not, by itself, make a package trusted; the person installing your package must have imported your public key into their GPG keyring, and must choose to trust it. However, a signature does allow a user to verify both the *integrity* and the *provenance* of the package, and it is a requirement for publishing packages to some official repositories.

## Create a GPG key

If you don't already have a GPG key, you can create one with:

```console
$ gpg --full-generate-key
```

You will be prompted to select a key type, key size and expiry date, and to provide a name and email address that will identify the key. The email address should be an address you control, as users will use it (along with your public key) to identify that the package really came from you.

## Obtain the identity of your key

Briefcase uses the *fingerprint* of your key to identify the signing identity. To see the fingerprints of all the secret keys on your system, run:

```console
$ gpg --list-secret-keys
```

Each key is listed with a `sec` entry, followed by the key's 40-character hexadecimal fingerprint. This fingerprint is the value you will provide as the `identity` for the Briefcase package command:

```console
$ briefcase package linux system --identity <fingerprint>
```

Alternatively, you can specify any portion of the fingerprint, the short key ID, or the name or email address associated with the key. If you have more than one secret key on your system, and you don't specify an identity, Briefcase will prompt you to select the identity to use.

## Distributing the signature

When Briefcase signs a package, the signature is stored in a file alongside the package:

- A `.deb` package is signed in place, and the signature is embedded in the package's `origin` signature field.
- An `.rpm` package is signed in place; the signature is embedded in the package header.
- An `.pkg.tar.zst` package is signed with a detached signature, producing a separate `<package>.sig` file that must be distributed alongside the package.

Before distributing your packages, you should export your public key and make it available so that users can verify your packages:

```console
$ gpg --export --armor <fingerprint>
```

This will output your public key in ASCII armor format, which can be added to a user's keyring with `gpg --import`. A user can then verify the integrity and provenance of your package with `gpg --verify <signature file> <package file>` (for `.pkg.tar.zst` packages), or with the package manager's own verification tooling (for `.deb` and `.rpm` packages).

## Packaging without signing

If you don't have a GPG key, or you don't want to sign your package, Briefcase will warn you and produce an unsigned package. You can also explicitly opt out of signing by providing the `--adhoc-sign` option:

```console
$ briefcase package linux system --adhoc-sign
```

As with other platforms, `--adhoc-sign` is useful during development and testing, but an unsigned package may not be acceptable for release.
