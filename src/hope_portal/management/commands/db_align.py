from argparse import ArgumentParser
from typing import Any

from django.core.management import BaseCommand, call_command


class Command(BaseCommand):
    help = "Align HOPE unmanaged models with the current HOPE database schema."
    requires_system_checks = []
    requires_migrations_checks = False

    def add_arguments(self, parser: ArgumentParser) -> None:
        parser.add_argument(
            "table",
            action="store",
            nargs="*",
            type=str,
            help="Optional list of tables to introspect. Introspects all configured HOPE tables when omitted.",
        )
        parser.add_argument(
            "--database",
            action="store",
            dest="database",
            default="hope_ro",
            help='Database alias to introspect. Defaults to "hope_ro".',
        )
        parser.add_argument(
            "--schema",
            action="store",
            dest="schema",
            default="public",
            help='Database schema to introspect. Defaults to "public".',
        )
        parser.add_argument(
            "--output-file",
            action="store",
            dest="output_file",
            default="_inspect.py",
            type=str,
            help='Destination filename under "modules/hope/models/". Defaults to "_inspect.py".',
        )

    def handle(self, *args: Any, **options: Any) -> None:
        table: list[str] = options["table"]
        database = options["database"]
        schema = options["schema"]
        output_file = options["output_file"]

        self.stdout.write(
            f"Aligning HOPE schema from database='{database}', schema='{schema}' into '{output_file}'",
            self.style.WARNING,
        )

        call_command(
            "inspect_hope",
            *table,
            database=database,
            schema=schema,
            output_file=output_file,
        )

        self.stdout.write(
            "Schema alignment complete. Restart application workers to load updated models.",
            self.style.SUCCESS,
        )
