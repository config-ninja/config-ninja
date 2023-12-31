# Config Ninja 🥷

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![🎨 poe (push)](https://github.com/bryant-finney/config-ninja/actions/workflows/push-poe.yaml/badge.svg)](https://github.com/bryant-finney/config-ninja/actions/workflows/push-poe.yaml)

Similar to [`confd`](https://github.com/kelseyhightower/confd), manage your system configuration files by populating [Jinja2](https://jinja.palletsprojects.com/en/3.1.x/) templates with data from a remote provider.

## Installation

To install using `pip`:

```sh
pip install config-ninja
```

## Development

The following system dependencies are required:

- [`poetry`](https://python-poetry.org/docs/#installation): install dependencies and manage virtual environments
- [`pre-commit`](https://pre-commit.com/#install): run linters and formatters for the package
- (optional) [`direnv`](https://direnv.net/docs/installation.html): automatically execute the [`.envrc`](./.envrc) script to manage project dependencies

Common development commands are managed by [`poethepoet`](https://github.com/nat-n/poethepoet); run `poe --help` for an up-to-date list of commands:

```txt
Poe the Poet - A task runner that works well with poetry.
version 0.24.4

USAGE
  poe [-h] [-v | -q] [--root PATH] [--ansi | --no-ansi] task [task arguments]

GLOBAL OPTIONS
  -h, --help     Show this help page and exit
  --version      Print the version and exit
  -v, --verbose  Increase command output (repeatable)
  -q, --quiet    Decrease command output (repeatable)
  -d, --dry-run  Print the task contents but don't actually run it
  --root PATH    Specify where to find the pyproject.toml
  --ansi         Force enable ANSI output
  --no-ansi      Force disable ANSI output

CONFIGURED TASKS
  setup-versioning  Install the 'poetry-dynamic-versioning' plugin to the local 'poetry' installation
  docs              Generate this package's docs
  build-docs        Run a command sequence to build the documentation suite
  serve-docs        Use 'pdoc' to launch an HTTP server for this package's docs
  lab               Run Jupyter Lab
  lint              Lint this package
  test              Test this package and report coverage
  test-watch        Run tests continuously by watching for file changes
  pre-release       Create a new pre-release and push it to GitHub
```
