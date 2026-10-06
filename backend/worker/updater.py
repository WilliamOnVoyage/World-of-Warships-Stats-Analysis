import asyncio
import os
import json
import traceback
from datetime import datetime, timezone
from dotenv import load_dotenv
load_dotenv()

from sqlmodel import create_engine, Session
from database.models import Player, PlayerSnapshot, create_partition_if_not_exists
from api.wargaming import WargamingAPIClient

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./wows_dev.db")
engine = create_engine(DATABASE_URL)

DATA_DIR = os.getenv("DATA_DIR", "/app/data" if os.path.exists("/app") else "data")
os.makedirs(DATA_DIR, exist_ok=True)
STATE_FILE = os.path.join(DATA_DIR, "scraper_state.json")

# ID ranges for active Wargaming regions
REGIONS = {
    "na": (1_000_000_000, 2_000_000_000),
    "eu": (500_000_000, 1_000_000_000),
    "asia": (2_000_000_000, 3_000_000_000)
}

def load_state():
    if os.path.exists(STATE_FILE):
        try:
            with open(STATE_FILE, "r") as f:
                return json.load(f)
        except Exception:
            pass
    return {"current_region": "na", "current_id": 1_000_000_000}

def save_state(region: str, current_id: int):
    try:
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, "w") as f:
            json.dump({"current_region": region, "current_id": current_id}, f)
    except Exception as e:
        print(f"Failed to save state: {e}")

async def scrape_region(region: str, start_id: int, end_id: int):
    print(f"[{datetime.now(timezone.utc).isoformat()}] Starting scraping for region {region.upper()} from ID {start_id}")
    
    app_id = os.getenv("WARGAMING_APP_ID")
    if not app_id:
        raise ValueError("WARGAMING_APP_ID environment variable not set.")
        
    client = WargamingAPIClient(application_id=app_id, realm=region)
    chunk_size = 100
    
    # Iterate through the ID range
    for current_id in range(start_id, end_id, chunk_size):
        batch = list(range(current_id, current_id + chunk_size))
        
        try:
            # The client handles rate limiting internally (10 req/s)
            data = await client.get_player_info(batch)
            
            if not data:
                # Save state and move on
                save_state(region, current_id + chunk_size)
                continue
                
            now = datetime.now(timezone.utc)
            
            with Session(engine) as session:
                create_partition_if_not_exists(session.get_bind(), now)
                valid_count = 0
                for acc_id_str, info in data.items():
                    if not info or info.get("hidden_profile"):
                        continue
                        
                    stats = info.get("statistics", {}).get("pvp", {})
                    
                    if not stats or stats.get("battles", 0) == 0:
                        continue
                        
                    acc_id = int(acc_id_str)
                    valid_count += 1
                    
                    # 1. Upsert Player
                    player = session.get(Player, acc_id)
                    if not player:
                        nickname_val = info.get("nickname") or "Unknown"
                        created_at_val = info.get("created_at")
                        created_at_dt = (
                            datetime.fromtimestamp(created_at_val, tz=timezone.utc)
                            if created_at_val is not None
                            else now
                        )
                        player = Player(
                            account_id=acc_id,
                            nickname=nickname_val,
                            realm=region,
                            created_at=created_at_dt
                        )
                    player.last_updated = now
                    session.add(player)
                    
                    # 2. Insert Snapshot
                    snapshot = PlayerSnapshot(
                        account_id=acc_id,
                        timestamp=now,
                        battles=stats.get("battles", 0),
                        wins=stats.get("wins", 0),
                        damage_dealt=stats.get("damage_dealt", 0),
                        survived=stats.get("survived_battles", 0),
                        frags=stats.get("frags", 0),
                        xp=stats.get("xp", 0)
                    )
                    session.add(snapshot)
                
                session.commit()
                if valid_count > 0:
                    print(f"[{region.upper()}] Processed {current_id} - {current_id+chunk_size} | Found {valid_count} active players")
                
            # Update state checkpoint
            save_state(region, current_id + chunk_size)
            
        except Exception as e:
            print(f"Error at {current_id}: {e}")
            traceback.print_exc()
            # Advance state past the failing chunk so we don't get stuck in a retry loop
            save_state(region, current_id + chunk_size)
            await asyncio.sleep(2)  # Short backoff on error
            
    await client.close()

async def main():
    state = load_state()
    current_region = state["current_region"]
    current_id = state["current_id"]
    
    # We loop forever, rotating through regions
    regions_list = list(REGIONS.keys())
    
    if current_region in regions_list:
        start_index = regions_list.index(current_region)
    else:
        start_index = 0
        
    while True:
        for i in range(start_index, len(regions_list)):
            region = regions_list[i]
            lower, upper = REGIONS[region]
            
            # If we are resuming, use the saved ID, otherwise use the lower bound
            start_id = current_id if (region == current_region) else lower
            
            await scrape_region(region, start_id, upper)
            
            # Reset current_id for the next region
            current_id = 0
            
        # Reset start_index to 0 to loop from the first region again
        start_index = 0
        current_region = regions_list[0]
        current_id = REGIONS[current_region][0]
        print("Completed a full cycle of all regions. Starting again.")

if __name__ == "__main__":
    asyncio.run(main())
