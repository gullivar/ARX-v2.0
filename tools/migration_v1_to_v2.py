import sys
import os
import json
import csv
import logging
from datetime import datetime

# Add parent dir to sys.path to import app modules
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../backend')))

from app.core.database import SessionLocal, engine
from app.models.pipeline import PipelineItem, CrawlResult, AnalysisResult, PipelineStatus, PipelineLog, Base

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

LEGACY_PATH = "../../v1.0_legacy"

def import_tranco(session):
    tranco_path = os.path.join(LEGACY_PATH, "arx-w-intel/tranco_top_1m.csv")
    if not os.path.exists(tranco_path):
        logger.warning(f"Tranco file not found at {tranco_path}")
        return

    logger.info(f"Importing Tranco Top 1M from {tranco_path}...")
    try:
        from sqlalchemy import insert
        count = 0
        batch = []
        with open(tranco_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            # Tranco format usually: rank,domain
            for row in reader:
                if len(row) < 2: continue
                fqdn = row[1]
                
                # Prepare dict for core insert
                batch.append({
                    "fqdn": fqdn,
                    "status": PipelineStatus.DISCOVERED,
                    "source": "tranco_top_1m",
                    "priority": 3,
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                })
                count += 1
                
                if len(batch) >= 10000:
                    stmt = insert(PipelineItem).values(batch).prefix_with("OR IGNORE")
                    session.execute(stmt)
                    session.commit()
                    batch = []
                    logger.info(f"Imported {count} Tranco items...")
            
            if batch:
                stmt = insert(PipelineItem).values(batch).prefix_with("OR IGNORE")
                session.execute(stmt)
                session.commit()
                
        logger.info(f"Tranco Import done. Total Scanned: {count}")
    except Exception as e:
        logger.error(f"Tranco Import Failed: {e}")
        session.rollback()

def import_merged_data(session):
    merged_path = os.path.join(LEGACY_PATH, "arx-w-intel/collector/dags/data/merged_data.json")
    if not os.path.exists(merged_path):
        logger.warning(f"Merged data file not found at {merged_path}")
        return

    logger.info(f"Importing Merged Data from {merged_path}...")
    try:
        from sqlalchemy import insert
        with open(merged_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        count = 0
        batch = []
        for entry in data:
            fqdn = entry.get('fqdn')
            if not fqdn: continue
            
            # Prepare dict
            batch.append({
                "fqdn": fqdn,
                "status": PipelineStatus.DISCOVERED,
                "source": entry.get('source', 'merged_json'),
                "priority": 3,
                "created_at": datetime.now(),
                "updated_at": datetime.now()
            })
            count += 1
            
            if len(batch) >= 5000:
                stmt = insert(PipelineItem).values(batch).prefix_with("OR IGNORE")
                session.execute(stmt)
                session.commit()
                batch = []
                logger.info(f"Imported {count} Merged items...")
        
        if batch:
            stmt = insert(PipelineItem).values(batch).prefix_with("OR IGNORE")
            session.execute(stmt)
            session.commit()
            
        logger.info(f"Merged Data Import done. Total: {count}")

    except Exception as e:
        logger.error(f"Merged Data Import Failed: {e}")
        session.rollback()

def import_dns_history(session):
    dns_path = os.path.join(LEGACY_PATH, "DNS_1-month_modify.csv")
    if not os.path.exists(dns_path):
        logger.warning(f"DNS history file not found at {dns_path}")
        return

    logger.info(f"Importing DNS 1-Month History from {dns_path}...")
    try:
        from sqlalchemy import insert
        count = 0
        batch = []
        # Use pandas if available for speed, or pure python csv
        # Pure python CSV is safer given environment constraints
        with open(dns_path, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            header = next(reader, None) # Skip header timestamp,fqdn
            
            seen_in_batch = set() # Simple dedup for this batch
            
            for row in reader:
                if len(row) < 2: continue
                fqdn = row[1].strip()
                if not fqdn: continue
                
                # Deduplicate roughly strictly to avoid massive redundant processing
                # Ideally we want unique FQDNs from this list
                
                # Check duplication in batch is easy
                if fqdn in seen_in_batch:
                    continue
                seen_in_batch.add(fqdn)
                
                # Prepare dict
                batch.append({
                    "fqdn": fqdn,
                    "status": PipelineStatus.DISCOVERED,
                    "source": "dns_history_1m",
                    "priority": 2, # High value real traffic
                    "created_at": datetime.now(),
                    "updated_at": datetime.now()
                })
                count += 1
                
                # Batch insert occasionally
                if len(batch) >= 5000:
                    stmt = insert(PipelineItem).values(batch).prefix_with("OR IGNORE")
                    session.execute(stmt)
                    session.commit()
                    batch = []
                    seen_in_batch.clear()
                    logger.info(f"Imported {count} unique DNS items...")
        
        if batch:
            stmt = insert(PipelineItem).values(batch).prefix_with("OR IGNORE")
            session.execute(stmt)
            session.commit()
            
        logger.info(f"DNS History Import done. Total Unique in File: {count}")

    except Exception as e:
        logger.error(f"DNS History Import Failed: {e}")
        session.rollback()

def migrate():
    session = SessionLocal()
    
    # 1. Import crawled_results_export.json
    crawled_path = os.path.join(LEGACY_PATH, "arx-w-intel/crawled_results_export.json")
    if os.path.exists(crawled_path):
        logger.info(f"Importing crawled results from {crawled_path}...")
        with open(crawled_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        for entry in data:
            try:
                fqdn = entry.get('fqdn')
                if not fqdn: continue
                
                # Check exist
                existing = session.query(PipelineItem).filter_by(fqdn=fqdn).first()
                if existing:
                    logger.info(f"Skipping existing: {fqdn}")
                    continue
                
                # Save content (if any)
                content = entry.get('content')
                content_path = None
                if content:
                    # Save into v2.0_new/data/crawled
                    # Script is in v2.0_new/tools
                    # We want v2.0_new/data/crawled
                    rel_path = f"../data/crawled/{fqdn}.txt"
                    abs_content_path = os.path.abspath(os.path.join(os.path.dirname(__file__), rel_path))
                    
                    # Store relative path for DB (relative to backend?)
                    # Let's verify dir exists
                    os.makedirs(os.path.dirname(abs_content_path), exist_ok=True)
                    
                    with open(abs_content_path, 'w', encoding='utf-8') as cf:
                        cf.write(content)
                    
                    # Store path relative to project root or data dir
                    content_path = f"data/crawled/{fqdn}.txt"
                
                # Create Item
                item = PipelineItem(
                    fqdn=fqdn,
                    status=PipelineStatus.CRAWLED_SUCCESS if content else PipelineStatus.CRAWLED_FAIL,
                    source="v1_export",
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                session.add(item)
                session.flush() # get ID
                
                # Create CrawlResult
                result = CrawlResult(
                    item_id=item.id,
                    url=entry.get('url'),
                    html_content_path=content_path,
                    http_status=200 if content else 0
                )
                session.add(result)
                session.add(PipelineLog(item_id=item.id, stage="MIGRATION", level="INFO", message="Imported from v1.0"))
                
            except Exception as e:
                logger.error(f"Error importing {entry.get('fqdn')}: {e}")
                session.rollback()
        
        session.commit()
        logger.info("Crawled results import done.")

    # 2. Import training_data.csv as KNOWLEDGE BASE
    csv_path = os.path.join(LEGACY_PATH, "arx-w-intel/training_data.csv")
    if os.path.exists(csv_path):
        logger.info(f"Importing KB from {csv_path}...")
        try:
            with open(csv_path, 'r', encoding='utf-8', errors='replace') as f:
                reader = csv.reader(f)
                next(reader, None) # Skip header if exists (saw header in cat output?) No, "487" looked like data.
                # Actually grep output showed "487",... as line 5. Let's assume consistent format.
                # The grep output: "487","690628","www.g-music.com.tw","/Arts & Entertainment/Music & Audio"
                
                for row in reader:
                    # Defensive parsing
                    if len(row) < 4: continue
                    fqdn = row[2]
                    category = row[3]
                    
                    if not fqdn or "." not in fqdn: continue
                    
                    # Check exist
                    if session.query(PipelineItem).filter_by(fqdn=fqdn).first():
                        continue
                        
                    item = PipelineItem(
                        fqdn=fqdn,
                        status=PipelineStatus.COMPLETED,
                        source="v1_training_csv",
                        priority=4, # Low priority archive
                        created_at=datetime.now()
                    )
                    session.add(item)
                    session.flush()
                    
                    analysis = AnalysisResult(
                        item_id=item.id,
                        category_main=category,
                        is_malicious=False, # Default for training data?
                        confidence_score=1.0,
                        llm_model_used="v1_training_data"
                    )
                    session.add(analysis)
                    
                    if len(session.new) > 1000:
                        session.commit()
                        logger.info("Committed batch of 1000...")
                        
            session.commit()
            logger.info("KB Import done.")
        except Exception as e:
            logger.error(f"CSV Import Failed: {e}")

    # 3. Import Tranco Top 1M
    import_tranco(session)
    
    # 4. Import Merged Data (Hagezi etc)
    import_merged_data(session)

    # 5. Import Real DNS History
    import_dns_history(session)

if __name__ == "__main__":
    migrate()
