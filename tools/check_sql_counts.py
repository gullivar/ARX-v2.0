from sqlalchemy import create_engine, text
import os

DB_URL = f"sqlite:///{os.path.abspath('backend/w_intel.db')}"
engine = create_engine(DB_URL)

with engine.connect() as conn:
    result = conn.execute(text("SELECT count(*) FROM analysis_results"))
    print(f"Analysis Results: {result.scalar()}")
    
    result2 = conn.execute(text("SELECT count(*) FROM pipeline_items WHERE status='COMPLETED'"))
    print(f"Completed Items: {result2.scalar()}")
