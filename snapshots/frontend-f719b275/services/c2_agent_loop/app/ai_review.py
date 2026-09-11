"""Deterministic, rules-only pre-review.

There is **no** real AI/OCR model attached in this environment. The pre-review
is a small deterministic rule set that produces an *advisory* hint for a human
administrator. It can never:

* change an application status,
* grant the ``agent`` role,
* send anything outside this host.

Every payload records ``mode``/``advisory``/``can_auto_approve`` so a consumer
cannot mistake the output for a decision.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any

MODE = "rules-only"
REQUIRED_FIELDS = ("full_name", "phone", "address", "email")


@dataclass
class ReviewResult:
    recommendation: str
    reasons: list[str] = field(default_factory=list)
    missing_fields: list[str] = field(default_factory=list)
    document_count: int = 0
    license_count: int = 0
    expired_licenses: int = 0

    def as_dict(self) -> dict[str, Any]:
        return {
            "mode": MODE,
            "engine": "goaa-c2-rules-v1",
            "advisory": True,
            "can_auto_approve": False,
            "recommendation": self.recommendation,
            "reasons": list(self.reasons),
            "missing_fields": list(self.missing_fields),
            "document_count": self.document_count,
            "license_count": self.license_count,
            "expired_licenses": self.expired_licenses,
        }


def _is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def pre_review(
    application: dict[str, Any],
    licenses: list[dict[str, Any]],
    documents: list[dict[str, Any]],
    *,
    today: date | None = None,
) -> ReviewResult:
    today = today or date.today()
    missing = [name for name in REQUIRED_FIELDS if _is_blank(application.get(name))]
    result = ReviewResult(
        recommendation="manual_review",
        missing_fields=missing,
        document_count=len(documents),
        license_count=len(licenses),
    )

    if missing:
        result.reasons.append("required applicant fields are missing: " + ", ".join(missing))
    if not licenses:
        result.reasons.append("no licence record supplied")
    if not documents:
        result.reasons.append("no supporting document uploaded")

    for lic in licenses:
        expires_on = lic.get("expires_on")
        no_expiry = bool(lic.get("no_expiry"))
        if no_expiry:
            continue
        if expires_on is None:
            result.reasons.append("licence has neither an expiry date nor a no-expiry flag")
            continue
        if isinstance(expires_on, str):
            try:
                expires_on = date.fromisoformat(expires_on)
            except ValueError:
                result.reasons.append("licence expiry date is not a valid ISO date")
                continue
        if expires_on < today:
            result.expired_licenses += 1
            result.reasons.append("a supplied licence is expired")

    if not result.reasons:
        result.recommendation = "looks_complete"
        result.reasons.append("all required fields present, licence and document supplied")
    return result
