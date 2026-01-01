from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.pipeline import PipelineItem, AnalysisResult, CrawlResult, PipelineStatus

def reset_uncategorized_to_discovered():
    db = SessionLocal()
    try:
        print("=== Resetting Uncategorized Items to DISCOVERED ===")
        
        # 1. Find IDs of items that are Uncategorized
        # We look for "Uncategorized" in AnalysisResult
        target_ids = db.query(AnalysisResult.item_id).filter(
            AnalysisResult.category_main == "Uncategorized"
        ).all()
        target_ids = [t[0] for t in target_ids]
        
        count = len(target_ids)
        print(f"Found {count} items marked as Uncategorized.")
        
        if count == 0:
            print("Nothing to reset.")
            return

        # 2. Delete Analysis Results (Clean slate)
        print(f"Deleting {count} AnalysisResult entries...")
        db.query(AnalysisResult).filter(AnalysisResult.item_id.in_(target_ids)).delete(synchronize_session=False)
        
        # 3. Delete Crawl Results (To force re-crawl)
        # Option: IF you trust the crawl content, skip this. But suspicious data suggests re-crawl.
        print(f"Deleting CrawlResult entries to force fresh crawl...")
        db.query(CrawlResult).filter(CrawlResult.item_id.in_(target_ids)).delete(synchronize_session=False)
        
        # 4. Update PipelineItem status to DISCOVERED
        print(f"Updating PipelineItem status to DISCOVERED...")
        # Process in batches to avoid lock issues
        batch_size = 5000
        for i in range(0, count, batch_size):
            batch_ids = target_ids[i:i+batch_size]
            db.query(PipelineItem).filter(PipelineItem.id.in_(batch_ids))\
                .update({PipelineItem.status: PipelineStatus.DISCOVERED}, synchronize_session=False)
            db.commit()
            print(f"Processed batch {i}-{i+len(batch_ids)}...")
            
        print("✅ Reset Complete. Orchestrator will pick these up automatically.")
            
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    reset_uncategorized_to_discovered()
