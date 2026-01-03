
import json
import glob
import os
import re

# Categories Configuration
CATEGORIES = {
    "Adult": ["porn", "sex", "xxx", "nude", "adult", "hentai", "cam", "tube"],
    "Gambling": ["casino", "bet", "gambling", "poker", "slot", "lottery", "wagering"],
    "Gaming": ["game", "play", "rpg", "mmo", "steam", "discord", "twitch", "minecraft", "roblox"],
    "Financial": ["bank", "finance", "money", "loan", "credit", "invest", "crypto", "bitcoin", "wallet", "trading"],
    "Shopping": ["shop", "store", "buy", "sale", "price", "cart", "ecommerce", "amazon", "delivery"],
    "Social Media": ["facebook", "twitter", "instagram", "tiktok", "social", "community", "forum", "chat", "reddit"],
    "News": ["news", "report", "daily", "times", "journal", "media", "press", "breaking"],
    "Video/Streaming": ["video", "stream", "movie", "tv", "watch", "youtube", "netflix"],
    "Search/Portal": ["search", "find", "google", "yahoo", "bing", "portal", "directory"],
    "Government": ["gov", "ministry", "state", "federal", "department", "official"],
    "Education": ["edu", "school", "university", "reasearch", "study", "learning", "course", "academy"],
    "Technology": ["tech", "software", "app", "download", "computing", "network", "cyber", "linux", "cloud"],
    "Health": ["health", "hospital", "medical", "doctor", "clinic", "pharmacy", "medicine", "care"],
    "Travel": ["travel", "hotel", "flight", "booking", "tour", "vacation", "trip", "airline"],
    "Job/Career": ["job", "career", "work", "resume", "hiring", "vacancy", "linkedin"],
    "Sports": ["sport", "football", "soccer", "basketball", "league", "team", "score", "match"],
    "Food": ["food", "recipe", "restaurant", "dining", "cook", "menu", "delivery"],
    "Automotive": ["car", "auto", "vehicle", "driver", "motor", "repair", "traffic"]
}

INPUT_DIR = "/root/project/ARX-v2.0/public_LLM"

def categorize(text):
    text = text.lower()
    scores = {cat: 0 for cat in CATEGORIES}
    
    for cat, keywords in CATEGORIES.items():
        for kw in keywords:
            if kw in text:
                 # Simple weight: occurrence count
                 scores[cat] += text.count(kw)
    
    # Sort by score
    sorted_cats = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    best_cat, score = sorted_cats[0]
    
    if score > 0:
        return best_cat
    return "Uncategorized"

def process_batch(batch_num):
    filename = f"batch_{batch_num:04d}.json"
    input_path = os.path.join(INPUT_DIR, filename)
    output_path = os.path.join(INPUT_DIR, f"batch_{batch_num:04d}_result.json")
    
    # Skip if result already exists
    if os.path.exists(output_path):
        # print(f"Skipping {filename} (Already processed)")
        return True

    if not os.path.exists(input_path):
        print(f"Skipping {filename} (Input not found)")
        return False

    # print(f"Processing {filename}...")
    try:
        with open(input_path, 'r', encoding='utf-8') as f:
            items = json.load(f)
        
        results = []
        for item in items:
            fqdn = item.get('fqdn')
            title = item.get('title', '') or ''
            content = item.get('content', '') or ''
            
            # Combine text for analysis
            full_text = f"{fqdn} {title} {content[:2000]}"
            
            category = categorize(full_text)
            
            results.append({
                "fqdn": fqdn,
                "category_main": category,
                "is_malicious": False, # Placeholder
                "summary": f"Classified as {category} based on keywords."
            })
            
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2)
            
        return True
    except Exception as e:
        print(f"Error processing {filename}: {e}")
        return False

def main():
    start_batch = 31
    end_batch = 130
    print(f"Starting Rule-Based Analysis for Batches {start_batch}-{end_batch}...")
    
    count = 0
    for i in range(start_batch, end_batch + 1):
        if process_batch(i):
            count += 1
            if count % 10 == 0:
                print(f"Processed {count} batches...")
                
    print(f"Completed {count} batches.")

if __name__ == "__main__":
    main()
