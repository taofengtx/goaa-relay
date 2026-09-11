"""
GOAA Authorization Kernel AK-1 — Canonical Serialization
===========================================================
Pure functions for canonical JSON serialization and SHA-256 hashing.

Rules (Appendix B of the design):
  - Encoding: UTF-8
  - Unicode normalization: NFC
  - Key ordering: lexicographic sorted
  - frozenset: sorted by canonical representation
  - Set-like tuple: sorted by canonical identity (via SetLikeTuple or helper)
  - Ordered tuple: maintain declaration order
  - Enum: .value string
  - datetime: UTC RFC3339 (e.g. "2026-06-15T10:30:00Z")
  - None: JSON null
  - SHA-256: 64-char lowercase hex

Design reference: GOAA_AUTHORIZATION_KERNEL_V0_DESIGN.md §12, Appendix B
"""

from __future__ import annotations

import hashlib
import json
import unicodedata
from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any


@dataclass(frozen=True)
class SetLikeTuple:
    """Wrapper to disambiguate set-like tuples from ordered tuples.

    A SetLikeTuple is canonicalized by sorting its items, while an
    ordered tuple (plain tuple) preserves declaration order.
    """

    items: tuple[Any, ...]


def normalize_text(value: str) -> str:
    """Normalize text to Unicode NFC form."""
    return unicodedata.normalize("NFC", value)


def format_utc_rfc3339(value: datetime) -> str:
    """Format a datetime as UTC RFC3339 string with Z suffix.

    Raises ValueError if the datetime is naive (no timezone).
    """
    if value.tzinfo is None:
        raise ValueError("datetime must be timezone-aware")
    utc = value.astimezone(timezone.utc)
    return utc.strftime("%Y-%m-%dT%H:%M:%S") + "Z"


def _canonical_value(value: Any) -> Any:
    """Recursively canonicalize a Python value for JSON serialization."""
    if value is None:
        return None
    if isinstance(value, (bool, int, float)):
        if isinstance(value, float) and (value != value or value in (float("inf"), float("-inf"))):
            raise ValueError(f"NaN/Infinity not allowed in canonical JSON: {value}")
        return value
    if isinstance(value, str):
        return normalize_text(value)
    if isinstance(value, bytes):
        raise TypeError("bytes not allowed in canonical JSON; decode to str first")
    if isinstance(value, Enum):
        return value.value
    if isinstance(value, datetime):
        return format_utc_rfc3339(value)
    if isinstance(value, SetLikeTuple):
        # Sort by canonical representation
        return sorted(
            (_canonical_value(item) for item in value.items),
            key=_canonical_sort_key,
        )
    if isinstance(value, frozenset):
        # Sort by canonical representation
        return sorted(
            (_canonical_value(item) for item in value),
            key=_canonical_sort_key,
        )
    if isinstance(value, tuple):
        # Ordered tuple: preserve order
        return [_canonical_value(item) for item in value]
    if isinstance(value, list):
        return [_canonical_value(item) for item in value]
    if isinstance(value, dict):
        return {
            normalize_text(str(k)): _canonical_value(v)
            for k, v in sorted(value.items(), key=lambda kv: normalize_text(str(kv[0])))
        }
    raise TypeError(f"unsupported type for canonical serialization: {type(value).__name__}")


def _canonical_sort_key(value: Any) -> str:
    """Return a sort key for a canonicalized JSON value.

    This ensures stable ordering across equivalent items.
    """
    if isinstance(value, str):
        return value
    if value is None:
        return ""
    if isinstance(value, bool):
        return "b" + str(value).lower()
    if isinstance(value, (int, float)):
        return f"n{value}"
    if isinstance(value, list):
        # Lists (from sets) need a deterministic representation
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value)


def canonicalize(value: object) -> object:
    """Recursively canonicalize a Python object for JSON serialization.

    Returns a JSON-serializable Python object (dicts, lists, strs, etc.)
    with all transformations applied (NFC, enum→value, timezone→UTC, etc.).
    """
    return _canonical_value(value)


def canonical_json_bytes(value: object) -> bytes:
    """Serialize a Python object to canonical JSON bytes.

    Output is UTF-8 encoded, NFC normalized, with sorted keys,
    compact separators, and no trailing newline.
    """
    canonical = _canonical_value(value)
    return json.dumps(
        canonical,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def sha256_hex(value: object) -> str:
    """Compute SHA-256 of the canonical JSON representation.

    Returns a 64-character lowercase hex string.
    """
    data = canonical_json_bytes(value)
    return hashlib.sha256(data).hexdigest()


def canonicalize_set_like_tuple(items: tuple[Any, ...]) -> list[Any]:
    """Canonicalize a set-like tuple: sort items by canonical representation.

    This is an alternative to SetLikeTuple for callers that prefer
    an explicit function call.
    """
    return sorted(
        (_canonical_value(item) for item in items),
        key=_canonical_sort_key,
    )
