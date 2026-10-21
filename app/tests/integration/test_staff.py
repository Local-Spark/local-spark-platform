"""Operator invitations use the real restricted auth role and MFA sessions."""

import asyncio
import json
from urllib.parse import unquote
from uuid import uuid4

import pyotp
import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError

from app.core.identity import Identity
from app.services.auth import AuthError
from app.services.staff import StaffService

pytestmark = pytest.mark.integration
PASSWORD = "A long test password 2026!"


async def action_token(admin, auth_service, email):
    async with admin.connect() as db:
        ciphertext = await db.scalar(
            text("""SELECT m.ciphertext FROM auth_mail m JOIN auth_actions a ON a.digest=m.action_digest
              JOIN user_accounts u ON u.id=a.user_id WHERE u.email=:email AND a.purpose='verify'
              ORDER BY a.expires_at DESC LIMIT 1"""),
            {"email": email},
        )
    payload = json.loads(auth_service.cipher.decrypt(ciphertext.encode()))
    return unquote(payload["body"].split("#token=")[1].splitlines()[0])


async def register_verified(auth_service, admin, email):
    await auth_service.register(email, email.split("@")[0], PASSWORD)
    await auth_service.consume_action(await action_token(admin, auth_service, email), "verify")


async def login_staff(auth_service, email):
    challenge = await auth_service.login(email, PASSWORD)
    assert challenge["mfa_required"]
    secret = challenge["setup_secret"]
    if secret is None:
        raise AssertionError("new operator should set up MFA")
    return await auth_service.verify_mfa(challenge["challenge"], pyotp.TOTP(secret).now())


async def test_invite_accept_mfa_revoke_and_audit(native_api, admin, auth_service, auth_database, database, settings):
    manager, invitee = "manager@example.com", "invitee@example.com"
    await register_verified(auth_service, admin, manager)
    async with admin.begin() as db:
        manager_id = await db.scalar(text("SELECT id FROM user_accounts WHERE email=:email"), {"email": manager})
        await db.execute(text("INSERT INTO platform_staff(actor_id) VALUES(:id)"), {"id": manager_id})
    manager_session = await login_staff(auth_service, manager)
    headers = {"Authorization": f"Bearer {manager_session['access_token']}", "Idempotency-Key": "invite-one"}
    response = await native_api.post("/api/v1/admin/staff/invitations", json={"email": invitee}, headers=headers)
    assert response.status_code == 202
    invitation_id = response.json()["id"]
    assert (
        await native_api.post("/api/v1/admin/staff/invitations", json={"email": invitee}, headers=headers)
    ).status_code == 200
    assert (
        await native_api.post("/api/v1/admin/staff/invitations", json={"email": "other@example.com"}, headers=headers)
    ).json()["error_code"] == "IDEMPOTENCY_CONFLICT"
    staff = StaffService(settings, auth_database)
    async with admin.connect() as db:
        ciphertext = await db.scalar(
            text("SELECT ciphertext FROM auth_mail WHERE staff_invitation_id=:id"), {"id": invitation_id}
        )
    assert invitee not in ciphertext
    token = json.loads(staff.cipher.decrypt(ciphertext.encode()))["body"].split("#token=")[1].splitlines()[0]
    assert (await native_api.get("/api/v1/admin/staff", headers=headers)).json()["invitations"][0][
        "status"
    ] == "pending"
    await register_verified(auth_service, admin, invitee)
    recipient_session = await auth_service.login(invitee, PASSWORD)
    recipient_headers = {"Authorization": f"Bearer {recipient_session['access_token']}"}
    assert (await native_api.get("/api/v1/staff/invitations/pending", headers=recipient_headers)).json() == {
        "pending": True,
        "revoked": False,
    }
    assert (await native_api.get("/api/v1/admin/staff", headers=recipient_headers)).status_code == 403
    wrong = await native_api.post(
        "/api/v1/staff/invitations/accept", json={"token": "x" * 32}, headers=recipient_headers
    )
    assert wrong.status_code == 400
    accepted = await native_api.post(
        "/api/v1/staff/invitations/accept", json={"token": token}, headers=recipient_headers
    )
    assert accepted.status_code == 200
    assert (await native_api.get("/api/v1/admin/staff", headers=recipient_headers)).status_code == 401
    challenge = await auth_service.login(invitee, PASSWORD)
    assert challenge["mfa_required"] and challenge["setup_secret"]
    new_session = await auth_service.verify_mfa(challenge["challenge"], pyotp.TOTP(challenge["setup_secret"]).now())
    new_headers = {"Authorization": f"Bearer {new_session['access_token']}"}
    assert (await native_api.get("/api/v1/staff/invitations/pending", headers=new_headers)).json() == {
        "pending": False,
        "revoked": False,
    }
    view = (await native_api.get("/api/v1/admin/staff", headers=new_headers)).json()
    assert len(view["operators"]) == 2 and view["invitations"][0]["status"] == "accepted"
    assert (
        await native_api.delete(f"/api/v1/admin/staff/invitations/{invitation_id}", headers=headers)
    ).status_code == 409
    assert (
        await native_api.post("/api/v1/staff/invitations/accept", json={"token": token}, headers=new_headers)
    ).status_code == 400
    target = next(row["actor_id"] for row in view["operators"] if row["email"] == invitee)
    assert (await native_api.delete(f"/api/v1/admin/staff/{target}", headers=new_headers)).status_code == 409
    assert (await native_api.delete(f"/api/v1/admin/staff/{target}", headers=headers)).status_code == 204
    assert (await native_api.get("/api/v1/admin/staff", headers=new_headers)).status_code == 401
    revoked_session = await auth_service.login(invitee, PASSWORD)
    assert "access_token" in revoked_session and not revoked_session.get("mfa_required")
    revoked_headers = {"Authorization": f"Bearer {revoked_session['access_token']}"}
    assert (await native_api.get("/api/v1/staff/invitations/pending", headers=revoked_headers)).json() == {
        "pending": False,
        "revoked": True,
    }
    assert (await native_api.get("/api/v1/admin/staff", headers=revoked_headers)).status_code == 403
    assert (await native_api.delete(f"/api/v1/admin/staff/{target}", headers=headers)).status_code == 204
    async with admin.connect() as db:
        assert await db.scalar(text("SELECT count(*) FROM platform_audit")) >= 3
        assert await db.scalar(text("SELECT count(*) FROM auth_audit WHERE event LIKE 'auth.staff.%'")) >= 3
    with pytest.raises(DBAPIError):
        async with database.transaction(uuid4(), manager_id) as db:
            await db.execute(text("UPDATE platform_staff SET active=true WHERE actor_id=:id"), {"id": target})


async def test_staff_guardrails_and_restricted_invitation_role(admin, auth_service, auth_database, settings):
    manager, recipient = "boss@example.com", "recipient@example.com"
    await register_verified(auth_service, admin, manager)
    await register_verified(auth_service, admin, recipient)
    async with admin.begin() as db:
        manager_id = await db.scalar(text("SELECT id FROM user_accounts WHERE email=:email"), {"email": manager})
        recipient_id = await db.scalar(text("SELECT id FROM user_accounts WHERE email=:email"), {"email": recipient})
        await db.execute(text("INSERT INTO platform_staff(actor_id) VALUES(:id)"), {"id": manager_id})
    staff = StaffService(settings, auth_database)
    with pytest.raises(AuthError, match="MFA_REQUIRED"):
        await staff.overview(manager_id)
    with pytest.raises(AuthError, match="STAFF_REQUIRED"):
        await staff.overview(recipient_id)
    await login_staff(auth_service, manager)
    with pytest.raises(AuthError, match="ALREADY_STAFF"):
        await staff.invite(manager_id, manager, "existing-staff")
    first = await staff.invite(manager_id, "first@example.com", "replay-key")
    assert (await staff.invite(manager_id, "first@example.com", "replay-key"))["id"] == first["id"]
    with pytest.raises(AuthError, match="IDEMPOTENCY_CONFLICT"):
        await staff.invite(manager_id, "other@example.com", "replay-key")
    with pytest.raises(AuthError, match="OPERATOR_NOT_FOUND"):
        await staff.revoke_operator(manager_id, uuid4())
    invitation = await staff.invite(manager_id, recipient, "recipient-key")
    async with admin.connect() as db:
        ciphertext = await db.scalar(
            text("SELECT ciphertext FROM auth_mail WHERE staff_invitation_id=:id"), {"id": invitation["id"]}
        )
    token = json.loads(staff.cipher.decrypt(ciphertext.encode()))["body"].split("#token=")[1].splitlines()[0]
    unverified = Identity(recipient_id, "test", str(recipient_id), "Recipient", recipient, False)
    with pytest.raises(AuthError, match="VERIFIED_EMAIL_REQUIRED"):
        await staff.accept(unverified, token)
    with pytest.raises(AuthError, match="INVALID_INVITATION"):
        await staff.accept(Identity(recipient_id, "test", str(recipient_id), "Recipient", recipient, True), "bad-token")
    await register_verified(auth_service, admin, "another-recipient@example.com")
    async with admin.connect() as db:
        other_id = await db.scalar(text("SELECT id FROM user_accounts WHERE email='another-recipient@example.com'"))
    outsider = Identity(other_id, "test", str(other_id), "Other", "another-recipient@example.com", True)
    assert await staff.access_state(outsider) == {"pending": False, "revoked": False}
    assert await staff.access_state(Identity(other_id, "test", str(other_id), "Other")) == {
        "pending": False,
        "revoked": False,
    }
    assert await staff.access_state(
        Identity(recipient_id, "test", str(recipient_id), "Recipient", recipient, True)
    ) == {"pending": True, "revoked": False}
    with pytest.raises(AuthError, match="INVITATION_EMAIL_MISMATCH"):
        await staff.accept(outsider, token)
    wrong = Identity(manager_id, "test", str(manager_id), "Manager", manager, True)
    with pytest.raises(AuthError, match="INVITATION_EMAIL_MISMATCH"):
        await staff.accept(wrong, token)
    with pytest.raises(DBAPIError):
        async with auth_database.transaction(uuid4(), recipient_id) as db:
            await db.execute(
                text("""INSERT INTO staff_invitations
                  (id,invited_by,email,token_digest,idempotency_key,expires_at)
                  VALUES(:id,:actor,:email,:digest,:key,now()+interval '1 day')"""),
                {
                    "id": uuid4(),
                    "actor": recipient_id,
                    "email": "fake@example.com",
                    "digest": "a" * 64,
                    "key": "forged",
                },
            )
    await staff.accept(Identity(recipient_id, "test", str(recipient_id), "Recipient", recipient, True), token)
    with pytest.raises(AuthError, match="INVITATION_ALREADY_ACCEPTED"):
        await staff.revoke_invitation(manager_id, invitation["id"])
    async with admin.begin() as db:
        await db.execute(text("UPDATE platform_staff SET active=false WHERE actor_id=:id"), {"id": recipient_id})
    await staff.revoke_operator(manager_id, recipient_id)


async def test_accept_rejects_account_already_promoted(admin, auth_service, auth_database, settings):
    manager, recipient = "chief@example.com", "promoted@example.com"
    await register_verified(auth_service, admin, manager)
    await register_verified(auth_service, admin, recipient)
    async with admin.begin() as db:
        manager_id = await db.scalar(text("SELECT id FROM user_accounts WHERE email=:email"), {"email": manager})
        recipient_id = await db.scalar(text("SELECT id FROM user_accounts WHERE email=:email"), {"email": recipient})
        await db.execute(text("INSERT INTO platform_staff(actor_id) VALUES(:id)"), {"id": manager_id})
    await login_staff(auth_service, manager)
    staff = StaffService(settings, auth_database)
    invitation = await staff.invite(manager_id, recipient, "race-promotion")
    async with admin.connect() as db:
        ciphertext = await db.scalar(
            text("SELECT ciphertext FROM auth_mail WHERE staff_invitation_id=:id"), {"id": invitation["id"]}
        )
    token = json.loads(staff.cipher.decrypt(ciphertext.encode()))["body"].split("#token=")[1].splitlines()[0]
    async with admin.begin() as db:
        await db.execute(text("INSERT INTO platform_staff(actor_id) VALUES(:id)"), {"id": recipient_id})
    with pytest.raises(AuthError, match="ALREADY_STAFF"):
        await staff.accept(Identity(recipient_id, "test", str(recipient_id), "Recipient", recipient, True), token)


async def test_invite_revocation_and_one_use_under_concurrency(admin, auth_service, auth_database, settings):
    manager = "operator@example.com"
    await register_verified(auth_service, admin, manager)
    async with admin.begin() as db:
        manager_id = await db.scalar(text("SELECT id FROM user_accounts WHERE email=:email"), {"email": manager})
        await db.execute(text("INSERT INTO platform_staff(actor_id) VALUES(:id)"), {"id": manager_id})
    await login_staff(auth_service, manager)
    staff = StaffService(settings, auth_database)
    results = await asyncio.gather(*(staff.invite(manager_id, "new@example.com", "same-key") for _ in range(3)))
    assert len({row["id"] for row in results}) == 1
    assert sum(not row["replayed"] for row in results) == 1
    with pytest.raises(AuthError, match="INVITATION_PENDING"):
        await staff.invite(manager_id, "new@example.com", "different-key")
    invitation_id = results[0]["id"]
    await staff.revoke_invitation(manager_id, invitation_id)
    await staff.revoke_invitation(manager_id, invitation_id)
    with pytest.raises(AuthError, match="INVITATION_NOT_FOUND"):
        await staff.revoke_invitation(manager_id, uuid4())
    renewed = await staff.invite(manager_id, "new@example.com", "new-key")
    assert renewed["id"] != invitation_id
    async with admin.begin() as db:
        await db.execute(
            text("UPDATE staff_invitations SET expires_at=now()-interval '1 second' WHERE id=:id"),
            {"id": renewed["id"]},
        )
    assert (await staff.overview(manager_id))["invitations"][0]["status"] == "expired"
