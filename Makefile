BUF := $(HOME)/bin/buf

help:
	@echo ================================================================================
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'
	@echo ================================================================================


.PHONY: build-python
compile-protos:		## compile protobuf python stubs
	poetry run python -m grpc_tools.protoc \
		--proto_path=./protos \
		--python_out=. \
		--mypy_out=. \
		--mypy_grpc_out=. \
		./protos/onyx_otc/v2/*.proto

.PHONY: install-buf
install-buf:		## install buf protobuf tool in ~/bin
	@./.dev/install-buf

.PHONY: install
install:		## install python packages via poetry
	poetry install --no-root

.PHONY: lint-proto
lint-proto:		## lint protobuf definitions
	@cd protos && $(BUF) lint --path onyx_otc

.PHONY: lint-py
lint-py:		## lint and fix python code
	@poetry run ./.dev/lint fix

.PHONY: lint-py-check
lint-py-check:		## check linting for python code
	@poetry run ./.dev/lint

.PHONY: test
test: 			## run unit tests with poetry
	@./.dev/test

outdated:		## show outdated python packages
	poetry show -o -a
