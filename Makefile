.PHONY: help runlocal
.DEFAULT_GOAL := help

define BROWSER_PYSCRIPT
import os, webbrowser, sys

from urllib.request import pathname2url

webbrowser.open("file://" + pathname2url(os.path.abspath(sys.argv[1])))
endef
export BROWSER_PYSCRIPT

define PRINT_HELP_PYSCRIPT
import re, sys

for line in sys.stdin:
	match = re.match(r'^([a-zA-Z_-]+):.*?## (.*)$$', line)
	if match:
		target, help = match.groups()
		print("%-20s %s" % (target, help))
endef
export PRINT_HELP_PYSCRIPT

BROWSER := python -c "$$BROWSER_PYSCRIPT"

help:
	@python -c "$$PRINT_HELP_PYSCRIPT" < $(MAKEFILE_LIST)

clean: ## clean development tree
	rm -fr ${BUILDDIR} ./~build junit.xml build pip-wheel-metadata dist src/*.egg-info .coverage coverage.xml .eggs .pytest_cache *.egg-info
	find src -name __pycache__ -o -name "*.py?" -o -name "*.orig" -prune | xargs rm -rf
	find tests -name __pycache__ -o -name "*.py?" -o -name "*.orig" -prune | xargs rm -rf


i18n:  ## update translation files
	cd src/hope_portal && uv run manage.py makemessages --locale es --locale fr --locale ar --locale pt --ignore '~*'
	uv run manage.py compilemessages


reset_migrations:  ## reset database migrations. WARNING!!: Use only until first deployment
	rm -f src/hope_portal/migrations/000*
	dropdb --if-exists hope_portal
	createdb hope_portal
	./manage.py makemigrations hope_portal
	git add src/hope_portal/migrations/*
	./manage.py develop
