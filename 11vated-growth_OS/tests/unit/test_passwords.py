"""Password hashing and strength policy."""

from growthos.security.passwords import (
    hash_password,
    is_strong_password,
    verify_password,
)


def test_hash_and_verify_roundtrip():
    hashed = hash_password("CorrectHorse9Battery")
    assert hashed != "CorrectHorse9Battery"
    assert verify_password(hashed, "CorrectHorse9Battery")
    assert not verify_password(hashed, "wrong-password")


def test_strong_password_policy():
    assert is_strong_password("StrongPass123")
    assert not is_strong_password("short1A")  # too short
    assert not is_strong_password("alllowercase123")  # no upper
    assert not is_strong_password("ALLUPPERCASE123")  # no lower
    assert not is_strong_password("NoDigitsHere")  # no digit
