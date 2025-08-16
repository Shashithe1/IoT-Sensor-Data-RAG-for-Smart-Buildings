import random
import time
import datetime
import duckdb

# ✅ Fixed import
from store import get_duck, init_duck


# Create schema + table
def init_table(con):
    con.execute("""
    CREATE TABLE IF NOT EXISTS readings (
        ts TIMESTAMP,
        building_id STRING,
        sensor_id STRING,
        metric STRING,
        value DOUBLE
    )
    """)


# Generate fake readings
def push_random(con):
    now = datetime.datetime.now()
    rows = []
    for sid in ["AHU-1", "CHILLER-2", "PUMP-3"]:
        for metric in ["temp", "vibration", "power"]:
            rows.append((now, "B1", sid, metric, random.uniform(0, 30)))
    con.executemany("INSERT INTO readings VALUES (?, ?, ?, ?, ?)", rows)


def run_simulator(duration_seconds=10, delay=1):
    con = get_duck()
    init_table(con)
    print(f"▶️ Starting sensor simulator for {duration_seconds} seconds...")
    start = time.time()
    while time.time() - start < duration_seconds:
        push_random(con)
        time.sleep(delay)
    print("✅ Simulation complete.")
