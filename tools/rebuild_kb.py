import sys
import os
import logging
from tqdm import tqdm

# Robust path setup
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)
backend_dir = os.path.join(project_root, 'backend')
sys.path.append(backend_dir)
print(f"Added {backend_dir} to sys.path")



from app.core.database import SessionLocal
from app.models.pipeline import PipelineItem, AnalysisResult, CrawlResult, PipelineStatus
# Note: We import vector_service locally inside function to avoid startup errors if libraries are missing during init

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def rebuild_kb():
    print("Initializing Database Session...")
    db = SessionLocal()
    
    try:
        print("Importing Vector Service...")
        from app.services.vector_service import vector_service
        
        print("Fetching analyzed items from SQL DB...")
        # Fetch all items that have an analysis result
        results = db.query(PipelineItem, AnalysisResult, CrawlResult)\
            .join(AnalysisResult, PipelineItem.id == AnalysisResult.item_id)\
            .outerjoin(CrawlResult, PipelineItem.id == CrawlResult.item_id)\
            .all()
            
        total = len(results)
        print(f"Found {total} items with analysis results. Starting Vector Indexing...")
        
        success_count = 0
        
        for item, analysis, crawl in tqdm(results, desc="Indexing"):
            try:
                # Reconstruct content snippet
                content_snippet = ""
                if crawl and crawl.html_content_path:
                    try:
                        # Path logic: stored as 'data/crawled/...' relative to backend
                        # We are at project root. Backend is ./backend
                        full_path = os.path.join('backend', crawl.html_content_path)
                        
                        if os.path.exists(full_path):
                            with open(full_path, 'r', encoding='utf-8', errors='ignore') as f:
                                content_snippet = f.read()[:1000] # First 1000 chars
                    except Exception as ex:
                        # logger.warning(f"Could not read content for {item.fqdn}: {ex}")
                        pass
                
                rich_summary = f"Summary: {analysis.summary}\n\nEvidence: {content_snippet}"
                
                vector_service.add_item(
                    fqdn=item.fqdn,
                    content_summary=rich_summary,
                    category=analysis.category_main,
                    is_malicious=analysis.is_malicious
                )
                
                # Update status to COMPLETED if not already (just consistency check)
                if item.status != PipelineStatus.COMPLETED:
                     item.status = PipelineStatus.COMPLETED
                     db.add(item)
                
                success_count += 1
                
                # Commit every 100 items
                if success_count % 100 == 0:
                    db.commit()

            except Exception as e:
                logger.error(f"Failed to index {item.fqdn}: {e}")
        
        db.commit()
        print(f"\n✅ Rebuild Complete! Indexed {success_count}/{total} items into ChromaDB.")
            
    except ImportError as ie:
        print(f"❌ Error: Could not import dependencies. {ie}")
    except Exception as e:
        print(f"❌ Critical Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    rebuild_kb()
