.PHONY: bootstrap check contract sim-smoke p1-sim test docs-check ci-safety repository-hygiene hardware-lock-check hardware-import-check

PYTHON ?= python3

bootstrap:
	$(PYTHON) scripts/tasks.py bootstrap

check:
	$(PYTHON) scripts/tasks.py check

contract:
	$(PYTHON) scripts/tasks.py contract

sim-smoke:
	$(PYTHON) scripts/tasks.py sim-smoke

p1-sim:
	$(PYTHON) scripts/tasks.py p1-sim

test:
	$(PYTHON) scripts/tasks.py test

docs-check:
	$(PYTHON) scripts/tasks.py docs-check

ci-safety:
	$(PYTHON) scripts/verify_ci_safety.py

repository-hygiene:
	$(PYTHON) scripts/verify_repository_hygiene.py

hardware-lock-check:
	$(PYTHON) scripts/verify_hardware_lock.py

hardware-import-check:
	$(PYTHON) scripts/verify_hardware_imports.py
