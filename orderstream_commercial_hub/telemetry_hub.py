import hashlib
import hmac
import json
import os
import time
from enum import Enum
from typing import Dict, Any, List, Optional

class AlertSeverity(str, Enum):
    HEALTHY = "HEALTHY"
    WARNING = "WARNING"
    CRITICAL_EVICTION_IMMINENT = "CRITICAL_EVICTION_IMMINENT"
    ALREADY_EVICTED = "ALREADY_EVICTED"

class TelemetryHub:
    """Manages 24/7 Soroban contract storage TTL monitoring and automated webhook alerts."""
    
    def __init__(self, db_file: str = "telemetry_subscriptions.json"):
        self.db_file = db_file
        self.subscriptions: Dict[str, Dict[str, Any]] = {}
        self.alert_history: List[Dict[str, Any]] = []
        self._load()

    def _load(self):
        if os.path.exists(self.db_file):
            try:
                with open(self.db_file, "r", encoding="utf-8") as f:
                    self.subscriptions = json.load(f)
            except Exception:
                self.subscriptions = {}

    def _save(self):
        try:
            with open(self.db_file, "w", encoding="utf-8") as f:
                json.dump(self.subscriptions, f, indent=2)
        except Exception:
            pass

    def register_contract(
        self,
        contract_id: str,
        owner_email: str,
        discord_webhook: Optional[str] = None,
        generic_webhook: Optional[str] = None,
        tier: str = "PRO_TELEMETRY"
    ) -> Dict[str, Any]:
        """Registers a live contract for continuous 24/7 storage TTL telemetry monitoring."""
        now = int(time.time())
        sub = {
            "contract_id": contract_id,
            "owner": owner_email,
            "discord_webhook": discord_webhook,
            "generic_webhook": generic_webhook,
            "tier": tier,
            "registered_at": now,
            "active": True,
            "last_checked": now,
            "last_status": AlertSeverity.HEALTHY.value
        }
        self.subscriptions[contract_id] = sub
        self._save()
        return sub

    def evaluate_contract_ttl(self, contract_id: str, current_ledger: int, live_until_ledger: int) -> Dict[str, Any]:
        """Evaluates ledger TTL delta and triggers alert state transitions."""
        remaining_ledgers = max(0, live_until_ledger - current_ledger)
        approx_hours_remaining = round((remaining_ledgers * 5) / 3600, 2)
        
        if remaining_ledgers == 0:
            severity = AlertSeverity.ALREADY_EVICTED
        elif remaining_ledgers < 4096:
            severity = AlertSeverity.CRITICAL_EVICTION_IMMINENT
        elif remaining_ledgers < 15000:
            severity = AlertSeverity.WARNING
        else:
            severity = AlertSeverity.HEALTHY
            
        sub = self.subscriptions.get(contract_id)
        if sub:
            sub["last_checked"] = int(time.time())
            sub["last_status"] = severity.value
            self._save()
            
        alert_event = {
            "contract_id": contract_id,
            "current_ledger": current_ledger,
            "live_until_ledger": live_until_ledger,
            "remaining_ledgers": remaining_ledgers,
            "approx_hours_remaining": approx_hours_remaining,
            "severity": severity.value,
            "timestamp": int(time.time()),
            "action_required": severity != AlertSeverity.HEALTHY
        }
        
        if severity != AlertSeverity.HEALTHY:
            self.alert_history.append(alert_event)
            
        return alert_event

    def format_discord_alert(self, alert_event: Dict[str, Any]) -> Dict[str, Any]:
        """Formats an executive Discord Webhook Embed for protocol operators."""
        is_critical = alert_event["severity"] == AlertSeverity.CRITICAL_EVICTION_IMMINENT.value
        color = 0xFF0033 if is_critical else 0xFFAA00
        
        return {
            "username": "OrderStream Soroban Sentinel",
            "avatar_url": "https://raw.githubusercontent.com/OrderStream/soroban-telemetry/master/assets/sentinel.png",
            "embeds": [{
                "title": f"Storage TTL Alarm: {alert_event['severity']}",
                "description": f"Contract `{alert_event['contract_id']}` is nearing host storage archival!",
                "color": color,
                "fields": [
                    {"name": "Remaining Ledgers", "value": str(alert_event["remaining_ledgers"]), "inline": True},
                    {"name": "Approx Time Remaining", "value": f"~{alert_event['approx_hours_remaining']} hours", "inline": True},
                    {"name": "Recommended Action", "value": "Execute extend_ttl immediately using Soroban SDK or CLI.", "inline": False}
                ],
                "footer": {"text": "OrderStream Telemetry Hub - Real-Time Protection"}
            }]
        }
