CODE = cli db manager storage

VENV ?= .venv
JOBS ?= 4

UID := $(shell id -u)
GID := $(shell id -g)


pre-init:
	sudo apt install python3.8 python3.8-venv python3.8-dev python3.8-distutils gcc

init:
	python3.8 -m venv $(VENV)
	$(VENV)/bin/python -m pip install --upgrade pip
	$(VENV)/bin/python -m pip install poetry
	$(VENV)/bin/poetry install

lint:
# 	$(VENV)/bin/black --skip-string-normalization --check $(CODE)
# 	$(VENV)/bin/flake8 --jobs $(JOBS) --statistics --show-source $(CODE)
# 	$(VENV)/bin/mypy $(CODE)

pretty:
	$(VENV)/bin/isort --apply --recursive $(CODE)
	$(VENV)/bin/black --skip-string-normalization $(CODE)

precommit_install:
	@git init
	echo '#!/bin/sh\nmake lint\n' > .git/hooks/pre-commit
	chmod +x .git/hooks/pre-commit
