SERVICE = staticnarrative
SERVICE_CAPS = StaticNarrative
SPEC_FILE = StaticNarrative.spec
LIB_DIR = lib
SCRIPTS_DIR = scripts
TEST_DIR = test
TEST_SCRIPT_NAME = run_tests.sh
COMPILE_REPORT = ./compile_report.json

.PHONY: test

default: compile

all: compile set-executable

compile:
	rm $(COMPILE_REPORT) || true
	KB_SDK_COMPILE_REPORT_FILE=$(COMPILE_REPORT) kb-sdk compile $(SPEC_FILE) \
		--verbose \
		--out $(LIB_DIR) \
		--pyclname $(SERVICE_CAPS).$(SERVICE_CAPS)Client \
		--pysrvname $(SERVICE_CAPS).$(SERVICE_CAPS)Server \
		--pyimplname $(SERVICE_CAPS).$(SERVICE_CAPS)Impl;

set-executable:
	chmod +x $(SCRIPTS_DIR)/*.sh
	chmod +x $(TEST_DIR)/$(TEST_SCRIPT_NAME)

test:
	sh $(TEST_DIR)/$(TEST_SCRIPT_NAME)

format:
	ruff format

lint:
	ruff check

lint-fix:
	ruff check --fix
