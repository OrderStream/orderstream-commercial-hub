import unittest
import time
from fastapi.testclient import TestClient
from orderstream_commercial_hub.license_gate import LicenseManager, LicenseTier
from orderstream_commercial_hub.audit_certifier import AuditCertifier
from orderstream_commercial_hub.telemetry_hub import TelemetryHub, AlertSeverity
from orderstream_commercial_hub.server import app

class TestCommercialHub(unittest.TestCase):
    def setUp(self):
        self.license_mgr = LicenseManager(secret_key="test_secret_key_123")
        self.certifier = AuditCertifier(registry_file="test_registry.json", secret_key="test_secret_key_123")
        self.telemetry = TelemetryHub(db_file="test_telemetry.json")
        self.client = TestClient(app)

    def tearDown(self):
        import os
        for f in ["test_registry.json", "test_telemetry.json"]:
            if os.path.exists(f):
                try:
                    os.remove(f)
                except Exception:
                    pass

    def test_license_issuance_and_verification_all_tiers(self):
        # Starter Tier
        starter_key = self.license_mgr.issue_license(
            client_name="Startup Inc",
            tier=LicenseTier.STARTER,
            duration_days=30
        )
        self.assertTrue(starter_key.startswith("OS-STARTER-"))
        starter_res = self.license_mgr.verify_license(starter_key)
        self.assertTrue(starter_res["valid"])
        self.assertEqual(starter_res["tier"], "STARTER")
        self.assertEqual(starter_res["max_repos"], 10)

        # Team Tier
        team_key = self.license_mgr.issue_license(
            client_name="ScaleUp Tech",
            tier=LicenseTier.TEAM,
            duration_days=60
        )
        self.assertTrue(team_key.startswith("OS-TEAM-"))
        team_res = self.license_mgr.verify_license(team_key)
        self.assertTrue(team_res["valid"])
        self.assertEqual(team_res["tier"], "TEAM")
        self.assertEqual(team_res["max_repos"], 50)

        # Enterprise Tier
        ent_key = self.license_mgr.issue_license(
            client_name="Global Bank Corp",
            tier=LicenseTier.ENTERPRISE,
            duration_days=365
        )
        self.assertTrue(ent_key.startswith("OS-ENTERPRISE-"))
        ent_res = self.license_mgr.verify_license(ent_key)
        self.assertTrue(ent_res["valid"])
        self.assertEqual(ent_res["tier"], "ENTERPRISE")
        self.assertEqual(ent_res["max_repos"], -1)

        # M&A Audit Tier
        audit_key = self.license_mgr.issue_license(
            client_name="Acquired Unicorn",
            tier=LicenseTier.MA_AUDIT,
            duration_days=90
        )
        self.assertTrue(audit_key.startswith("OS-MA_AUDIT-"))
        audit_res = self.license_mgr.verify_license(audit_key)
        self.assertTrue(audit_res["valid"])
        self.assertEqual(audit_res["tier"], "MA_AUDIT")

        # Pro Backward-Compatibility
        pro_key = self.license_mgr.issue_license(
            client_name="Legacy Pro User",
            tier=LicenseTier.PRO,
            duration_days=30,
            max_repos=15
        )
        self.assertTrue(pro_key.startswith("OS-PRO-"))
        pro_res = self.license_mgr.verify_license(pro_key)
        self.assertTrue(pro_res["valid"])
        self.assertEqual(pro_res["tier"], "PRO")
        self.assertEqual(pro_res["max_repos"], 15)

    def test_license_tamper_detection(self):
        key = self.license_mgr.issue_license("Legit Company", LicenseTier.STARTER)
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

        # Healthy state
        h = self.telemetry.evaluate_contract_ttl("C_DELEGATE_VAULT_001", current_ledger=100000, live_until_ledger=150000)
        self.assertEqual(h["severity"], AlertSeverity.HEALTHY.value)
        self.assertFalse(h["action_required"])

        # Warning state
        w = self.telemetry.evaluate_contract_ttl("C_DELEGATE_VAULT_001", current_ledger=100000, live_until_ledger=110000)
        self.assertEqual(w["severity"], AlertSeverity.WARNING.value)
        self.assertTrue(w["action_required"])

        # Critical imminent eviction
        c = self.telemetry.evaluate_contract_ttl("C_DELEGATE_VAULT_001", current_ledger=100000, live_until_ledger=102000)
        self.assertEqual(c["severity"], AlertSeverity.CRITICAL_EVICTION_IMMINENT.value)
        self.assertTrue(c["action_required"])

        embed = self.telemetry.format_discord_alert(c)
        self.assertEqual(embed["embeds"][0]["color"], 0xFF0033)
        self.assertIn("CRITICAL_EVICTION_IMMINENT", embed["embeds"][0]["title"])

    def test_telemetry_ingest_and_stats(self):
        record = self.telemetry.ingest_event({
            "source": "ci-flake-quarantine",
            "event_type": "flake_isolated",
            "repository": "OrderStream/enterprise-app",
            "severity": "WARNING",
            "details": {"test_name": "test_order_race_condition", "retry_count": 3}
        })
        self.assertEqual(record["status"], "INGESTED")
        self.assertTrue(record["event_id"].startswith("evt_"))

        events = self.telemetry.get_events(limit=10)
        self.assertTrue(len(events) >= 1)
        self.assertEqual(events[-1]["event_type"], "flake_isolated")

        stats = self.telemetry.get_stats()
        self.assertTrue(stats["total_events_ingested"] >= 1)

    def test_server_api_pricing_and_ingest_endpoints(self):
        # 1. Test /api/pricing
        res = self.client.get("/api/pricing")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        tier_prices = {t["id"]: t["price_usd"] for t in data["tiers"]}
        self.assertEqual(tier_prices.get("starter"), 499)
        self.assertEqual(tier_prices.get("team"), 1499)
        self.assertEqual(tier_prices.get("enterprise_platform"), 4999)
        self.assertEqual(tier_prices.get("ma_ip_audit"), 15000)

        # 2. Test /api/license/issue and /api/license/verify
        issue_res = self.client.post("/api/license/issue", json={
            "client_name": "Apex Quant Fund",
            "tier": "TEAM",
            "duration_days": 30
        })
        self.assertEqual(issue_res.status_code, 200)
        key = issue_res.json()["license_key"]
        self.assertTrue(key.startswith("OS-TEAM-"))

        verify_res = self.client.post("/api/license/verify", json={"license_key": key})
        self.assertEqual(verify_res.status_code, 200)
        self.assertTrue(verify_res.json()["valid"])
        self.assertEqual(verify_res.json()["tier"], "TEAM")

        # 3. Test /api/telemetry/ingest
        ingest_res = self.client.post("/api/telemetry/ingest", json={
            "source": "pr-cost-firewall",
            "event_type": "cost_spike_blocked",
            "repository": "OrderStream/payments",
            "details": {"saved_amount_usd": 140}
        })
        self.assertEqual(ingest_res.status_code, 200)
        self.assertEqual(ingest_res.json()["status"], "INGESTED")

if __name__ == "__main__":
    unittest.main()
