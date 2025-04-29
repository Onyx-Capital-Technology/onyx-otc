# Onyx Websocket API v2

[![PyPI version](https://badge.fury.io/py/onyx-otc.svg)](https://badge.fury.io/py/onyx-otc)
[![Python versions](https://img.shields.io/pypi/pyversions/onyx-otc.svg)](https://pypi.org/project/onyx-otc)
[![Python downloads](https://img.shields.io/pypi/dd/onyx-otc.svg)](https://pypi.org/project/onyx-otc)
[![build](https://github.com/Onyx-Capital-Technology/onyx-otc/actions/workflows/build.yml/badge.svg)](https://github.com/Onyx-Capital-Technology/onyx-otc/actions/workflows/build.yml)


The websocket API v2 support both JSON and [Protobuf](https://protobuf.dev/) (binary) encoding. The protobuf encoding is more efficient and faster than JSON encoding.


| Environment | Protocol | URL                                  |
|-------------|----------|--------------------------------------|
| Production  | JSON     | wss://ws.onyxhub.co/stream/v2        |
| Production  | Protobuf | wss://ws.onyxhub.co/stream/v2/binary |
| UAT  | JSON     | wss://ws.uat.onyxhub.co/stream/v2        |
| UAT  | Protobuf | wss://ws.uat.onyxhub.co/stream/v2/binary |


## Installation

Install the library via pip:

```bash
pip install onyx-otc
```

To install the library with command line support

```bash
pip install onyx-otc[cli]
```


## Example

Install the library with command line support and run the client:

```bash
onyx --help
```

Stream tickers for a list of product symbols.

```bash
onyx stream -t ebob -t brt
```

Stream tradable quotes for a list of contract symbols.

```bash
onyx stream -r brtm25@ice -r ebobm25@ice
```

## Protobuf support

The binary endpoints uses protobuf encoding and the definitions are available in the [protos/onyx_otc/v2](https://github.com/Onyx-Capital-Technology/onyx-otc/tree/main/protos/onyx_otc/v2) directory.

## Other resources

* [Onyx Flux Rest API docs](https://api.onyxhub.co/v1/docs)
* [Onyx Flux web app](https://www.onyxcapitalgroup.com/flux)
