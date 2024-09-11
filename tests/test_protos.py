from onyx_exchange.v1 import requests_pb2, responses_pb2

def test_protos():
    assert requests_pb2.ExchangeRequest
    assert responses_pb2.ExchangeResponse
