$(VENV_DIR).DEFAULT_GOAL := help

PYTHON_BIN=python3.9
VENV_DIR=./.venv
BIN_DIR=./bin


define HELP_BODY
Please use 'make [target]'. Available targets:

QUALITY CONTROL
test                 Run tests; pass args to pytest with 'args=[pytest args]'
fmt                  Apply formatters; use with check=1 to check instead of modify
clean                Remove artifcats in $(VENV_DIR)
endef


.PHONY: help
help:
	@: $(info $(HELP_BODY))

$(VENV_DIR):
	$(PYTHON_BIN) -m venv $(VENV_DIR)
	$@/bin/pip install --upgrade pip
	$@/bin/pip install wheel
	$@/bin/pip install --no-cache -r requirements.txt


.PHONY: test
test: $(VENV_DIR)
	$(VENV_DIR)/bin/pytest $(args)


.PHONY: fmt
fmt: $(VENV_DIR)
ifdef check
	$(VENV_DIR)/bin/black --check src tests
	$(VENV_DIR)/bin/isort --check src tests
else
	$(VENV_DIR)/bin/black src tests
	$(VENV_DIR)/bin/isort src tests
endif


.PHONY: clean
clean:
	rm -rf $(VENV_DIR)
	rm -rf $(BIN_DIR)
