"""
GOAA Authorization Kernel AK-1 — Canonical Serialization Unit Tests
=====================================================================
Tests: canonical JSON, NFC normalization, ordering rules, SHA-256.

Framework: unittest (standard library). No pytest dependency.
All tests are pure — no I/O, no subprocess, no network.
"""

from __future__ import annotations

import unittest
import unicodedata
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from authorization_kernel.canonical_serialization import (
    SetLikeTuple,
    canonical_json_bytes,
    canonicalize,
    canonicalize_set_like_tuple,
    format_utc_rfc3339,
    normalize_text,
    sha256_hex,
)
from authorization_kernel.enums import ActionEffect


class _TestEnum(Enum):
    A = "alpha"
    B = "beta"


# ============================================================
# normalize_text
# ============================================================

class TestNormalizeText(unittest.TestCase):

    def test_nfc_identical(self) -> None:
        # "é" in composed form (U+00E9)
        composed = "\u00e9"
        self.assertEqual(normalize_text(composed), composed)

    def test_nfc_decomposed_to_composed(self) -> None:
        # "é" as e + combining acute (U+0065 U+0301)
        decomposed = "\u0065\u0301"
        composed = "\u00e9"
        self.assertEqual(normalize_text(decomposed), composed)

    def test_ascii_unchanged(self) -> None:
        self.assertEqual(normalize_text("hello"), "hello")


# ============================================================
# format_utc_rfc3339
# ============================================================

class TestFormatUtcRfc3339(unittest.TestCase):

    def test_utc_datetime(self) -> None:
        dt = datetime(2026, 6, 15, 10, 30, 0, tzinfo=timezone.utc)
        self.assertEqual(format_utc_rfc3339(dt), "2026-06-15T10:30:00Z")

    def test_non_utc_timezone(self) -> None:
        from datetime import timedelta
        tz = timezone(timedelta(hours=-7))
        dt = datetime(2026, 6, 15, 3, 30, 0, tzinfo=tz)
        # 03:30 -07:00 = 10:30 UTC
        self.assertEqual(format_utc_rfc3339(dt), "2026-06-15T10:30:00Z")

    def test_naive_datetime_rejected(self) -> None:
        dt = datetime(2026, 6, 15, 10, 0, 0)
        with self.assertRaises(ValueError):
            format_utc_rfc3339(dt)


# ============================================================
# canonicalize — individual types
# ============================================================

class TestCanonicalize(unittest.TestCase):

    def test_none(self) -> None:
        self.assertIsNone(canonicalize(None))

    def test_bool(self) -> None:
        self.assertTrue(canonicalize(True))
        self.assertFalse(canonicalize(False))

    def test_int(self) -> None:
        self.assertEqual(canonicalize(42), 42)

    def test_float(self) -> None:
        self.assertEqual(canonicalize(3.14), 3.14)

    def test_float_nan_rejected(self) -> None:
        with self.assertRaises(ValueError):
            canonicalize(float("nan"))

    def test_float_inf_rejected(self) -> None:
        with self.assertRaises(ValueError):
            canonicalize(float("inf"))

    def test_str_nfc(self) -> None:
        decomposed = "\u0065\u0301"
        result = canonicalize(decomposed)
        self.assertEqual(result, "\u00e9")

    def test_bytes_rejected(self) -> None:
        with self.assertRaises(TypeError):
            canonicalize(b"bytes not allowed")

    def test_enum_value(self) -> None:
        result = canonicalize(_TestEnum.A)
        self.assertEqual(result, "alpha")

    def test_datetime_utc(self) -> None:
        dt = datetime(2026, 6, 15, 10, 0, 0, tzinfo=timezone.utc)
        result = canonicalize(dt)
        self.assertEqual(result, "2026-06-15T10:00:00Z")

    def test_frozenset_sorted(self) -> None:
        result = canonicalize(frozenset({"z", "a", "m"}))
        self.assertEqual(result, ["a", "m", "z"])

    def test_ordered_tuple_preserved(self) -> None:
        result = canonicalize(("b", "a", "c"))
        # Ordered tuple preserves order
        self.assertEqual(result, ["b", "a", "c"])

    def test_set_like_tuple_sorted(self) -> None:
        result = canonicalize(SetLikeTuple(("z", "a", "m")))
        self.assertEqual(result, ["a", "m", "z"])

    def test_dict_keys_sorted(self) -> None:
        result = canonicalize({"z": 1, "a": 2, "m": 3})
        self.assertEqual(list(result.keys()), ["a", "m", "z"])

    def test_dict_key_nfc(self) -> None:
        decomposed_key = "\u0065\u0301"  # é decomposed
        composed_key = "\u00e9"  # é composed
        result = canonicalize({decomposed_key: 1})
        self.assertIn(composed_key, result)

    def test_nested_structure(self) -> None:
        value = {
            "effects": frozenset({ActionEffect.DELETE, ActionEffect.READ}),
            "name": "test",
        }
        result = canonicalize(value)
        self.assertIsInstance(result, dict)
        self.assertEqual(
            result["effects"],
            ["delete", "read"],  # sorted by value
        )


# ============================================================
# canonical_json_bytes
# ============================================================

class TestCanonicalJsonBytes(unittest.TestCase):

    def test_compact_separators(self) -> None:
        data = {"a": 1, "b": 2}
        raw = canonical_json_bytes(data)
        self.assertNotIn(b" ", raw)
        self.assertIn(b":", raw)

    def test_utf8_encoding(self) -> None:
        data = {"key": "\u00e9"}
        raw = canonical_json_bytes(data)
        self.assertIsInstance(raw, bytes)
        self.assertIn("\u00e9".encode("utf-8"), raw)

    def test_sorted_keys(self) -> None:
        data = {"z": 1, "a": 2}
        raw = canonical_json_bytes(data)
        self.assertEqual(raw, b'{"a":2,"z":1}')

    def test_nfc_normalized(self) -> None:
        # Decomposed é → composed é should produce same bytes
        decomposed = "\u0065\u0301"
        composed = "\u00e9"
        raw_a = canonical_json_bytes({"key": decomposed})
        raw_b = canonical_json_bytes({"key": composed})
        self.assertEqual(raw_a, raw_b)


# ============================================================
# sha256_hex
# ============================================================

class TestSha256Hex(unittest.TestCase):

    def test_returns_64_char_lowercase(self) -> None:
        h = sha256_hex({"test": "data"})
        self.assertEqual(len(h), 64)
        self.assertEqual(h, h.lower())

    def test_same_input_same_hash(self) -> None:
        a = sha256_hex({"a": 1, "b": 2})
        b = sha256_hex({"b": 2, "a": 1})  # same after key sort
        self.assertEqual(a, b)

    def test_different_input_different_hash(self) -> None:
        a = sha256_hex({"value": "hello"})
        b = sha256_hex({"value": "world"})
        self.assertNotEqual(a, b)

    def test_nfc_consistency(self) -> None:
        decomposed = "\u0065\u0301"
        composed = "\u00e9"
        h1 = sha256_hex({"key": decomposed})
        h2 = sha256_hex({"key": composed})
        self.assertEqual(h1, h2)

    def test_frozenset_order_independence(self) -> None:
        h1 = sha256_hex(frozenset({"c", "a", "b"}))
        h2 = sha256_hex(frozenset({"a", "b", "c"}))
        self.assertEqual(h1, h2)

    def test_ordered_tuple_preserves_order(self) -> None:
        h1 = sha256_hex(("a", "b"))
        h2 = sha256_hex(("b", "a"))
        self.assertNotEqual(h1, h2)

    def test_set_like_tuple_vs_ordered_tuple(self) -> None:
        # SetLikeTuple sorts; ordered tuple preserves
        h_set = sha256_hex(SetLikeTuple(("b", "a")))
        h_ordered = sha256_hex(("b", "a"))
        # SetLikeTuple → ["a", "b"], ordered → ["b", "a"]
        self.assertNotEqual(h_set, h_ordered)


# ============================================================
# canonicalize_set_like_tuple
# ============================================================

class TestCanonicalizeSetLikeTuple(unittest.TestCase):

    def test_sorts_by_canonical_representation(self) -> None:
        result = canonicalize_set_like_tuple(("z", "a", "m"))
        self.assertEqual(result, ["a", "m", "z"])

    def test_treats_enums_by_value(self) -> None:
        result = canonicalize_set_like_tuple(
            (ActionEffect.DELETE, ActionEffect.READ)
        )
        self.assertEqual(result, ["delete", "read"])


# ============================================================
# Integration: Known-cross checks
# ============================================================

class TestIntegration(unittest.TestCase):

    def test_enum_in_dict_produces_stable_hash(self) -> None:
        data_a = {"effect": ActionEffect.DELETE}
        data_b = {"effect": ActionEffect.DELETE}
        self.assertEqual(sha256_hex(data_a), sha256_hex(data_b))

    def test_datetime_stability(self) -> None:
        dt = datetime(2026, 6, 15, 10, 0, 0, tzinfo=timezone.utc)
        h = sha256_hex({"timestamp": dt})
        self.assertEqual(len(h), 64)

    def test_none_in_dict(self) -> None:
        h = sha256_hex({"value": None})
        self.assertEqual(len(h), 64)


if __name__ == "__main__":
    unittest.main()
