"""Unit tests for Revenue Scout pure logic (no DB)."""

from __future__ import annotations

from growthos.services.scout import _domain_of, _fingerprint, _normalize_email


def test_normalize_email_lowercases_and_strips() -> None:
    assert _normalize_email("  Jane@Example.COM ") == "jane@example.com"
    assert _normalize_email(None) is None


def test_domain_of_website() -> None:
    assert _domain_of("https://www.joesdental.com/contact") == "joesdental.com"
    assert _domain_of("http://acme.co") == "acme.co"
    assert _domain_of(None) is None


def test_fingerprint_is_stable_and_sensitive() -> None:
    a = _fingerprint("Hi Joe, I noticed your website has no booking form.")
    b = _fingerprint("Hi Joe, I noticed your website has no booking form.")
    c = _fingerprint("Hi Sam, I saw your restaurant listing in OpenStreetMap.")
    assert a == b
    assert a != c
    assert len(a) == 16
