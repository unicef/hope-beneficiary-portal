import os
import sys
import time
from pathlib import Path

from constance.test import override_config
from faker import Faker

import pytest

faker = Faker()


def _setup_models():
    import django
    from django.apps import apps
    from django.conf import settings
    from django.db import connection
    from django.db.backends.utils import truncate_name
    from django.db.models import Model

    database_name = "_test_portal"
    settings.POWER_QUERY_DB_ALIAS = "default"
    settings.DATABASES["default"]["NAME"] = database_name
    settings.DATABASES["default"]["TEST"] = {
        "NAME": database_name,
        "MIRROR": False,
        "CHARSET": "utf8",
        "MIGRATE": True,
    }

    settings.DATABASE_ROUTERS = ()
    del settings.DATABASES["hope_ro"]
    django.setup()

    for m in apps.get_app_config("hope").get_models():
        if m._meta.proxy:
            opts = m._meta.proxy_for_model._meta
        else:
            opts = m._meta
        if opts.app_label not in ("contenttypes", "sites"):
            db_table = ("_hope_ro__{0.app_label}_{0.model_name}".format(opts)).lower()
            m._meta.db_table = truncate_name(db_table, connection.ops.max_name_length())
            m._meta.managed = True
            m.save = Model.save


def pytest_addoption(parser):
    pass


def pytest_configure(config):
    here = Path(__file__).parent
    root = here.parent
    sys.path.insert(0, str(here / "extras"))
    sys.path.insert(0, str(root / "src"))
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "hope_portal.config.settings")
    _setup_models()

    from django.conf import settings

    settings.CSRF_COOKIE_SECURE = False
    settings.SESSION_COOKIE_SECURE = False
    settings.CACHE_PREFIX = str(time.time())


@pytest.fixture(autouse=True)
def enable_flow_flags():
    from django.conf import settings

    original_flags = dict(getattr(settings, "FLAGS", {}))
    settings.FLAGS.update(
        {
            "FLOW_START_REGISTRATION": [("boolean", True)],
            "FLOW_START_SMS": [("boolean", True)],
            "FLOW_START_EMAIL": [("boolean", True)],
            "FLOW_START_AUTH": [("boolean", True)],
            "FLOW_ACCOUNT_CREATE": [("boolean", True)],
            "FLOW_ASK": [("boolean", True)],
            "FLOW_INFO": [("boolean", True)],
        }
    )

    yield

    settings.FLAGS = original_flags


@pytest.fixture(autouse=True)
def _default_name_questions_enabled_for_tests():
    """VERIFICATION_ENABLE_NAME_QUESTIONS defaults to False in the app (see constance.py),
    but most of the test suite uses given/middle/last name as its go-to field for generic
    question-generation mechanics, predating that toggle. Keep that working by default here;
    tests exercising the toggle itself override it explicitly with @override_config."""
    with override_config(VERIFICATION_ENABLE_NAME_QUESTIONS=True):
        yield
