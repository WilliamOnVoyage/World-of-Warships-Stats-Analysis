import pytest
from httpx import AsyncClient, ASGITransport
from main import app

@pytest.mark.asyncio
async def test_health_check():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}

@pytest.mark.asyncio
async def test_root():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to the WOWS Stats API"}

import os
from sqlmodel import Session, SQLModel, create_engine
from main import app, get_session
from api.wargaming import WargamingAPIClient
from unittest.mock import AsyncMock
import database.models # Import models so they are registered in SQLModel.metadata

# Setup in-memory DB
sqlite_url = "sqlite://"
engine = create_engine(sqlite_url, connect_args={"check_same_thread": False})

def get_session_override():
    with Session(engine) as session:
        yield session

app.dependency_overrides[get_session] = get_session_override

@pytest.fixture(autouse=True)
def setup_db():
    SQLModel.metadata.create_all(engine)
    yield
    SQLModel.metadata.drop_all(engine)

@pytest.mark.asyncio
async def test_get_player_stats(mocker):
    # Mock the Wargaming API
    mock_client = AsyncMock()
    mock_client.get_account_id.return_value = 99999
    
    mock_info = {
        "99999": {
            "account_id": 99999,
            "nickname": "TestPlayer",
            "hidden_profile": False,
            "statistics": {
                "battles": 50,
                "distance": 1000,
                "pvp": {
                    "battles": 50,
                    "wins": 30,
                    "survived_battles": 10,
                    "frags": 20,
                    "damage_dealt": 50000,
                    "xp": 100000
                }
            }
        }
    }
    mock_client.get_player_info.return_value = mock_info
    mock_client.get_clan_account_info.return_value = None
    mock_client.get_ship_stats.return_value = []

    # Patch the initialization in main.py to use our mock
    mocker.patch("main.WargamingAPIClient", return_value=mock_client)
    
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/player/TestPlayer")
        
    assert response.status_code == 200
    data = response.json()
    assert data["username"] == "TestPlayer"
    assert data["accountId"] == 99999
    
    assert len(data["history"]) == 1
    assert data["history"][0]["battles"] == 50
    assert data["history"][0]["winRate"] == 60.0

@pytest.mark.asyncio
async def test_leaderboard_endpoint():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/leaderboard?category=win_rate&min_battles=0")
    assert response.status_code == 200
    data = response.json()
    assert "leaderboard" in data
    assert data["category"] == "win_rate"

@pytest.mark.asyncio
async def test_internal_pipeline_status():
    headers = {"X-Internal-Key": "wows-secret-internal-key-2026"}
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/internal/pipeline/status", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert "totalPlayers" in data
    assert "pipelineStates" in data

@pytest.mark.asyncio
async def test_leaderboard_with_modes():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        for mode in ["pvp", "solo", "div", "rank", "pve"]:
            response = await ac.get(f"/api/leaderboard?category=win_rate&mode={mode}&min_battles=0")
            assert response.status_code == 200
            data = response.json()
            assert data["mode"] == mode
            assert "leaderboard" in data

@pytest.mark.asyncio
async def test_encyclopedia_endpoints(mocker):
    # Mock WG API client for sync or direct query
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/encyclopedia/ships?limit=10")
        assert response.status_code == 200
        data = response.json()
        assert "ships" in data
        assert "total" in data

@pytest.mark.asyncio
async def test_clan_leaderboard():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/leaderboard/clans")
        assert response.status_code == 200
        data = response.json()
        assert "clans" in data
