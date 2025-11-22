from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

db = SQLAlchemy()

class FlightCalculation(db.Model):
    __tablename__ = 'flight_calculations'

    # Required fields for both databases
    id = db.Column(db.Integer, primary_key=True)
    departure = db.Column(db.String(100), nullable=False)
    destination = db.Column(db.String(100), nullable=False)
    passengers = db.Column(db.Integer, nullable=False, default=1)
    round_trip = db.Column(db.Boolean, nullable=False, default=False)
    cabin_class = db.Column(db.String(50), nullable=False, default='economy')
    fuel_burn_kg = db.Column(db.Float, nullable=False)
    total_co2_kg = db.Column(db.Float, nullable=False)
    co2_per_passenger_kg = db.Column(db.Float, nullable=False)
    co2_tonnes = db.Column(db.Float, nullable=False)
    distance_km = db.Column(db.Float, nullable=False)
    distance_miles = db.Column(db.Float, nullable=False)
    flight_info = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    # Optional fields with defaults (will work with both SQLite and SQL Server)
    calculation_method = db.Column(db.String(50), nullable=True, default=None)
    departure_airport_id = db.Column(db.Integer, nullable=True, default=None)
    destination_airport_id = db.Column(db.Integer, nullable=True, default=None)
    created_by = db.Column(db.String(100), nullable=True, default=None)

    def to_dict(self):
        return {
            'id': self.id,
            'departure': self.departure,
            'destination': self.destination,
            'passengers': self.passengers,
            'round_trip': self.round_trip,
            'cabin_class': self.cabin_class,
            'fuel_burn_kg': self.fuel_burn_kg,
            'total_co2_kg': self.total_co2_kg,
            'co2_per_passenger_kg': self.co2_per_passenger_kg,
            'co2_tonnes': self.co2_tonnes,
            'distance_km': self.distance_km,
            'distance_miles': self.distance_miles,
            'flight_info': self.flight_info,
            'created_at': self.created_at.isoformat(),
            'data_source': self.calculation_method or 'CALCULATION'
        }

# Simple Airport model that works with both databases
class Airport(db.Model):
    __tablename__ = 'airports'
    
    id = db.Column(db.Integer, primary_key=True)
    iata_code = db.Column(db.String(3), nullable=False)
    name = db.Column(db.String(200), nullable=True)
    city = db.Column(db.String(100), nullable=True)
    country = db.Column(db.String(100), nullable=True)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    
    # Optional fields for SQL Server compatibility
    icao_code = db.Column(db.String(4), nullable=True)
    timezone = db.Column(db.String(50), nullable=True)
    search_field = db.Column(db.String(300), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=True)

    def to_dict(self):
        return {
            'iata_code': self.iata_code,
            'name': self.name or f"{self.iata_code} Airport",
            'city': self.city or 'Unknown',
            'country': self.country or 'Unknown',
            'latitude': self.latitude,
            'longitude': self.longitude,
            'search': self.search_field or f"{self.city or 'Unknown'}, {self.country or 'Unknown'} ({self.iata_code})"
        }