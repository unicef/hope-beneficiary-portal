# Contributing

## Requirements

- [uv](https://docs.astral.sh/uv/)
- [direnv](https://direnv.net/)

## Checkout and configure development environment

```shell

    git checkout https://github.com/unicef/hope-beneficiary-portal.git
    cd hope-beneficiary-portal
    uv venv .venv
    uv sync

    ./manage.py env --develop > .envrc  # create initial development configuration
    direnv allow .  # enable enviroment
    createdb hope_portal  # create postgres database on localhost

```

## Running the tests

To run the tests, you can use the following command:

```shell
    pytest
```

## Code style

This project uses `ruff` to enforce code style. You can run the linter with the following command:

```shell
    ruff check .
```
