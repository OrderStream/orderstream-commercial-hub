import base64
import os
from typing import Optional
from fastapi import FastAPI, HTTPException, Body
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .license_gate import LicenseManager, LicenseTier
from .audit_certifier import AuditCertifier
from .telemetry_hub import TelemetryHub

app = FastAPI(
    title="OrderStream Commercial Monetization Hub",
    description="Official customer payment, audit certification, and subscription engine",
    version="1.0.0"
)

license_mgr = LicenseManager()
audit_certifier = AuditCertifier()
telemetry_hub = TelemetryHub()

STATIC_DIR = os.path.join(os.path.dirname(__file__), "..", "static")
if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

@app.get("/", response_class=HTMLResponse)
def index():
    html_file = os.path.join(STATIC_DIR, "index.html")
    if os.path.exists(html_file):
        with open(html_file, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>OrderStream Commercial Monetization Hub</h1>"

@app.get("/api/pricing")
def get_pricing():
    return {
        "settlement_wallets": {
            "stellar": {
                "address": "GABFQIK63R2NETJM7T673EAMZN4RJLLGP3OFUEJU5ZVTGWUKULZJNL6",
                "memo": "400566831",
                "accepted_assets": ["USDC", "XLM"]
            },
            "evm_base": {
                "address": "0x5de2b62434754bfd39ef350a3a867ed3eced5074",
                "network": "Base",
                "accepted_assets": ["USDC", "ETH"]
            },
            "credit_card": "https://polar.sh/OrderStream"
        },
        "tiers": [
            {
                "id": "starter",
                "name": "Starter Suite",
                "price_usd": 499,
                "type": "monthly",
                "max_repos": 10,
                "description": "Essential automated PR guards: semantic-merge-guard, pr-cost-firewall, auto-heal-deps, and env-sync-gate with up to 500 CI runs/mo."
            },
            {
                "id": "team",
                "name": "Team Platform",
                "price_usd": 1499,
                "type": "monthly",
                "max_repos": 50,
                "description": "Full OrderStream suite including ci-flake-quarantine deterministic replay, zero-downtime shadow DB migration guard, ai-hallucination-wall, and 24/7 telemetry alarms."
            },
            {
                "id": "enterprise_platform",
                "name": "Enterprise Engineering Mesh",
                "price_usd": 4999,
                "type": "monthly",
                "max_repos": -1,
                "description": "Unlimited repositories, full 102-solver suite across 10 Pillars (MVCC B-Tree virtual index, Roaring commit graphs, FastCDC Merkle streaming, SAT lockfile merge driver, CRIU runner preemption, SLSA L4 provenance, CRDT distributed Git engine, Prompt Injection AST Sanitizer, Phantom Package Firewall, On-Chain Storage TTL Sentinel, and Tarjan Poly-Sync Deadlock Tracer), dedicated 24/7 cloud keeper, custom SLA, and SOC2 compliance exports."
            },
            {
                "id": "ma_ip_audit",
                "name": "M&A IP & Security Audit",
                "price_usd": 15000,
                "type": "one_time",
                "max_repos": -1,
                "description": "Deep AST fuzzy fingerprint copyleft audit, snippet license sheriff certification, formal invariant verification, and executive forensic IP Cleanliness Certificate."
            },
            {
                "id": "audit_certificate",
                "name": "Official Soroban Security Audit Certificate",
                "price_usd": 2500,
                "type": "per_audit",
                "max_repos": 1,
                "description": "One-command WASM bytecode inspection, 1,000-step storage TTL boundary fuzzing, and cryptographic SHA-256 certificate issuance."
            },
            {
                "id": "telemetry_pro",
                "name": "24/7 Soroban Telemetry Sentinel",
                "price_usd": 199,
                "type": "monthly",
                "max_repos": 5,
                "description": "Continuous on-chain event stream monitoring with Discord/Slack webhook alarms before storage TTL eviction."
            }
        ],
        "pillars": {
            "pillar1_vcs_storage": "MVCC B-Tree Virtual Index, Bitmap-Sharded Commit Graphs, FastCDC Merkle Chunking, Unicode NFKC Gate, Loose Object Compressor, Delta Chain Governor, Reflog Compactor, Sharded Tree Cache, Symlink Sanitizer, Alternates Pool",
            "pillar2_repo_topology": "Multi-Repo Tx Protocol, SAT-Graph Merge Driver, Behavioral Contract Hypergraph, Cryptographic Merkle Redaction, Polyrepo Graph Sorter, Sparse Checkout Synthesizer, Monorepo Boundary Enforcer, Virtual Workspace Linker, Atomic Tag Orchestrator, Workspace Deadlock Resolver",
            "pillar3_runner_isolation": "Action Context Taint Engine, Zero-Trust Cache Attestation, Single-Address Wasm Server, Preemptive CRIU Hypervisor, cgroup v2 Reaper, Action Secret Leak Firewall, Step Timeout Predictor, Matrix Execution Pruner, Network Egress Jail, Concurrency Slot Scheduler",
            "pillar4_supply_chain": "SLSA Level 4 Attestation, RFC 3161 Merkle Timestamp, In-Tree AST Micro-Patcher, SMT Reachability Solver, SBOM Delta Differ, Typosquatting Detector, Registry Mirror Validator, Proc-Macro Auditor, License Compliance Matrix, Abandonment Forecaster",
            "pillar5_gitops_scale": "Cloud Event Bus Reverse-Compiler, API Multiplexer & Traffic Shaper, CRDT Distributed Git Engine, Semantic AST Blame, Terraform State Conflict Guard, K8s Manifest Semantic Diff, Cloud Cost Egress Optimizer, Secret Rotation Orchestrator, Immutable Infrastructure Certifier, Policy As Code Evaluator",
            "pillar6_socio_technical": "Dynamic Context Policy Engine, Differential Fuzzing Auto-Merge, Dynamic State Diff Projection, Tree-Sitter SCIP Indexer, Code Churn Risk Assessor, Reviewer Load Balancer, Semantic PR Collapser, Dead Code Exterminator, Test Coverage Gap Solver, Review Deadlock Breaker",
            "pillar7_ai_agent_defenses": "AST Prompt Injection Sanitizer, Phantom Package Slopsquatting Firewall, Agent Loop Cost Circuit Breaker, Synthetic Code Entropy Watermarker, RAG Embedding Staleness Cleaner, Agent Permission Sandbox, Context Window Optimizer, Hallucinated API Firewall, Agentic Git Rebase Governor, Adversarial Benchmark Auditor",
            "pillar8_smart_contracts_wasm": "Storage TTL Decay Sentinel, WASM Linear Memory & Gas Profiler, Reentrancy Guard Flow Analyzer, Fixed-Point Arithmetic Overflow Gate, Multi-Oracle Freshness Verifier, WASI Syscall Capability Validator, Tail Call Trampoline Synthesizer, Contract Upgrade Storage Checker, Multisig Timelock Coordinator, Wasm SIMD128 Vectorizer",
            "pillar9_distributed_consensus": "Poly-Sync Deadlock Tracer (Tarjan SCC), Protobuf Wire-Format Oracle, Schema Lock Preflight Simulator, Distributed Trace Context Healer, Circular RPC Detector, API Contract Drift Sentry, Distributed Idempotency Validator, Event Loop Lag Blame Hunter, Actor Backpressure Autopilot, WAL Replication Lag Forecaster",
            "pillar10_dev_ergonomics_governance": "High-Speed SIMD Log PII Filter, Process Credential Exfiltration Barrier, Multi-Sink GDPR Erasure Authority, Zero-Disruption Git Secret Scrubber, HyperLogLog Cardinality Governor, Workspace Context Snapshot Restorer, Semantic Code Search Graph, Flaky Test Bisector, Cross-AZ Egress Traffic Cop, Serverless Cold Start Prewarmer, Snippet Copyleft License Sheriff, Zero-Downtime Migration Sandbox"
        }
    }

@app.post("/api/audit/certify")
def create_audit_certificate(payload: dict = Body(...)):
    contract_name = payload.get("contract_name", "Untitled Contract")
    wasm_b64 = payload.get("wasm_b64", "")
    sponsor = payload.get("sponsor", "G_ANONYMOUS_SPONSOR")
    payment_tx = payload.get("payment_tx", "simulated_testnet_tx")
    
    if wasm_b64:
        try:
            wasm_bytes = base64.b64decode(wasm_b64)
        except Exception:
            wasm_bytes = wasm_b64.encode("utf-8")
    else:
        wasm_bytes = b"\x00asm\x01\x00\x00\x00" # Standard WASM binary header
        
    cert = audit_certifier.certify_contract(
        contract_name=contract_name,
        wasm_bytes=wasm_bytes,
        sponsor_address=sponsor,
        payment_tx=payment_tx
    )
    return cert

@app.get("/api/audit/verify/{cert_id}")
def verify_audit_certificate(cert_id: str):
    result = audit_certifier.verify_certificate(cert_id)
    if not result.get("valid"):
        raise HTTPException(status_code=404, detail=result.get("reason"))
    return result

@app.post("/api/license/issue")
def issue_license(payload: dict = Body(...)):
    client_name = payload.get("client_name")
    tier_str = payload.get("tier", "STARTER").upper()
    duration_days = int(payload.get("duration_days", 30))
    payment_tx = payload.get("payment_tx", "direct_crypto_tx")
    max_repos = payload.get("max_repos")
    if max_repos is not None:
        max_repos = int(max_repos)
    
    if not client_name:
        raise HTTPException(status_code=400, detail="client_name is required")
        
    tier_mapping = {
        "STARTER": LicenseTier.STARTER,
        "TEAM": LicenseTier.TEAM,
        "ENTERPRISE": LicenseTier.ENTERPRISE,
        "MA_AUDIT": LicenseTier.MA_AUDIT,
        "PRO": LicenseTier.PRO
    }
    tier = tier_mapping.get(tier_str, LicenseTier.STARTER)
    key = license_mgr.issue_license(
        client_name=client_name,
        tier=tier,
        duration_days=duration_days,
        max_repos=max_repos,
        payment_tx=payment_tx
    )
    verification = license_mgr.verify_license(key)
    return {
        "license_key": key,
        "metadata": verification
    }

@app.post("/api/license/verify")
def verify_license(payload: dict = Body(...)):
    key = payload.get("license_key")
    if not key:
        raise HTTPException(status_code=400, detail="license_key is required")
    res = license_mgr.verify_license(key)
    return res

@app.post("/api/telemetry/register")
def register_telemetry(payload: dict = Body(...)):
    contract_id = payload.get("contract_id")
    email = payload.get("owner_email")
    discord_webhook = payload.get("discord_webhook")
    
    if not contract_id or not email:
        raise HTTPException(status_code=400, detail="contract_id and owner_email are required")
        
    sub = telemetry_hub.register_contract(
        contract_id=contract_id,
        owner_email=email,
        discord_webhook=discord_webhook
    )
    return sub

@app.post("/api/telemetry/evaluate")
def evaluate_telemetry(payload: dict = Body(...)):
    contract_id = payload.get("contract_id")
    current_ledger = int(payload.get("current_ledger", 100000))
    live_until_ledger = int(payload.get("live_until_ledger", 103000))
    
    if not contract_id:
        raise HTTPException(status_code=400, detail="contract_id is required")
        
    alert = telemetry_hub.evaluate_contract_ttl(contract_id, current_ledger, live_until_ledger)
    discord_payload = telemetry_hub.format_discord_alert(alert) if alert["action_required"] else None
    return {
        "alert": alert,
        "discord_embed": discord_payload
    }

@app.post("/api/telemetry/ingest")
def ingest_telemetry(payload: dict = Body(...)):
    """Ingests real-time CI metrics, flaky test events, merge conflicts, or TTL metrics."""
    if not payload:
        raise HTTPException(status_code=400, detail="Empty telemetry payload")
    record = telemetry_hub.ingest_event(payload)
    return record

@app.get("/api/telemetry/events")
def get_telemetry_events(limit: int = 50):
    return {"events": telemetry_hub.get_events(limit=limit)}

@app.get("/api/telemetry/stats")
def get_telemetry_stats():
    return telemetry_hub.get_stats()

