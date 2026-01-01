from sqlalchemy.orm import Session
from app.core.database import SessionLocal
from app.models.category import CategoryDefinition

# Expert Descriptions for High-Precision LLM Classification
# Format: [Core Definition]. [Inclusions/Examples]. [Exclusions/Criteria].
CATEGORY_DESCRIPTIONS = {
    "Business/IT": "Websites representing corporate entities or providing professional services and technology solutions. Includes SaaS platforms, IT consulting, software documentation, and corporate portfolios. Excludes sites explicitly focused on selling physical consumer goods (Shopping).",
    "News/Media": "Sources of current events, journalism, and public information. Includes online newspapers, broadcast networks, weather reports, and editorial blogs. Content is typically factual and updated frequently.",
    "Education": "Institutions and resources dedicated to learning and academic research. Includes universities, schools, online courses (MOOCs), dictionaries, libraries, and scholarly journals.",
    "Government": "Official websites of government bodies, agencies, and civic services. Includes ministries, embassies, city councils, tax offices, and military sites. Often uses .gov or .mil TLDs.",
    "Shopping": "Websites dedicated to selling goods or services to consumers. Includes online retail stores, marketplaces (like Amazon), auction sites, and product catalogs that feature a shopping cart or checkout process.",
    "Entertainment": "Sites designed for leisure, amusement, and pop culture consumption. Includes movie reviews, celebrity news, humor/memes, comics, and art showcases. Excludes Adult content.",
    "Travel": "Services for planning and booking travel. Includes airlines, hotels, tourism guides, travel agencies, maps, and car rentals.",
    "Sports": "Content related to athletic activities, teams, and competitions. Includes match scores, sports news, fan clubs, and fantasy leagues.",
    "Social Network": "Platforms allowing users to create profiles and interact with others. Includes social media (Facebook, X), professional networking (LinkedIn), dating apps, and forums.",
    "Email/Chat": "Communication tools for messaging. Includes webmail providers, instant messaging clients, and team collaboration platforms (Slack, Discord).",
    "Games": "Websites focused on video games. Includes playable browser games, game reviews, walkthroughs, cheating tools, and gaming community forums.",
    "Streaming/Video": "Platforms primarily for hosting and viewing video or live stream content. Includes YouTube, Twitch, Vimeo, and OTT services. Focus is on heavy media consumption.",
    "P2P/FileSharing": "Platforms and protocols designed for sharing digital files between users or hosting files for public download. Includes BitTorrent indices, cloud file storage with public sharing(Cyberlockers), and warez sites. Often poses a high risk of malware distribution.",
    "Gambling": "Sites involving wagering money on uncertain outcomes. Includes online casinos, sports betting, poker, lotteries, and sweepstakes.",
    "Adult": "Content containing explicit sexual material, pornography, or erotica. Intended for mature audiences only.",
    "Crypto/Finance": "Services related to money management and digital assets. Includes online banking, stock trading, cryptocurrency exchanges, wallets, insurance, and financial news.",
    "Malicious": "Websites confirmed to incur harm. Includes phishing pages, malware downloads, Command & Control (C2) servers, and scam sites.",
    "Uncategorized": "Websites that cannot be classified due to lack of content or access issues. Includes 404/403 errors, default server pages, 'Under Construction' placeholders, or purely non-textual sites."
}

def update_descriptions():
    db: Session = SessionLocal()
    try:
        updated_count = 0
        print("Starting Category Description Update...")
        
        for name, desc in CATEGORY_DESCRIPTIONS.items():
            cat = db.query(CategoryDefinition).filter(CategoryDefinition.name == name).first()
            if cat:
                if cat.description != desc:
                    print(f"Updating '{name}'...")
                    cat.description = desc
                    updated_count += 1
            else:
                print(f"Creating missing category: '{name}'")
                db.add(CategoryDefinition(name=name, description=desc, is_system=(name in ["Uncategorized", "Malicious"])))
                updated_count += 1
        
        db.commit()
        print(f"✅ Successfully updated {updated_count} categories with expert descriptions.")
        
    except Exception as e:
        print(f"❌ Error updating categories: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    update_descriptions()
