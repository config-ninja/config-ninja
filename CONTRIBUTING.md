# Contributing to `config-ninja`

Thank you for your interest in contributing to `config-ninja`! We appreciate your help to make this project better.

## Table of Contents

- [Contributing to `config-ninja`](#contributing-to-config-ninja)
  - [Table of Contents](#table-of-contents)
  - [Code of Conduct](#code-of-conduct)
  - [How Can I Contribute?](#how-can-i-contribute)
    - [Reporting Bugs 🪲](#reporting-bugs-)
    - [Suggesting Features / Enhancements ✨](#suggesting-features--enhancements-)
    - [Pull Requests](#pull-requests)
  - [Development Setup](#development-setup)
  - [License](#license)

## Code of Conduct

Please note that by participating in this project, you are expected to adhere to the [Community Code of Conduct](https://about.gitlab.com/community/contribute/code-of-conduct/). Treat each other with respect to create a positive and inclusive environment. 🥳

## How Can I Contribute?

There are several ways you can contribute to `config-ninja`.

### Reporting Bugs 🪲

If you encounter any bugs while using `config-ninja`, please [open a new bug issue] using the [bug_report.md] template.

### Suggesting Features / Enhancements ✨

If you have any ideas or suggestions to improve `config-ninja`, please [open a new issue] using the [feature_request.md] or [propose_enhancement.md] template.

### Pull Requests

Pull requests for bug fixes, enhancements, and new features are very welcome. To contribute code to `config-ninja`, follow these steps:

1. Create [a fork of the repository](https://github.com/bryant-finney/config-ninja/fork)
2. Implement your changes in the fork, ensuring they adhere to the project's [linters and formatters](.pre-commit-config.yaml)
3. Open a new pull request from your fork to the `config-ninja` repository, and provide a detailed
   description of your changes

> [!NOTE]
> Each contribution must pass all CI/CD and linting tests in order to be considered.

Once your pull request is submitted, it will be reviewed by the project maintainers. Please be patient, as it may take some time to receive feedback.

## Development Setup

The following system dependencies are required:

- [`poetry`](https://python-poetry.org/docs/#installation): manage dependencies and virtual environments
- [`pre-commit`](https://pre-commit.com/#install): run linters and formatters for the package
  - > [!TIP]
    > `pre-commit` is included as a `dev` dependency; however, it tends to work better when it's installed at the user / system level
- (optional) [`direnv`](https://direnv.net/docs/installation.html): automatically execute the [`.envrc`](./.envrc) script to install project dependencies
  - if you don't want to set up `direnv`, you can manually run `. ./.envrc` instead

Common development commands are managed by [`poethepoet`](https://github.com/nat-n/poethepoet); run `poe --help` for an up-to-date list of commands:

```sh
❯ poe --help
Poe the Poet - A task runner that works well with poetry.
version 0.24.4

USAGE
  poe [-h] [-v | -q] [--root PATH] [--ansi | --no-ansi] task [task arguments]

GLOBAL OPTIONS
  -h, --help     Show this help page and exit
  --version      Print the version and exit
  -v, --verbose  Increase command output (repeatable)
  -q, --quiet    Decrease command output (repeatable)
  -d, --dry-run  Print the task contents without actually running it
  --root PATH    Specify where to find the pyproject.toml
  --ansi         Force enable ANSI output
  --no-ansi      Force disable ANSI output

CONFIGURED TASKS
  setup-versioning  Install the 'poetry-dynamic-versioning' plugin to the local 'poetry' installation
  docs              Generate the package docs
  serve-docs        Use 'pdoc' to launch an HTTP server for the package docs
  lab               Run Jupyter Lab
  lint              Lint this package
  test              Test this package and report coverage
  test-watch        Run tests continuously by watching for file changes
  pre-release       Create a new pre-release and push it to GitHub
```

## License

By contributing to `config-ninja`, you agree that your contributions will be licensed under the project's [OSI approved license](LICENSE).

[bug_report.md]: .github/ISSUE_TEMPLATE/bug_report.md
[feature_request.md]: .github/ISSUE_TEMPLATE/feature_request.md
[open a new bug issue]: https://github.com/bryant-finney/config-ninja/issues/new?assignees=&labels=bug&projects=&template=bug_report.md&title=bug%3A+...
[open a new issue]: https://github.com/bryant-finney/config-ninja/issues/new/choose
[propose_enhancement.md]: .github/ISSUE_TEMPLATE/propose_enhancement.md
