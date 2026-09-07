from app.security import hash_password, verify_password


def test_passwords_are_hashed_and_verifiable():
    encoded = hash_password("verdant-demo")
    assert encoded != "verdant-demo"
    assert verify_password("verdant-demo", encoded)
    assert not verify_password("wrong-password", encoded)
