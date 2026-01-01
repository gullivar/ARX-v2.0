import os
import logging
from sqlalchemy.orm import Session
from app.models.pipeline import DomainFilter
from app.core.database import SessionLocal

logger = logging.getLogger(__name__)

class PolicyService:
    def __init__(self):
        self.blacklist_trie = set()  # Using set for suffix checking optimization
        self.whitelist_set = set() # Exact matches for now, or use same logic
        self.oisd_loaded = False
        
        # Paths
        self.project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
        self.oisd_path = os.path.join(self.project_root, "backend/data/oisd_domainswild2_big.txt")

    def load_policies(self):
        """
        Load DB policies + File-based blocklists
        """
        logger.info("Loading Policies...")
        self.blacklist_trie.clear()
        self.whitelist_set.clear()

        # 1. Load OISD (Static File)
        if os.path.exists(self.oisd_path):
            try:
                count = 0
                with open(self.oisd_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if not line or line.startswith("#"):
                            continue
                        # Store as reversed logic or just store domain
                        # Optimization: Store domain in set. 
                        # Check: if "sub.example.com". Check "example.com" in set.
                        self.blacklist_trie.add(line.lower())
                        count += 1
                logger.info(f"Loaded {count} domains from OISD Blocklist.")
                self.oisd_loaded = True
            except Exception as e:
                logger.error(f"Failed to load OISD list: {e}")
        else:
            logger.warning(f"OISD Blocklist not found at {self.oisd_path}")

        # 2. Load DB Policies (User Overrides)
        db = SessionLocal()
        try:
            filters = db.query(DomainFilter).filter(DomainFilter.is_active == True).all()
            for f in filters:
                pat = f.pattern.lower().strip()
                if f.type == "BLACKLIST":
                    # DB patterns might be "*.example.com" or "example.com"
                    clean_pat = pat.replace("*.", "")
                    self.blacklist_trie.add(clean_pat)
                elif f.type == "WHITELIST":
                    clean_pat = pat.replace("*.", "")
                    self.whitelist_set.add(clean_pat)
            logger.info(f"Loaded {len(filters)} policies from DB.")
        finally:
            db.close()

    def is_blocked(self, fqdn: str) -> bool:
        """
        Check if FQDN is blocked.
        Logic:
        1. Check Whitelist (Allow if match)
        2. Check Blacklist (Block if match)
        
        Matching: Matches suffix. E.g. "ads.google.com" matched by "google.com" block.
        """
        fqdn = fqdn.lower().strip()
        
        # 1. Whitelist Check (Pass-through)
        # Check all parent domains
        parts = fqdn.split('.')
        # Candidates: continued.com, example.continued.com ...
        # Range len(parts)-1 because TLD (com) usually isn't blocked alone, but maybe?
        # Let's check all segments down to TLD just in case.
        
        for i in range(len(parts) - 1): # stop before TLD alone? OISD includes domains.
            # i=0: full fqdn
            # i=len-2: example.com
            # i=len-1: com (Avoid)
            sub = ".".join(parts[i:])
            if sub in self.whitelist_set:
                return False # Explicitly Allowed

        # 2. Blacklist Check
        for i in range(len(parts) - 1):
            sub = ".".join(parts[i:])
            if sub in self.blacklist_trie:
                return True # Blocked

        return False

policy_service = PolicyService()
