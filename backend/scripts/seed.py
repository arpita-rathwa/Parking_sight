import csv
import os
import random
import sys
import uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(  # noqa: E402
    0, os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)

from sqlalchemy import text  # noqa: E402

from shared.auth.jwt import get_password_hash  # noqa: E402
from shared.models.cameras import Camera  # noqa: E402
from shared.models.congestion_scores import CongestionScore  # noqa: E402
from shared.models.database import Base, get_engine, get_session  # noqa: E402
from shared.models.enforcement_log import EnforcementLog  # noqa: E402
from shared.models.users import Organization, User  # noqa: E402
from shared.models.violations import Violation  # noqa: E402
from shared.models.zones import Zone  # noqa: E402


def clear_data(db):
    for table in [
        "enforcement_log",
        "congestion_scores",
        "violations",
        "cameras",
        "zones",
        "users",
        "organizations",
        "users",
    ]:
        db.execute(text(f"TRUNCATE TABLE {table} CASCADE"))
    db.commit()
    print("Cleared existing data")


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
    zones_list = []
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
        zones_list.append(zone)
    db.commit()
    print(f"Seeded {len(zones_list)} zones")
    return zones_list


def seed_organization(db):
    org = Organization(
        id=uuid.uuid4(), name="Bengaluru Traffic Police"
    )
    db.add(org)
    db.commit()
    print(f"Seeded organization: {org.name}")
    return org


def seed_users(db, org):
    users_data = [
        ("admin@parksight.com", "admin123", "Admin User", "admin"),
        ("operator@parksight.com", "operator123", "Operator User", "operator"),
        ("planner@parksight.com", "planner123", "Planner User", "planner"),
        ("reviewer@parksight.com", "reviewer123", "Reviewer User", "reviewer"),
        ("officer1@parksight.com", "officer123", "Ravi Kumar", "officer"),
        ("officer2@parksight.com", "officer123", "Priya Sharma", "officer"),
        ("officer3@parksight.com", "officer123", "Anita Desai", "officer"),
        ("officer4@parksight.com", "officer123", "Vijay Patil", "officer"),
        ("officer5@parksight.com", "officer123", "Suresh Reddy", "officer"),
    ]
    users_list = []
    for email, pw, name, role in users_data:
        user = User(
            id=uuid.uuid4(),
            organization_id=org.id,
            email=email,
            hashed_password=get_password_hash(pw),
            full_name=name,
            role=role,
        )
        db.add(user)
        users_list.append(user)
    db.commit()
    print(f"Seeded {len(users_list)} users")
    return users_list


def seed_violations_from_csv(db, csv_path):
    zones = db.query(Zone).all()
    zone_map = {z.police_station: z for z in zones}
    cameras = {}
    batch = []
    count = 0
    violation_types = []

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            try:
                lat = float(row["latitude"])
                lng = float(row["longitude"])
            except (ValueError, KeyError):
                continue

            station = row.get("police_station", "Unknown")
            zone = zone_map.get(station) or zone_map.get("Madiwala", zones[0])

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
            vtype = row.get("violation_type", "NO PARKING")
            if vtype not in violation_types:
                violation_types.append(vtype)

            violation = Violation(
                id=uuid.uuid4(),
                camera_id=camera.id,
                timestamp=ts,
                coordinates=f"SRID=4326;POINT({lng} {lat})",
                confidence_score=random.uniform(0.75, 0.99),
                vehicle_type=row.get("vehicle_type", "CAR"),
                violation_type=vtype,
                resolved=random.random() < 0.4,
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
    return violation_types


def seed_congestion_scores(db, zones, hours=72):
    now = datetime.now(timezone.utc)
    batch = []
    count = 0

    for zone in zones:
        base_violations = random.randint(5, 50)
        base_density = random.uniform(20, 80)
        for h in range(hours, 0, -1):
            ts = now - timedelta(hours=h)
            hour_factor = 1.0 + 0.5 * abs(12 - ts.hour) / 12
            weekday_factor = 1.3 if ts.weekday() < 5 else 0.7
            viol = int(
                base_violations
                * hour_factor
                * weekday_factor
                * random.uniform(0.7, 1.3)
            )
            density = (
                base_density * hour_factor * weekday_factor * random.uniform(0.8, 1.2)
            )
            speed_drop = random.uniform(5, 40) * hour_factor
            impact = (
                viol * 0.35 + speed_drop * 0.25 + density * 0.15
            ) * random.uniform(0.8, 1.2)
            weather = random.uniform(0.8, 1.2)

            score = CongestionScore(
                id=uuid.uuid4(),
                zone_id=zone.id,
                timestamp=ts,
                speed_drop_percent=round(speed_drop, 1),
                violation_count=viol,
                impact_score=round(min(impact, 100), 1),
                traffic_density=round(density, 1),
                weather_factor=round(weather, 2),
            )
            batch.append(score)
            count += 1

            if count % 500 == 0:
                db.bulk_save_objects(batch)
                db.commit()
                batch = []

    if batch:
        db.bulk_save_objects(batch)
        db.commit()
    print(f"Seeded {count} congestion score entries")


def seed_enforcement_logs(db, users, zones):
    officers = [u for u in users if u.role == "officer"]
    if not officers:
        print("No officers found, skipping enforcement logs")
        return

    now = datetime.now(timezone.utc)
    batch = []
    count = 0

    for officer in officers:
        assigned_zones = random.sample(zones, min(3, len(zones)))
        for zone in assigned_zones:
            dispatched = now - timedelta(
                hours=random.randint(1, 12),
                minutes=random.randint(0, 59),
            )
            arrived = dispatched + timedelta(minutes=random.randint(5, 25))
            resolved = (
                arrived + timedelta(minutes=random.randint(10, 60))
                if random.random() < 0.7
                else None
            )
            outcome = (
                random.choice(["citation_issued", "warning_given", "no_action"])
                if resolved
                else "pending"
            )

            log = EnforcementLog(
                id=uuid.uuid4(),
                officer_id=officer.id,
                zone_id=zone.id,
                dispatched_at=dispatched,
                arrived_at=arrived,
                resolved_at=resolved,
                outcome=outcome,
            )
            batch.append(log)
            count += 1

    db.bulk_save_objects(batch)
    db.commit()
    print(f"Seeded {count} enforcement log entries")


if __name__ == "__main__":
    engine = get_engine()
    Base.metadata.create_all(bind=engine)
    db = get_session()
    try:
        clear_data(db)
        org = seed_organization(db)
        users = seed_users(db, org)
        zones = seed_zones(db)
        csv_path = os.path.join(
            os.path.dirname(
                os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            ),
            "docs",
            "jan_to_may_police_violation_data.csv",
        )
        if os.path.exists(csv_path):
            seed_violations_from_csv(db, csv_path)
        else:
            print(f"CSV not found at {csv_path}, skipping violation seeding")
        seed_congestion_scores(db, zones, hours=72)
        seed_enforcement_logs(db, users, zones)
        print("Seed complete!")
    finally:
        db.close()
