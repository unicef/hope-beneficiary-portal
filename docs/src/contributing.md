# Contributing

## Requirements

- [uv](https://docs.astral.sh/uv/)
- [direnv](https://direnv.net/)

## Checkout and configure development environment

``` shell

    git checkout https://github.com/unicef/hope-beneficiary-portal.git
    cd hope-beneficiary-portal
    uv venv .venv
    uv sync
    pre-commit install
    ./manage.py env --develop > .envrc  # create initial development configuration
    direnv allow .  # enable enviroment
    createdb hope_portal  # create postgres database on localhost

```

### Develop Frontend

This project uses [Tailwind CSS](https://tailwindcss.com/) and [django-tailwind](https://github.com/timonweb/django-tailwind)
to manege theme and CSS. If you need to work on the UI  you can either:

- Run `./manage.py tailwind start` in another shell

OR

- Run `./manage.py tailwind dev` instead of `./manage.py runserver`


Both the solutions will monitor the filesystem fo any changes on the source tree and rebuild the CSS if needed.

!!! note
    If you want to make the browser auto-reload the current page on source changes just add this entry to your `.envrc`:

        export EXTRA_MIDDLEWARES="django_browser_reload.middleware.BrowserReloadMiddleware,"




## Running the tests

To run the tests, you can use the following command:

``` shell
    pytest
```

## Code style

This project uses `ruff` to enforce code style. You can run the linter with the following command:

``` shell
    ruff check .
```
