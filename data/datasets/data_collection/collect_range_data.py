import pandas as pd
import numpy as np
import os
from datetime import datetime, timedelta

# --- Configuration ---
NUM_TRIPS = 1200  # Collects more than the required 1,000+ rows
OUTPUT_FILE = '../raw/historical_trips.csv'
START_DATE = datetime(2024, 1, 1, 8, 0, 0)

# --- Data Generation Functions ---


def generate_realistic_trip_data(n):
    """Generates synthetic EV trip data for range prediction."""

    data = {}

    # 1. Time & Distance
    timestamps = [START_DATE + timedelta(hours=i * 24 / n) for i in range(n)]
    data['timestamp'] = timestamps
    data['distance_km'] = np.random.uniform(
        5, 100, n).round(1)  # 5-100 km trips

    # 2. Battery Levels (The core variables)
    data['start_battery'] = np.random.uniform(50, 95, n).astype(int)

    # Simple linear consumption model (modified for realism)
    consumption_rate = np.random.uniform(0.15, 0.25, n)  # kWh/km

    # Estimate battery drop (based on a nominal 50 kWh battery, 100% = 50kWh)
    estimated_kwh_used = data['distance_km'] * consumption_rate
    estimated_percent_drop = (estimated_kwh_used / 50) * 100

    # Add noise and influence of external factors (speed, temp, traffic)
    speed_factor = np.random.uniform(0.9, 1.1, n)
    temp_factor = np.random.uniform(0.95, 1.05, n)

    data['battery_drop'] = estimated_percent_drop * speed_factor * temp_factor

    # Calculate end_battery, ensuring it stays realistic (0-100)
    data['end_battery'] = np.clip(
        data['start_battery'] - data['battery_drop'], 10, 80).astype(int)

    # 3. Other Features
    data['duration_minutes'] = (
        data['distance_km'] / np.random.uniform(30, 80, n)) * 60
    data['avg_speed_kmh'] = (data['distance_km'] /
                             data['duration_minutes']) * 60

    data['temperature_celsius'] = np.random.uniform(15, 35, n).round(1)

    traffic_conditions = ['low', 'medium', 'heavy']
    data['traffic_condition'] = np.random.choice(
        traffic_conditions, n, p=[0.4, 0.4, 0.2])

    # 4. Battery Degradation (small, cumulative effect)
    # Simulate a small, accumulating degradation over time
    data['battery_degradation'] = np.linspace(
        0.1, 1.5, n) + np.random.uniform(-0.1, 0.1, n)
    data['battery_degradation'] = np.clip(
        data['battery_degradation'], 0.1, 3.0).round(2)

    df = pd.DataFrame(data)

    # Select and reorder columns according to the required schema
    df = df[[
        'timestamp',
        'distance_km',
        'start_battery',
        'end_battery',
        'duration_minutes',
        'avg_speed_kmh',
        'temperature_celsius',
        'traffic_condition',
        'battery_degradation'
    ]]

    return df


# --- Execution ---
if __name__ == "__main__":

    df = generate_realistic_trip_data(NUM_TRIPS)

    # Ensure the output directory exists
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)

    # Save the file
    df.to_csv(OUTPUT_FILE, index=False)

    print(f"Successfully generated {len(df)} rows of data.")
    print(f"File saved to: {OUTPUT_FILE}")
    print("\n--- Quick Data Preview ---")
    print(df.head())
