# `config-ninja`

Manage operating system configuration files based on data in the cloud.

**Usage**:

```console
$ config-ninja [OPTIONS] COMMAND [ARGS]...
```

**Options**:

- `-c, --config PATH`: Path to `config-ninja`'s own configuration file.
- `-v, --version`: Print the version and exit.
- `--install-completion`: Install completion for the current shell.
- `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
- `--help`: Show this message and exit.

**Commands**:

- `apply`: Apply the specified configuration to the system.
- `get`: Print the value of the specified configuration object.
- `monitor`: Apply all configuration objects to the filesystem, and poll for changes.
- `self`: Operate on this installation of `config-ninja`.
- `version`: Print the version and exit.

## `config-ninja apply`

Apply the specified configuration to the system.

**Usage**:

```console
$ config-ninja apply [OPTIONS] [KEY]
```

**Arguments**:

- `[KEY]`: If specified, only apply the configuration object with this key.

**Options**:

- `-p, --poll`: Enable polling; print the configuration on changes.
- `--help`: Show this message and exit.

## `config-ninja get`

Print the value of the specified configuration object.

**Usage**:

```console
$ config-ninja get [OPTIONS] KEY
```

**Arguments**:

- `KEY`: The key of the configuration object to retrieve \[required\]

**Options**:

- `-p, --poll`: Enable polling; print the configuration on changes.
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
- `print`: If specified, only apply the configuration object with this key.
- `uninstall`: Uninstall the `config-ninja` `systemd` service.

### `config-ninja self install`

Install `config-ninja` as a `systemd` service.

Both `--env` and `--var` can be passed multiple times.

Example:

```console
$ config-ninja self install --env FOO,BAR,BAZ --env SPAM --var EGGS=42
```

The environment variables `FOO`, `BAR`, `BAZ`, and `SPAM` will be read from the current shell and written to the service file, while `EGGS` will be set to `42`.

**Usage**:

```console
$ config-ninja self install [OPTIONS]
```

**Options**:

- `-e, --env NAME[,NAME...]`: Embed these environment variables into the unit file. Can be used multiple times.
- `-p, --print-only`: Just print the `config-ninja.service` file; do not write.
- `--run-as user[:group]`: Configure the systemd unit to run the service as this user (and optionally group).
- `-u, --user, --user-mode`: User mode installation (does not require `sudo`)
- `--var VARIABLE=VALUE`: Embed the specified `VARIABLE=VALUE` into the unit file. Can be used multiple times.
- `-w, --workdir PATH`: Run the service from this directory.
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

- `-p, --print-only`: Just print the `config-ninja.service` file; do not write.
- `-u, --user, --user-mode`: User mode installation (does not require `sudo`)
- `--help`: Show this message and exit.

## `config-ninja version`

Print the version and exit.

**Usage**:

```console
$ config-ninja version [OPTIONS]
```

**Options**:

- `--help`: Show this message and exit.
