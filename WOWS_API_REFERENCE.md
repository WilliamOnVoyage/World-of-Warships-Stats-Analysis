# World of Warships (WoWs) API Reference

This document serves as a quick reference for the essential Wargaming.net API endpoints we will use for the WoWs Stats Tracker. 

## Base URLs by Region
The API endpoint domain changes depending on the player's server region:
- **NA:** `https://api.worldofwarships.com`
- **EU:** `https://api.worldofwarships.eu`
- **ASIA:** `https://api.worldofwarships.asia`

*All requests require your `application_id` as a query parameter.*

---

## 1. Player Search (Account List)
Used to find a player's `account_id` using their in-game username.

- **Endpoint:** `GET /wows/account/list/`
- **Parameters:**
  - `application_id` (string, required)
  - `search` (string, required): Player name to search for (minimum 3 characters).
- **Response Schema:**
  ```json
  {
    "status": "ok",
    "meta": {"count": 1},
    "data": [
      {
        "nickname": "zmlzeze",
        "account_id": 1008331251
      }
    ]
  }
  ```

---

## 2. Player Personal Data (Account Info)
Used to get the overall and PVP statistics for one or more players.

- **Endpoint:** `GET /wows/account/info/`
- **Parameters:**
  - `application_id` (string, required)
  - `account_id` (string, required): Comma-separated list of account IDs (up to 100 per request).
- **Response Schema:**
  ```json
  {
    "status": "ok",
    "data": {
      "1008331251": {
        "hidden_profile": false,
        "statistics": {
          "battles": 3143,
          "distance": 117155,
          "pvp": {
            "wins": 1742,
            "damage_dealt": 213130514,
            "survived_battles": 1356,
            "frags": 3612,
            "planes_killed": 5550,
            "xp": 3923528
          }
        }
      }
    }
  }
  ```

---

## 3. Player Ship Statistics
Used to get the performance of a player on every specific ship they have played.

- **Endpoint:** `GET /wows/ships/stats/`
- **Parameters:**
  - `application_id` (string, required)
  - `account_id` (string, required): Player ID.
- **Response Data:** Returns an array of objects for each `ship_id` containing battles, wins, damage, etc.

---

## 4. Encyclopedia (Static Game Data)
Used to map numeric IDs (like `ship_id`) to human-readable names and types.

- **Endpoint:** `GET /wows/encyclopedia/ships/`
- **Parameters:**
  - `application_id` (string, required)
  - `limit` (int): For pagination (max 100).
  - `page_no` (int): Page number.
- **Response Data:** Returns ship names, tier, nation, type (e.g., Destroyer, Cruiser), and images.

---

## 5. Historical Player Data (Stats By Date)
Used to retrieve snapshots of a player's statistics for specific past dates. This is critical for charting historical trends and calculating recent performance (e.g., "last 7 days").

- **Endpoint:** `GET /wows/account/statsbydate/`
- **Parameters:**
  - `application_id` (string, required)
  - `account_id` (string, required): Player ID.
  - `dates` (string, optional): Comma-separated list of dates (format: `YYYYMMDD`). If not provided, it may return up to 28 days of history by default depending on the region's API configuration.
- **Response Schema:**
  ```json
  {
    "status": "ok",
    "data": {
      "1008331251": {
        "pvp": {
          "20230510": {
            "battles": 3140,
            "wins": 1740,
            "damage_dealt": 213000000
          },
          "20230511": {
            "battles": 3143,
            "wins": 1742,
            "damage_dealt": 213130514
          }
        }
      }
    }
  }
  ```
  *Note: While this endpoint provides historical data, the official Wargaming API does not guarantee 10 years of unbroken match-by-match history. This is why our own "Lazy Tracking" database pipeline is crucial—we pull whatever history we can get via `statsbydate`, but we also save our own daily snapshots going forward to guarantee data integrity.*
