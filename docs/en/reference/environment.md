# Briefcase configuration options

## Environment variables

### `BRIEFCASE_HOME`

When briefcase runs, it will download the support files, tools, and SDKs necessary to support building and packaging apps. By default, it will store the files in a platform-native cache folder:

- macOS: `~/Library/Caches/org.beeware.briefcase`
- Windows: `%LOCALAPPDATA%\BeeWare\briefcase\Cache`
- Linux: `~/.cache/briefcase`

If you want to use a different folder to store the Briefcase resources, you can define a `BRIEFCASE_HOME` environment variable.

There are three restrictions on this path specification:

1. The path must already exist. If it doesn't exist, you should create it manually.
2.  It *must not* contain any spaces.
3.  It *must not* be on a network drive.

The second two restrictions both exist because some of the tools that Briefcase uses (in particular, the Android SDK) do not work in these locations.

### `BRIEFCASE_ALLOW_EMULATION`

/// warning | Do not use in production

It is *highly* inadvisable to generate production apps while this environment variable is set.

///

Both macOS and Windows provide mechanisms for running x86_64 binaries on ARM64 hardware. These tools can make it very difficult to generate a packaged application, as it can be difficult to ensure a packaged application contains code matching the right architecture when the platform provides misleading answers about the current platform. As a result, Briefcase will raise an error if it detects that the version of Python that is being used doesn't match the underlying hardware architecture.

However, it is possible to disable this check by setting the `BRIEFCASE_ALLOW_EMULATION` environment variable. This will cause Briefcase to output a warning if it appears that Python is running in emulation mode, but it will allow Briefcase commands to run.

### HTTP downloads

Briefcase honors the following environment variables when downloading tools, support packages, and other resources:

- `HTTP_PROXY`: The proxy URL for HTTP requests.
- `HTTPS_PROXY`: The proxy URL for HTTPS requests.
- `ALL_PROXY`: The proxy URL for requests of either scheme.
- `NO_PROXY`: A comma-separated list of hosts or URLs that should bypass proxies.
- `SSL_CERT_FILE`: A CA certificate bundle file to use instead of the default certificates.
- `SSL_CERT_DIR`: A directory of CA certificates in the <nospell>OpenSSL</nospell> layout (prepared using `c_rehash`) to use instead of the default certificates. `SSL_CERT_FILE` takes precedence if both certificate variables are set.

For full details and examples, see the [<nospell>httpx2</nospell> environment variable documentation](https://pydantic.dev/docs/httpx2/api/environment_variables/).

If a download fails, check that certificate paths exist, have the correct type, and are readable, and that proxy URLs are valid and reachable. Correct or unset variables that refer to obsolete certificate or proxy configurations.
