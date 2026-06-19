import csv
import os
import sys
import uuid
from datetime import datetime, timezone

sys.path.insert(
    0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)  # noqa: E402

from shared.auth.jwt import get_password_hash  # noqa: E402
from shared.models.database import Base, SessionLocal, engine  # noqa: E402
from shared.models.users import User  # noqa: E402
from shared.models.zones import Zone  # noqa: E402


def seed_zones(db):
    police_stations = [
        ("Madiwala", 12.92, 77.62),
        ("Bellandur", 12.93, 77.68),
        ("Byatarayanapura", 13.02, 77.59),
        ("Upparpet", 12.97, 77.57),
        ("Shivajinagar", 12.98, 77.60),
        ("Pulikeshinagar", 13.00, 77.61),
        ("Vijayanagara", 12.97, 77.54),
        ("Cubbon Park", 12.98, 77.59),
        ("K.R. Pura", 13.01, 77.69),
        ("City Market", 12.97, 77.57),
        ("HSR Layout", 12.91, 77.63),
        ("Thalagattapura", 12.87, 77.54),
        ("HAL Old Airport", 12.95, 77.68),
        ("High Ground", 12.99, 77.59),
    ]
    for name, lat, lng in police_stations:
        zone = Zone(
            id=uuid.uuid4(),
            name=name,
            boundary=(
                f"SRID=4326;POLYGON(({lng-0.02} {lat-0.02}, {lng+0.02} {lat-0.02}, "
                f"{lng+0.02} {lat+0.02}, {lng-0.02} {lat+0.02}, {lng-0.02} {lat-0.02}))"
            ),
            police_station=name,
            city="Bengaluru",
        )
        db.add(zone)
    db.commit()
    print(f"Seeded {len(police_stations)} zones")


def seed_users(db):
    users_data = [
        ("admin@parksight.com", "admin123", "Admin User", "admin"),
        ("operator@parksight.com", "operator123", "Operator User", "operator"),
        ("planner@parksight.com", "planner123", "Planner User", "planner"),
        ("officer@parksight.com", "officer123", "Officer User", "officer"),
    ]
    for email, pw, name, role in users_data:
        user = User(
            id=uuid.uuid4(),
            email=email,
            hashed_password=get_password_hash(pw),
            full_name=name,
            role=role,
        )
        db.add(user)
    db.commit()
    print("Seeded 4 users")


def seed_violations_from_csv(db, csv_path):
    from shared.models.cameras import Camera
    from shared.models.violations import Violation

    zones = db.query(Zone).all()
    zone_map = {z.police_station: z for z in zones}
    cameras = {}
    batch = []
    count = 0

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                lat = float(row["latitude"])
                lng = float(row["longitude"])
            except (ValueError, KeyError):
                continue

            station = row.get("police_station", "Unknown")
            zone = zone_map.get(station) or list(zone_map.values())[0]

            ts_str = row.get("created_datetime", "")
            try:
                ts = datetime.fromisoformat(ts_str.replace("+00", "+00:00"))
            except ValueError:
                ts = datetime.now(timezone.utc)

            camera_key = f"{station}:{zone.id}"
            if camera_key not in cameras:
                cam = Camera(
                    id=uuid.uuid4(),
                    name=f"Camera {station}",
                    location=f"SRID=4326;POINT({lng} {lat})",
                    zone_id=zone.id,
                    status="active",
                )
                db.add(cam)
                db.flush()
                cameras[camera_key] = cam

            camera = cameras[camera_key]

            violation = Violation(
                id=uuid.uuid4(),
                camera_id=camera.id,
                timestamp=ts,
                coordinates=f"SRID=4326;POINT({lng} {lat})",
                confidence_score=0.85,
                vehicle_type=row.get("vehicle_type", "CAR"),
                violation_type=row.get("violation_type", "NO PARKING"),
                resolved=False,
            )
            batch.append(violation)
            count += 1

            if count % 1000 == 0:
                db.bulk_save_objects(batch)
                db.commit()
                batch = []
                print(f"Seeded {count} violations...")

    if batch:
        db.bulk_save_objects(batch)
        db.commit()
    print(f"Total violations seeded: {count}")


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        seed_users(db)
        seed_zones(db)
        csv_path = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ),
            "jan to may police violation_anonymized791b166 (1).csv",
        )
        if os.path.exists(csv_path):
            seed_violations_from_csv(db, csv_path)
        else:
            print(f"CSV not found at {csv_path}, skipping violation seeding")
    finally:
        db.close()
