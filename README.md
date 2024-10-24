# Config Ninja 🥷

[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![🎨 poe (push)](https://github.com/config-ninja/config-ninja/actions/workflows/push-poe.yaml/badge.svg)](https://github.com/config-ninja/config-ninja/actions/workflows/push-poe.yaml)
[![pylint](https://config-ninja.github.io/config-ninja/reports/pylint.svg)](https://config-ninja.github.io/config-ninja/reports/pylint-report.txt)
[![codecov](https://codecov.io/gh/config-ninja/config-ninja/graph/badge.svg?token=R3DFDSNK9U)](https://codecov.io/gh/config-ninja/config-ninja)
[![pre-commit.ci status](https://results.pre-commit.ci/badge/github/config-ninja/config-ninja/main.svg)](https://results.pre-commit.ci/latest/github/config-ninja/config-ninja/main)
[![Checked with mypy](https://www.mypy-lang.org/static/mypy_badge.svg)](https://config-ninja.github.io/config-ninja/reports/mypy-html)
[![docs: pdoc](https://img.shields.io/badge/docs-pdoc-blueviolet?logo=github)](https://config-ninja.github.io/config-ninja/config_ninja.html)
[![readthedocs](https://readthedocs.org/projects/config-ninja/badge/?version=latest)](https://config-ninja.readthedocs.io/en/latest/home.html)
[![PyPI version](https://badge.fury.io/py/config-ninja.svg)](https://badge.fury.io/py/config-ninja)
[![Downloads](https://static.pepy.tech/badge/config-ninja/month)](https://pepy.tech/project/config-ninja)

Similar to [`confd`](https://github.com/kelseyhightower/confd), manage your system configuration files by populating [Jinja2](https://jinja.palletsprojects.com/en/3.1.x/) templates with data from a remote provider.

The `config-ninja` agent monitors the backend source for changes. When the source data is changed, the agent updates the local configuration file with the new data:

```mermaid
sequenceDiagram
		loop polling
			 config-ninja->>backend: query for changes
		end

		backend->>+config-ninja: [backend changed] fetch config
		config-ninja->>-filesystem: write updated configuration file
```

## Features

- ✅ Integration with [AWS AppConfig](https://jinja.palletsprojects.com/en/3.1.x/) for managing server configuration files
- ✅ Extensible design supports backends for new providers and formats
- ✅ [`jinja2`](https://jinja.palletsprojects.com/en/3.1.x/) templating for arbitrary configuration file formats
- ✅ Execute [`poethepoet`](https://poethepoet.natn.io/index.html) tasks after updating files

## Installation

`config-ninja` is installed using the official installer or with `pip` / `pipx`. After installation, you can enable `config-ninja` as a `systemd` service.

### Official Installer

The recommended way to install `config-ninja` is with the official installer:

```sh
curl -sSL https://config-ninja.github.io/config-ninja/install.py | python3 -
```

To view available installation options, run the installer with the `--help` flag:

```sh
curl -sSL https://config-ninja.github.io/config-ninja/install.py | python3 - --help
```

```
usage: install [-h] [--version VERSION] [--pre] [--uninstall] [--force] [--path PATH] [--backends BACKENDS]

Installs the latest (or given) version of config-ninja

options:
	-h, --help           show this help message and exit
	--version VERSION    install named version
	--pre                allow pre-release versions to be installed
	--uninstall          uninstall config-ninja
	--force              respond 'yes' to confirmation prompts; overwrite existing installations
	--path PATH          install config-ninja to this directory
	--backends BACKENDS  comma-separated list of package extras to install, or 'none' to install no backends
```

#### With `pip` / `pipx`

Alternatively, use `pip` / `pipx` to install [all available backends](https://config-ninja.github.io/config-ninja/config_ninja/contrib.html#available-backends) (or choose a specific one):

```sh
pipx install 'config-ninja[all]'
```

#### With [`uv`](https://github.com/astral-sh/uv)

```sh
uv tool install 'config-ninja[all]'
```

### Enable the `systemd` Service

After installing `config-ninja`, enable it as a `systemd` service for the current user:

```sh
# omit '--user' to install the agent at the system level
config-ninja self install --user
```

## How It Works

To demonstrate how the mechanics work (using the [local backend](https://config-ninja.readthedocs.io/en/latest/config_ninja/contrib/local.html)):

1. create a settings file for `config-ninja`:
   ```sh
   cat <<EOF >config-ninja-settings.yaml
   CONFIG_NINJA_OBJECTS:
   	 example-0:
   		 dest:
   			 format: json
   			 path: ./.local/settings.json
   		 source:
   			 backend: local
   			 format: toml
   			 init:
   				 kwargs:
   					 path: ./.local/config.toml
   EOF
   ```
2. run `config-ninja` in monitor mode:
   ```sh
   config-ninja apply --poll
   ```
3. in a separate shell, create the `config.toml`:
   ```sh
   cat <<EOF >./.local/config.toml
   [example-0]
   a = "first value"
   b = "second value
   EOF
   ```
4. Inspect the `settings.json` file created by `config-ninja`:
   ```sh
   cat ./.local/settings.json
   ```
   ```json
   {
     "example-0": {
       "a": "first value",
       "b": "second value"
     }
   }
   ```
5. Make changes to the data in `config.toml`, and `config-ninja` will update `settings.json` accordingly:
   ```sh
   cat <<EOF >>./.local/config.toml
   [example-1]
   c = "third value"
   d = "fourth value
   EOF
   cat ./.local/settings.json
   ```
   ```json
   {
     "example-0": {
       "a": "first value",
       "b": "second value"
     },
     "example-1": {
       "c": "third value",
       "d": "fourth value"
     }
   }
   ```
   Chances are, you'll want to update the `config-ninja-settings.yaml` file to use a remote backend (instead of `local`). See [config_ninja.contrib](https://config-ninja.github.io/config-ninja/config_ninja/contrib.html) for a list of supported config providers.
