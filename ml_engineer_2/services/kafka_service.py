from confluent_kafka import Producer, Consumer
import lightgbm as lgb
import pandas as pd
import json
from datetime import datetime

model = lgb.Booster(model_file="../model/model.txt")

FEATURE_COLS = [
    "raw_count", "centroid_lat", "centroid_lon", "police_station",
    "junction_name", "n_unique_devices", "n_unique_vehicles",
    "pct_approved", "pct_weekend", "mode_hour", "hour_std"
]

TOPIC_RAW    = "parking.violations.raw"
TOPIC_SCORED = "parking.hotspots.scored"

producer = Producer({"bootstrap.servers": "localhost:9092"})
consumer = Consumer({
    "bootstrap.servers": "localhost:9092",
    "group.id": "hotspot-scorer",
    "auto.offset.reset": "earliest"
})

def publish_violation(event: dict):
    producer.produce(
        TOPIC_RAW,
        key=str(event.get("cluster_id")),
        value=json.dumps(event)
    )
    producer.flush()

def consume_and_score():
    consumer.subscribe([TOPIC_RAW])
    print(f"Listening on '{TOPIC_RAW}'... (Ctrl+C to stop)")
    try:
        while True:
            msg = consumer.poll(timeout=1.0)
            if msg is None or msg.error():
                continue
            raw = json.loads(msg.value().decode())
            row = pd.DataFrame([raw])
            row["police_station"] = row["police_station"].astype("category")
            row["junction_name"]  = row["junction_name"].astype("category")
            score = float(model.predict(row[FEATURE_COLS])[0])
            tier  = "HIGH" if score >= 70 else ("MEDIUM" if score >= 40 else "LOW")
            result = {**raw, "impact_score": round(score, 4), "priority_tier": tier}
            producer.produce(TOPIC_SCORED, key=str(raw["cluster_id"]), value=json.dumps(result))
            producer.flush()
            print(f"Scored cluster {raw['cluster_id']}: {score:.2f} ({tier})")
    except KeyboardInterrupt:
        consumer.close()

if __name__ == "__main__":
    consume_and_score()