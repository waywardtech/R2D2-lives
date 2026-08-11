.PHONY: bootstrap check contract sim-smoke test docs-check

PYTHON ?= python3

bootstrap:
	$(PYTHON) scripts/tasks.py bootstrap

check:
	$(PYTHON) scripts/tasks.py check

contract:
	$(PYTHON) scripts/tasks.py contract

sim-smoke:
	$(PYTHON) scripts/tasks.py sim-smoke

test:
	$(PYTHON) scripts/tasks.py test

docs-check:
	$(PYTHON) scripts/tasks.py docs-check

