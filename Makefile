BUF := $(HOME)/bin/buf

help:
	@echo ================================================================================
	@fgrep -h "##" $(MAKEFILE_LIST) | fgrep -v fgrep | sed -e 's/\\$$//' | sed -e 's/##//'
	@echo ================================================================================


.PHONY: build-python
compile-protos:		## compile protobuf python stubs
	mkdir -p ./onyx_exchange/protobuf
	poetry run python -m grpc_tools.protoc \
		--proto_path=./protos \
		--python_out=. \
		./protos/onyx_exchange/v1/*.proto


.PHONY: lint
lint:			## lint protobuf definitions
	@cd protos && $(BUF) lint --path onyx_exchange

.PHONY: install-buf
install-buf:		## install buf protobuf tool in ~/bin
	@./.dev/install-buf


install:		## install python packages via poetry
	poetry install --no-root

.PHONY: test
test: 				## run unit tests with poetry
	@./.dev/test

outdated:		## show outdated python packages
	poetry show -o -a
