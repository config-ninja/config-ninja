# `config-ninja`

Manage operating system configuration files based on data in the cloud.

**Usage**:

```console
$ config-ninja [OPTIONS] COMMAND [ARGS]...
```

**Options**:

- `--settings-file PATH`
- `--version / --no-version`
- `--install-completion`: Install completion for the current shell.
- `--show-completion`: Show completion for the current shell, to copy it or customize the installation.
- `--help`: Show this message and exit.

**Commands**:

- `apply`: Apply the specified configuration to the...
- `get`: Print the value of the specified...
- `monitor`: Apply all configuration objects to the...
- `self`: Operate on [bold blue]config-ninja[/]'s...
- `version`: Print the version and exit.

## `config-ninja apply`

Apply the specified configuration to the system.

**Usage**:

```console
$ config-ninja apply [OPTIONS] KEY
```

**Arguments**:

- `KEY`: [required]

**Options**:

- `--poll / --no-poll`: [default: no-poll]
- `--help`: Show this message and exit.

## `config-ninja get`

Print the value of the specified configuration object.

**Usage**:

```console
$ config-ninja get [OPTIONS] KEY
```

**Arguments**:

- `KEY`: [required]

**Options**:

- `--poll / --no-poll`: [default: no-poll]
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

Operate on [bold blue]config-ninja[/]'s own configuration file.

**Usage**:

```console
$ config-ninja self [OPTIONS] COMMAND [ARGS]...
```

**Options**:

- `--help`: Show this message and exit.

**Commands**:

- `print`: Print the configuration file.

### `config-ninja self print`

Print the configuration file.

**Usage**:

```console
$ config-ninja self print [OPTIONS]
```

**Options**:

- `--help`: Show this message and exit.

## `config-ninja version`

Print the version and exit.

**Usage**:

```console
$ config-ninja version [OPTIONS]
```

**Options**:

- `--help`: Show this message and exit.
