from otc.v1 import requests_pb2, responses_pb2

def test_protos():
    assert requests_pb2.OtcRequest
    assert responses_pb2.OtcResponse
