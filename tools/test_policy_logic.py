import sys
import os
import asyncio
import logging

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
BACKEND_DIR = os.path.join(PROJECT_ROOT, "backend")
sys.path.append(BACKEND_DIR)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- Pydantic v2 Compatibility ---
import pydantic
try:
    from pydantic_settings import BaseSettings
    if not hasattr(pydantic, 'BaseSettings'):
        pydantic.BaseSettings = BaseSettings
except ImportError:
    pass
# ---------------------------------

from app.services.policy_service import policy_service

def test_manual_policy():
    print("--- Testing Policy Service ---")
    
    # 1. Force Load
    policy_service.load_policies()
    
    # 2. Test Cases
    cases = [
        ("zzwpsm.cn", True),
        ("google.com", False),
        ("ads.google.com", False), # OISD wild logic?
        ("tracker.example.com", False), # Assuming example.com not blocked
        ("doubleclick.net", True), # Likely blocked
        ("zzveirrwywhgc.store", True)
    ]
    
    for fqdn, expected in cases:
        result = policy_service.is_blocked(fqdn)
        status = "✅" if result == expected else "❌"
        print(f"{status} {fqdn}: Blocked={result} (Expected={expected})")
        
    print(f"Total Blacklist Rules: {len(policy_service.blacklist_trie)}")

if __name__ == "__main__":
    test_manual_policy()
