from app import create_app
# Import db and models from your consolidated models file (backend/app/models/user.py)
from app.models.user import db, User, Vehicle, Trip, EcoScore
from werkzeug.security import generate_password_hash
from datetime import datetime, timedelta
import random

# Initialize Flask App Context
app = create_app()

def seed_data():
    with app.app_context():
        print("🗑️  Cleaning database...")
        db.drop_all()
        db.create_all()
        print("✅ Database tables recreated.")

        # ==========================================
        # 1. CREATE USERS
        # ==========================================
        print("👤 Creating users...")
        
        # User 1: The Main Test User
        user1 = User(
            email='test@example.com',
            password_hash=generate_password_hash('password123'),
            first_name='Rahul',
            last_name='Sharma',
            city='Mumbai',
            country='India',
            total_co2_saved=12.5, # kg
            total_trips=15,
            current_eco_score=85,
            badges=['Early Adopter', 'Carbon Hero']
        )

        # User 2: For Leaderboard Comparison
        user2 = User(
            email='priya@example.com',
            password_hash=generate_password_hash('password123'),
            first_name='Priya',
            last_name='Patel',
            city='Ahmedabad',
            country='India',
            total_co2_saved=45.2,
            total_trips=42,
            current_eco_score=92,
            badges=['Green Driver']
        )

        db.session.add_all([user1, user2])
        db.session.flush() # Flush to generate IDs

        # ==========================================
        # 2. CREATE VEHICLES
        # ==========================================
        print("Tb Creating vehicles...")

        # Vehicle for User 1
        v1 = Vehicle(
            user_id=user1.id,
            make='Tata',
            model='Nexon EV',
            year=2023,
            battery_capacity_kwh=40.5,
            efficiency_kwh_per_km=0.13,
            current_battery_health=98.5,
            purchase_date=datetime(2023, 1, 15).date()
        )

        # Vehicle for User 2
        v2 = Vehicle(
            user_id=user2.id,
            make='MG',
            model='ZS EV',
            year=2022,
            battery_capacity_kwh=50.3,
            efficiency_kwh_per_km=0.15,
            current_battery_health=94.0,
            purchase_date=datetime(2022, 6, 20).date()
        )

        db.session.add_all([v1, v2])
        db.session.flush()

        # ==========================================
        # 3. CREATE TRIPS (History for User 1)
        # ==========================================
        print("🚗 Creating trips...")

        trips = []
        
        # Trip 1: Today
        t1 = Trip(
            user_id=user1.id,
            vehicle_id=v1.id,
            start_latitude=19.0760,
            start_longitude=72.8777,
            end_latitude=19.2183,
            end_longitude=72.9781,
            distance_km=22.5,
            duration_minutes=45,
            start_battery_percentage=80,
            end_battery_percentage=72,
            co2_generated_grams=450,
            co2_saved_vs_petrol_grams=2500, # 2.5kg saved
            eco_score=88,
            temperature_celsius=28,
            cost_rupees=45.0,
            started_at=datetime.utcnow() - timedelta(hours=2),
            completed_at=datetime.utcnow() - timedelta(hours=1, minutes=15)
        )

        # Trip 2: Yesterday
        t2 = Trip(
            user_id=user1.id,
            vehicle_id=v1.id,
            start_latitude=19.0760,
            start_longitude=72.8777,
            end_latitude=18.5204,
            end_longitude=73.8567,
            distance_km=148.0,
            duration_minutes=180,
            start_battery_percentage=100,
            end_battery_percentage=45,
            co2_generated_grams=2800,
            co2_saved_vs_petrol_grams=18500, # 18.5kg saved
            eco_score=92,
            temperature_celsius=30,
            cost_rupees=250.0,
            started_at=datetime.utcnow() - timedelta(days=1, hours=5),
            completed_at=datetime.utcnow() - timedelta(days=1, hours=2)
        )

        # Trip 3: Last Week
        t3 = Trip(
            user_id=user1.id,
            vehicle_id=v1.id,
            start_latitude=19.0760,
            start_longitude=72.8777,
            end_latitude=19.0330,
            end_longitude=73.0297,
            distance_km=35.2,
            duration_minutes=60,
            start_battery_percentage=50,
            end_battery_percentage=40,
            co2_generated_grams=700,
            co2_saved_vs_petrol_grams=4200, # 4.2kg saved
            eco_score=75,
            temperature_celsius=26,
            cost_rupees=70.0,
            started_at=datetime.utcnow() - timedelta(days=5),
            completed_at=datetime.utcnow() - timedelta(days=5, minutes=60)
        )

        trips.extend([t1, t2, t3])
        db.session.add_all(trips)
        db.session.flush()

        # ==========================================
        # 4. CREATE ECO SCORES
        # ==========================================
        print("🌱 Creating eco scores...")

        es1 = EcoScore(
            user_id=user1.id,
            trip_id=t1.id,
            driving_efficiency_score=90,
            route_cleanliness_score=85,
            charging_greenness_score=80,
            maintenance_score=100,
            total_score=88,
            rank_position=150
        )

        es2 = EcoScore(
            user_id=user1.id,
            trip_id=t2.id,
            driving_efficiency_score=95,
            route_cleanliness_score=90,
            charging_greenness_score=90,
            maintenance_score=100,
            total_score=92,
            rank_position=148
        )

        db.session.add_all([es1, es2])

        # Commit everything
        db.session.commit()
        print("✨ Database seeded successfully!")
        print(f"👉 Login with: test@example.com / password123")

if __name__ == '__main__':
    seed_data()