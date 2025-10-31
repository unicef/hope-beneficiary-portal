# Hope Beneficiary Portal


[![Test](https://github.com/unicef/hope-beneficiary-portal/actions/workflows/test.yml/badge.svg)](https://github.com/unicef/hope-beneficiary-portal/actions/workflows/test.yml)
[![Lint](https://github.com/unicef/hope-beneficiary-portal/actions/workflows/lint.yml/badge.svg)](https://github.com/unicef/hope-beneficiary-portal/actions/workflows/lint.yml)
[![codecov](https://codecov.io/github/unicef/hope-beneficiary-portal/graph/badge.svg?token=FBUB7HML5S)](https://codecov.io/github/unicef/hope-beneficiary-portal)
[![Documentation](https://github.com/unicef/hope-beneficiary-portal/actions/workflows/docs.yml/badge.svg)](https://unicef.github.io/hope-beneficiary-portal/)
[![Pypi](https://badge.fury.io/py/unicef-hope-beneficiary-portal.svg)](https://badge.fury.io/py/unicef-hope-beneficiary-portal)

## About

HOPE Beneficiary Portal is beneficiary oriented application that allow beneficiaries to collect retrieve the data that the system knows about them.

The system ask the registration number of the beneficiary and after provided the user is asked to answer some question about the in found house.
If the user answer to all the questions it would be redirected to a page with he will find all the information about his payment and data that the system knows about him.

There is a safety guard that allows each registration number to be attempt only a limited number of times per day.


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
