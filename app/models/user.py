from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import uuid

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    phone = db.Column(db.String(20))
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    profile_picture_url = db.Column(db.Text)
    city = db.Column(db.String(100))
    country = db.Column(db.String(100))
    preferred_language = db.Column(db.String(10), default='en')
    total_co2_saved = db.Column(db.Float, default=0.0)
    total_trips = db.Column(db.Integer, default=0)
    current_eco_score = db.Column(db.Integer, default=0)
    badges = db.Column(db.JSON, default=list)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    vehicles = db.relationship('Vehicle', backref='user', lazy=True, cascade='all, delete-orphan')
    trips = db.relationship('Trip', backref='user', lazy=True, cascade='all, delete-orphan')
    eco_scores = db.relationship('EcoScore', backref='user', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'email': self.email,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'city': self.city,
            'country': self.country,
            'total_co2_saved': self.total_co2_saved,
            'total_trips': self.total_trips,
            'current_eco_score': self.current_eco_score,
            'badges': self.badges,
            'created_at': self.created_at.isoformat()
        }

    @property
    def name(self):
        """Convenience property for user name"""
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.first_name or self.email.split('@')[0]


class Vehicle(db.Model):
    __tablename__ = 'vehicles'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    make = db.Column(db.String(100))
    model = db.Column(db.String(100))
    year = db.Column(db.Integer)
    battery_capacity_kwh = db.Column(db.Float)
    efficiency_kwh_per_km = db.Column(db.Float)
    purchase_date = db.Column(db.Date)
    current_battery_health = db.Column(db.Float, default=100.0)
    current_battery_percentage = db.Column(db.Float, default=100.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    trips = db.relationship('Trip', backref='vehicle', lazy=True, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'make': self.make,
            'model': self.model,
            'year': self.year,
            'battery_capacity_kwh': self.battery_capacity_kwh,
            'efficiency_kwh_per_km': self.efficiency_kwh_per_km,
            'current_battery_health': self.current_battery_health,
            'current_battery_percentage': self.current_battery_percentage
        }


class Trip(db.Model):
    __tablename__ = 'trips'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    vehicle_id = db.Column(db.Integer, db.ForeignKey('vehicles.id'), nullable=True)

    # Location info
    start_location = db.Column(db.String(255), default='Unknown')
    end_location = db.Column(db.String(255), default='Unknown')
    start_latitude = db.Column(db.Float)
    start_longitude = db.Column(db.Float)
    end_latitude = db.Column(db.Float)
    end_longitude = db.Column(db.Float)

    # Trip metrics
    distance_km = db.Column(db.Float, default=0.0)
    duration_minutes = db.Column(db.Integer, default=0)
    avg_speed_kmh = db.Column(db.Float)

    # Battery info
    start_battery_percentage = db.Column(db.Float)
    end_battery_percentage = db.Column(db.Float)

    # Environmental metrics
    co2_generated_grams = db.Column(db.Float, default=0.0)
    co2_saved_vs_petrol_grams = db.Column(db.Float, default=0.0)
    energy_consumed_kwh = db.Column(db.Float)

    # Cost & Score
    cost_rupees = db.Column(db.Float)
    eco_score = db.Column(db.Integer, default=0)

    # Environmental conditions
    weather_condition = db.Column(db.String(50))
    temperature_celsius = db.Column(db.Float)
    traffic_condition = db.Column(db.String(50))

    # Timestamps
    started_at = db.Column(db.DateTime)
    completed_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    # Relationships
    eco_score_record = db.relationship('EcoScore', backref='trip', uselist=False, cascade='all, delete-orphan')

    def to_dict(self):
        return {
            'id': self.id,
            'start_location': self.start_location,
            'end_location': self.end_location,
            'distance_km': self.distance_km,
            'duration_minutes': self.duration_minutes,
            'co2_generated_grams': self.co2_generated_grams,
            'co2_saved_vs_petrol_grams': self.co2_saved_vs_petrol_grams,
            'co2_saved_kg': round(self.co2_saved_vs_petrol_grams / 1000, 2) if self.co2_saved_vs_petrol_grams else 0,
            'eco_score': self.eco_score,
            'temperature_celsius': self.temperature_celsius,
            'cost_rupees': self.cost_rupees,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'status': 'completed' if self.completed_at else 'in_progress'
        }


class EcoScore(db.Model):
    __tablename__ = 'eco_scores'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    trip_id = db.Column(db.Integer, db.ForeignKey('trips.id'))

    driving_efficiency_score = db.Column(db.Integer)
    route_cleanliness_score = db.Column(db.Integer)
    charging_greenness_score = db.Column(db.Integer)
    maintenance_score = db.Column(db.Integer)
    total_score = db.Column(db.Integer)

    badges_earned = db.Column(db.JSON, default=list)
    rank_position = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'driving_efficiency_score': self.driving_efficiency_score,
            'route_cleanliness_score': self.route_cleanliness_score,
            'charging_greenness_score': self.charging_greenness_score,
            'maintenance_score': self.maintenance_score,
            'total_score': self.total_score,
            'badges_earned': self.badges_earned,
            'rank_position': self.rank_position
        }
