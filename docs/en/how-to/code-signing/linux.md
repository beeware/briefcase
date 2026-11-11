# Linux { #code-signing-linux }

## Overview

Linux system packages (`.deb`, `.rpm` and `.pkg.tar.zst`) can be signed using a [GNU Privacy Guard](https://gnupg.org/) (GPG) key. Unlike macOS and Windows, Linux has no central authority that issues signing certificates. A GPG signature lets users verify the integrity and provenance of a package, but it does not by itself make a package trusted; the person installing your package must import your public key into their GPG keyring and choose to trust it. A signature is required for publishing packages to some official repositories.

## Create a GPG key

If you don't already have a GPG key, you can create one with:

```console
$ gpg --full-generate-key
```

You will be prompted to select a key type, key size and expiry date, and to provide a name and email address that will identify the key. If possible, use an ECC key based on Curve 25519 (an `ed25519` signing key), which is the default in recent GnuPG versions and produces smaller, faster signatures. If you need to support older tools that don't understand ECC keys, generate an RSA key of at least 4096 bits instead. The email address should be an address you control, as users will use it (along with your public key) to identify that the package really came from you.

If you plan to sign packages built with Docker, create a key that does not require a passphrase: when GnuPG prompts you to enter a passphrase, leave the field blank and confirm. When a signing key is exported to a Docker container, GnuPG cannot prompt for the passphrase, so a key with a passphrase will fail the signing step. See [Docker builds](#docker-builds) for details.

## Obtain the identity of your key

Briefcase uses the *fingerprint* of your key to identify the signing identity. To see the fingerprints of all the secret keys on your system, run:

```console
$ gpg --list-secret-keys
```

Each key is listed with a `sec` entry, followed by the key's 40-character hexadecimal fingerprint. This fingerprint is the value you will provide as the `identity` for the Briefcase package command:

```console
$ briefcase package linux system --identity <fingerprint>
```

Alternatively, you can specify any portion of the fingerprint, the short key ID, or the name or email address associated with the key. If you don't specify an identity, Briefcase will prompt you to select the identity to use from the secret keys available on your system, or to opt out of signing. If you have only one secret key, it is offered as the default selection.

## Distributing the signature

When Briefcase signs a package, the signature is stored in a file alongside the package:

- A `.deb` package is signed in place, and the signature is embedded in the package's `origin` signature field.
- An `.rpm` package is signed in place; the signature is embedded in the package header.
- An `.pkg.tar.zst` package is signed with a detached signature, producing a separate `<package>.sig` file that must be distributed alongside the package.

Before distributing your packages, you should export your public key and make it available so that users can verify your packages:

```console
$ gpg --export --armor <fingerprint>
```

This will output your public key in ASCII armor format. You can publish it on a public keyserver (e.g., with `gpg --send-keys --keyserver keys.openpgp.org <fingerprint>`), or you can host the exported `.asc` file on your own website. Users can then add your key to their keyring with `gpg --import <file>` (or `gpg --recv-keys <fingerprint>`).

A user can then verify the integrity and provenance of your package:

- `debsig-verify` for `.deb` packages (using a policy that declares your key as trusted).
- `rpmkeys --checksig` (or `rpm --checksig`) for `.rpm` packages, once RPM is configured to trust your key.
- `gpg --verify <signature file> <package file>` for `.pkg.tar.zst` packages.

## Packaging without signing

If you don't have a GPG key, or you don't want to sign your package, Briefcase will warn you and produce an unsigned package. You can also explicitly opt out of signing by providing the `--adhoc-sign` option:

```console
$ briefcase package linux system --adhoc-sign
```

As with other platforms, `--adhoc-sign` is useful during development and testing, but an unsigned package may not be acceptable for release.

## Docker builds

Linux system packages can be signed when building with Docker (i.e., when the `--target` option is used), using the same GPG signing identity as native builds.

When signing a package built with Docker, Briefcase exports the selected secret key from the host machine's GPG keyring, and imports it into the build container so that the signing step can run inside the container. The exported key is removed immediately after signing, and is never stored in the Docker image.

One caveat applies when building with Docker: because the signing step runs inside a headless container, GnuPG is not able to prompt for a passphrase. If your signing key requires a passphrase, the signing step will fail. To sign packages built with Docker, use a key (or sub-key) that does not require a passphrase, or build the package without the `--target` option and sign it natively.
