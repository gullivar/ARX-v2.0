import sys
import os

# Add backend to path
sys.path.append(os.getcwd())

import logging
logging.basicConfig(level=logging.DEBUG)

def test_init():
    print("Testing VectorService Init...")
    try:
        from app.services.vector_service import vector_service
        print(f"Service instantiated: {vector_service}")
        print(f"Collection: {vector_service.collection}")
        
        if vector_service.collection is None:
            print("❌ Collection is NONE. Init failed.")
        else:
            print("✅ Collection is READY.")
            print(f"Count: {vector_service.collection.count()}")

    except Exception as e:
        print(f"❌ Exception during import/init: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_init()
