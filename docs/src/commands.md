# Management Commands

This project provides the following management commands:

## inspect_hope

This command introspects the database tables in the given database/schema and outputs a Django model module.

### Arguments

-   `table`: Selects what tables or views should be introspected.
-   `--database`: Nominates a database to introspect. Defaults to using the "default" database.
-   `--schema`: Nominates a schema to introspect. Defaults to using the "public" schema.
-   `--output-file`: The name of the output file.

## develop

This command configures the development environment. It runs the `upgrade` command, configures the site settings, creates a default group, and sets up flags.

## upgrade

This command runs migrations, creates extra permissions, and removes stale content types. It can also create a superuser if the `admin-email` and `admin-password` are provided.

### Arguments

-   `--with-checks`: Run checks.
-   `--no-migrate`: Do not run migrations.
-   `--prompt`: Let ask for confirmation.
-   `--debug`: debug mode.
-   `--no-static`: Do not run collectstatic.
-   `--admin-email`: Admin email.
-   `--admin-password`: Admin password.

## db_align

This command aligns unmanaged HOPE models with the current HOPE database schema by regenerating `modules/hope/models/_inspect.py`.

### Arguments

-   `table`: Optional list of tables to introspect. If omitted, all configured HOPE tables are introspected.
-   `--database`: Database alias to introspect. Defaults to `hope_ro`.
-   `--schema`: Schema to introspect. Defaults to `public`.
-   `--output-file`: Destination filename under `modules/hope/models/`. Defaults to `_inspect.py`.
