import os
import httpx
import asyncio
from typing import Dict, Any, List, Optional
from aiolimiter import AsyncLimiter
from datetime import datetime

class WargamingAPIClient:
    def __init__(self, application_id: str, realm: str = "na", rate_limiter: Optional[AsyncLimiter] = None):
        self.application_id = application_id
        self.realm = realm.lower()
        
        realm_mapping = {
            "na": "https://api.worldofwarships.com",
            "eu": "https://api.worldofwarships.eu",
            "asia": "https://api.worldofwarships.asia"
        }
        self.base_url = realm_mapping.get(self.realm, realm_mapping["na"])
        
        # Shared or instance rate limiter
        self.rate_limiter = rate_limiter or AsyncLimiter(10, 1)
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=30.0)

    async def close(self):
        await self.client.aclose()

    async def _make_request(self, endpoint: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Internal method to handle rate limiting and JSON parsing."""
        params["application_id"] = self.application_id
        
        async with self.rate_limiter:
            response = await self.client.get(endpoint, params=params)
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "ok":
                raise Exception(f"Wargaming API Error: {data.get('error', 'Unknown Error')}")
                
            return data.get("data", {})

    async def get_account_id(self, username: str) -> Optional[int]:
        """Search for a player and return their exact account ID."""
        params = {"search": username, "type": "exact"}
        data = await self._make_request("/wows/account/list/", params)
        
        if data and len(data) > 0:
            return data[0]["account_id"]
        return None

    async def get_player_info(
        self,
        account_ids: List[int],
        extra: Optional[str] = None
    ) -> Dict[str, Any]:
        """Get cumulative PVP statistics and game modes for a list of account IDs (max 100)."""
        if not account_ids:
            return {}
            
        account_ids_str = ",".join(map(str, account_ids))
        params = {"account_id": account_ids_str}
        if extra:
            params["extra"] = extra
        
        return await self._make_request("/wows/account/info/", params)

    async def get_ship_stats(self, account_id: int) -> List[Dict[str, Any]]:
        """Get per-ship statistics for a single player."""
        params = {"account_id": str(account_id)}
        data = await self._make_request("/wows/ships/stats/", params)
        return data.get(str(account_id), [])

    async def get_clan_account_info(self, account_id: int) -> Optional[Dict[str, Any]]:
        """Get player clan membership info."""
        params = {"account_id": str(account_id), "extra": "clan"}
        data = await self._make_request("/wows/clans/accountinfo/", params)
        return data.get(str(account_id))

    async def get_clan_info(self, clan_id: int) -> Optional[Dict[str, Any]]:
        """Get clan details and roster."""
        params = {"clan_id": str(clan_id), "extra": "members"}
        data = await self._make_request("/wows/clans/info/", params)
        return data.get(str(clan_id))

    async def search_clans(self, search: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Search clans by tag or name."""
        params = {"search": search, "limit": limit}
        data = await self._make_request("/wows/clans/list/", params)
        return data if isinstance(data, list) else []

    async def get_clans_list(self, page_no: int = 1, limit: int = 100) -> List[Dict[str, Any]]:
        """Fetch page of clans from official registry."""
        params = {"page_no": page_no, "limit": limit}
        data = await self._make_request("/wows/clans/list/", params)
        return data if isinstance(data, list) else []

    async def get_clans_batch_info(self, clan_ids: List[int]) -> Dict[str, Any]:
        """Fetch rosters and details for up to 100 clans in a single request."""
        if not clan_ids:
            return {}
        params = {"clan_id": ",".join(map(str, clan_ids)), "extra": "members"}
        return await self._make_request("/wows/clans/info/", params)

    async def get_encyclopedia_ships(
        self,
        page_no: int = 1,
        limit: int = 100
    ) -> Dict[str, Any]:
        """Fetch page of ships from official encyclopedia."""
        params = {
            "page_no": page_no,
            "limit": limit,
            "fields": "ship_id,name,tier,type,nation,images.small,images.large,is_premium,description"
        }
        return await self._make_request("/wows/encyclopedia/ships/", params)

    async def get_ship_info(self, ship_id: int) -> Optional[Dict[str, Any]]:
        """Fetch full technical dossier and profile for a specific ship."""
        params = {"ship_id": str(ship_id)}
        data = await self._make_request("/wows/encyclopedia/ships/", params)
        if data and isinstance(data, dict) and str(ship_id) in data:
            return data[str(ship_id)]
        return None
