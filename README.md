# Config Ninja 🥷

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![🎨 poe (push)](https://github.com/bryant-finney/config-ninja/actions/workflows/push-poe.yaml/badge.svg)](https://github.com/bryant-finney/config-ninja/actions/workflows/push-poe.yaml)
[![pylint](https://bryant-finney.github.io/config-ninja/reports/pylint.svg)](https://bryant-finney.github.io/config-ninja/reports/pylint-report.txt)
[![codecov](https://codecov.io/gh/bryant-finney/config-ninja/graph/badge.svg?token=R3DFDSNK9U)](https://codecov.io/gh/bryant-finney/config-ninja)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/bryant-finney/config-ninja/main.svg)](https://results.pre-commit.ci/latest/github/bryant-finney/config-ninja/main)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://bryant-finney.github.io/config-ninja/reports/mypy-html)
[![docs: pdoc](https://img.shields.io/badge/docs-pdoc-blueviolet?logo=github)](https://bryant-finney.github.io/config-ninja/config_ninja.html)

Similar to [`confd`](https://github.com/kelseyhightower/confd), manage your system configuration files by populating [Jinja2](https://jinja.palletsprojects.com/en/3.1.x/) templates with data from a remote provider.

## Installation

To install using `pip`:

```sh
pip install config-ninja
```

## Quick Start

To demonstrate the mechanics locally:

1. create a settings file for `config-ninja`:
   ```sh
   cat <<EOF >config-ninja-settings.yaml
   CONFIG_NINJA_OBJECTS:
     example-0:
       dest:
         format: json
         path: ./.local/config.json
       source:
         backend: local
         format: toml
         init:
           kwargs:
             path: ./.local/config.toml
   EOF
   ```
2. start `config-ninja` in `monitor` mode:
   ```sh
   config-ninja monitor
   ```
3. in a separate shell, create the `config.toml`:
   ```sh
   cat <<EOF >./.local/config.toml
   [example-0]
   a = "first value"
   b = "second value
   EOF
   ```
4. inspect the generated `settings.json`:
   ```sh
   cat settings.json
   ```
   ```json
   {
     "example-0": {
       "a": "first value",
       "b": "second value"
     }
   }
   ```

Chances are, you'll want to update the `config-ninja-settings.yaml` file to use a remote backend (instead of `local`). See [config_ninja.contrib](https://bryant-finney.github.io/config-ninja/config_ninja/contrib.html) for a list of supported config providers.

## Configuration Architecture

The `config-ninja` agent monitors the backend source for changes. When the source data is changed, the agent updates the local configuration file with the new data:

```mermaid
sequenceDiagram
    loop polling
       config-ninja->>backend: query for changes
    end

    backend->>+config-ninja: [backend changed] fetch config
    config-ninja->>-filesystem: write updated configuration file
```
