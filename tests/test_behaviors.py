"""Behaviour-layer stories: pure domain function tests."""

from __future__ import annotations

import pytest

from bitranox_template_py_cli.domain import behaviors


@pytest.mark.os_agnostic
def test_build_greeting_returns_canonical_text() -> None:
    """Verify build_greeting returns the canonical greeting string."""
    assert behaviors.build_greeting() == "Hello World"


@pytest.mark.os_agnostic
def test_build_greeting_returns_str() -> None:
    """build_greeting must return a str instance."""
    assert isinstance(behaviors.build_greeting(), str)


@pytest.mark.os_agnostic
def test_canonical_greeting_constant_value() -> None:
    """CANONICAL_GREETING must be the expected literal."""
    assert behaviors.CANONICAL_GREETING == "Hello World"


@pytest.mark.os_agnostic
def test_build_greeting_uses_canonical_constant() -> None:
    """build_greeting must return the same object as CANONICAL_GREETING."""
    assert behaviors.build_greeting() is behaviors.CANONICAL_GREETING
