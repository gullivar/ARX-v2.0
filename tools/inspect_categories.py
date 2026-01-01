from sqlalchemy import func
from app.core.database import SessionLocal
from app.models.pipeline import AnalysisResult

def inspect_categories():
    db = SessionLocal()
    try:
        print("=== Category Distribution Inspection ===")
        # Group by category_main to see all distinct values
        usage = db.query(AnalysisResult.category_main, func.count(AnalysisResult.id))\
                  .group_by(AnalysisResult.category_main)\
                  .order_by(func.count(AnalysisResult.id).desc()).all()
        
        total_count = 0
        for cat, count in usage:
            cat_name = f"'{cat}'" if cat else "NULL/None"
            print(f"{cat_name}: {count:,}")
            total_count += count
            
        print(f"=== Total Items: {total_count:,} ===")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    inspect_categories()
