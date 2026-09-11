"""End-to-end behaviour of the applicant → administrator → agent loop."""

from __future__ import annotations

import uuid

from conftest import PNG_BYTES, SESSION_SECRET, app_sql, bearer, grant_role_via_operator, login, register

BASE = "/api/v1/agent-loop"
PASSWORD = "correct-horse-battery"


def _email(prefix: str) -> str:
    return f"{prefix}-{uuid.uuid4().hex[:12]}@example.test"


def _new_account(client, prefix: str) -> tuple[str, str]:
    email = _email(prefix)
    register(client, email, password=PASSWORD, full_name=f"{prefix.title()} Tester")
    return email, login(client, email, PASSWORD)


def _new_admin(client) -> str:
    email, token = _new_account(client, "admin")
    grant_role_via_operator(email, "admin")
    return token


def _draft_payload(email: str, **overrides) -> dict:
    payload = {
        "full_name": "Ada Lovelace",
        "phone": "+1 555 0100",
        "email": email,
        "address": "1 Analytical Engine Way, London",
        "terms_accepted": True,
        "licenses": [
            {
                "license_type": "real-estate-salesperson",
                "license_number": "RE-1234567",
                "issuer": "State Board",
                "jurisdiction": "CA",
                "expires_on": "2030-01-01",
            }
        ],
    }
    payload.update(overrides)
    return payload


def _save_draft(client, token: str, email: str, **overrides):
    return client.put(f"{BASE}/applications/me", json=_draft_payload(email, **overrides), headers=bearer(token))


def _upload(client, token: str, *, side: str = "front", payload: bytes = PNG_BYTES, content_type: str = "image/png"):
    return client.post(
        f"{BASE}/documents",
        content=payload,
        headers={**bearer(token), "Content-Type": content_type, "X-Document-Side": side},
    )


def _submit(client, token: str, key: str | None = None):
    headers = bearer(token)
    if key:
        headers["Idempotency-Key"] = key
    return client.post(f"{BASE}/applications/me/submit", headers=headers)


# ---------------------------------------------------------------------------
# the full loop
# ---------------------------------------------------------------------------
def test_full_loop_from_applicant_to_approved_agent_and_suspension(client):
    email, token = _new_account(client, "applicant")

    assert client.get(f"{BASE}/applications/me", headers=bearer(token)).json()["application"] is None
    assert client.get(f"{BASE}/agent/panel", headers=bearer(token)).status_code == 403

    draft = _save_draft(client, token, email)
    assert draft.status_code == 200, draft.text
    application = draft.json()["application"]
    assert application["status"] == "draft"
    assert application["own_view"] is True
    assert application["licenses"][0]["license_number"] == "RE-1234567"
    application_id = application["id"]

    upload = _upload(client, token)
    assert upload.status_code == 201, upload.text
    document = upload.json()["document"]
    assert "storage_key" not in upload.text
    assert document["storage_label"] == "c2-local-private"
    assert document["scanner"] == "stub"
    assert document["ocr_mode"] == "rules-only"
    assert document["scan_status"] == "stub"

    submitted = _submit(client, token)
    assert submitted.status_code == 200, submitted.text
    assert submitted.json()["application"]["status"] == "submitted"
    review = submitted.json()["pre_review"]
    assert review["advisory"] is True
    assert review["can_auto_approve"] is False
    assert review["mode"] == "rules-only"
    assert review["recommendation"] == "looks_complete"

    assert _submit(client, token).status_code == 409  # already submitted -> read-only

    admin_token = _new_admin(client)
    queue = client.get(f"{BASE}/admin/applications", headers=bearer(admin_token))
    assert queue.status_code == 200
    item = next(i for i in queue.json()["items"] if i["id"] == application_id)
    assert item["own_view"] is False
    assert email not in queue.text, "administrator views must mask the applicant e-mail"
    assert "RE-1234567" not in queue.text, "administrator views must mask the licence number"

    detail = client.get(f"{BASE}/admin/applications/{application_id}", headers=bearer(admin_token))
    assert detail.status_code == 200
    assert email not in detail.text
    assert "1234567" not in detail.text

    approve = client.post(
        f"{BASE}/admin/applications/{application_id}/approve",
        headers={**bearer(admin_token), "Idempotency-Key": "approve-key-1"},
    )
    assert approve.status_code == 200, approve.text
    assert approve.json()["agent_role_granted"] is True
    assert approve.json()["application"]["status"] == "approved"

    replay = client.post(
        f"{BASE}/admin/applications/{application_id}/approve",
        headers={**bearer(admin_token), "Idempotency-Key": "approve-key-1"},
    )
    assert replay.status_code == 200
    assert replay.json() == approve.json(), "a replayed approval must return the stored response"
    assert app_sql(f"select count(*) from user_roles r join users u on u.id = r.user_id "
                   f"where lower(u.email) = lower('{email}') and r.role = 'agent'") == "1"
    assert app_sql(f"select count(*) from agent_applications a join users u on u.id = a.user_id "
                   f"where lower(u.email) = lower('{email}')") == "1"

    panel = client.get(f"{BASE}/agent/panel", headers=bearer(token))
    assert panel.status_code == 200, panel.text
    assert panel.json()["status"] == "active"

    suspend = client.post(
        f"{BASE}/admin/applications/{application_id}/suspend",
        json={"reason": "licence under investigation"},
        headers=bearer(admin_token),
    )
    assert suspend.status_code == 200
    assert suspend.json()["application"]["status"] == "suspended"
    assert client.get(f"{BASE}/agent/panel", headers=bearer(token)).status_code == 403


def test_submit_requires_terms_licence_and_document(client):
    email, token = _new_account(client, "incomplete")
    assert _submit(client, token).status_code == 409  # no draft at all

    _save_draft(client, token, email, terms_accepted=False, licenses=[])
    response = _submit(client, token)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "terms_not_accepted"

    _save_draft(client, token, email, terms_accepted=True, licenses=[])
    assert _submit(client, token).json()["error"]["code"] == "no_license"

    _save_draft(client, token, email, terms_accepted=True)
    assert _submit(client, token).json()["error"]["code"] == "no_document"

    assert _upload(client, token).status_code == 201
    assert _submit(client, token).status_code == 200


def test_submit_is_idempotent(client):
    email, token = _new_account(client, "idem")
    _save_draft(client, token, email)
    _upload(client, token)

    first = _submit(client, token, key="submit-key-1")
    assert first.status_code == 200
    second = _submit(client, token, key="submit-key-1")
    assert second.status_code == 200
    assert second.json() == first.json()

    other = _submit(client, token, key="submit-key-2")
    assert other.status_code == 409  # different key, still locked


def test_documents_require_an_application(client):
    _, token = _new_account(client, "noapp")
    response = _upload(client, token)
    assert response.status_code == 409
    assert response.json()["error"]["code"] == "no_application"


def test_upload_rejects_unsupported_and_mismatched_payloads(client):
    email, token = _new_account(client, "badupload")
    _save_draft(client, token, email)

    assert _upload(client, token, payload=b"not an image", content_type="image/png").status_code == 415
    assert _upload(client, token, payload=b"", content_type="image/png").status_code == 422
    mismatch = _upload(client, token, payload=PNG_BYTES, content_type="application/pdf")
    assert mismatch.status_code == 415
    assert mismatch.json()["error"]["code"] == "content_type_mismatch"
    assert _upload(client, token, side="nonsense").status_code == 422


def test_documents_are_owner_scoped_and_served_through_signed_links(client):
    email, token = _new_account(client, "docs")
    _save_draft(client, token, email)
    document = _upload(client, token).json()["document"]

    link = client.get(f"{BASE}/documents/{document['id']}/link", headers=bearer(token))
    assert link.status_code == 200
    url = link.json()["url"]
    assert url.startswith(f"{BASE}/downloads/")

    download = client.get(url, headers=bearer(token))
    assert download.status_code == 200
    assert download.content == PNG_BYTES

    # an unauthenticated caller gets nothing
    client.cookies.clear()
    assert client.get(url).status_code == 401

    # another account cannot even discover the document
    _, other_token = _new_account(client, "nosy")
    assert client.get(f"{BASE}/documents/{document['id']}/link", headers=bearer(other_token)).status_code == 404
    assert client.get(url, headers=bearer(other_token)).status_code == 403

    # a tampered link is refused
    assert client.get(url + "x", headers=bearer(token)).status_code == 403

    # an expired link is refused
    from app.security import new_download_token

    expired = new_download_token(SESSION_SECRET.encode(), document["id"], _user_id(email), -5)
    assert client.get(f"{BASE}/downloads/{expired}", headers=bearer(token)).status_code == 403


def _user_id(email: str) -> str:
    return app_sql(f"select id from users where lower(email) = lower('{email}')")


def test_licence_rows_are_updated_in_place(client):
    email, token = _new_account(client, "licence")
    licence_id = _save_draft(client, token, email).json()["application"]["licenses"][0]["id"]

    updated = _save_draft(
        client,
        token,
        email,
        licenses=[
            {
                "id": licence_id,
                "license_type": "real-estate-salesperson",
                "license_number": "RE-7654321",
                "issuer": "State Board",
                "jurisdiction": "CA",
                "expires_on": "2031-01-01",
            }
        ],
    ).json()["application"]
    assert updated["licenses"][0]["id"] == licence_id, "re-saving must update the licence row, not replace it"
    assert updated["licenses"][0]["license_number"] == "RE-7654321"
    assert app_sql(f"select count(*) from agent_licenses l join agent_applications a on a.id = l.application_id "
                   f"join users u on u.id = a.user_id where lower(u.email) = lower('{email}')") == "1"


def test_rejection_and_information_requests_are_audited(client):
    email, token = _new_account(client, "reject")
    _save_draft(client, token, email)
    _upload(client, token)
    application_id = _submit(client, token).json()["application"]["id"]
    admin_token = _new_admin(client)

    request_info = client.post(
        f"{BASE}/admin/applications/{application_id}/request-info",
        json={"note": "please supply the back of the licence"},
        headers=bearer(admin_token),
    )
    assert request_info.status_code == 200
    assert request_info.json()["application"]["status"] == "info_requested"
    assert _save_draft(client, token, email).status_code == 200  # editable again

    reject = client.post(
        f"{BASE}/admin/applications/{application_id}/reject",
        json={"reason": "licence could not be verified"},
        headers=bearer(admin_token),
    )
    assert reject.status_code == 200
    assert reject.json()["application"]["status"] == "rejected"
    assert client.get(f"{BASE}/agent/panel", headers=bearer(token)).status_code == 403

    audit_trail = client.get(
        f"{BASE}/admin/audit", params={"application_id": application_id}, headers=bearer(admin_token)
    )
    assert audit_trail.status_code == 200
    actions = {item["action"] for item in audit_trail.json()["items"]}
    assert {
        "application.created",
        "application.draft_saved",
        "document.uploaded",
        "application.submitted",
        "application.request_info",
        "application.reject",
    } <= actions

    assert psql_audit_is_intact(application_id)


def psql_audit_is_intact(application_id: str) -> bool:
    from conftest import psql

    tamper = psql(f"update agent_review_events set action = 'tampered' where application_id = '{application_id}'",
                  as_migrate=False)
    if tamper.returncode == 0 or not (
        "append-only" in tamper.stderr or "permission denied" in tamper.stderr
    ):
        return False
    owner_tamper = psql(
        f"update agent_review_events set action = 'tampered' where application_id = '{application_id}'"
    )
    return owner_tamper.returncode != 0 and "append-only" in owner_tamper.stderr


def test_ai_pre_review_is_advisory_and_rerunnable(client):
    email, token = _new_account(client, "preview")
    _save_draft(client, token, email)
    _upload(client, token)
    application_id = _submit(client, token).json()["application"]["id"]
    admin_token = _new_admin(client)

    rerun = client.post(f"{BASE}/admin/applications/{application_id}/rerun-ai", headers=bearer(admin_token))
    assert rerun.status_code == 200
    review = rerun.json()["pre_review"]
    assert review["advisory"] is True
    assert review["can_auto_approve"] is False
    assert review["mode"] == "rules-only"
    assert review["recommendation"] == "looks_complete"

    detail = client.get(f"{BASE}/admin/applications/{application_id}", headers=bearer(admin_token))
    assert detail.json()["application"]["status"] == "submitted", "a pre-review must never decide an application"


def test_pre_review_rules_flag_incomplete_or_expired_records():
    """Unit-level check of the deterministic rules (no model is attached)."""
    import datetime

    from app.ai_review import pre_review

    result = pre_review(
        {"full_name": "Ada", "phone": "", "address": None, "email": "ada@example.test"},
        [{"license_type": "x", "license_number": "1", "expires_on": datetime.date(2000, 1, 1)}],
        [{"id": "doc"}],
        today=datetime.date(2026, 9, 10),
    ).as_dict()
    assert result["recommendation"] == "manual_review"
    assert set(result["missing_fields"]) == {"phone", "address"}
    assert result["expired_licenses"] == 1
    assert result["can_auto_approve"] is False
    assert result["advisory"] is True


def test_pre_review_flags_a_missing_licence_and_document():
    from app.ai_review import pre_review

    result = pre_review(
        {"full_name": "Ada", "phone": "1", "address": "2", "email": "ada@example.test"},
        [],
        [],
    ).as_dict()
    assert result["recommendation"] == "manual_review"
    assert result["license_count"] == 0
    assert result["document_count"] == 0


def test_admin_role_cannot_be_granted_through_the_api(client):
    _, token = _new_account(client, "roleuser")
    admin_token = _new_admin(client)
    target = _user_id(_email_of(token, client))

    forbidden = client.post(
        f"{BASE}/admin/users/{target}/roles",
        json={"role": "admin"},
        headers=bearer(admin_token),
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "role_not_assignable"


def _email_of(token: str, client) -> str:
    return client.get(f"{BASE}/auth/me", headers=bearer(token)).json()["user"]["email"]


def test_other_accounts_cannot_read_someone_elses_application(client):
    email, token = _new_account(client, "private")
    application_id = _save_draft(client, token, email).json()["application"]["id"]
    _, other_token = _new_account(client, "outsider")
    response = client.get(f"{BASE}/applications/{application_id}", headers=bearer(other_token))
    assert response.status_code == 404
