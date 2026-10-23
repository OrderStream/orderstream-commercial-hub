import unittest
import time
from orderstream_commercial_hub.license_gate import LicenseManager, LicenseTier
from orderstream_commercial_hub.audit_certifier import AuditCertifier
from orderstream_commercial_hub.telemetry_hub import TelemetryHub, AlertSeverity

class TestCommercialHub(unittest.TestCase):
    def setUp(self):
        self.license_mgr = LicenseManager(secret_key="test_secret_key_123")
        self.certifier = AuditCertifier(registry_file="test_registry.json", secret_key="test_secret_key_123")
        self.telemetry = TelemetryHub(db_file="test_telemetry.json")

    def tearDown(self):
        import os
        for f in ["test_registry.json", "test_telemetry.json"]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass

    def test_license_issuance_and_verification(self):
        key = self.license_mgr.issue_license(
            client_name="Acme Corp",
            tier=LicenseTier.PRO,
            duration_days=30,
            max_repos=15
        )
        self.assertTrue(key.startswith("OS-PRO-"))
        res = self.license_mgr.verify_license(key)
        self.assertTrue(res["valid"])
        self.assertEqual(res["client"], "Acme Corp")
        self.assertEqual(res["tier"], "PRO")
        self.assertEqual(res["max_repos"], 15)

    def test_license_tamper_detection(self):
        key = self.license_mgr.issue_license("Legit Company", LicenseTier.PRO)
        # Modify the last character of signature
        tampered_key = key[:-1] + ("0" if key[-1] != "0" else "1")
        res = self.license_mgr.verify_license(tampered_key)
        self.assertFalse(res["valid"])
        self.assertIn("signature mismatch", res["reason"].lower())

    def test_audit_certificate_generation_and_seal(self):
        dummy_wasm = b"\x00asm\x01\x00\x00\x00\x01\x04\x01\x60\x00\x00"
        cert = self.certifier.certify_contract(
            contract_name="SorobanLendingPool",
            wasm_bytes=dummy_wasm,
            sponsor_address="GB5VNZDEMOADDRESS778899",
            payment_tx="stellar_tx_001"
        )
        self.assertIn("OS-AUDIT-2026-", cert["certificate_id"])
        self.assertEqual(cert["status"], "VERIFIED_SECURE")
        self.assertEqual(len(cert["invariants_checked"]), 5)

        # Verify registry lookup
        verif = self.certifier.verify_certificate(cert["certificate_id"])
        self.assertTrue(verif["valid"])
        self.assertEqual(verif["certificate"]["contract_name"], "SorobanLendingPool")

    def test_telemetry_ttl_evaluation_and_alarms(self):
        sub = self.telemetry.register_contract(
            contract_id="C_DELEGATE_VAULT_001",
            owner_email="ops@delegate.xyz",
            discord_webhook="https://discord.com/api/webhooks/test"
        )
        self.assertEqual(sub["contract_id"], "C_DELEGATE_VAULT_001")

        # 1. Healthy state (>25k ledgers)
        h = self.telemetry.evaluate_contract_ttl("C_DELEGATE_VAULT_001", current_ledger=100000, live_until_ledger=150000)
        self.assertEqual(h["severity"], AlertSeverity.HEALTHY.value)
        self.assertFalse(h["action_required"])

        # 2. Warning state (<15k ledgers)
        w = self.telemetry.evaluate_contract_ttl("C_DELEGATE_VAULT_001", current_ledger=100000, live_until_ledger=110000)
        self.assertEqual(w["severity"], AlertSeverity.WARNING.value)
        self.assertTrue(w["action_required"])

        # 3. Critical imminent eviction (<4096 ledgers)
        c = self.telemetry.evaluate_contract_ttl("C_DELEGATE_VAULT_001", current_ledger=100000, live_until_ledger=102000)
        self.assertEqual(c["severity"], AlertSeverity.CRITICAL_EVICTION_IMMINENT.value)
        self.assertTrue(c["action_required"])

        # Verify Discord payload formatting
        embed = self.telemetry.format_discord_alert(c)
        self.assertEqual(embed["embeds"][0]["color"], 0xFF0033)
        self.assertIn("CRITICAL_EVICTION_IMMINENT", embed["embeds"][0]["title"])

if __name__ == "__main__":
    unittest.main()
