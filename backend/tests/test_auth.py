from shared.auth.jwt import create_access_token, get_password_hash, verify_password


def test_password_hashing():
    password = "test123"
    hashed = get_password_hash(password)
    assert verify_password(password, hashed)
    assert not verify_password("wrong", hashed)


def test_token_creation():
    token = create_access_token({"sub": "test-user", "role": "admin"})
    assert token is not None
    assert isinstance(token, str)
