import os
import httpx
import asyncio
from typing import Dict, Any, List, Optional
from aiolimiter import AsyncLimiter
from datetime import datetime

class WargamingAPIClient:
    def __init__(self, application_id: str, realm: str = "na"):
        self.application_id = application_id
        self.realm = realm
        
        # Determine base URL by realm
        realm_mapping = {
            "na": "https://api.worldofwarships.com",
            "eu": "https://api.worldofwarships.eu",
            "asia": "https://api.worldofwarships.asia"
        }
        self.base_url = realm_mapping.get(realm.lower(), realm_mapping["na"])
        
        # Rate limit: max 10 requests per second
        self.rate_limiter = AsyncLimiter(10, 1)
        self.client = httpx.AsyncClient(base_url=self.base_url)

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

    async def get_player_info(self, account_ids: List[int]) -> Dict[str, Any]:
        """Get cumulative PVP statistics for a list of account IDs (max 100)."""
        if not account_ids:
            return {}
            
        account_ids_str = ",".join(map(str, account_ids))
        params = {"account_id": account_ids_str}
        
        return await self._make_request("/wows/account/info/", params)

    async def get_player_stats_by_date(self, account_id: int, dates: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Get historical PVP statistics. 
        Dates should be format YYYYMMDD. If dates is None, API defaults to last 28 days (if available).
        """
        params = {"account_id": str(account_id)}
        if dates:
            params["dates"] = ",".join(dates)
            
        return await self._make_request("/wows/account/statsbydate/", params)
