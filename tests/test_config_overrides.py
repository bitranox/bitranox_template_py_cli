"""Unit tests for CLI configuration overrides (--set SECTION.KEY=VALUE).

Tests cover parsing, value coercion, nest-override mechanics, and full
apply_overrides integration with the Config class.
"""

from __future__ import annotations

import importlib
import importlib.util
import json
from typing import TYPE_CHECKING, Any

import pytest
from lib_layered_config import Config

from bitranox_template_py_cli.adapters.config.overrides import (
    ConfigOverride,
    apply_overrides,
    coerce_value,
    parse_override,
    select_json_loads,
    stdlib_json_loads,
)

if TYPE_CHECKING:
    from types import ModuleType

# orjson is required only below Python 3.14 (it has no free-threaded build); from 3.14 it is an
# extra the dev install does not pull in, so its arms run wherever it is installed.
_ORJSON_INSTALLED = importlib.util.find_spec("orjson") is not None
_needs_orjson = pytest.mark.skipif(
    not _ORJSON_INSTALLED, reason="orjson is not installed (not required from Python 3.14)"
)

# ======================== parse_override tests ========================


@pytest.mark.os_agnostic
def test_parse_override_simple_key() -> None:
    """Simple SECTION.KEY=VALUE produces correct section and single-element key_path."""
    result = parse_override("lib_log_rich.console_level=DEBUG")

    assert result == ConfigOverride(section="lib_log_rich", key_path=("console_level",), value="DEBUG")


@pytest.mark.os_agnostic
def test_parse_override_nested_key() -> None:
    """Dotted key path beyond section creates multi-element key_path."""
    result = parse_override("lib_log_rich.payload_limits.message_max_chars=8192")

    assert result.section == "lib_log_rich"
    assert result.key_path == ("payload_limits", "message_max_chars")
    assert result.value == 8192


@pytest.mark.os_agnostic
def test_parse_override_value_containing_equals() -> None:
    """Value containing '=' is preserved intact after the first split."""
    result = parse_override("section.key=val=ue")

    assert result.value == "val=ue"


@pytest.mark.os_agnostic
def test_parse_override_empty_value() -> None:
    """Empty value after '=' produces empty string."""
    result = parse_override("section.key=")

    assert result.value == ""


@pytest.mark.os_agnostic
def test_parse_override_rejects_missing_equals() -> None:
    """Override without '=' raises ValueError."""
    with pytest.raises(ValueError, match="must contain '='"):
        parse_override("section.key_no_equals")


@pytest.mark.os_agnostic
def test_parse_override_rejects_no_dot_in_key() -> None:
    """Override without dot in key part raises ValueError."""
    with pytest.raises(ValueError, match="must contain at least one dot"):
        parse_override("sectiononly=value")


@pytest.mark.os_agnostic
def test_parse_override_rejects_empty_section() -> None:
    """Leading dot produces empty section, which is rejected."""
    with pytest.raises(ValueError, match="section name is empty"):
        parse_override(".key=value")


@pytest.mark.os_agnostic
def test_parse_override_rejects_empty_key_component() -> None:
    """Double dot in key path produces empty component, which is rejected."""
    with pytest.raises(ValueError, match="empty component"):
        parse_override("section..key=value")


@pytest.mark.os_agnostic
def test_parse_override_rejects_trailing_dot_in_key() -> None:
    """Trailing dot produces empty final key component."""
    with pytest.raises(ValueError, match="empty component"):
        parse_override("section.key.=value")


@pytest.mark.os_agnostic
def test_parse_override_rejects_equals_only() -> None:
    """Bare '=value' with no dot in key part raises ValueError."""
    with pytest.raises(ValueError, match="must contain at least one dot"):
        parse_override("=value")


@pytest.mark.os_agnostic
def test_parse_override_rejects_bare_equals() -> None:
    """Bare '=' with empty everything raises ValueError."""
    with pytest.raises(ValueError, match="must contain at least one dot"):
        parse_override("=")


# ======================== coerce_value tests ========================


@pytest.mark.os_agnostic
def test_coerce_value_true() -> None:
    """JSON 'true' coerces to Python True."""
    assert coerce_value("true") is True


@pytest.mark.os_agnostic
def test_coerce_value_false() -> None:
    """JSON 'false' coerces to Python False."""
    assert coerce_value("false") is False


@pytest.mark.os_agnostic
def test_coerce_value_integer() -> None:
    """Numeric string coerces to int."""
    assert coerce_value("42") == 42
    assert isinstance(coerce_value("42"), int)


@pytest.mark.os_agnostic
def test_coerce_value_float() -> None:
    """Decimal numeric string coerces to float."""
    result = coerce_value("3.14")
    assert result == 3.14
    assert isinstance(result, float)


@pytest.mark.os_agnostic
def test_coerce_value_null() -> None:
    """JSON 'null' coerces to Python None."""
    assert coerce_value("null") is None


@pytest.mark.os_agnostic
def test_coerce_value_json_array() -> None:
    """JSON array string coerces to list."""
    assert coerce_value('["a","b"]') == ["a", "b"]


@pytest.mark.os_agnostic
def test_coerce_value_json_object() -> None:
    """JSON object string coerces to dict."""
    assert coerce_value('{"k":"v"}') == {"k": "v"}


@pytest.mark.os_agnostic
def test_coerce_value_plain_string() -> None:
    """Non-JSON string falls back to raw string."""
    assert coerce_value("DEBUG") == "DEBUG"


@pytest.mark.os_agnostic
def test_coerce_value_empty_string() -> None:
    """Empty string returns empty string."""
    assert coerce_value("") == ""


@pytest.mark.os_agnostic
def test_coerce_value_negative_number() -> None:
    """Negative number coerces correctly."""
    assert coerce_value("-5") == -5


@pytest.mark.os_agnostic
def test_coerce_value_unicode_string() -> None:
    """Unicode string falls back to raw string."""
    assert coerce_value("日本語") == "日本語"


@pytest.mark.os_agnostic
def test_coerce_value_string_with_spaces() -> None:
    """String containing spaces falls back to raw string."""
    assert coerce_value("hello world") == "hello world"


@pytest.mark.os_agnostic
def test_coerce_value_negative_float() -> None:
    """Negative float coerces correctly."""
    result = coerce_value("-3.14")
    assert result == -3.14
    assert isinstance(result, float)


@pytest.mark.os_agnostic
def test_coerce_value_scientific_notation() -> None:
    """Scientific notation coerces to float."""
    result = coerce_value("1e10")
    assert result == 1e10


@pytest.mark.os_agnostic
def test_parse_override_deeply_nested_key() -> None:
    """Three-level nesting produces correct key_path."""
    result = parse_override("s.a.b.c=42")

    assert result.section == "s"
    assert result.key_path == ("a", "b", "c")
    assert result.value == 42


@pytest.mark.os_agnostic
def test_parse_override_unicode_value() -> None:
    """Unicode characters in the value are preserved."""
    result = parse_override("s.key=こんにちは")

    assert result.value == "こんにちは"


@pytest.mark.os_agnostic
def test_parse_override_value_with_newline_json() -> None:
    """A JSON string with an escaped newline is parsed into a real newline."""
    result = parse_override('s.key="line1\\nline2"')

    assert result.value == "line1\nline2"


# ======================== JSON backend selection ========================

_NON_FINITE = ["NaN", "Infinity", "-Infinity", "1e400", "[1, NaN]", '{"a": Infinity}']
_PARSED_ALIKE = [
    "true",
    "false",
    "null",
    "42",
    "-7",
    "3.14",
    "-1.5e3",
    '["a", "b"]',
    '{"a": {"b": [1, 2.5]}}',
    '"x\\ny"',
]


@pytest.mark.os_agnostic
@pytest.mark.parametrize("raw", _NON_FINITE)
def test_stdlib_json_loads_refuses_non_finite_numbers_like_orjson(raw: str) -> None:
    """stdlib json accepts NaN, Infinity and an overflowing literal; orjson refuses them, so this does too."""
    with pytest.raises(ValueError, match="non-finite"):
        stdlib_json_loads(raw)


@pytest.mark.os_agnostic
@pytest.mark.parametrize("raw", _NON_FINITE)
def test_coerce_value_keeps_a_non_finite_number_as_the_raw_string(raw: str) -> None:
    """A refused number falls back to the string the user typed, whichever backend parses it."""
    assert coerce_value(raw) == raw


@pytest.mark.os_agnostic
@pytest.mark.parametrize("raw", _PARSED_ALIKE)
def test_stdlib_json_loads_parses_ordinary_json(raw: str) -> None:
    """The stdlib backend parses the values a --set override carries."""
    assert stdlib_json_loads(raw) == json.loads(raw)


@_needs_orjson
@pytest.mark.os_agnostic
@pytest.mark.parametrize("raw", _PARSED_ALIKE)
def test_stdlib_json_loads_agrees_with_orjson(raw: str) -> None:
    """Both backends give the same value, so a --set override means the same on every interpreter."""
    orjson = importlib.import_module("orjson")

    assert stdlib_json_loads(raw) == orjson.loads(raw)


def _import_must_not_run() -> ModuleType | None:
    raise AssertionError("orjson must never be imported on a free-threaded build")


@pytest.mark.os_agnostic
def test_select_json_loads_never_imports_orjson_on_a_free_threaded_build() -> None:
    """Importing orjson there would turn the GIL back on, so the selector does not even try."""
    assert select_json_loads(free_threaded=True, import_orjson=_import_must_not_run) is stdlib_json_loads


@pytest.mark.os_agnostic
def test_select_json_loads_falls_back_to_stdlib_without_orjson() -> None:
    """Without orjson installed (the 3.14+ default), the stdlib backend parses."""
    assert select_json_loads(free_threaded=False, import_orjson=lambda: None) is stdlib_json_loads


@_needs_orjson
@pytest.mark.os_agnostic
def test_select_json_loads_uses_orjson_where_it_can_run() -> None:
    """On a GIL build with orjson installed, orjson parses."""
    orjson = importlib.import_module("orjson")

    assert select_json_loads(free_threaded=False, import_orjson=lambda: orjson) is orjson.loads


# ======================== apply_overrides tests ========================


def _make_config(data: dict[str, Any]) -> Config:
    """Create a minimal Config instance from a data dict for testing."""
    meta: dict[str, Any] = {}
    return Config(data, meta)


@pytest.mark.os_agnostic
def test_apply_overrides_empty_tuple_returns_same_instance() -> None:
    """No overrides returns the original Config instance unchanged."""
    config = _make_config({"s": {"k": 1}})

    result = apply_overrides(config, ())

    assert result is config


@pytest.mark.os_agnostic
def test_apply_overrides_single_override() -> None:
    """Single override sets the value in the correct section."""
    config = _make_config({"s": {"k": 1, "other": "kept"}})

    result = apply_overrides(config, ("s.k=2",))

    assert result["s"]["k"] == 2
    assert result["s"]["other"] == "kept"


@pytest.mark.os_agnostic
def test_apply_overrides_nested_key() -> None:
    """Nested key override creates intermediate dicts."""
    config = _make_config({"s": {"existing": "kept"}})

    result = apply_overrides(config, ("s.nested.deep=42",))

    assert result["s"]["nested"]["deep"] == 42
    assert result["s"]["existing"] == "kept"


@pytest.mark.os_agnostic
def test_apply_overrides_multiple_overrides() -> None:
    """Multiple overrides all apply to the result."""
    config = _make_config({"s": {"a": 1, "b": 2}})

    result = apply_overrides(config, ("s.a=10", "s.b=20"))

    assert result["s"]["a"] == 10
    assert result["s"]["b"] == 20


@pytest.mark.os_agnostic
def test_apply_overrides_preserves_unmodified_sections() -> None:
    """Sections not targeted by overrides remain unchanged."""
    config = _make_config({"s1": {"k": "original"}, "s2": {"k": "untouched"}})

    result = apply_overrides(config, ("s1.k=changed",))

    assert result["s1"]["k"] == "changed"
    assert result["s2"]["k"] == "untouched"


@pytest.mark.os_agnostic
def test_apply_overrides_creates_missing_section() -> None:
    """Override targeting a non-existent section creates it."""
    config = _make_config({"existing": {"k": 1}})

    result = apply_overrides(config, ("new_section.key=value",))

    assert result["new_section"]["key"] == "value"
    assert result["existing"]["k"] == 1


@pytest.mark.os_agnostic
def test_apply_overrides_boolean_coercion() -> None:
    """Boolean values are correctly coerced from JSON strings."""
    config = _make_config({"s": {"flag": False}})

    result = apply_overrides(config, ("s.flag=true",))

    assert result["s"]["flag"] is True


@pytest.mark.os_agnostic
def test_apply_overrides_does_not_mutate_original() -> None:
    """Original config is not modified by apply_overrides."""
    config = _make_config({"s": {"k": "original"}})

    result = apply_overrides(config, ("s.k=changed",))

    assert config["s"]["k"] == "original"
    assert result["s"]["k"] == "changed"


@pytest.mark.os_agnostic
def test_apply_overrides_rejects_malformed_input() -> None:
    """Malformed override string raises ValueError."""
    config = _make_config({"s": {"k": 1}})

    with pytest.raises(ValueError, match="must contain '='"):
        apply_overrides(config, ("invalid",))


@pytest.mark.os_agnostic
def test_apply_overrides_names_the_cli_as_the_source_of_an_overridden_key() -> None:
    """An overridden key reports the CLI as its origin, not the layer it replaced.

    ``Config.with_overrides`` records an overridden key as the library's generic
    ``override`` layer; the rebuild names the command line (``cli``), so ``config``
    answers "where did this come from" with the invocation, never with the file
    holding the value that was just replaced.
    """
    config = Config({"s": {"k": 1}}, {"s.k": {"layer": "file", "path": "/etc/app.toml", "key": "s.k"}})

    result = apply_overrides(config, ("s.k=2",))

    assert result["s"]["k"] == 2
    assert result.origin("s.k") == {"layer": "cli", "path": None, "key": "s.k"}


@pytest.mark.os_agnostic
def test_apply_overrides_leaves_an_untouched_key_with_its_own_source() -> None:
    """Only the keys ``--set`` supplied are relabelled; the rest keep their layer."""
    config = Config(
        {"s": {"k": 1, "other": "kept"}},
        {
            "s.k": {"layer": "file", "path": "/etc/app.toml", "key": "s.k"},
            "s.other": {"layer": "env", "path": None, "key": "s.other"},
        },
    )

    result = apply_overrides(config, ("s.k=2",))

    assert result.origin("s.other") == {"layer": "env", "path": None, "key": "s.other"}


# ======================== conflicting overrides ========================


@pytest.mark.os_agnostic
@pytest.mark.parametrize(
    "overrides",
    [("a.b=1", "a.b.c=2"), ("a.b.c=2", "a.b=1"), ('a.b={"c": 1}', "a.b.d=2"), ("a.b.c=1", "a.x=0", "a.b=2")],
    ids=["value-then-key-under-it", "key-under-it-then-value", "json-table-then-key-under-it", "not-adjacent"],
)
def test_apply_overrides_refuses_a_key_given_both_a_value_and_keys_under_it(overrides: tuple[str, ...]) -> None:
    """Either order used to go wrong: a TypeError, or the earlier override silently dropped."""
    with pytest.raises(ValueError, match=r"conflicting --set overrides: a\.b is given a value and a\.b\."):
        apply_overrides(_make_config({}), overrides)


@pytest.mark.os_agnostic
def test_apply_overrides_lets_the_last_of_two_values_for_one_key_win() -> None:
    result = apply_overrides(_make_config({}), ("a.b=1", "a.b=2"))

    assert result["a"]["b"] == 2


@pytest.mark.os_agnostic
def test_apply_overrides_keeps_sibling_keys_that_share_a_prefix_of_letters() -> None:
    """``a.b`` and ``a.bc`` are siblings, not a value and a key under it."""
    result = apply_overrides(_make_config({}), ("a.b=1", "a.bc.d=2"))

    assert result["a"] == {"b": 1, "bc": {"d": 2}}
