"""REFERENCE ONLY: fail-closed control-ref authorization predicate.

NOT A DEPLOYED GATEWAY. Callers MUST NOT pass caller-supplied owner, lease,
control or remote snapshots in production; a separate trusted service must
fetch and attest their provenance and hold the HMAC key outside ChatGPT.
Direct GitHub/Drive credentials must be unavailable to untrusted clients.
"""
from __future__ import annotations

import hashlib
import hmac
import json
import re
from typing import Any, Callable, Mapping

PROJECT = "MOCHIVNST"
CONTROL_REF = "refs/heads/control/mochivnst-writer-gate"
ACTION = "control_ref_update"
FIELDS = frozenset({
    "project_id", "owner_label", "owner_generation",
    "session_id", "lease_epoch", "control_epoch", "work_item",
    "action", "resource", "main_sha", "control_sha",
    "docs_revision", "issued_at_epoch", "expires_at_epoch", "nonce",
})
SHA40 = re.compile(r"^[0-9a-f]{40}$")
NonceConsume = Callable[[str, int], bool]


def authorize_control_update(
    intent: Mapping[str, Any] | None,
    signature: str | None,
    secret: bytes | None,
    owner: Mapping[str, Any] | None,
    lease: Mapping[str, Any] | None,
    control: Mapping[str, Any] | None,
    remote: Mapping[str, Any] | None,
    now_epoch: int,
    consume_nonce: NonceConsume | None,
) -> tuple[bool, str]:
    """Evaluate fetched, attested snapshots; fail closed on any mismatch.

    This pure function is NOT sufficient for remote enforcement. The
    independent gateway must enforce credential separation, trusted reads,
    atomic nonce consumption, and GitHub expected-head CAS itself.
    """
    try:
        if any(not isinstance(x, Mapping) for x in (intent, owner, lease, control, remote)):
            return False, "missing_trusted_snapshot"
        if not isinstance(secret, bytes) or len(secret) < 32:
            return False, "missing_secret"
        if not isinstance(signature, str) or not re.fullmatch(r"[0-9a-f]{64}", signature):
            return False, "invalid_signature"
        if not isinstance(now_epoch, int) or isinstance(now_epoch, bool):
            return False, "invalid_clock"
        if not callable(consume_nonce):
            return False, "missing_atomic_nonce_store"
        if set(intent) != FIELDS:
            return False, "invalid_claim_shape"
        required_strings = (
            "project_id", "owner_label", "session_id", "work_item",
            "action", "resource", "main_sha", "control_sha",
            "docs_revision", "nonce",
        )
        if any(not isinstance(intent[k], str) or not intent[k].strip()
               or len(intent[k]) > 256 for k in required_strings):
            return False, "invalid_claim_value"
        numeric = ("owner_generation", "lease_epoch", "control_epoch",
                   "issued_at_epoch", "expires_at_epoch")
        if any(type(intent[k]) is not int or intent[k] < 0 for k in numeric):
            return False, "invalid_claim_number"
        if intent["project_id"] != PROJECT or intent["resource"] != CONTROL_REF:
            return False, "wrong_project_or_resource"
        if intent["action"] != ACTION:
            return False, "wrong_action"
        if not SHA40.fullmatch(intent["main_sha"]) or not SHA40.fullmatch(intent["control_sha"]):
            return False, "invalid_git_sha"
        if (intent["issued_at_epoch"] > now_epoch + 5
                or intent["issued_at_epoch"] < now_epoch - 30
                or intent["expires_at_epoch"] <= now_epoch
                or intent["expires_at_epoch"] > intent["issued_at_epoch"] + 120):
            return False, "expired_or_future_claim"
        encoded = json.dumps(dict(intent), sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True).encode("utf-8")
        expected = hmac.new(secret, encoded, hashlib.sha256).hexdigest()
        if not hmac.compare_digest(signature, expected):
            return False, "bad_hmac"

        # These documents/refs MUST be loaded by the trusted gateway, not by
        # the caller or by a repository workflow controlled by a PR author.
        if (owner.get("project_id") != PROJECT or owner.get("state") != "ACTIVE"
                or owner.get("generation") != intent["owner_generation"]
                or owner.get("label") != intent["owner_label"]):
            return False, "owner_mismatch"
        if (lease.get("project_id") != PROJECT or lease.get("state") != "HELD"
                or lease.get("epoch") != intent["lease_epoch"]
                or lease.get("owner_generation") != intent["owner_generation"]
                or lease.get("session_id") != intent["session_id"]
                or lease.get("work_item") != intent["work_item"]
                or type(lease.get("expires_at_epoch")) is not int
                or lease["expires_at_epoch"] <= now_epoch):
            return False, "lease_mismatch"
        if (control.get("project_id") != PROJECT
                or control.get("control_ref") != CONTROL_REF
                or control.get("activation") != "ACTIVE"
                or control.get("state") != "HELD"
                or control.get("permit_write") is not True
                or control.get("control_epoch") != intent["control_epoch"]
                or control.get("holder_session_id") != intent["session_id"]):
            return False, "control_inactive_or_mismatch"
        if (remote.get("project_id") != PROJECT
                or remote.get("main_sha") != intent["main_sha"]
                or remote.get("control_sha") != intent["control_sha"]
                or remote.get("docs_revision") != intent["docs_revision"]
                or remote.get("main_protected") is not True
                or remote.get("control_protected") is not True
                or remote.get("control_writer_mode") != "DEDICATED_APP_ONLY"):
            return False, "remote_state_or_acl_mismatch"
        # consume_nonce MUST be backed by an atomic, persistent, project-bound
        # store; an in-memory set is ONLY suitable for synthetic tests.
        if not consume_nonce(intent["nonce"], intent["expires_at_epoch"]):
            return False, "replay_or_nonce_store_unavailable"
        return True, "synthetic_predicate_satisfied_not_remote_enforcement"
    except (TypeError, ValueError, KeyError, OverflowError):
        return False, "invalid_input"
