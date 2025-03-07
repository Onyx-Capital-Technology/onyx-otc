# Onyx OTC

[![PyPI version](https://badge.fury.io/py/onyx-otc.svg)](https://badge.fury.io/py/onyx-otc)
[![Python versions](https://img.shields.io/pypi/pyversions/onyx-otc.svg)](https://pypi.org/project/onyx-otc)
[![Python downloads](https://img.shields.io/pypi/dd/onyx-otc.svg)](https://pypi.org/project/onyx-otc)
[![build](https://github.com/Onyx-Capital-Technology/onyx-otc/actions/workflows/build.yml/badge.svg)](https://github.com/Onyx-Capital-Technology/onyx-otc/actions/workflows/build.yml)

* [Onyx Flux Rest API docs](https://api.onyxhub.co/v1/docs)
* [Onyx Flux Websocket API v2 docs](https://ws.dev.onyxhub.co/doc/v2)
* [Onyx Flux web app](https://www.onyxcapitalgroup.com/flux)

## Websocket API v2

The websocket API v2 support both JSON and protobuf (binary) encoding. The protobuf encoding is more efficient and faster than JSON encoding.


## Example

The examples directory contains a simple example of how to use the websocket API v2.

To use the example, first install the all packages via

```bash
make install-all
```

Then run the example with the following command:

```bash
python examples/wsv2.py --help
```

Stream tickers for a list of product symbols.

```bash
python examples/wsv2.py -t ebob -t brt
```

Stream tradable quotes for a list of contract symbols.

```bash
python examples/wsv2.py -r brtm25@ice -r ebobm25@ice
```
