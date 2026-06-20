import redis
import json

r = redis.Redis(host="localhost", port=6379, db=0)
QUEUE_KEY = "parking:hotspot:priority_queue"

def push_hotspots(cluster_summary_json_path: str, top_n: int = 20):
    import pandas as pd
    df = pd.read_json(cluster_summary_json_path)
    top = df.nlargest(top_n, "impact_score")

    r.delete(QUEUE_KEY)
    mapping = {}
    for _, row in top.iterrows():
        payload = json.dumps({
            "cluster_id":     int(row["cluster"]),
            "centroid_lat":   round(row["centroid_lat"], 6),
            "centroid_lon":   round(row["centroid_lon"], 6),
            "police_station": row["police_station"],
            "junction_name":  row["junction_name"],
            "impact_score":   round(row["impact_score"], 4),
            "raw_count":      int(row["raw_count"]),
            "distinct_days":  int(row["distinct_days"]),
        })
        mapping[payload] = float(row["impact_score"])

    r.zadd(QUEUE_KEY, mapping)
    print(f"✅ {r.zcard(QUEUE_KEY)} hotspots pushed to Redis queue")

def peek_top(n=5):
    items = r.zrevrange(QUEUE_KEY, 0, n - 1, withscores=True)
    for rank, (payload_bytes, score) in enumerate(items, 1):
        p = json.loads(payload_bytes)
        print(f"#{rank}  score={score:.2f}  cluster={p['cluster_id']}  station={p['police_station']}")

if __name__ == "__main__":
    push_hotspots("../model/cluster_summary.json")
    peek_top()