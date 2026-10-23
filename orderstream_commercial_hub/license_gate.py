import base64
import hashlib
import hmac
import json
import os
import time
from enum import Enum
from typing import Dict, Any, Optional

DEFAULT_SECRET = os.getenv("ORDERSTREAM_SECRET_KEY", "os_master_secret_2026_stellar_prod_secure")

class LicenseTier(str, Enum):
    PRO = "PRO"
    ENTERPRISE = "ENTERPRISE"

class LicenseManager:
    """Issues and cryptographically validates OrderStream Pro & Enterprise license keys."""
    
    def __init__(self, secret_key: str = DEFAULT_SECRET):
        self.secret_key = secret_key.encode("utf-8")
        
    def issue_license(
        self,
        client_name: str,
        tier: LicenseTier,
        duration_days: int = 30,
        max_repos: int = 15,
        payment_tx: Optional[str] = None
    ) -> str:
        """Issues an offline-verifiable cryptographically signed license key."""
        now = int(time.time())
        expires_at = now + (duration_days * 86400)
        
        payload = {
            "client": client_name,
            "tier": tier.value,
            "issued_at": now,
            "expires_at": expires_at,
            "max_repos": -1 if tier == LicenseTier.ENTERPRISE else max_repos,
            "tx": payment_tx or "direct_wallet"
        }
        
        payload_bytes = json.dumps(payload, separators=(',', ':'), sort_keys=True).encode("utf-8")
        payload_b64 = base64.urlsafe_b64encode(payload_bytes).decode("utf-8").rstrip("=")
        
        sig = hmac.new(self.secret_key, payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()[:16]
        return f"OS-{tier.value}-{payload_b64}-{sig}"

    def verify_license(self, license_key: str) -> Dict[str, Any]:
        """Validates license signature, expiry, and repo quota. Returns verification metadata."""
        if not license_key or not license_key.startswith("OS-"):
            return {"valid": False, "reason": "Invalid license prefix"}
            
        parts = license_key.split("-")
        if len(parts) != 4:
            return {"valid": False, "reason": "Malformed license structure"}
            
        _, tier_str, payload_b64, signature = parts
        
        expected_sig = hmac.new(self.secret_key, payload_b64.encode("utf-8"), hashlib.sha256).hexdigest()[:16]
        if not hmac.compare_digest(expected_sig, signature):
            return {"valid": False, "reason": "Cryptographic signature mismatch"}
            
        try:
            padded_b64 = payload_b64 + "=" * (-len(payload_b64) % 4)
            payload_bytes = base64.urlsafe_b64decode(padded_b64.encode("utf-8"))
            data = json.loads(payload_bytes.decode("utf-8"))
        except Exception as e:
            return {"valid": False, "reason": f"Corrupt payload decoding: {str(e)}"}
            
        now = int(time.time())
        if now > data.get("expires_at", 0):
            return {
                "valid": False,
                "reason": "License expired",
                "expired_at": data.get("expires_at"),
                "client": data.get("client")
            }
            
        return {
            "valid": True,
            "client": data.get("client"),
            "tier": data.get("tier"),
            "expires_at": data.get("expires_at"),
            "days_remaining": round((data.get("expires_at") - now) / 86400, 1),
            "max_repos": data.get("max_repos"),
            "tx": data.get("tx")
        }
