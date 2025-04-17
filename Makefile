BUF := $(HOME)/bin/buf

help:
	@echo ================================================================================
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'
	@echo ================================================================================


.PHONY: compile-protos
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
	poetry install

.PHONY: install-all
install-all:		## install python all packages via poetry
	poetry install --all-extras

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

.PHONY: docs
docs:			## build documentation
	@poetry run mkdocs build

.PHONY: docs-publish
docs-publish:		## publish the book to github pages
	poetry run mkdocs gh-deploy

.PHONY: docs-serve
docs-serve:		## serve documentation
	@poetry run mkdocs serve --watch onyx_otc
