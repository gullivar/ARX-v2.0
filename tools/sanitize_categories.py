from sqlalchemy.orm import Session
from sqlalchemy import not_
from app.core.database import SessionLocal
from app.models.pipeline import AnalysisResult

STANDARD_CATEGORIES = [
    "Business/IT", "News/Media", "Education", "Government", "Shopping",
    "Entertainment", "Travel", "Sports", "Social Network", "Email/Chat",
    "Games", "Streaming/Video", "P2P/FileSharing", "Gambling", "Adult",
    "Crypto/Finance", "Malicious", "Uncategorized"
]

def sanitize_categories():
    db = SessionLocal()
    try:
        print("=== Sanitizing Invalid Categories ===")
        
        # Check count before
        invalid_count = db.query(AnalysisResult)\
            .filter(not_(AnalysisResult.category_main.in_(STANDARD_CATEGORIES)))\
            .count()
            
        print(f"Found {invalid_count} items with invalid categories.")
        
        if invalid_count > 0:
            print("Updating invalid categories to 'Uncategorized'...")
            # Bulk Update
            db.query(AnalysisResult)\
              .filter(not_(AnalysisResult.category_main.in_(STANDARD_CATEGORIES)))\
              .update({AnalysisResult.category_main: "Uncategorized"}, synchronize_session=False)
            
            db.commit()
            print(f"✅ Successfully sanitized {invalid_count} items.")
        else:
            print("No invalid categories found.")
            
    except Exception as e:
        print(f"Error: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    sanitize_categories()
