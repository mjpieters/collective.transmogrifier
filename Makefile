### Defensive settings for make:
#     https://tech.davis-hansson.com/p/make/
SHELL:=bash
.ONESHELL:
.SHELLFLAGS:=-xeu -o pipefail -O inherit_errexit -c
.SILENT:
.DELETE_ON_ERROR:
MAKEFLAGS+=--warn-undefined-variables
MAKEFLAGS+=--no-builtin-rules

# We like colors
# From: https://coderwall.com/p/izxssa/colored-makefile-for-golang-projects
RED=`tput setaf 1`
GREEN=`tput setaf 2`
RESET=`tput sgr0`
YELLOW=`tput setaf 3`

PLONE5=5.2-latest
PLONE6=6.0-latest

CODE_QUALITY_VERSION=1.0.1
LINT=docker run --rm -v "$(PWD)":/github/workspace plone/code-quality:${CODE_QUALITY_VERSION} check

PACKAGE_NAME=collective.transmogrifier
PACKAGE_PATH=src/
CHECK_PATH=setup.py docs/source/conf.py $(PACKAGE_PATH)

all: build

# Add the following 'help' target to your Makefile
# And add help text after each target name starting with '\#\#'
.PHONY: help
help: ## This help message
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "\033[36m%-30s\033[0m %s\n", $$1, $$2}'

bin/pip:
	@echo "$(GREEN)==> Setup Virtual Env$(RESET)"
	python3.11 -m venv .
	bin/pip install -U pip wheel

bin/black bin/isort bin/pyroma bin/zpretty: bin/pip
	@echo "$(GREEN)==> Install Code Quality tools$(RESET)"
	bin/pip install -r https://raw.githubusercontent.com/plone/code-quality/v$(CODE_QUALITY_VERSION)/requirements.txt
	@echo "$(GREEN)==> Install pre-commit hook$(RESET)"
	echo -e '#!/usr/bin/env bash\nmake lint' > .git/hooks/pre-commit && chmod ug+x .git/hooks/pre-commit

.PHONY: build-plone-5.2
build-plone-5.2: bin/pip bin/black ## Build Plone 5.2
	@echo "$(GREEN)==> Build with Plone 5.2$(RESET)"
	bin/pip install Plone -c https://dist.plone.org/release/$(PLONE5)/constraints.txt
	bin/pip install -e ".[test]"
	bin/mkwsgiinstance -d . -u admin:admin

.PHONY: build-plone-6.0
build-plone-6.0: bin/pip bin/black ## Build Plone 6.0
	@echo "$(GREEN)==> Build with Plone 6.0$(RESET)"
	bin/pip install Plone -c https://dist.plone.org/release/$(PLONE6)/constraints.txt
	bin/pip install -e ".[test]"
	bin/mkwsgiinstance -d . -u admin:admin

.PHONY: build
build: build-plone-6.0 ## Build Plone 6.0

.PHONY: clean
clean: ## Remove old virtualenv and creates a new one
	@echo "$(RED)==> Cleaning environment and build$(RESET)"
	rm -rf bin lib lib64 include share etc var inituser pyvenv.cfg .installed.cfg

.PHONY: black
black: bin/black ## Format codebase
	bin/black $(CHECK_PATH)

.PHONY: isort
isort: bin/isort ## Format imports in the codebase
	bin/isort $(CHECK_PATH)

zpretty: bin/zpretty ## Format xml and zcml with zpretty
	find "${PACKAGE_PATH}" -name '*.xml' | xargs bin/zpretty -x -i
	find "${PACKAGE_PATH}" -name '*.zcml' | xargs bin/zpretty -z -i

.PHONY: format
format: black isort zpretty ## Format the codebase according to our standards

.PHONY: lint
lint: lint-isort lint-black lint-flake8 lint-zpretty ## check code style

.PHONY: lint-black
lint-black: ## validate black formating
	$(LINT) black "$(CHECK_PATH)"

.PHONY: lint-flake8
lint-flake8: ## validate black formating
	$(LINT) flake8 "$(CHECK_PATH)"

.PHONY: lint-isort
lint-isort: ## validate using isort
	$(LINT) isort "$(CHECK_PATH)"

.PHONY: lint-pyroma
lint-pyroma: ## validate using pyroma
	$(LINT) .

.PHONY: lint-zpretty
lint-zpretty: ## validate ZCML/XML using zpretty
	$(LINT) zpretty "$(PACKAGE_PATH)"

.PHONY: test
test: ## run tests
	PYTHONWARNINGS=ignore ./bin/zope-testrunner --auto-color --auto-progress --test-path $(PACKAGE_PATH)

.PHONY: start
start: ## Start a Plone instance on localhost:8080
	PYTHONWARNINGS=ignore ./bin/runwsgi etc/zope.ini
