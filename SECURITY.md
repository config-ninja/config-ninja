# Security policy

## Scope of security vulnerabilities

The `config-ninja` agent is a Python package designed to read and write system configuration files. Due to the dynamic nature of Python itself and the design of `config-ninja`, the execution of arbitrary code is supported by design. For example:

- `config-ninja` can be executed as the `root` user to overwrite sensitive files on the host OS
- `config-ninja` can be configured to execute arbitrary scripts, snippets, commands, or programs when triggered by remote or local backends

The agent is meant to be installed, configured, and operated on secured systems by trusted administrators. As such, vulnerabilities relating to untrusted input are not considered vulnerabilities in `config-ninja` itself but rather a vulnerability of its deployment environment. If you think `config-ninja`'s stance in these areas can be hardened, please file an issue for a new feature request.

Similarly, various packages and utilities (specified within this package's `dev` dependencies group) are utilized by `config-ninja`'s test suite. These packages, as well as the testing code, are not requirements of `config-ninja` or distributed with the service; they are only used for development and testing purposes. A best effort is made to keep these `dev` dependencies up-to-date and free of vulnerabilities; however, vulnerabilities in the test suite or `dev` dependencies are not considered vulnerabilities of `config-ninja`.

## Reporting a vulnerability

If you have found a possible vulnerability that is not excluded by the above [scope](#scope-of-security-vulnerabilities), please consider [privately reporting a security vulnerability](https://docs.github.com/en/code-security/security-advisories/guidance-on-reporting-and-writing-information-about-vulnerabilities/privately-reporting-a-security-vulnerability#privately-reporting-a-security-vulnerability) at the following URL: https://github.com/config-ninja/config-ninja/security

## Vulnerability disclosures

Critical vulnerabilities will be disclosed via GitHub's [security advisory](https://github.com/config-ninja/config-ninja/security).
