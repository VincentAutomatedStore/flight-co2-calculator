from sqlalchemy.orm import Session, joinedload
from database.models import FlightCalculation, Airport
from .airport_service import AirportService
from datetime import datetime
import logging
import requests
import json

logger = logging.getLogger(__name__)

class CalculationService:
    def __init__(self, db: Session):
        self.db = db
        self.airport_service = AirportService(db)
    
    def calculate_emissions(self, calculation_data: dict):
        """Calculate flight emissions using REAL ICAO API"""
        try:
            departure_code = calculation_data['departure']
            destination_code = calculation_data['destination']
            passengers = calculation_data.get('passengers', 1)
            round_trip = calculation_data.get('round_trip', False)
            cabin_class = calculation_data.get('cabin_class', 'economy')
            
            logger.info(f"🔄 Calculating emissions for {departure_code} -> {destination_code}")
            
            # Use REAL ICAO API instead of hardcoded calculation
            results = self._call_icao_api(departure_code, destination_code, passengers, round_trip, cabin_class)
            
            # Get or CREATE airport objects for database relationship
            dep_airport = self._get_or_create_airport(departure_code)
            dest_airport = self._get_or_create_airport(destination_code)
            
            if not dep_airport or not dest_airport:
                raise ValueError(f"Could not find or create airports: {departure_code}, {destination_code}")
            
            # Create flight info string
            flight_info = f"{departure_code} to {destination_code} - {results['distance_km']}km"
            if round_trip:
                flight_info += " (Round Trip)"
            flight_info += f" • {cabin_class.replace('_', ' ').title()}"
            
            # Determine calculation method based on data source
            if results.get('data_source') == 'ICAO_API':
                calculation_method = 'ICAO_API'
            elif results.get('data_source') == 'ENHANCED_CALCULATION':
                calculation_method = 'ICAO_ENHANCED'
            else:
                calculation_method = 'ICAO_BASIC'
            
            # Create flight calculation record
            calculation = FlightCalculation(
                # These are REQUIRED and cannot be NULL
                departure_airport_id=dep_airport.id,
                destination_airport_id=dest_airport.id,
                
                # Basic flight data
                passengers=passengers,
                round_trip=round_trip,
                cabin_class=cabin_class,
                
                # Distance data
                distance_km=results['distance_km'],
                distance_miles=results['distance_miles'],
                
                # Emission results
                fuel_burn_kg=results['fuel_burn_kg'],
                total_co2_kg=results['total_co2_kg'],
                co2_per_passenger_kg=results['co2_per_passenger_kg'],
                co2_tonnes=results['co2_tonnes'],
                
                # Metadata
                calculation_method=calculation_method,
                flight_info=flight_info
            )
            
            self.db.add(calculation)
            self.db.commit()
            self.db.refresh(calculation)
            
            logger.info(f"✅ Successfully calculated: {results['co2_per_passenger_kg']} kg CO₂")
            
            return self._calculation_to_dict(calculation, departure_code, destination_code, results.get('data_source'))
            
        except Exception as e:
            self.db.rollback()
            logger.error(f"❌ Calculation error: {str(e)}")
            raise
    
    def calculate_emissions_with_params(self, calculation_data: dict, batch_params: dict = None):
        """Calculate flight emissions with optional batch parameter overrides"""
        try:
            # If batch parameters provided, override individual calculation data
            if batch_params:
                calculation_data = {
                    **calculation_data,  # Keep original data
                    'passengers': batch_params.get('passengers', calculation_data.get('passengers', 1)),
                    'cabin_class': batch_params.get('cabinClass', calculation_data.get('cabin_class', 'economy')),
                    'round_trip': batch_params.get('roundTrip', calculation_data.get('round_trip', False))
                }
            
            return self.calculate_emissions(calculation_data)
            
        except Exception as e:
            logger.error(f"❌ Batch parameter calculation error: {str(e)}")
            raise

    def _get_or_create_airport(self, airport_code: str):
        """Get existing airport or create a minimal one - FIXED SESSION VERSION"""
        try:
            # Try to get existing airport first
            airport = self.airport_service.get_airport_by_code(airport_code)
            if airport:
                return airport
            
            # Check if we can safely create a new airport
            try:
                # Test if session is in a state that allows new operations
                self.db.connection()
            except Exception as session_error:
                logger.warning(f"🔄 Session issue for {airport_code}, attempting to recover...")
                try:
                    # Try to rollback and start fresh
                    self.db.rollback()
                except:
                    # If rollback fails, try to get existing again
                    airport = self.airport_service.get_airport_by_code(airport_code)
                    if airport:
                        return airport
                    # If all else fails, return None
                    return None
            
            # Create a minimal airport record
            logger.info(f"🆕 Creating airport record for: {airport_code}")
            
            # Get coordinates from fallback
            coords = self._get_airport_coordinates(airport_code)
            
            new_airport = Airport(
                iata_code=airport_code,
                name=f"{airport_code} Airport",
                city="Unknown",
                country="Unknown",
                latitude=coords[0],
                longitude=coords[1],
                search=f"{airport_code} Airport"
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
                airport = self.db.query(Airport).filter(Airport.iata_code == airport_code).first()
                return airport
            except:
                return None

    def _get_airport_coordinates(self, airport_code: str):
        """Get coordinates for common airports"""
        airport_coords = {
            # Canadian airports
            'YYZ': (43.677719, -79.624819),  # Toronto
            'YVR': (49.194698, -123.179192), # Vancouver
            'YYC': (51.121389, -114.007778), # Calgary
            'YUL': (45.470556, -73.740833),  # Montreal
            'YOW': (45.322500, -75.667222),  # Ottawa
            'YYT': (47.618610, -52.751945),  # St. John's
            'YYJ': (48.646944, -123.425833), # Victoria
            'YEG': (53.309723, -113.579722), # Edmonton
            'YHZ': (44.880833, -63.508610),  # Halifax
            'YWG': (49.910000, -97.239444),  # Winnipeg
            
            # US airports
            'JFK': (40.639751, -73.778925),
            'LAX': (33.942791, -118.410042),
            'LHR': (51.470022, -0.454295),
            'CDG': (49.009691, 2.547925),
            'DXB': (25.252778, 55.364445),
            'SIN': (1.359211, 103.989306),
        }
        
        return airport_coords.get(airport_code.upper(), (0.0, 0.0))
    
    def _calculation_to_dict(self, calculation, departure_code, destination_code, data_source):
        """Convert calculation to dictionary for response"""
        return {
            'id': calculation.id,
            'departure': departure_code,
            'destination': destination_code,
            'passengers': calculation.passengers,
            'round_trip': calculation.round_trip,
            'cabin_class': calculation.cabin_class,
            'fuel_burn_kg': calculation.fuel_burn_kg,
            'total_co2_kg': calculation.total_co2_kg,
            'co2_per_passenger_kg': calculation.co2_per_passenger_kg,
            'co2_tonnes': calculation.co2_tonnes,
            'distance_km': calculation.distance_km,
            'distance_miles': calculation.distance_miles,
            'data_source': data_source or 'CALCULATION',
            'flight_info': calculation.flight_info,
            'created_at': calculation.created_at.isoformat() if calculation.created_at else None
        }
    
    # WITH NO FALLBACK IF ICAO FAILES
    def _call_icao_api(self, departure: str, destination: str, passengers: int, round_trip: bool, cabin_class: str):
        """Call the real ICAO API - STRICT MODE: No fallbacks"""
        try:
            logger.info(f"🌐 Calling ICAO API for {departure} -> {destination}")
            
            url = "https://icec.icao.int/Home/PassengerCompute"
            
            # CORRECTED: Map cabin class to ICAO numeric format
            cabin_class_mapping = {
                "economy": 0,
                "premium_economy": 1, 
                "business": 2,
                "first": 3
            }
            
            icao_cabin_class = cabin_class_mapping.get(cabin_class, 0)
            
            # Get airport names
            dep_airport = self._get_or_create_airport(departure)
            dest_airport = self._get_or_create_airport(destination)
            
            departure_name = self.format_airport_name(dep_airport)
            destination_name = self.format_airport_name(dest_airport)
            
            # CORRECTED: Proper ICAO API payload
            payload = {
                "AirportCodeDeparture": departure.upper(),
                "AirportCodeDestination": [destination.upper()],
                "CabinClass": icao_cabin_class,
                "Departure": departure_name,
                "Destination": [destination_name],
                "IsRoundTrip": round_trip,
                "NumberOfPassenger": passengers
            }
            
            headers = {
                "Content-Type": "application/json; charset=UTF-8",
                "Accept": "application/json, text/javascript, */*; q=0.01",
                "X-Requested-With": "XMLHttpRequest",
                "Origin": "https://icec.icao.int",
                "Referer": "https://icec.icao.int/calculator",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            }
            
            response = requests.post(url, json=payload, headers=headers, timeout=30)
            
            logger.info(f"📡 ICAO API Response Status: {response.status_code}")
            
            if response.status_code == 200:
                try:
                    data = response.json()
                    return self._parse_icao_response(data, departure, destination, passengers, round_trip, cabin_class)
                except json.JSONDecodeError as e:
                    logger.error(f"❌ JSON decode error for {departure}->{destination}: {e}")
                    # STRICT MODE: Don't fallback, raise exception
                    raise Exception(f"ICAO API returned invalid JSON: {e}")
            else:
                logger.error(f"❌ ICAO API returned status {response.status_code}")
                # STRICT MODE: Don't fallback, raise exception
                raise Exception(f"ICAO API returned status {response.status_code}")
                
        except requests.exceptions.Timeout:
            logger.error(f"⏰ ICAO API timeout for {departure}->{destination}")
            raise Exception("ICAO API timeout - no fallback calculation performed")
        except requests.exceptions.ConnectionError:
            logger.error(f"🔌 ICAO API connection error for {departure}->{destination}")
            raise Exception("ICAO API connection error - no fallback calculation performed")
        except Exception as e:
            logger.error(f"❌ ICAO API call failed for {departure}->{destination}: {e}")
            # STRICT MODE: Re-raise the exception instead of falling back
            raise

    # # WITH FALLBACK IF ICAO FAILES
    # def _call_icao_api(self, departure: str, destination: str, passengers: int, round_trip: bool, cabin_class: str):
    #     """Call the real ICAO API with better error handling"""
    #     try:
    #         logger.info(f"🌐 Calling ICAO API for {departure} -> {destination}")
            
    #         url = "https://icec.icao.int/Home/PassengerCompute"
            
    #         # CORRECTED: Map cabin class to ICAO numeric format
    #         cabin_class_mapping = {
    #             "economy": 0,        # ICAO uses 0 for Economy
    #             "premium_economy": 1, # ICAO uses 1 for Premium Economy  
    #             "business": 2,        # ICAO uses 2 for Business
    #             "first": 3            # ICAO uses 3 for First
    #         }
            
    #         icao_cabin_class = cabin_class_mapping.get(cabin_class, 0)
            
    #         # Use the actual airport names from database if available
    #         dep_airport = self._get_or_create_airport(departure)
    #         dest_airport = self._get_or_create_airport(destination)
            
    #         departure_name = f"{departure.upper()} Airport"
    #         destination_name = f"{destination.upper()} Airport"
            
    #         if dep_airport and dep_airport.name and dep_airport.name != "Unknown Airport":
    #             departure_name = dep_airport.name
    #         if dest_airport and dest_airport.name and dest_airport.name != "Unknown Airport":
    #             destination_name = dest_airport.name
            
    #         # CORRECTED: Proper ICAO API payload
    #         payload = {
    #             "AirportCodeDeparture": departure.upper(),
    #             "AirportCodeDestination": [destination.upper()],
    #             "CabinClass": icao_cabin_class,  # Now sending numeric value
    #             "Departure": departure_name,
    #             "Destination": [destination_name],
    #             "IsRoundTrip": round_trip,
    #             "NumberOfPassenger": passengers
    #         }

    #         headers = {
    #             "Content-Type": "application/json; charset=UTF-8",
    #             "Accept": "application/json, text/javascript, */*; q=0.01",
    #             "X-Requested-With": "XMLHttpRequest",
    #             "Origin": "https://icec.icao.int",
    #             "Referer": "https://icec.icao.int/calculator",
    #             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    #         }
            
    #         # Add timeout and better error handling
    #         response = requests.post(url, json=payload, headers=headers, timeout=30)
            
    #         logger.info(f"📡 ICAO API Response Status: {response.status_code}")
            
    #         if response.status_code == 200:
    #             try:
    #                 # Try to parse JSON with better error handling
    #                 data = response.json()
    #                 return self._parse_icao_response(data, departure, destination, passengers, round_trip, cabin_class)
    #             except json.JSONDecodeError as e:
    #                 logger.error(f"❌ JSON decode error for {departure}->{destination}: {e}")
    #                 logger.error(f"📄 Response text: {response.text[:500]}...")
    #                 # Try to extract data from HTML response if JSON fails
    #                 return self._parse_html_fallback(response.text, departure, destination, passengers, round_trip, cabin_class)
    #         else:
    #             logger.error(f"❌ ICAO API returned status {response.status_code}")
    #             logger.error(f"📄 Response text: {response.text[:500]}...")
    #             raise Exception(f"ICAO API returned status {response.status_code}")
                
    #     except requests.exceptions.Timeout:
    #         logger.error(f"⏰ ICAO API timeout for {departure}->{destination}")
    #         return self._calculate_enhanced_fallback(departure, destination, passengers, round_trip, cabin_class)
    #     except requests.exceptions.ConnectionError:
    #         logger.error(f"🔌 ICAO API connection error for {departure}->{destination}")
    #         return self._calculate_enhanced_fallback(departure, destination, passengers, round_trip, cabin_class)
    #     except Exception as e:
    #         logger.error(f"❌ ICAO API call failed for {departure}->{destination}: {e}")
    #         return self._calculate_enhanced_fallback(departure, destination, passengers, round_trip, cabin_class)

    def _parse_icao_response(self, icao_response: dict, departure: str, destination: str, passengers: int, round_trip: bool, cabin_class: str):
        """Parse ICAO API response"""
        result_summary = None
        for summary in icao_response.get('resultSummary', []):
            if summary.get('cabinClass') == 0 and summary.get('isClassFound', False):
                result_summary = summary
                break
        
        if not result_summary:
            raise ValueError("No valid results found in ICAO response")
        
        total_co2 = 0
        total_fuel = 0
        total_distance = 0
        
        for leg in result_summary.get('details', []):
            total_co2 += leg.get('co2', 0)
            total_fuel += leg.get('avgFuel', 0)
            total_distance += leg.get('tripDistance', 0)
        
        co2_per_passenger = total_co2
        total_co2_for_passengers = co2_per_passenger * passengers
        
        fuel_per_passenger = total_co2 / 3.16
        total_fuel_for_passengers = fuel_per_passenger * passengers

        return {
            'fuel_burn_kg': round(total_fuel_for_passengers),
            'total_co2_kg': round(total_co2_for_passengers),
            'co2_per_passenger_kg': round(co2_per_passenger),
            'co2_tonnes': round(total_co2_for_passengers / 1000, 3),
            'distance_km': round(total_distance),
            'distance_miles': round(total_distance * 0.621371),
            'cabin_class': cabin_class,
            'data_source': 'ICAO_API'
        }

    def _parse_html_fallback(self, html_content: str, departure: str, destination: str, passengers: int, round_trip: bool, cabin_class: str):
        """Fallback parsing when ICAO returns HTML instead of JSON - IMPROVED"""
        try:
            logger.info(f"🔄 Attempting HTML fallback parsing for {departure}->{destination}")
            
            # Check for specific error patterns
            html_lower = html_content.lower()
            
            if "rate limit" in html_lower or "too many requests" in html_lower:
                logger.warning(f"🚫 Rate limit detected for {departure}->{destination}")
                raise Exception("ICAO API rate limit exceeded")
            
            if "error" in html_lower or "not found" in html_lower or "DOCTYPE html" in html_content:
                logger.warning(f"🚫 ICAO API returned HTML error page for {departure}->{destination}")
                # This is likely a temporary ICAO API issue, use enhanced fallback
                return self._calculate_enhanced_fallback(departure, destination, passengers, round_trip, cabin_class)
            
            # Try to extract any useful information from the HTML
            if "carbon" in html_lower or "emission" in html_lower:
                # Might be a different page structure, try to find numbers
                import re
                # Look for numbers that could be distances or emissions
                numbers = re.findall(r'\b\d{1,5}\b', html_content)
                if numbers:
                    logger.info(f"🔍 Found potential numbers in HTML response: {numbers[:5]}")
            
            # If we can't parse useful data, use enhanced fallback
            logger.warning(f"📄 Could not parse HTML response for {departure}->{destination}, using enhanced fallback")
            return self._calculate_enhanced_fallback(departure, destination, passengers, round_trip, cabin_class)
            
        except Exception as e:
            logger.error(f"❌ HTML fallback failed for {departure}->{destination}: {e}")
            return self._calculate_enhanced_fallback(departure, destination, passengers, round_trip, cabin_class)

    def _calculate_enhanced_fallback(self, departure: str, destination: str, passengers: int, round_trip: bool, cabin_class: str):
        """Enhanced fallback when ICAO API fails with better error handling"""
        try:
            # Calculate real distance with better error handling
            distance_km = 0
            try:
                distance_km = self.airport_service.calculate_distance(departure, destination)
            except Exception as e:
                logger.warning(f"📏 Distance calculation failed for {departure}->{destination}: {e}")
            
            if distance_km == 0:
                # Use common route distances as fallback
                common_distances = {
                    # Add more common routes here
                    'ALA-FRU': 200,  # Almaty to Bishkek
                    'FRU-ALA': 200,
                }
                
                route_key = f"{departure.upper()}-{destination.upper()}"
                distance_km = common_distances.get(route_key, 800)  # Default to 800km
                logger.info(f"📏 Using estimated distance for {route_key}: {distance_km} km")
            
            # Rest of the calculation logic remains the same...
            CO2_PER_KG_FUEL = 3.16
            BASE_FUEL_PER_PAX_KM = 0.01766
            
            cabin_multipliers = {
                "economy": 1.0, "premium_economy": 1.3, "business": 1.8, "first": 2.5
            }
            
            multiplier = cabin_multipliers.get(cabin_class, 1.0)
            fuel_per_passenger_one_way = distance_km * BASE_FUEL_PER_PAX_KM * multiplier
            
            if round_trip:
                fuel_per_passenger_total = fuel_per_passenger_one_way * 2
                co2_per_passenger = fuel_per_passenger_total * CO2_PER_KG_FUEL
            else:
                fuel_per_passenger_total = fuel_per_passenger_one_way
                co2_per_passenger = fuel_per_passenger_one_way * CO2_PER_KG_FUEL
            
            total_co2 = co2_per_passenger * passengers
            total_fuel = fuel_per_passenger_total * passengers

            return {
                'fuel_burn_kg': round(total_fuel),
                'total_co2_kg': round(total_co2),
                'co2_per_passenger_kg': round(co2_per_passenger),
                'co2_tonnes': round(total_co2 / 1000, 3),
                'distance_km': round(distance_km),
                'distance_miles': round(distance_km * 0.621371),
                'cabin_class': cabin_class,
                'data_source': 'ENHANCED_FALLBACK'
            }
            
        except Exception as e:
            logger.error(f"❌ Enhanced fallback failed for {departure}->{destination}: {e}")
            return self._calculate_basic_fallback(departure, destination, passengers, round_trip, cabin_class)

    def _calculate_basic_fallback(self, departure: str, destination: str, passengers: int, round_trip: bool, cabin_class: str):
        """Basic fallback"""
        try:
            distance_km = self.airport_service.calculate_distance(departure, destination)
            if distance_km == 0:
                distance_km = 1500
        except:
            distance_km = 1500
        
        base_distance = 5000
        distance_factor = distance_km / base_distance
        
        if distance_km <= 1000:
            base_co2 = 90
        elif distance_km <= 4000:
            base_co2 = 110
        else:
            base_co2 = 140
        
        co2_per_passenger = base_co2 * distance_factor
        
        cabin_multipliers = {
            "economy": 1.0, "premium_economy": 1.3, "business": 1.8, "first": 2.5
        }
        
        multiplier = cabin_multipliers.get(cabin_class.lower(), 1.0)
        co2_per_passenger *= multiplier
        
        if round_trip:
            co2_per_passenger *= 2
        
        total_co2 = co2_per_passenger * passengers
        fuel_burn = total_co2 / 3.16

        return {
            'fuel_burn_kg': round(fuel_burn),
            'total_co2_kg': round(total_co2),
            'co2_per_passenger_kg': round(co2_per_passenger),
            'co2_tonnes': round(total_co2 / 1000, 3),
            'distance_km': round(distance_km),
            'distance_miles': round(distance_km * 0.621371),
            'cabin_class': cabin_class,
            'data_source': 'BASIC_CALCULATION'
        }
    
    def get_calculation_history(self, limit: int = None):
        """Get calculation history with optional limit"""
        try:
            logger.info("🔍 Getting calculation history...")
            
            # Build query without hardcoded limit
            query = self.db.query(FlightCalculation)\
                .order_by(FlightCalculation.created_at.desc())
            
            # Apply limit only if specified
            if limit:
                query = query.limit(limit)
            
            calculations = query.all()
            
            logger.info(f"✅ Found {len(calculations)} calculations")
            
            # Rest of the method remains the same...
            results = []
            for calc in calculations:
                try:
                    departure_code = self._get_airport_code_by_id(calc.departure_airport_id)
                    destination_code = self._get_airport_code_by_id(calc.destination_airport_id)
                    
                    # Determine data source from calculation method
                    if calc.calculation_method == 'ICAO_API':
                        data_source = 'ICAO_API'
                    elif calc.calculation_method == 'ICAO_ENHANCED':
                        data_source = 'ENHANCED_CALCULATION'
                    elif calc.calculation_method == 'ICAO_BASIC':
                        data_source = 'BASIC_CALCULATION'
                    else:
                        data_source = 'CALCULATION'
                    
                    result = {
                        'id': calc.id,
                        'departure': departure_code,
                        'destination': destination_code,
                        'passengers': calc.passengers,
                        'round_trip': calc.round_trip,
                        'cabin_class': calc.cabin_class,
                        'fuel_burn_kg': calc.fuel_burn_kg,
                        'total_co2_kg': calc.total_co2_kg,
                        'co2_per_passenger_kg': calc.co2_per_passenger_kg,
                        'co2_tonnes': calc.co2_tonnes,
                        'distance_km': calc.distance_km,
                        'distance_miles': calc.distance_miles,
                        'data_source': data_source,
                        'flight_info': calc.flight_info,
                        'created_at': calc.created_at.isoformat() if calc.created_at else None
                    }
                    
                    results.append(result)
                    
                except Exception as e:
                    logger.error(f"❌ Error processing calculation {calc.id}: {e}")
                    # Fallback logic...
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"💥 Error in get_calculation_history: {e}")
            raise

    def _get_airport_code_by_id(self, airport_id: int):
        """Get airport code by ID directly from database"""
        try:
            if not airport_id:
                return "Unknown"
            
            airport = self.db.query(Airport).filter(Airport.id == airport_id).first()
            if airport:
                return airport.code
            else:
                return "Unknown"
        except Exception as e:
            logger.error(f"❌ Error getting airport {airport_id}: {e}")
            return "Unknown"

    def _extract_airports_from_flight_info(self, flight_info: str):
        """Extract airport codes from flight_info string as fallback"""
        if not flight_info:
            return "Unknown", "Unknown"
        
        try:
            # Multiple possible formats:
            # Format 1: "YYZ to YVR - 1234km • Economy"
            # Format 2: "JFK to LHR"
            # Format 3: "New York (JFK) to London (LHR)"
            
            if ' to ' in flight_info:
                parts = flight_info.split(' to ')
                if len(parts) >= 2:
                    departure_raw = parts[0].strip()
                    destination_raw = parts[1].split(' - ')[0].strip() if ' - ' in parts[1] else parts[1].strip()
                    
                    # Clean both codes
                    departure = self._clean_airport_code(departure_raw)
                    destination = self._clean_airport_code(destination_raw)
                    
                    return departure, destination
            
            return "Unknown", "Unknown"
        except Exception as e:
            print(f"❌ Error in _extract_airports_from_flight_info: {e}")
            return "Unknown", "Unknown"

    def delete_calculation(self, calculation_id: int):
        """Delete a calculation"""
        calculation = self.db.query(FlightCalculation).filter(FlightCalculation.id == calculation_id).first()
        if calculation:
            self.db.delete(calculation)
            self.db.commit()
            return True
        return False
    
    def get_calculation_history_simple(self, limit: int = None):
        """Simple version without hardcoded limit - USES CORRECT TABLE NAME"""
        try:
            logger.info("🔍 Getting calculation history (simple method)...")
            
            # First check which table exists
            try:
                from sqlalchemy import text
                result = self.db.execute(text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name = 'flight_calculations';
                """))
                existing_tables = [row[0] for row in result]
                logger.info(f"📋 Found calculation tables: {existing_tables}")
                
                if not existing_tables:
                    logger.error("❌ No flight calculation tables found!")
                    return []
                    
            except Exception as table_check_error:
                logger.error(f"❌ Error checking tables: {table_check_error}")
                return []
            
            # Build query - this should now work with the correct table name
            query = self.db.query(FlightCalculation)\
                .order_by(FlightCalculation.created_at.desc())
            
            # Apply limit only if specified
            if limit:
                query = query.limit(limit)
            
            calculations = query.all()
            
            logger.info(f"✅ Found {len(calculations)} calculations in enhanced database")
            
            results = []
            for calc in calculations:
                try:
                    departure_code = self._get_airport_code_direct(calc.departure_airport_id)
                    destination_code = self._get_airport_code_direct(calc.destination_airport_id)
                    
                    if departure_code == "Unknown" and calc.flight_info:
                        departure_code, destination_code = self._extract_simple(calc.flight_info)
                    
                    result = {
                        'id': calc.id,
                        'departure': departure_code,
                        'destination': destination_code,
                        'passengers': calc.passengers,
                        'round_trip': calc.round_trip,
                        'cabin_class': calc.cabin_class,
                        'fuel_burn_kg': calc.fuel_burn_kg,
                        'total_co2_kg': calc.total_co2_kg,
                        'co2_per_passenger_kg': calc.co2_per_passenger_kg,
                        'co2_tonnes': calc.co2_tonnes,
                        'distance_km': calc.distance_km,
                        'distance_miles': calc.distance_miles,
                        'data_source': getattr(calc, 'calculation_method', 'CALCULATION'),
                        'flight_info': calc.flight_info,
                        'created_at': calc.created_at.isoformat() if calc.created_at else None
                    }
                    
                    results.append(result)
                    logger.info(f"✅ Processed: {departure_code} -> {destination_code}")
                    
                except Exception as e:
                    logger.error(f"❌ Error processing calculation {calc.id}: {e}")
                    continue
            
            return results
            
        except Exception as e:
            logger.error(f"💥 Error in get_calculation_history_simple: {e}")
            return []  # Return empty array instead of crashing
            
    def _get_airport_code_direct(self, airport_id):
        """Direct airport code lookup"""
        try:
            if not airport_id:
                return "Unknown"
            airport = self.db.query(Airport).filter(Airport.id == airport_id).first()
            return airport.code if airport else "Unknown"
        except:
            return "Unknown"

    def _extract_simple(self, flight_info):
        """Simple extraction from flight_info"""
        try:
            if not flight_info:
                return "Unknown", "Unknown"
            
            # Simple pattern: "XXX to YYY"
            if ' to ' in flight_info:
                parts = flight_info.split(' to ')
                if len(parts) >= 2:
                    dep = parts[0].strip()[:3]  # Take first 3 chars
                    dest = parts[1].strip()[:3]  # Take first 3 chars
                    return dep, dest
        except:
            pass
        return "Unknown", "Unknown"

    def _extract_airports_robust(self, calculation):
        """Robust airport extraction using multiple methods"""
        try:
            # Method 1: Try to get from airport relationships if they exist
            if hasattr(calculation, 'departure_airport_id') and calculation.departure_airport_id:
                dep_airport = self.db.query(Airport).filter(Airport.id == calculation.departure_airport_id).first()
                if dep_airport:
                    departure = dep_airport.code
                    dest_airport = self.db.query(Airport).filter(Airport.id == calculation.destination_airport_id).first()
                    if dest_airport:
                        return departure, dest_airport.code
            
            # Method 2: Extract from flight_info string
            if calculation.flight_info:
                # Common flight_info format: "YYZ to YVR - 1234km • Economy"
                if ' to ' in calculation.flight_info:
                    parts = calculation.flight_info.split(' to ')
                    if len(parts) >= 2:
                        departure = parts[0].strip()
                        # Get destination before the dash
                        destination_part = parts[1].split(' - ')[0].strip()
                        # Clean up any extra text
                        departure = self._clean_airport_code(departure)
                        destination = self._clean_airport_code(destination_part)
                        if departure != 'Unknown' and destination != 'Unknown':
                            return departure, destination
            
            # Method 3: Check if there are direct departure/destination fields
            if hasattr(calculation, 'departure') and calculation.departure:
                departure = self._clean_airport_code(calculation.departure)
                destination = self._clean_airport_code(calculation.destination) if hasattr(calculation, 'destination') else 'Unknown'
                if departure != 'Unknown':
                    return departure, destination
            
            # Method 4: Last resort - try to parse from any string field
            for field in ['flight_info', 'departure', 'destination']:
                if hasattr(calculation, field):
                    value = getattr(calculation, field)
                    if value and isinstance(value, str):
                        # Look for 3-letter airport codes
                        import re
                        codes = re.findall(r'\b[A-Z]{3}\b', value)
                        if len(codes) >= 2:
                            return codes[0], codes[1]
            
            return "Unknown", "Unknown"
            
        except Exception as e:
            print(f"❌ Error extracting airports: {e}")
            return "Unknown", "Unknown"

    def _clean_airport_code(self, code):
        """Clean and validate airport code"""
        if not code or code == 'Unknown':
            return "Unknown"
        
        # Remove common prefixes/suffixes and extract 3-letter code
        code = str(code).strip().upper()
        
        # If it's already a 3-letter code, return it
        if len(code) == 3 and code.isalpha():
            return code
        
        # Extract from strings like "New York (JFK)" or "JFK Airport"
        import re
        match = re.search(r'\b([A-Z]{3})\b', code)
        if match:
            return match.group(1)
        
        # Check if it's in our known airports list
        known_airports = ['JFK', 'LHR', 'LAX', 'YYZ', 'YVR', 'CDG', 'DXB', 'SIN', 'NRT', 'CPH', 'AAL']
        for airport in known_airports:
            if airport in code:
                return airport
        
        return "Unknown"