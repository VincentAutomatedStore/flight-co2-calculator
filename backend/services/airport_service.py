import pandas as pd
from sqlalchemy.orm import Session
from sqlalchemy import or_
from database.models import Airport
import logging

logger = logging.getLogger(__name__)

class AirportService:
    def __init__(self, db: Session):
        self.db = db
    
    def import_airports_from_array(self, airports_data: list):
        """Import airports from a JavaScript-style array"""
        try:
            airports_imported = 0
            
            for airport_data in airports_data:
                # Map your JavaScript object to our database model
                iata_code = airport_data.get('code', '').strip().upper()
                name = airport_data.get('name', '')
                city = airport_data.get('city', '')
                country = airport_data.get('country', '')
                search_field = airport_data.get('search', '')
                
                # Skip if missing essential data
                if not iata_code or not name or not city or not country:
                    continue
                
                # Create search field if not provided
                if not search_field:
                    search_field = f"{city}, {country} ({iata_code})"
                
                # Check if airport already exists
                existing_airport = self.get_airport_by_code(iata_code)
                
                if existing_airport:
                    # Update existing airport
                    existing_airport.name = name
                    existing_airport.city = city
                    existing_airport.country = country
                    existing_airport.search_field = search_field
                else:
                    # Create new airport with NULL for icao_code instead of empty string
                    airport = Airport(
                        iata_code=iata_code,
                        icao_code=None,  # Use NULL instead of empty string
                        name=name,
                        city=city,
                        country=country,
                        latitude=None,
                        longitude=None,
                        timezone='',
                        search_field=search_field
                    )
                    self.db.add(airport)
                
                airports_imported += 1
            
            self.db.commit()
            logger.info(f"Successfully imported {airports_imported} airports from array")
            return airports_imported
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error importing airports from array: {str(e)}")
            raise

    def import_airports_from_csv(self, csv_file_path: str):
        """Import airports from CSV file"""
        try:
            df = pd.read_csv(csv_file_path)
            
            # Expected columns (adjust based on your CSV)
            required_columns = ['iata_code', 'name', 'city', 'country']
            
            for col in required_columns:
                if col not in df.columns:
                    raise ValueError(f"Missing required column: {col}")
            
            airports_imported = 0
            for _, row in df.iterrows():
                # Create searchable field
                search_field = f"{row['city']}, {row['country']} ({row['iata_code']})"
                
                airport = Airport(
                    iata_code=row['iata_code'],
                    icao_code=row.get('icao_code', ''),
                    name=row['name'],
                    city=row['city'],
                    country=row['country'],
                    latitude=row.get('latitude'),
                    longitude=row.get('longitude'),
                    timezone=row.get('timezone', ''),
                    search_field=search_field
                )
                
                # Use merge to handle duplicates
                self.db.merge(airport)
                airports_imported += 1
            
            self.db.commit()
            logger.info(f"Successfully imported {airports_imported} airports")
            return airports_imported
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"Error importing airports: {str(e)}")
            raise
    
    def search_airports(self, query: str, limit: int = 20):
        """Search airports by IATA code, city, country, or name"""
        if not query or len(query) < 2:
            return []
        
        search_term = f"%{query.lower()}%"
        
        airports = self.db.query(Airport).filter(
            or_(
                Airport.iata_code.ilike(search_term),
                Airport.city.ilike(search_term),
                Airport.country.ilike(search_term),
                Airport.name.ilike(search_term),
                Airport.search_field.ilike(search_term)
            )
        ).limit(limit).all()
        
        return [airport.to_dict() for airport in airports]
    
    def get_airport_by_code(self, airport_code: str):
        """Get airport by code using correct schema"""
        try:
            if not airport_code:
                return None
                
            # Try by iata_code first
            airport = self.db.query(Airport)\
                .filter(Airport.iata_code == airport_code.upper())\
                .first()
            
            if airport:
                return airport
                
            # Try by icao_code as fallback
            airport = self.db.query(Airport)\
                .filter(Airport.icao_code == airport_code.upper())\
                .first()
                
            return airport
            
        except Exception as e:
            logger.error(f"Error getting airport {airport_code}: {e}")
            return None

    def _get_or_create_airport(self, airport_code: str):
        """Get existing airport or create a minimal one - UPDATED FOR SQL SERVER SCHEMA"""
        try:
            # Try to get existing airport first
            airport = self.airport_service.get_airport_by_code(airport_code)
            if airport:
                return airport
            
            # Create a minimal airport record with correct SQL Server schema
            logger.info(f"🆕 Creating airport record for: {airport_code}")
            
            # Get coordinates from fallback
            coords = self._get_airport_coordinates(airport_code)
            
            new_airport = Airport(
                iata_code=airport_code.upper(),
                icao_code=None,
                name=f"{airport_code.upper()} Airport",
                city="Unknown",
                country="Unknown",
                latitude=coords[0],
                longitude=coords[1],
                timezone=None,
                search_field=f"Unknown, Unknown ({airport_code.upper()})"  # Correct column name
            )
            
            self.db.add(new_airport)
            try:
                self.db.commit()
                self.db.refresh(new_airport)
                logger.info(f"✅ Created airport: {airport_code}")
                return new_airport
            except Exception as commit_error:
                logger.error(f"❌ Commit failed for airport {airport_code}: {commit_error}")
                self.db.rollback()
                # Try to get existing airport as fallback
                airport = self.airport_service.get_airport_by_code(airport_code)
                return airport
                
        except Exception as e:
            logger.error(f"❌ Failed to create airport {airport_code}: {e}")
            # Final fallback - try to get any existing airport
            try:
                airport = self.db.query(Airport).filter(Airport.iata_code == airport_code.upper()).first()
                return airport
            except:
                return None
                
    def calculate_distance(self, dep_iata: str, dest_iata: str) -> float:
        """Calculate distance between two airports"""
        dep_airport = self.get_airport_by_code(dep_iata)
        dest_airport = self.get_airport_by_code(dest_iata)
        
        if not dep_airport or not dest_airport:
            raise ValueError("One or both airports not found")
        
        if (dep_airport.latitude and dep_airport.longitude and 
            dest_airport.latitude and dest_airport.longitude):
            # Simple distance calculation
            distance_km = self._calculate_simple_distance(
                dep_airport.latitude, dep_airport.longitude,
                dest_airport.latitude, dest_airport.longitude
            )
            return round(distance_km)
        else:
            # Fallback to predefined distances
            return self._get_fallback_distance(dep_iata, dest_iata)
    
    def _calculate_simple_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Simple distance calculation using Haversine formula"""
        from math import radians, sin, cos, sqrt, atan2
        
        # Convert to radians
        lat1, lon1, lat2, lon2 = map(radians, [lat1, lon1, lat2, lon2])
        
        # Haversine formula
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * atan2(sqrt(a), sqrt(1-a))
        radius_earth_km = 6371  # Earth's radius in km
        distance_km = radius_earth_km * c
        
        return distance_km
    
    def _get_fallback_distance(self, dep_iata: str, dest_iata: str) -> float:
        """Fallback distance calculation for airports without coordinates"""
        # Common routes with approximate distances
        common_distances = {
            ('AAL', 'CPH'): 5000,
            ('CPH', 'AAL'): 5000,
            ('JFK', 'LHR'): 5534,
            ('LHR', 'JFK'): 5534,
            ('LAX', 'NRT'): 8807,
            ('NRT', 'LAX'): 8807,
            ('JFK', 'CDG'): 5834,
            ('CDG', 'JFK'): 5834,
        }
        
        key = (dep_iata, dest_iata)
        if key in common_distances:
            return common_distances[key]
        
        # Default average distance
        return 5000