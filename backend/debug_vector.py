import sys
import os
sys.path.append(os.getcwd())

try:
    from app.services.vector_service import vector_service
    print("VectorService imported successfully.")
    
    print("Testing Search...")
    results = vector_service.search("test")
    print(f"Search Results: {results}")

    print("Testing Add...")
    vector_service.add_item("test.com", "Summary: Test\n\nEvidence: Test Content", "Test", True)
    print("Add Successful.")

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
