from app.services.vector_service import vector_service

def test_lookup():
    fqdn = "www.crazygames.co.kr"
    print(f"Testing lookup for {fqdn}...")
    try:
        # 1. Exact Match Test
        res = vector_service.get_item(fqdn)
        print(f"Exact Match Result: {res}")
        
        # 2. Search Test
        res2 = vector_service.search(fqdn)
        print(f"Search Result: {res2}")
        
    except Exception as e:
        print(f"CRASH: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_lookup()
