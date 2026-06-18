import asyncio
import os
from datetime import datetime, timezone
from sqlmodel import create_engine, Session, select
from database.models import Player, PlayerSnapshot, create_partition_if_not_exists
from api.wargaming import WargamingAPIClient

# Database connection
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./wows_dev.db")
engine = create_engine(DATABASE_URL)

async def run_daily_update():
    """
    Nightly cron job to update all players in the active roster.
    """
    print(f"[{datetime.utcnow().isoformat()}] Starting daily stats update...")
    
    app_id = os.getenv("WARGAMING_APP_ID")
    if not app_id:
        print("Error: WARGAMING_APP_ID environment variable not set.")
        return

    client = WargamingAPIClient(application_id=app_id)
    
    # Ensure this month's partition exists
    now = datetime.utcnow()
    create_partition_if_not_exists(engine, now)
    
    with Session(engine) as session:
        # Get all players
        players = session.exec(select(Player)).all()
        account_ids = [p.account_id for p in players]
        
        if not account_ids:
            print("No players in active roster. Exiting.")
            await client.close()
            return
            
        print(f"Found {len(account_ids)} players in roster. Fetching updates...")
        
        # Batch into chunks of 100
        chunk_size = 100
        for i in range(0, len(account_ids), chunk_size):
            batch = account_ids[i:i + chunk_size]
            
            try:
                data = await client.get_player_info(batch)
                
                for acc_id_str, info in data.items():
                    if not info or info.get("hidden_profile"):
                        continue
                        
                    stats = info.get("statistics", {}).get("pvp", {})
                    overall = info.get("statistics", {})
                    
                    if not stats:
                        continue
                        
                    acc_id = int(acc_id_str)
                    
                    # Create today's snapshot
                    snapshot = PlayerSnapshot(
                        account_id=acc_id,
                        timestamp=now,
                        battles=overall.get("battles", 0),
                        wins=stats.get("wins", 0),
                        damage_dealt=stats.get("damage_dealt", 0),
                        survived=stats.get("survived_battles", 0),
                        frags=stats.get("frags", 0),
                        xp=stats.get("xp", 0)
                    )
                    
                    # Update Player last_updated
                    player = session.get(Player, acc_id)
                    if player:
                        player.last_updated = now
                        session.add(player)
                        
                    session.add(snapshot)
                
                # Commit batch
                session.commit()
                print(f"Successfully processed batch {i//chunk_size + 1}")
                
            except Exception as e:
                print(f"Error processing batch: {e}")
                session.rollback()
                
    await client.close()
    print(f"[{datetime.utcnow().isoformat()}] Daily stats update completed.")

if __name__ == "__main__":
    asyncio.run(run_daily_update())
