"""
Initialize database with synthetic data directly using Supabase API
"""
from services import DatabaseService
from datetime import datetime, timedelta
import random


def seed_database():
    """Seed the database with synthetic data"""
    db = DatabaseService()
    
    print("=" * 70)
    print("SEEDING DATABASE WITH SYNTHETIC DATA")
    print("=" * 70)
    
    # Generate meter readings for past 6 months
    print("\n1. Creating meter readings...")
    readings = []
    current_date = datetime.now()
    current_reading = 3500.0  # Starting meter reading
    
    for i in range(6, 0, -1):
        reading_date = current_date - timedelta(days=30 * i)
        consumption = 150 + random.uniform(-30, 50)  # 120-200 kWh variation
        current_reading += consumption
        
        readings.append({
            "meter_id": "METER001",
            "customer_id": "CUST001",
            "reading_value": round(current_reading, 2),
            "reading_date": reading_date.strftime("%Y-%m-%d"),
            "created_at": reading_date.isoformat()
        })
    
    # Insert readings
    for reading in readings:
        try:
            db.insert_meter_reading(reading)
            print(f"   ✓ Inserted: {reading['reading_date']} - {reading['reading_value']} kWh")
        except Exception as e:
            print(f"   ✗ Error: {e}")
    
    print(f"\n✓ Created {len(readings)} meter readings")
    
    # Verify
    print("\n2. Verifying data...")
    historical = db.get_historical_readings("METER001", limit=10)
    print(f"   ✓ Found {len(historical)} readings in database")
    
    if historical:
        print("\n   Latest readings:")
        for r in historical[:3]:
            print(f"      {r['reading_date']}: {r['reading_value']} kWh")
    
    print("\n" + "=" * 70)
    print("✓ DATABASE SEEDED SUCCESSFULLY!")
    print("=" * 70)
    print("\nYou can now:")
    print("  1. Start the API: python app.py")
    print("  2. Test tariff calc: python test_tariff.py")
    print("=" * 70)


if __name__ == "__main__":
    seed_database()
