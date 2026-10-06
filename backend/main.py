import os
from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select, create_engine
from sqlalchemy import func, text
from database.models import Player, PlayerSnapshot, create_partition_if_not_exists
from api.wargaming import WargamingAPIClient
from datetime import datetime, timedelta, timezone
import logging

logger = logging.getLogger(__name__)

DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://wows_admin:DevAdminPass2026@localhost:5432/wows_stats_dev")
engine = create_engine(DATABASE_URL)

app = FastAPI(
    title="World of Warships Stats API",
    description="Backend API for WOWS Stats Tracker",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_TRACKED_PLAYERS = 1000

def get_session():
    with Session(engine) as session:
        yield session

@app.get("/")
async def root():
    return {"message": "Welcome to the WOWS Stats API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}


@app.get("/api/stats/overview")
async def get_global_stats(session: Session = Depends(get_session)):
    """Returns aggregate statistics for the landing page."""
    player_count = session.exec(select(func.count()).select_from(Player)).one()
    
    # Get aggregate battle stats from the latest snapshot per player
    # We use a subquery to get the most recent snapshot for each player
    latest_snapshots_query = text("""
        SELECT COALESCE(SUM(sub.battles), 0) AS total_battles,
               COALESCE(AVG(CASE WHEN sub.battles > 0 THEN sub.wins * 100.0 / sub.battles ELSE 0 END), 0) AS avg_win_rate
        FROM (
            SELECT DISTINCT ON (account_id) account_id, battles, wins
            FROM player_snapshot
            ORDER BY account_id, timestamp DESC
        ) sub
    """)
    result = session.exec(latest_snapshots_query).first()

    total_battles = int(result[0]) if result else 0
    avg_win_rate = round(float(result[1]), 2) if result else 0.0

    return {
        "totalPlayers": player_count,
        "totalBattles": total_battles,
        "avgWinRate": avg_win_rate,
        "status": "online"
    }


@app.get("/api/player/{username}")
async def get_player_stats(
    username: str,
    refresh: bool = False,
    session: Session = Depends(get_session)
):
    # 1. Check if player exists in our DB (case-insensitive)
    statement = select(Player).where(func.lower(Player.nickname) == username.lower())
    player = session.exec(statement).first()
    
    app_id = os.getenv("WARGAMING_APP_ID", "demo")
    client = WargamingAPIClient(application_id=app_id)
    
    now = datetime.now(timezone.utc)

    try:
        # Fetch from Wargaming API if player not in DB or refresh requested
        if not player or refresh:
            if not player:
                # Check user cap for dev database
                player_count = session.exec(select(func.count()).select_from(Player)).one()
                if player_count >= MAX_TRACKED_PLAYERS:
                    await client.close()
                    raise HTTPException(status_code=400, detail="Development database has reached its 1000 user capacity limit.")
                    
                account_id = await client.get_account_id(username)
                if not account_id:
                    await client.close()
                    raise HTTPException(status_code=404, detail="Player not found in Wargaming database")
                
                # Add player
                player = Player(account_id=account_id, nickname=username, realm="na", last_updated=now, created_at=now)
                session.add(player)
            else:
                account_id = player.account_id
                player.last_updated = now
                session.add(player)
            
            # Fetch current cumulative stats
            info_data = await client.get_player_info([account_id])
            info = info_data.get(str(account_id), {})
            stats = info.get("statistics", {}).get("pvp", {})
            
            if stats and stats.get("battles", 0) > 0:
                # Save today's cumulative snapshot using PVP (Random Battles) stats
                create_partition_if_not_exists(session.get_bind(), now)
                snapshot = PlayerSnapshot(
                    account_id=account_id,
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
            session.refresh(player)
    finally:
        await client.close()

    # Fetch historical stats from our DB
    stats_stmt = (
        select(PlayerSnapshot)
        .where(PlayerSnapshot.account_id == player.account_id)
        .order_by(PlayerSnapshot.timestamp.desc())
        .limit(90)
    )
    snapshots = session.exec(stats_stmt).all()
    
    if not snapshots:
        raise HTTPException(status_code=404, detail="No stats available for player")
        
    latest = snapshots[0]
    
    # Calculate some derived stats
    win_rate = (latest.wins / latest.battles * 100) if latest.battles > 0 else 0
    avg_damage = (latest.damage_dealt / latest.battles) if latest.battles > 0 else 0
    
    # Format for frontend
    history = []
    for s in reversed(snapshots):
        history.append({
            "date": s.timestamp.strftime("%Y-%m-%d"),
            "battles": s.battles,
            "winRate": round((s.wins / s.battles * 100) if s.battles > 0 else 0, 2),
            "avgDamage": round((s.damage_dealt / s.battles) if s.battles > 0 else 0, 0)
        })

    return {
        "username": player.nickname,
        "accountId": player.account_id,
        "realm": player.realm,
        "lastUpdated": player.last_updated.isoformat(),
        "stats": {
            "battles": latest.battles,
            "winRate": round(win_rate, 2),
            "avgDamage": round(avg_damage, 0),
            "survived": latest.survived,
            "frags": latest.frags,
            "xp": latest.xp
        },
        "history": history
    }

