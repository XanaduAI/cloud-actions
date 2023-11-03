# Install Python Poetry

This action will install and setup [python-poetry](https://python-poetry.org/).

Unlike [snok/install-poetry](https://github.com/snok/install-poetry), this action does NOT
rely on the [poetry installer](https://install.python-poetry.org/).

The poetry installer is recommended for desktop and personal usage, in CI environments, it is best
to setup poetry from Pypi for maximum control. There have been issues where CI builds failed as 
`install.python-poetry.org` was down.

```yaml
- uses: actions/checkout@v4
- uses: actions/setup-python@v4
- uses: XanaduAI/cloud-actions/install-python-poetry@main
- run: poetry --version
```

## Inputs

### Install a specific version of Poetry
By default, the latest version of poetry available on Pypi is installed.
But you can pass a specific version to install, this is recommended in CI as it would
make the builds more deterministic.
```yaml
- uses: XanaduAI/cloud-actions/install-python-poetry@main
  with:
    poetry_version: 1.6.2
```

### Install poetry to a specific directory
The default installation directory is within `/tmp/`. But you can
change it using `poetry_home`:
```yaml
- uses: XanaduAI/cloud-actions/install-python-poetry@main
  with:
    poetry_version: 1.6.2
    poetry_home: /some/other/directory
```
A python venv is created in the directory, and poetry is installed within that venv.
This ensures that poetry and the calling workflow python packages do not intermix as
that may lead to poetry attempting to manage it's own dependencies (and can break).

### Adding poetry to PATH
The default behavior is to add poetry to PATH by creating a symlink.
This action does NOT update PATH as it can change the python interpreter that
is being used by the calling workflow. The symlink is created to `/usr/local/bin/poetry`.
In case you do not want to create the symlink, use the input `add_poetry_to_path` to toggle the behavior.
If this is set to false, you have to invoke poetry by calling the binary directly.
```yaml
- uses: XanaduAI/cloud-actions/install-python-poetry@main
  id: setup_poetry
  with:
    poetry_version: 1.6.2
    poetry_home: /some/other/directory
    add_poetry_to_path: false

- run: ${{ steps.setup_poetry.outputs.poetry_bin }} --version
```


## Outputs:

- `poetry_home` -> The directory where poetry is installed
- `poetry_bin` -> Path to the poetry binary ($POETRY_HOME/bin/poetry)


