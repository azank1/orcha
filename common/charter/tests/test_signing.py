"""Sign → verify roundtrip and tamper detection (FR-2)."""

from __future__ import annotations

import pytest
from charter.model import AACCharter
from charter.signing import sign_charter, verify_charter
from helpers import make_charter, make_keypair


class TestSignVerify:
    def test_roundtrip(self):
        private_key_b64, public_key_b64 = make_keypair()
        signed = sign_charter(make_charter("charter:test"), private_key_b64)

        assert signed["charter_hash"]
        assert signed["operator_signature"]["algorithm"] == "Ed25519"
        assert signed["operator_signature"]["public_key"] == public_key_b64
        assert verify_charter(signed, public_key_b64) is True
        # The signed charter still validates against the model.
        AACCharter(**signed)

    def test_tampered_scope_fails(self):
        private_key_b64, public_key_b64 = make_keypair()
        signed = sign_charter(make_charter("charter:test"), private_key_b64)
        signed["authorized_scope"]["max_transaction_value"] = "999999.00"

        assert verify_charter(signed, public_key_b64) is False

    def test_tampered_stored_hash_fails(self):
        private_key_b64, public_key_b64 = make_keypair()
        signed = sign_charter(make_charter("charter:test"), private_key_b64)
        signed["charter_hash"] = "0" * 64

        assert verify_charter(signed, public_key_b64) is False

    def test_wrong_key_fails(self):
        private_key_b64, _ = make_keypair()
        _, other_public_key_b64 = make_keypair()
        signed = sign_charter(make_charter("charter:test"), private_key_b64)

        assert verify_charter(signed, other_public_key_b64) is False

    def test_unsigned_charter_fails(self):
        _, public_key_b64 = make_keypair()
        assert verify_charter(make_charter("charter:test"), public_key_b64) is False

    def test_bad_seed_rejected(self):
        with pytest.raises(ValueError, match="32-byte"):
            sign_charter(make_charter("charter:test"), "dG9vLXNob3J0")
