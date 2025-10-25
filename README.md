# Hope Beneficiary Portal


[![Test](https://github.com/unicef/hope-beneficiary-portal/actions/workflows/test.yml/badge.svg)](https://github.com/unicef/hope-beneficiary-portal/actions/workflows/test.yml)
[![Lint](https://github.com/unicef/hope-beneficiary-portal/actions/workflows/lint.yml/badge.svg)](https://github.com/unicef/hope-beneficiary-portal/actions/workflows/lint.yml)
[![codecov](https://codecov.io/github/unicef/hope-beneficiary-portal/graph/badge.svg?token=FBUB7HML5S)](https://codecov.io/github/unicef/hope-beneficiary-portal)
[![Documentation](https://github.com/unicef/hope-beneficiary-portal/actions/workflows/docs.yml/badge.svg)](https://unicef.github.io/hope-beneficiary-portal/)
[![Pypi](https://badge.fury.io/py/unicef-hope-beneficiary-portal.svg)](https://badge.fury.io/py/unicef-hope-beneficiary-portal)
[![Docker Pulls](https://img.shields.io/docker/pulls/unicef/hope-beneficiary-portal)](https://hub.docker.com/repository/docker/unicef/hope-beneficiary-portal/tags)

## Contributing

### Requirements

- [uv](https://docs.astral.sh/uv/)
- [direnv](https://direnv.net/)

### Checkout and configure development environment

```shell

    git checkout https://github.com/unicef/hope-beneficiary-portal.git
    cd hope-beneficiary-portal
    uv venv .venv
    uv sync

    ./manage.py env --develop > .envrc  # create initial development configuration
    direnv allow .  # enable enviroment
    createdb hope_portal  # create postgres database on localhost

```
