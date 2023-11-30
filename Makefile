SERVICE = staticnarrative
SERVICE_CAPS = StaticNarrative
SPEC_FILE = StaticNarrative.spec
URL = https://kbase.us/services/staticnarrative
DIR = $(shell pwd)
LIB_DIR = lib
SCRIPTS_DIR = scripts
TEST_DIR = test
LBIN_DIR = bin
WORK_DIR = /kb/module/work/tmp
EXECUTABLE_SCRIPT_NAME = run_$(SERVICE_CAPS)_async_job.sh
STARTUP_SCRIPT_NAME = start_server.sh
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
		--pysrvname $(SERVICE_CAPS).$(SERVICE_CAPS)Server \
		--pyimplname $(SERVICE_CAPS).$(SERVICE_CAPS)Impl;

set-executable:
	chmod +x $(SCRIPTS_DIR)/entrypoint.sh
	chmod +x $(LBIN_DIR)/$(EXECUTABLE_SCRIPT_NAME)
	chmod +x $(SCRIPTS_DIR)/$(STARTUP_SCRIPT_NAME)
	chmod +x $(TEST_DIR)/$(TEST_SCRIPT_NAME)

test:
	sh $(TEST_DIR)/$(TEST_SCRIPT_NAME)

clean:
	rm -rfv $(LBIN_DIR)
