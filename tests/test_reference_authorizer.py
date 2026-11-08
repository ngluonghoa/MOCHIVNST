"""Synthetic contract tests. No direct production GitHub/Drive calls."""
import copy
import hashlib
import hmac
import json
import unittest

from governance.reference_authorizer import authorize_control_update

NOW = 100000
SECRET = b"synthetic-test-only-key-32-bytes--"
CONTROL = "refs/heads/control/mochivnst-writer-gate"


class TestReferenceAuthorizer(unittest.TestCase):
    def setUp(self):
        self.intent = {
            "project_id": "MOCHIVNST",
            "owner_label": "authorized-owner-label",
            "owner_generation": 1,
            "session_id": "scoped-session",
            "lease_epoch": 15,
            "control_epoch": 4,
            "work_item": "P0_SCOPE_ONLY",
            "action": "control_ref_update",
            "resource": CONTROL,
            "main_sha": "a" * 40,
            "control_sha": "b" * 40,
            "docs_revision": "revision-123",
            "issued_at_epoch": NOW - 2,
            "expires_at_epoch": NOW + 30,
            "nonce": "synthetic-once-only",
        }
        self.owner = {
            "project_id": "MOCHIVNST", "state": "ACTIVE",
            "generation": 1, "label": "authorized-owner-label",
        }
        self.lease = {
            "project_id": "MOCHIVNST", "state": "HELD",
            "epoch": 15, "owner_generation": 1,
            "session_id": "scoped-session", "work_item": "P0_SCOPE_ONLY",
            "expires_at_epoch": NOW + 200,
        }
        self.control = {
            "project_id": "MOCHIVNST", "control_ref": CONTROL,
            "activation": "ACTIVE", "state": "HELD",
            "permit_write": True, "control_epoch": 4,
            "holder_session_id": "scoped-session",
        }
        self.remote = {
            "project_id": "MOCHIVNST", "main_sha": "a" * 40,
            "control_sha": "b" * 40, "docs_revision": "revision-123",
            "main_protected": True, "control_protected": True,
            "control_writer_mode": "DEDICATED_APP_ONLY",
        }
        self.used = set()

    def signature(self, claim):
        payload = json.dumps(claim, sort_keys=True, separators=(",", ":"),
                             ensure_ascii=True).encode()
        return hmac.new(SECRET, payload, hashlib.sha256).hexdigest()

    def check(self, *, intent=None, owner=None, lease=None, control=None,
              remote=None, secret=SECRET, signature=None, now=NOW,
              consume=None):
        c = copy.deepcopy(self.intent if intent is None else intent)
        if consume is None:
            def consume(nonce, expiry):
                if nonce in self.used:
                    return False
                self.used.add(nonce)
                return True
        return authorize_control_update(
            c, self.signature(c) if signature is None else signature,
            secret, self.owner if owner is None else owner,
            self.lease if lease is None else lease,
            self.control if control is None else control,
            self.remote if remote is None else remote,
            now, consume,
        )

    def test_synthetic_positive_only_not_remote_proof(self):
        self.assertEqual(
            self.check(),
            (True, "synthetic_predicate_satisfied_not_remote_enforcement"),
        )

    def test_nonce_replay_denied(self):
        self.assertTrue(self.check()[0])
        self.assertEqual(self.check(), (False, "replay_or_nonce_store_unavailable"))

    def test_unsigned_or_missing_issuer_key_denied(self):
        self.assertEqual(self.check(secret=b""), (False, "missing_secret"))
        self.assertEqual(self.check(secret=b"a"*31), (False, "missing_secret"))
        self.assertEqual(self.check(signature="f"*64), (False, "bad_hmac"))
        self.assertEqual(self.check(signature="bad"), (False, "invalid_signature"))

    def test_missing_atomic_nonce_store_denied(self):
        self.assertEqual(self.check(consume=False), (False, "missing_atomic_nonce_store"))
        self.assertEqual(self.check(consume=lambda *_: False),
                         (False, "replay_or_nonce_store_unavailable"))

    def test_cross_project_claim_and_resource_denied(self):
        for key, value in [
            ("project_id", "MOCHIFX"), ("resource", "refs/heads/main"),
            ("action", "docs_write"),
        ]:
            with self.subTest(key=key):
                c = {**self.intent, key: value}
                self.assertFalse(self.check(intent=c)[0])

    def test_owner_mismatch_denied(self):
        for key, value in [
            ("project_id", "MOCHIFX"), ("state", "FROZEN"),
            ("generation", 2), ("label", "another-chat"),
        ]:
            with self.subTest(key=key):
                o = {**self.owner, key: value}
                self.assertEqual(self.check(owner=o)[1], "owner_mismatch")

    def test_lease_scope_staleness_denied(self):
        for key, value in [
            ("project_id", "MOCHIFX"), ("state", "FROZEN"),
            ("epoch", 14), ("owner_generation", 2),
            ("session_id", "other-writer"), ("work_item", "OTHER"),
            ("expires_at_epoch", NOW),
        ]:
            with self.subTest(key=key):
                l = {**self.lease, key: value}
                self.assertEqual(self.check(lease=l)[1], "lease_mismatch")

    def test_control_freeze_and_provenance_denied(self):
        for key, value in [
            ("project_id", "MOCHIFX"), ("control_ref", "refs/heads/other"),
            ("activation", "NOT_ACTIVE"), ("state", "FROZEN"),
            ("permit_write", False), ("control_epoch", 3),
            ("holder_session_id", "stale-chat"),
        ]:
            with self.subTest(key=key):
                control = {**self.control, key: value}
                self.assertEqual(self.check(control=control)[1],
                                 "control_inactive_or_mismatch")

    def test_remote_head_revision_protection_denied(self):
        for key, value in [
            ("project_id", "MOCHIFX"), ("main_sha", "c"*40),
            ("control_sha", "d"*40), ("docs_revision", "stale"),
            ("main_protected", False), ("control_protected", False),
            ("control_writer_mode", "SHARED_OAUTH_TOKEN"),
        ]:
            with self.subTest(key=key):
                remote = {**self.remote, key: value}
                self.assertEqual(self.check(remote=remote)[1],
                                 "remote_state_or_acl_mismatch")

    def test_missing_remote_or_docs_snapshot_denied(self):
        self.assertEqual(self.check(owner={})[1], "owner_mismatch")
        self.assertEqual(self.check(remote={})[1], "remote_state_or_acl_mismatch")
        self.assertFalse(authorize_control_update(
            self.intent, self.signature(self.intent), SECRET,
            None, self.lease, self.control, self.remote, NOW,
            lambda *_: True)[0])

    def test_expired_or_future_claim_denied(self):
        for key, value in [
            ("issued_at_epoch", NOW - 31),
            ("issued_at_epoch", NOW + 6),
            ("expires_at_epoch", NOW),
            ("expires_at_epoch", NOW + 121),
        ]:
            with self.subTest(key=key):
                intent = {**self.intent, key: value}
                self.assertEqual(self.check(intent=intent)[1], "expired_or_future_claim")

    def test_claim_shape_and_data_validation(self):
        self.assertEqual(self.check(intent={**self.intent, "extra": "notallowed"})[1],
                         "invalid_claim_shape")
        self.assertEqual(self.check(intent={**self.intent, "main_sha": "abc"})[1],
                         "invalid_git_sha")
        self.assertEqual(self.check(intent={**self.intent, "lease_epoch": True})[1],
                         "invalid_claim_number")
        self.assertEqual(self.check(intent={**self.intent, "nonce": ""})[1],
                         "invalid_claim_value")


if __name__ == "__main__":
    unittest.main()
