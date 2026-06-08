#!/usr/bin/env python3
"""
CraftWorld Price Fetcher
Corre cada hora via GitHub Actions.
Consulta GeckoTerminal pool por pool y guarda prices.json en el repo.
"""

import json
import time
import requests
from datetime import datetime, timezone

TOKENS = [
    {"pool": "0xda021b3d91f82bf2bcfc1a8709545c3a643d47de", "name": "COIN",        "isCoin": True },
    {"pool": "0xf14ad4a21a9e71ba967b8b99e278d03a1933b44a", "name": "WATER",       "isCoin": False},
    {"pool": "0xc356cd52364541379ad4d31a889b7031e758220a", "name": "FIRE",        "isCoin": False},
    {"pool": "0xe973dc221bb031010ec673105ed8b04c9e713b9d", "name": "EARTH",       "isCoin": False},
    {"pool": "0xb287ea5a5cd4f2b74571e30fdec96241aa5163d9", "name": "MUD",         "isCoin": False},
    {"pool": "0x8b1a1b7b43a53904b0a05406c13399079e553501", "name": "CLAY",        "isCoin": False},
    {"pool": "0x6d8839a585f7877a5e218a217c07334980f04a4a", "name": "SAND",        "isCoin": False},
    {"pool": "0xa09dda31b854720b6d2f28dee9c87b05d0b80d14", "name": "COPPER",      "isCoin": False},
    {"pool": "0xda4145a4975b1219e85a233673187309c4840044", "name": "STONE",       "isCoin": False},
    {"pool": "0xfa3a564b27deb29781f80032df662a4406eebef6", "name": "CERAMICS",    "isCoin": False},
    {"pool": "0x7aa1cc00ca62982ab10d12fd4f6b6687f33011ad", "name": "GLASS",       "isCoin": False},
    {"pool": "0x70c063f17dacb35e4b3df06c8f36020416a44a3c", "name": "STEEL",       "isCoin": False},
    {"pool": "0x0016c4c602cc1a96a9d35fe133a7e374d3cdc26d", "name": "SCREWS",      "isCoin": False},
    {"pool": "0x708804f7f9e3960e282fc1835ff55439319c1925", "name": "BOLTS",       "isCoin": False},
    {"pool": "0x491a412400840651c243acfc1ed9947ffe8a4e8f", "name": "CEMENT",      "isCoin": False},
    {"pool": "0xd1d6bb059c97295f7437ad423111047cbcddf4c6", "name": "SEAWATER",    "isCoin": False},
    {"pool": "0xe63f8cefea9a17a259bb3b375929bd10d5e1cdfa", "name": "ALGAE",       "isCoin": False},
    {"pool": "0x0ab775634107063a7c16c6c8e0fd6bda1f219ae6", "name": "PLASTICS",    "isCoin": False},
    {"pool": "0x0ffb7bd0bc009a01f9f9e95a0f563bad2189f151", "name": "FIBERGLASS",  "isCoin": False},
    {"pool": "0x6f363e6760876a4c66730fbbefccdd3014b6220c", "name": "OIL",         "isCoin": False},
    {"pool": "0x6ccd01c951e57d82be8dccb90c01a58bfb4d83cd", "name": "HEAT",        "isCoin": False},
    {"pool": "0x54ae64826ca9d440ede8c33e6cf4cfa1a3aa5801", "name": "LAVA",        "isCoin": False},
    {"pool": "0x4343846ebe54dcd40ba572275640230d533296e5", "name": "OXYGEN",      "isCoin": False},
    {"pool": "0x4782e36bbe6e9abca5357d3e43a090fa772de71b", "name": "GAS",         "isCoin": False},
    {"pool": "0x7bf03c63adfded079adbd9f807ccce0fd28b8fd8", "name": "STEAM",       "isCoin": False},
    {"pool": "0x0f8f4dcf1b6eb9f5c0e8fbb9cd6879aa3983c8bc", "name": "FUEL",        "isCoin": False},
    {"pool": "0xefc128c4cb990a5ecc88ff71e9efcc0eaef434d2", "name": "ACID",        "isCoin": False},
    {"pool": "0x346e30b7ca273fb001eec84fabf2b693617df710", "name": "SULFUR",      "isCoin": False},
    {"pool": "0xb0a3c31aae83526fd6ee75aac552822d676f46b2", "name": "ENERGY",      "isCoin": False},
    {"pool": "0xbb155716cd99d7ef8fd3fb45c91d39958c95b088", "name": "HYDROGEN",    "isCoin": False},
    {"pool": "0x85172e7ff5040366fa5a3caf7b1bd969bb06b570", "name": "DYNAMITE",    "isCoin": False},
    {"pool": "0x9b3b09e4e3339eb429292c0054f0ab97aed5bcc1", "name": "KEY",         "isCoin": False},
    {"pool": "0x884a266b3c1e70cc32ed2af6483070e81b20830c", "name": "CERAMIC_KEY", "isCoin": False},
    {"pool": "0x7ac99f731a96ada40371fa2a4ec1527d0b6a48fb", "name": "GLASS_KEY",   "isCoin": False},
    {"pool": "0xb67521d41a2c499ceb1288e70563ca34618da866", "name": "DYNO_KEY",    "isCoin": False},
]

GT_BASE = "https://api.geckoterminal.com/api/v2/networks/ronin/pools"
DELAY   = 2.5  # segundos entre requests (rate limit: 30/min = 2s mínimo)

def fetch_pool(pool_addr, retries=4):
    for attempt in range(retries):
        try:
            r = requests.get(
                f"{GT_BASE}/{pool_addr}",
                headers={"Accept": "application/json;version=20230302"},
                timeout=20
            )
            if r.status_code == 429:
                wait = 5 * (attempt + 1)
                print(f"  429 rate limit — esperando {wait}s...")
                time.sleep(wait)
                continue
            if not r.ok:
                print(f"  HTTP {r.status_code}")
                return None
            a = r.json().get("data", {}).get("attributes", {})
            if not a:
                return None
            return {
                "price_usd": float(a.get("base_token_price_usd") or 0) or 0,
                "vol_24h":   float((a.get("volume_usd") or {}).get("h24") or 0) or 0,
                "vol_1h":    float((a.get("volume_usd") or {}).get("h1")  or 0) or 0,
                "chg_24h":   float((a.get("price_change_percentage") or {}).get("h24") or 0) or 0,
                "chg_1h":    float((a.get("price_change_percentage") or {}).get("h1")  or 0) or 0,
                "liquidity": float(a.get("reserve_in_usd") or 0) or 0,
                "fdv":       float(a.get("fdv_usd") or 0) or 0,
                "txs_24h":   (a.get("transactions", {}).get("h24", {}).get("buys", 0) or 0) +
                             (a.get("transactions", {}).get("h24", {}).get("sells", 0) or 0),
            }
        except Exception as e:
            print(f"  Error intento {attempt+1}: {e}")
            if attempt < retries - 1:
                time.sleep(3)
    return None


def main():
    ts = datetime.now(timezone.utc).isoformat()
    print(f"=== CraftWorld Price Fetch — {ts} ===")

    prices = {}
    ok = 0

    for i, t in enumerate(TOKENS):
        print(f"[{i+1}/{len(TOKENS)}] {t['name']}...", end=" ", flush=True)
        d = fetch_pool(t["pool"])
        if d and d["price_usd"] > 0:
            prices[t["pool"]] = {**d, "name": t["name"], "ts": ts}
            ok += 1
            print(f"${d['price_usd']:.6f}")
        else:
            print("sin datos")
        if i < len(TOKENS) - 1:
            time.sleep(DELAY)

    # Calcular price_coin
    coin_token = next((t for t in TOKENS if t["isCoin"]), None)
    coin_usd = prices.get(coin_token["pool"], {}).get("price_usd", 0) if coin_token else 0

    for t in TOKENS:
        if t["pool"] in prices:
            usd = prices[t["pool"]]["price_usd"]
            prices[t["pool"]]["price_coin"] = 1.0 if t["isCoin"] else (usd / coin_usd if coin_usd > 0 else 0)
            prices[t["pool"]]["coin_usd"] = coin_usd

    # Guardar prices.json
    output = {
        "ts":       ts,
        "ok":       ok,
        "total":    len(TOKENS),
        "coin_usd": coin_usd,
        "prices":   prices,
    }
    with open("prices.json", "w") as f:
        json.dump(output, f, indent=2)

    print(f"\n✅ {ok}/{len(TOKENS)} tokens OK → prices.json guardado")


if __name__ == "__main__":
    main()
