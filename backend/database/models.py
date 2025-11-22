from sqlalchemy import Column, Integer, String, Float, Boolean, DateTime, Text, JSON, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

Base = declarative_base()

class Airport(Base):
    __tablename__ = 'airports'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    iata_code = Column(String(3), unique=True, nullable=False, index=True)
    icao_code = Column(String(4), unique=True, index=True, nullable=True)
    name = Column(String(200), nullable=False)
    city = Column(String(100), nullable=False)
    country = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=True)
    longitude = Column(Float, nullable=True)
    timezone = Column(String(50), nullable=True)
    search_field = Column(String(300), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<Airport({self.iata_code}: {self.city}, {self.country})>"
    
    def to_dict(self):
        return {
            'code': self.iata_code,
            'name': self.name,
            'city': self.city,
            'country': self.country,
            'search': self.search_field or f"{self.city}, {self.country} ({self.iata_code})",
            'latitude': self.latitude,
            'longitude': self.longitude,
            'iata_code': self.iata_code,
            'icao_code': self.icao_code
        }
    
class FlightCalculation(Base):
    __tablename__ = 'flight_calculations'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Airport relationships
    departure_airport_id = Column(Integer, ForeignKey('airports.id'), nullable=False)
    destination_airport_id = Column(Integer, ForeignKey('airports.id'), nullable=False)
    
    departure_airport = relationship("Airport", foreign_keys=[departure_airport_id], backref="departure_calculations")
    destination_airport = relationship("Airport", foreign_keys=[destination_airport_id], backref="destination_calculations")
    
    # Flight details
    passengers = Column(Integer, nullable=False, default=1)
    round_trip = Column(Boolean, nullable=False, default=False)
    cabin_class = Column(String(20), nullable=False, default='economy')
    
    # Calculation results
    distance_km = Column(Float, nullable=False)
    distance_miles = Column(Float, nullable=False)
    fuel_burn_kg = Column(Float, nullable=False)
    total_co2_kg = Column(Float, nullable=False)
    co2_per_passenger_kg = Column(Float, nullable=False)
    co2_tonnes = Column(Float, nullable=False)
    
    # Additional metadata
    calculation_method = Column(String(50), default='ICAO_API')
    flight_info = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100), nullable=True)
    
    def __repr__(self):
        return f"<FlightCalculation({self.id}: {self.departure_airport_id}->{self.destination_airport_id})>"
    
    def to_dict(self):
        # Get airport codes safely
        departure_code = "Unknown"
        destination_code = "Unknown"
        
        if self.departure_airport:
            departure_code = self.departure_airport.iata_code
        if self.destination_airport:
            destination_code = self.destination_airport.iata_code
        
        # Map calculation_method to data_source for frontend compatibility
        data_source_map = {
            'ICAO_API': 'ICAO_API',
            'ICAO_ENHANCED': 'ENHANCED_CALCULATION', 
            'ICAO_BASIC': 'BASIC_CALCULATION',
            'ICAO': 'CALCULATION'
        }
        data_source = data_source_map.get(self.calculation_method, 'CALCULATION')
        
        return {
            'id': self.id,
            'departure': departure_code,
            'destination': destination_code,
            'passengers': self.passengers,
            'round_trip': self.round_trip,
            'cabin_class': self.cabin_class,
            'distance_km': self.distance_km,
            'distance_miles': self.distance_miles,
            'fuel_burn_kg': self.fuel_burn_kg,
            'total_co2_kg': self.total_co2_kg,
            'co2_per_passenger_kg': self.co2_per_passenger_kg,
            'co2_tonnes': self.co2_tonnes,
            'calculation_method': self.calculation_method,
            'data_source': data_source,
            'flight_info': self.flight_info or f"{departure_code} to {destination_code} - {self.distance_km}km",
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'departure_airport_id': self.departure_airport_id,
            'destination_airport_id': self.destination_airport_id
        }
        
    def to_simple_dict(self):
        """Simplified version for API responses"""
        return {
            'id': self.id,
            'departure': self.departure_airport.iata_code if self.departure_airport else "Unknown",
            'destination': self.destination_airport.iata_code if self.destination_airport else "Unknown",
            'passengers': self.passengers,
            'round_trip': self.round_trip,
            'cabin_class': self.cabin_class,
            'distance_km': self.distance_km,
            'distance_miles': self.distance_miles,
            'total_co2_kg': self.total_co2_kg,
            'co2_per_passenger_kg': self.co2_per_passenger_kg,
            'data_source': self.calculation_method,
            'flight_info': self.flight_info,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }