from app.core.database import engine
from app.models.pipeline import Base
from app.models.category import CategoryDefinition
from sqlalchemy.orm import Session
from app.core.database import SessionLocal

def init_db():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("Database tables created successfully!")
    seed_categories()

def seed_categories():
    db = SessionLocal()
    try:
        # Standard 18 Categories
        cats = [
            "Business/IT", "News/Media", "Education", "Government",
            "Shopping", "Entertainment", "Travel", "Sports",
            "Social Network", "Email/Chat",
            "Games", "Streaming/Video", "P2P/FileSharing", "Gambling", "Adult", "Crypto/Finance",
            "Malicious", "Uncategorized"
        ]
        
        for name in cats:
            exists = db.query(CategoryDefinition).filter(CategoryDefinition.name == name).first()
            if not exists:
                print(f"Seeding category: {name}")
                db.add(CategoryDefinition(name=name, is_system=(name in ["Uncategorized", "Malicious"])))
        db.commit()
    except Exception as e:
        print(f"Error seeding categories: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    init_db()
