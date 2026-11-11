from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def test_hash_is_not_plaintext_and_is_salted():
    h1 = hash_password("correct horse")
    h2 = hash_password("correct horse")
    assert h1 != "correct horse"
    assert h1 != h2  # 每次 salt 不同


def test_verify_password():
    h = hash_password("correct horse")
    assert verify_password("correct horse", h) is True
    assert verify_password("wrong", h) is False


def test_token_roundtrip():
    token = create_access_token("user-123")
    assert decode_access_token(token) == "user-123"


def test_tampered_token_is_rejected():
    token = create_access_token("user-123")
    assert decode_access_token(token + "x") is None


def test_expired_token_is_rejected():
    token = create_access_token("user-123", expires_minutes=-1)
    assert decode_access_token(token) is None