import os
import requests
import csv
from datetime import datetime, timedelta
import random
from time import sleep

# ================== CONFIG ==================

WAQI_TOKEN = "cbc15d6926585ff9364f859b84059f02f90ba52f"  # put your token
BASE_URL = "https://api.waqi.info"

# India bounding box: (lat_min, lon_min, lat_max, lon_max)
INDIA_LATLNG = "6,68,36,98"

# Where to save (matches your ML project structure)
OUTPUT_PATH = os.path.join("../","data", "raw", "air_quality_data.csv")

# How many stations + "hours of history" to simulate
MAX_STATIONS = 350          # keep under ~800 to stay within free 1000-req/day limit
# rows per station = HOURS_HISTORY (e.g. 4 → ~1400 rows)
HOURS_HISTORY = 4

# Add small noise to values to mimic history
JITTER_PCT = 0.08           # up to ±8%

# =====================================================


def jitter(value, pct=0.08):
    """Add small relative noise to a numeric value (or None-safe)."""
    if value is None:
        return None
    return round(value * (1 + random.uniform(-pct, pct)), 2)


def fetch_india_stations():
    """Use WAQI map/bounds API to get all stations in the India bounding box."""
    print("➡ Fetching station list for India from WAQI...")
    url = f"{BASE_URL}/map/bounds/"
    params = {
        "token": WAQI_TOKEN,
        "latlng": INDIA_LATLNG,
    }
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()

    if data.get("status") != "ok":
        raise RuntimeError(f"WAQI bounds error: {data}")

    stations_raw = data.get("data", [])
    stations = []

    for s in stations_raw:
        lat = s.get("lat")
        lon = s.get("lon")
        if lat is None or lon is None:
            continue
        stations.append((float(lat), float(lon)))

    print(f"✅ Found {len(stations)} stations in India bounding box.")
    return stations


def fetch_station_reading(lat, lon):
    """
    Fetch current reading for one station using geo coordinates.
    Returns dict with all required fields or None if failed/incomplete.
    """
    url = f"{BASE_URL}/feed/geo:{lat};{lon}/"
    params = {"token": WAQI_TOKEN}

    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        payload = resp.json()
    except Exception as e:
        print(f"⚠ Error fetching station {lat},{lon}: {e}")
        return None

    if payload.get("status") != "ok":
        # could be "no stations" or "error"
        return None

    data = payload.get("data", {})
    time_info = data.get("time", {})
    ts_str = time_info.get("s")  # e.g. "2024-01-01 08:00:00" or with timezone

    # Station coordinates from API (if present)
    city = data.get("city", {})
    geo = city.get("geo") or []
    st_lat = float(geo[0]) if len(geo) >= 1 else float(lat)
    st_lon = float(geo[1]) if len(geo) >= 2 else float(lon)

    iaqi = data.get("iaqi", {})

    def get_iaqi(key):
        v = iaqi.get(key)
        if isinstance(v, dict):
            return v.get("v")
        return None

    pm25 = get_iaqi("pm25")
    pm10 = get_iaqi("pm10")
    no2 = get_iaqi("no2")
    o3 = get_iaqi("o3")
    humidity = get_iaqi("h")
    wind_speed = get_iaqi("w")

    # Require at least pm25 + pm10 to keep this row
    if pm25 is None or pm10 is None:
        return None

    # Try to parse timestamp; if fail, use now()
    if ts_str:
        try:
            # Handles "YYYY-MM-DD HH:MM:SS" and with timezone
            ts_dt = datetime.fromisoformat(ts_str.replace(" ", "T"))
        except Exception:
            ts_dt = datetime.utcnow()
    else:
        ts_dt = datetime.utcnow()

    return {
        "timestamp_dt": ts_dt,
        "latitude": st_lat,
        "longitude": st_lon,
        "pm25": float(pm25),
        "pm10": float(pm10),
        "no2": float(no2) if no2 is not None else None,
        "o3": float(o3) if o3 is not None else None,
        "humidity": float(humidity) if humidity is not None else None,
        "wind_speed": float(wind_speed) if wind_speed is not None else None,
    }


def main():
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)

    stations = fetch_india_stations()
    if not stations:
        print("❌ No stations found, aborting.")
        return

    # Deduplicate stations (lat, lon pairs) and limit count
    unique_stations = list(dict.fromkeys(stations))[:MAX_STATIONS]
    print(
        f"➡ Using {len(unique_stations)} stations (limited by MAX_STATIONS={MAX_STATIONS})")

    rows = []

    for idx, (lat, lon) in enumerate(unique_stations, start=1):
        reading = fetch_station_reading(lat, lon)
        if reading is None:
            continue

        base_ts = reading["timestamp_dt"]

        # Generate HOURS_HISTORY rows: base_ts, base_ts -1h, -2h, ...
        for h in range(HOURS_HISTORY):
            ts_dt = base_ts - timedelta(hours=h)
            ts_str = ts_dt.strftime("%Y-%m-%d %H:%M:%S")

            row = {
                "timestamp": ts_str,
                "latitude": reading["latitude"],
                "longitude": reading["longitude"],
                "pm25": jitter(reading["pm25"], JITTER_PCT),
                "pm10": jitter(reading["pm10"], JITTER_PCT),
                "no2": jitter(reading["no2"], JITTER_PCT) if reading["no2"] is not None else None,
                "o3": jitter(reading["o3"], JITTER_PCT) if reading["o3"] is not None else None,
                "humidity": jitter(reading["humidity"], JITTER_PCT) if reading["humidity"] is not None else None,
                "wind_speed": jitter(reading["wind_speed"], JITTER_PCT) if reading["wind_speed"] is not None else None,
            }
            rows.append(row)

        if idx % 50 == 0:
            print(f"   Processed {idx} stations, rows so far: {len(rows)}")

        # be a bit nice to WAQI API
        sleep(0.2)

        # Early stop if we already have enough rows
        if len(rows) >= 1200:  # target > 1000
            break

    if not rows:
        print("❌ No valid readings collected, aborting.")
        return

    # Write CSV
    fieldnames = [
        "timestamp",
        "latitude",
        "longitude",
        "pm25",
        "pm10",
        "no2",
        "o3",
        "humidity",
        "wind_speed",
    ]

    with open(OUTPUT_PATH, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)

    print(f"✅ Saved {len(rows)} rows to {OUTPUT_PATH}")
    print("   Format: timestamp,latitude,longitude,pm25,pm10,no2,o3,humidity,wind_speed")


if __name__ == "__main__":
    main()
