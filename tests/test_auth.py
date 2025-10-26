import time
from backend.auth import generate_token, decode_token


def test_token_encode_decode():
    payload = {'user_id': 1, 'role': 'test'}
    token = generate_token(payload, expires_in=5)  # short TTL for test
    assert token is not None

    decoded = decode_token(token)
    assert decoded is not None
    assert decoded.get('user_id') == 1
    assert decoded.get('role') == 'test'


def test_token_expiration():
    payload = {'user_id': 2}
    token = generate_token(payload, expires_in=1)
    assert token is not None
    # valid immediately
    assert decode_token(token) is not None
    # wait for it to expire
    time.sleep(1.5)
    assert decode_token(token) is None
