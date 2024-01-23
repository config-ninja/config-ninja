# `config-ninja`

Manage operating system configuration files based on data in the cloud.

**Usage**:

```console
$ config-ninja [OPTIONS] COMMAND [ARGS]...
```

**Options**:

- `--config PATH`: Path to `config-ninja`'s own configuration file.
- `--version`: Print the version and exit.
- `--install-completion`: Install completion for the current shell.
- `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
- `--help`: Show this message and exit.

**Commands**:

- `apply`: Apply the specified configuration to the system.
- `get`: Print the value of the specified configuration object.
- `monitor`: Apply all configuration objects to the filesystem, and poll for changes.
- `self`: Operate on this installation of config-ninja.
- `version`: Print the version and exit.

## `config-ninja apply`

Apply the specified configuration to the system.

**Usage**:

```console
$ config-ninja apply [OPTIONS] KEY
```

**Arguments**:

- `KEY`: The key of the configuration object to retrieve [required]

**Options**:

- `--poll`: Enable polling; print the configuration on changes.
- `--help`: Show this message and exit.

## `config-ninja get`

Print the value of the specified configuration object.

**Usage**:

```console
$ config-ninja get [OPTIONS] KEY
```

**Arguments**:

- `KEY`: The key of the configuration object to retrieve [required]

**Options**:

- `--poll`: Enable polling; print the configuration on changes.
- `--help`: Show this message and exit.

## `config-ninja monitor`

Apply all configuration objects to the filesystem, and poll for changes.

**Usage**:

```console
$ config-ninja monitor [OPTIONS]
```

**Options**:

- `--help`: Show this message and exit.

## `config-ninja self`

Operate on this installation of `config-ninja`.

**Usage**:

```console
$ config-ninja self [OPTIONS] COMMAND [ARGS]...
```

**Options**:

- `--help`: Show this message and exit.

**Commands**:

- `install`: Install `config-ninja` as a `systemd` service.
- `print`: Print the configuration file.
- `uninstall`: Uninstall the `config-ninja` `systemd` service.

### `config-ninja self install`

Install `config-ninja` as a `systemd` service.

The `--env` argument can be passed multiple times with comma-separated strings.

Example:

```console
$ config-ninja self install --env FOO,BAR,BAZ --env SPAM --env EGGS
```

The environment variables `FOO`, `BAR`, `BAZ`, `SPAM`, and `EGGS` will be read from the current shell and written to the service file.

**Usage**:

```console
$ config-ninja self install [OPTIONS]
```

**Options**:

- `--env-names TEXT`: Embed these environment variables into the unit file.
- `--print-only`: Just print the `config-ninja.service` file; do not write.
- `--user`: User mode installation (does not require `sudo`)
- `--workdir PATH`: Run the service from this directory.
- `--help`: Show this message and exit.

### `config-ninja self print`

Print `config-ninja`'s settings.

**Usage**:

```console
$ config-ninja self print [OPTIONS]
```

**Options**:

- `--help`: Show this message and exit.

### `config-ninja self uninstall`

Uninstall the `config-ninja` `systemd` service.

**Usage**:

```console
$ config-ninja self uninstall [OPTIONS]
```

**Options**:

- `--print-only`: Just print the `config-ninja.service` file; do not write.
- `--user`: User mode installation (does not require `sudo`)
- `--help`: Show this message and exit.

## `config-ninja version`

Print the version and exit.

**Usage**:

```console
$ config-ninja version [OPTIONS]
```

**Options**:

- `--help`: Show this message and exit.
