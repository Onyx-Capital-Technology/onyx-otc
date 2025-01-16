from onyx_otc.v2 import requests_pb2, responses_pb2


def test_protos() -> None:
    assert requests_pb2.OtcRequest is not None
    assert responses_pb2.OtcResponse is not None
