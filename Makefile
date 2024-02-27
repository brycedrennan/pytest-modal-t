SHELL := /bin/bash
python_version = 3.11.8
venv_prefix = pytest-modal
venv_name = $(venv_prefix)-$(python_version)
pyenv_instructions=https://github.com/pyenv/pyenv#installation
pyenv_virt_instructions=https://github.com/pyenv/pyenv-virtualenv#pyenv-virtualenv
requirements_file = tests/requirements-dev.txt

init: require_pyenv  ## Setup a dev environment for local development.
	# 3.11 on arm64 requires sudo use. see https://github.com/pyenv/pyenv/issues/2588
	@if ! pyenv versions --skip-envs --skip-aliases --bare | grep -q $(python_version); then \
		echo "Python $(python_version) not found. Installing..."; \
		sudo pyenv install $(python_version) -s; \
		sudo chown $$USER:$(id -gn) /Users/$$USER/.pyenv/versions/$(python_version); \
		echo -e "\033[0;32m ✔️  🐍 $(python_version) installed \033[0m"; \
	else \
		echo -e "\033[0;32m ✔️  🐍 $(python_version) is already installed. Skipping installation. \033[0m"; \
	fi;
	@if ! [ -d "$$(pyenv root)/versions/$(venv_name)" ]; then\
		pyenv virtualenv $(python_version) $(venv_name);\
	fi;
	@pyenv local $(venv_name)
	@echo -e "\033[0;32m ✔️  🐍 $(venv_name) virtualenv activated \033[0m"
	@pip install --upgrade pip-tools
	@if [ -f "$(requirements_file)" ]; then\
		pip-sync $(requirements_file);\
	fi
	#pip install -e .
	# the compiled requirements don't included OS specific subdependencies so we trigger those this way
	# pip install `pip freeze | grep "^torch=="`
	@echo -e "\nEnvironment setup! ✨ 🍰 ✨ 🐍 \n\nCopy this path to tell PyCharm where your virtualenv is. You may have to click the refresh button in the pycharm file explorer.\n"
	@echo -e "\033[0;32m"
	@pyenv which python
	@echo -e "\n\033[0m"
	@echo -e "The following commands are available to run in the Makefile\n"
	@make -s help

af: autoformat  ## Alias for `autoformat`
autoformat:  ## Run the autoformatter.
	@-ruff check --config tests/ruff.toml . --fix-only
	@ruff format --config tests/ruff.toml .

test:  ## Run the tests.
	@pytest
	@echo -e "The tests pass! ✨ 🍰 ✨"

test-fast:  ## Run the fast tests.
	@pytest -m "not gputest"
	@echo -e "The non-gpu tests pass! ✨ 🍰 ✨"

lint:  ## Run the code linter.
	@ruff check --config tests/ruff.toml .
	@echo -e "No linting errors - well done! ✨ 🍰 ✨"

type-check: ## Run the type checker.
	@mypy --config-file tox.ini .

check-fast:  ## Run autoformatter, linter, typechecker, and fast tests
	@make autoformat
	@make lint
	@make type-check
	@make test-fast

build-pkg:  ## Build the package
	python setup.py sdist bdist_wheel
	python setup.py bdist_wheel --plat-name=win-amd64

deploy:  ## Deploy the package to pypi.org
	pip install twine wheel
	-git tag $$(python setup.py -V)
	git push --tags
	rm -rf dist
	make build-pkg
	#python setup.py sdist
	@twine upload --verbose dist/* -u __token__;
	rm -rf build
	rm -rf dist
	@echo "Deploy successful! ✨ 🍰 ✨"

requirements:  ## Freeze the requirements.txt file
	pip-compile tests/requirements-dev.in --output-file=tests/requirements-dev.txt --upgrade --resolver=backtracking

require_pyenv:
	@if ! [ -x "$$(command -v pyenv)" ]; then\
	  echo -e '\n\033[0;31m ❌ pyenv is not installed.  Follow instructions here: $(pyenv_instructions)\n\033[0m';\
	  exit 1;\
	else\
	  echo -e "\033[0;32m ✔️  pyenv installed\033[0m";\
	fi

.PHONY: docs

docs:
	mkdocs serve


help: ## Show this help message.
	@## https://gist.github.com/prwhite/8168133#gistcomment-1716694
	@echo -e "$$(grep -hE '^\S+:.*##' $(MAKEFILE_LIST) | sed -e 's/:.*##\s*/:/' -e 's/^\(.\+\):\(.*\)/\\x1b[36m\1\\x1b[m:\2/' | column -c2 -t -s :)" | sort