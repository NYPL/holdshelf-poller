.DEFAULT: help

help:
	@echo "make help"
	@echo "    display this help statement"
	@echo "make test"
	@echo "    run associated test suite with pytest"
	@echo "make test-verbose"
	@echo "    run associated test suite with pytest in verbose mode with full stdout"
	@echo "make lint"
	@echo "    lint project files using the flake8 linter"

test:
	pytest

test-verbose:
	pytest -v -r P

lint:
	flake8 --exclude *env
