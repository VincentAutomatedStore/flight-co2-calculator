import csv
import pandas as pd
import os
import logging
import shutil
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Dict, List
from .calculation_service import CalculationService
from .airport_service import AirportService

logger = logging.getLogger(__name__)

class BatchService:
    def __init__(self, db_session):
        self.db = db_session
    
    def _count_csv_rows(self, file_path):
        """Count total rows in CSV file"""
        try:
            with open(file_path, 'r', encoding='utf-8-sig') as file:
                # Read sample to detect header
                sample = file.read(1024)
                file.seek(0)
                
                has_header = any(keyword in sample.upper() for keyword in 
                               ['DEPARTURE', 'DESTINATION', 'PASSENGER', 'CABIN', 'ROUND'])
                
                csv_reader = csv.reader(file)
                
                # Skip header if present
                if has_header:
                    next(csv_reader, None)
                
                # Count rows
                row_count = sum(1 for row in csv_reader)
                return row_count
        except Exception as e:
            print(f"❌ Error counting CSV rows: {e}")
            return 0
    
    def _validate_airport_code(self, code):
        """Validate and clean airport code"""
        if not code or not isinstance(code, str):
            return None
        
        code = code.strip().upper()
        clean_code = ''.join(c for c in code if c.isalpha())[:3]
        
        if len(clean_code) != 3:
            return None
        
        try:
            from database.models import Airport
            airport = self.db.query(Airport).filter(Airport.iata_code == clean_code).first()
            
            if airport:
                return clean_code
            else:
                print(f"❌ Airport not found in database: {clean_code}")
                return None
        except Exception as e:
            print(f"❌ Airport validation error for {clean_code}: {e}")
            return None


class DirectBatchService:
    def __init__(self, db_session):
        self.db = db_session
        # ADD THIS PROGRESS TRACKING
        self.current_progress = {
            'status': 'idle',
            'message': 'Ready for processing',
            'current_row': 0,
            'total_rows': 0,
            'processed_rows': 0,
            'error_rows': 0,
            'progress_percent': 0
        }

    def update_progress(self, **kwargs):
        """Update progress information - FIXED VERSION"""
        for key, value in kwargs.items():
            if key in self.current_progress:
                self.current_progress[key] = value
        
        # DEBUG: Print the full progress state to see what's happening
        print(f"🔄 Progress updated: {self.current_progress}")
        
        # Ensure status is always set during processing
        if 'status' not in kwargs and self.current_progress.get('current_row', 0) > 0:
            # If we're processing rows but status wasn't explicitly set, ensure it's 'processing'
            if self.current_progress['status'] == 'idle':
                self.current_progress['status'] = 'processing'

    def reset_progress(self):
        """Reset progress to idle state"""
        self.current_progress.update({
            'status': 'idle',
            'message': 'Ready for processing',
            'current_row': 0,
            'total_rows': 0,
            'processed_rows': 0,
            'error_rows': 0,
            'progress_percent': 0
        })
    
    def clean_csv_header(self, header):
        """Remove BOM and clean CSV header"""
        cleaned_header = []
        for field in header:
            # Remove BOM character if present
            if field.startswith('\ufeff'):
                field = field.replace('\ufeff', '')
            # Clean the field name
            field = field.strip().lower()
            # Map common column names
            if field in ['departure_iata', 'departure', 'from', 'origin']:
                field = 'departure_iata'
            elif field in ['destination_iata', 'destination', 'to', 'arrival']:
                field = 'destination_iata'
            elif field in ['passengers', 'pax']:
                field = 'passengers'
            elif field in ['cabin_class', 'cabin', 'class']:
                field = 'cabin_class'
            elif field in ['round_trip', 'roundtrip', 'return']:
                field = 'round_trip'
            cleaned_header.append(field)
        return cleaned_header
    
    def _validate_airport_code(self, code):
        """Validate and clean airport code - SIMPLIFIED VERSION"""
        if not code or not isinstance(code, str):
            return None
        
        code = code.strip().upper()
        clean_code = ''.join(c for c in code if c.isalpha())[:3]
        
        if len(clean_code) != 3:
            return None
        
        # SIMPLIFIED: Just return the code for now, don't check database
        return clean_code
    
    def _get_airport_id(self, iata_code):
        """Get airport ID from IATA code"""
        try:
            from database.models import Airport
            airport = self.db.query(Airport).filter(Airport.iata_code == iata_code).first()
            return airport.id if airport else None
        except Exception as e:
            print(f"❌ Error getting airport ID for {iata_code}: {e}")
            return None
    
    def _debug_model_structure(self):
        """Debug the EnhancedFlightCalculation model structure"""
        try:
            from database.models import FlightCalculation as EnhancedFlightCalculation
            import inspect
            
            print("🔍 DEBUG: EnhancedFlightCalculation model structure:")
            for name, value in inspect.getmembers(EnhancedFlightCalculation):
                if not name.startswith('_') and not inspect.ismethod(value):
                    print(f"   {name}: {type(value)}")
            
            # Try to create an instance to see what fields are required
            test_instance = EnhancedFlightCalculation()
            print("✅ Model can be instantiated")
            return True
        except Exception as e:
            print(f"❌ Model debug failed: {e}")
            return False
    
    # STRICT MODE - NO FALLBACK IF ICAO FAILS
    def process_flight_csv(self, file_path, batch_size=50, batch_params=None):
        """Process CSV using direct function calls - STRICT MODE: No fallbacks on ICAO failure"""
        try:
            print(f"🔄 Processing {file_path} with DIRECT FUNCTION CALLS - STRICT MODE")
            print(f"📋 Batch parameters: {batch_params}")
            
            # Use default batch params if none provided
            if batch_params is None:
                batch_params = {
                    'passengers': 1,
                    'cabinClass': 'economy',
                    'roundTrip': False
                }
            
            # RESET PROGRESS AT START
            self.reset_progress()
            self.update_progress(
                status='processing',  # Set status to processing
                message=f'Starting processing of {file_path} with {batch_params} - STRICT MODE',
                current_row=0,
                processed_rows=0,
                error_rows=0
            )
            
            if not os.path.exists(file_path):
                self.update_progress(status='failed', message=f'File not found: {file_path}')
                return {'success': False, 'error': f'File not found: {file_path}'}
            
            # Get original filename for timestamped movement
            original_filename = os.path.basename(file_path)
            
            processed_rows = 0
            error_rows = 0
            results = []
            batch_count = 0
            
            # Use utf-8-sig to handle BOM automatically
            with open(file_path, 'r', encoding='utf-8-sig') as file:
                csv_reader = csv.reader(file)
                
                # Read and clean header
                header = next(csv_reader, None)
                if header:
                    cleaned_header = self.clean_csv_header(header)
                    print(f"📋 CSV header (cleaned): {cleaned_header}")
                else:
                    print(f"❌ Empty CSV file")
                    self.update_progress(status='failed', message='Empty CSV file')
                    return {'success': False, 'error': 'Empty CSV file'}
                
                total_rows = sum(1 for row in csv_reader)
                file.seek(0)  # Reset to beginning
                next(csv_reader, None)  # Skip header again
                
                # UPDATE PROGRESS WITH TOTAL ROWS - MAKE SURE STATUS STAYS 'processing'
                self.update_progress(
                    status='processing',  # Keep status as processing
                    total_rows=total_rows,
                    message=f'Processing {total_rows} rows from {file_path} with batch params: {batch_params} - STRICT MODE'
                )
                
                for row_num, row in enumerate(csv_reader, start=2):
                    try:
                        # Update progress more frequently - every 5 rows instead of batch_size
                        if row_num % 5 == 0 or row_num == 2:
                            self.update_progress(
                                status='processing',
                                current_row=row_num,
                                processed_rows=processed_rows,
                                error_rows=error_rows,
                                progress_percent=((row_num - 2) / total_rows * 100) if total_rows > 0 else 0,
                                message=f'Processing row {row_num} of {total_rows} - {processed_rows} successful, {error_rows} failed'
                            )
                        
                        # Progress update (keep your existing logging)
                        if row_num % batch_size == 0 or row_num == 2:
                            progress_percent = (row_num / total_rows) * 100 if total_rows > 0 else 0
                            print(f"📊 Progress: {row_num}/{total_rows} rows ({progress_percent:.1f}%) - {processed_rows} successful, {error_rows} errors")
                        
                        if len(row) < 2:
                            print(f"⚠️ Row {row_num}: insufficient columns, skipping")
                            error_rows += 1
                            self.update_progress(
                                status='processing',  # Keep status as processing
                                error_rows=error_rows
                            )
                            results.append({
                                'row': row_num,
                                'success': False,
                                'error': 'Insufficient columns'
                            })
                            continue
                        
                        # Create dictionary from row using cleaned header
                        row_dict = {}
                        for i, field in enumerate(cleaned_header):
                            if i < len(row):
                                row_dict[field] = row[i]
                        
                        # Extract data using cleaned field names
                        departure_iata_raw = row_dict.get('departure_iata', '').strip().upper()
                        destination_iata_raw = row_dict.get('destination_iata', '').strip().upper()
                        
                        # Validate airport codes (SIMPLIFIED - just check format)
                        departure = self._validate_airport_code(departure_iata_raw)
                        destination = self._validate_airport_code(destination_iata_raw)
                        
                        if not departure or not destination:
                            print(f"⚠️ Row {row_num}: invalid airport codes '{departure_iata_raw}' -> '{destination_iata_raw}', skipping")
                            error_rows += 1
                            self.update_progress(
                                status='processing',  # Keep status as processing
                                error_rows=error_rows
                            )
                            results.append({
                                'row': row_num,
                                'success': False,
                                'error': f'Invalid airport codes: {departure_iata_raw} -> {destination_iata_raw}'
                            })
                            continue
                        
                        if departure == destination:
                            print(f"⚠️ Row {row_num}: same airport {departure}, skipping")
                            error_rows += 1
                            self.update_progress(
                                status='processing',  # Keep status as processing
                                error_rows=error_rows
                            )
                            results.append({
                                'row': row_num,
                                'success': False,
                                'error': f'Same airport: {departure}'
                            })
                            continue
                        
                        # USE BATCH PARAMETERS INSTEAD OF CSV VALUES
                        # Override CSV values with batch parameters
                        passengers = batch_params['passengers']
                        cabin_class = batch_params['cabinClass']
                        round_trip = batch_params['roundTrip']
                        
                        print(f"🛫 Processing row {row_num}: {departure} -> {destination} with params: {passengers}pax, {cabin_class}, {round_trip and 'round trip' or 'one way'}")
                        
                        # Use direct function call from app.py - STRICT MODE: No fallbacks
                        from app import get_icao_emissions
                        try:
                            result = get_icao_emissions(
                                departure=departure,
                                destination=destination,
                                passengers=passengers,
                                round_trip=round_trip,
                                cabin_class=cabin_class
                            )
                            
                            if result:
                                # Create flight info
                                flight_info = f"{departure} to {destination} - {result.get('distance_km', 0)}km"
                                if round_trip:
                                    flight_info += " (Round Trip)"
                                flight_info += f" • {cabin_class.replace('_', ' ').title()}"
                                
                                # FIXED: Use EnhancedFlightCalculation for automation database
                                from database.models import FlightCalculation as EnhancedFlightCalculation
                                
                                # Get airport IDs
                                departure_airport_id = self._get_airport_id(departure)
                                destination_airport_id = self._get_airport_id(destination)
                                
                                # Create calculation
                                try:
                                    calculation_data = {
                                        'passengers': passengers,
                                        'round_trip': round_trip,
                                        'cabin_class': cabin_class,
                                        'fuel_burn_kg': float(result.get('fuel_burn_kg', 0)),
                                        'total_co2_kg': float(result.get('total_co2_kg', 0)),
                                        'co2_per_passenger_kg': float(result.get('co2_per_passenger_kg', 0)),
                                        'co2_tonnes': float(result.get('co2_tonnes', 0)),
                                        'distance_km': float(result.get('distance_km', 0)),
                                        'distance_miles': float(result.get('distance_miles', 0)),
                                        'flight_info': flight_info,
                                        'calculation_method': result.get('data_source', 'DIRECT_CALL'),
                                    }
                                    
                                    # Add airport IDs if we have them
                                    if departure_airport_id:
                                        calculation_data['departure_airport_id'] = departure_airport_id
                                    if destination_airport_id:
                                        calculation_data['destination_airport_id'] = destination_airport_id
                                    
                                    calculation = EnhancedFlightCalculation(**calculation_data)
                                    self.db.add(calculation)
                                    
                                    # Commit every batch_size rows
                                    if processed_rows % batch_size == 0:
                                        self.db.commit()
                                        batch_count += 1
                                        print(f"💾 Committed batch {batch_count} ({processed_rows} total processed)")
                                    
                                    processed_rows += 1
                                    # UPDATE PROGRESS WITH PROCESSED ROWS - KEEP STATUS AS 'processing'
                                    self.update_progress(
                                        status='processing',  # Keep status as processing
                                        processed_rows=processed_rows,
                                        progress_percent=(row_num / total_rows * 100) if total_rows > 0 else 0,
                                        message=f'Processed {processed_rows} rows successfully'
                                    )
                                    results.append({
                                        'row': row_num,
                                        'departure': departure,
                                        'destination': destination,
                                        'success': True,
                                        'calculation_id': calculation.id,
                                        'batch_params_applied': batch_params  # Track which params were used
                                    })
                                    print(f"✅ Row {row_num} processed successfully - ID: {calculation.id}")
                                    
                                except Exception as db_error:
                                    self.db.rollback()
                                    error_rows += 1
                                    self.update_progress(
                                        status='processing',  # Keep status as processing even on errors
                                        error_rows=error_rows
                                    )
                                    results.append({
                                        'row': row_num,
                                        'success': False,
                                        'error': f'Database error: {str(db_error)}'
                                    })
                                    print(f"❌ Database error for {departure}->{destination}: {db_error}")
                                    continue
                                    
                            else:
                                # STRICT MODE: If ICAO returns no result, count as error
                                error_rows += 1
                                self.update_progress(
                                    status='processing',  # Keep status as processing
                                    error_rows=error_rows
                                )
                                results.append({
                                    'row': row_num,
                                    'success': False,
                                    'error': 'ICAO API returned no data'
                                })
                                print(f"❌ Row {row_num}: ICAO API returned no data for {departure}->{destination}")
                                
                        except Exception as icao_error:
                            # STRICT MODE: Catch ICAO API exceptions and count as errors
                            error_rows += 1
                            self.update_progress(
                                status='processing',  # Keep status as processing
                                error_rows=error_rows
                            )
                            error_msg = f"ICAO API failed: {str(icao_error)}"
                            results.append({
                                'row': row_num,
                                'success': False,
                                'error': error_msg
                            })
                            print(f"❌ Row {row_num} ICAO API error for {departure}->{destination}: {error_msg}")
                            continue
                            
                    except Exception as e:
                        error_rows += 1
                        self.update_progress(
                            status='processing',  # Keep status as processing even on exceptions
                            error_rows=error_rows
                        )
                        results.append({
                            'row': row_num,
                            'success': False,
                            'error': f'Unexpected error: {str(e)}'
                        })
                        print(f"❌ Row {row_num} unexpected error: {str(e)}")
                        self.db.rollback()
                        continue
            
            # Final commit
            try:
                self.db.commit()
                print("💾 Final commit completed")
            except Exception as e:
                self.db.rollback()
                print(f"❌ Final commit error: {e}")
            
            print(f"🎉 STRICT MODE Processing complete: {processed_rows} successful, {error_rows} errors")
            
            # Calculate success rate BEFORE using it
            success_rate = (processed_rows / (processed_rows + error_rows)) * 100 if (processed_rows + error_rows) > 0 else 0
            
            # CRITICAL: UPDATE PROGRESS TO COMPLETED
            self.update_progress(
                status='completed',  # FINALLY set to completed
                message=f'STRICT MODE Processing completed: {processed_rows} successful, {error_rows} errors',
                processed_rows=processed_rows,
                error_rows=error_rows,
                progress_percent=100
            )
            
            # Return result with batch params info
            return {
                'success': True,
                'processed_rows': processed_rows,
                'error_rows': error_rows,
                'total_rows': processed_rows + error_rows,
                'results': results,
                'original_filename': original_filename,
                'success_rate': round(success_rate, 1),
                'batch_params_used': batch_params,  # Include which params were used
                'strict_mode': True  # Indicate strict mode was used
            }
            
        except Exception as e:
            print(f"💥 File processing error: {str(e)}")
            self.db.rollback()
            self.update_progress(
                status='failed',  # Set to failed on exception
                message=f'STRICT MODE Processing failed: {str(e)}',
                error_rows=error_rows + 1
            )
            return {
                'success': False,
                'error': str(e),
                'processed_rows': 0,
                'error_rows': 0,
                'strict_mode': True
            }
        
    # # WITH FALLBACK IF ICAO FAILES
    # def process_flight_csv(self, file_path, batch_size=50, batch_params=None):
    #     """Process CSV using direct function calls - UPDATED WITH BATCH PARAMS"""
    #     try:
    #         print(f"🔄 Processing {file_path} with DIRECT FUNCTION CALLS")
    #         print(f"📋 Batch parameters: {batch_params}")
            
    #         # Use default batch params if none provided
    #         if batch_params is None:
    #             batch_params = {
    #                 'passengers': 1,
    #                 'cabinClass': 'economy',
    #                 'roundTrip': False
    #             }
            
    #         # RESET PROGRESS AT START
    #         self.reset_progress()
    #         self.update_progress(
    #             status='processing',  # Set status to processing
    #             message=f'Starting processing of {file_path} with {batch_params}',
    #             current_row=0,
    #             processed_rows=0,
    #             error_rows=0
    #         )
            
    #         if not os.path.exists(file_path):
    #             self.update_progress(status='failed', message=f'File not found: {file_path}')
    #             return {'success': False, 'error': f'File not found: {file_path}'}
            
    #         # Get original filename for timestamped movement
    #         original_filename = os.path.basename(file_path)
            
    #         processed_rows = 0
    #         error_rows = 0
    #         results = []
    #         batch_count = 0
            
    #         # Use utf-8-sig to handle BOM automatically
    #         with open(file_path, 'r', encoding='utf-8-sig') as file:
    #             csv_reader = csv.reader(file)
                
    #             # Read and clean header
    #             header = next(csv_reader, None)
    #             if header:
    #                 cleaned_header = self.clean_csv_header(header)
    #                 print(f"📋 CSV header (cleaned): {cleaned_header}")
    #             else:
    #                 print(f"❌ Empty CSV file")
    #                 self.update_progress(status='failed', message='Empty CSV file')
    #                 return {'success': False, 'error': 'Empty CSV file'}
                
    #             total_rows = sum(1 for row in csv_reader)
    #             file.seek(0)  # Reset to beginning
    #             next(csv_reader, None)  # Skip header again
                
    #             # UPDATE PROGRESS WITH TOTAL ROWS - MAKE SURE STATUS STAYS 'processing'
    #             self.update_progress(
    #                 status='processing',  # Keep status as processing
    #                 total_rows=total_rows,
    #                 message=f'Processing {total_rows} rows from {file_path} with batch params: {batch_params}'
    #             )
                
    #             for row_num, row in enumerate(csv_reader, start=2):
    #                 try:
    #                     # Update progress more frequently - every 5 rows instead of batch_size
    #                     if row_num % 5 == 0 or row_num == 2:
    #                         self.update_progress(
    #                             status='processing',
    #                             current_row=row_num,
    #                             processed_rows=processed_rows,
    #                             error_rows=error_rows,
    #                             progress_percent=((row_num - 2) / total_rows * 100) if total_rows > 0 else 0,
    #                             message=f'Processing row {row_num} of {total_rows} - {processed_rows} successful'
    #                         )
                        
    #                     # Progress update (keep your existing logging)
    #                     if row_num % batch_size == 0 or row_num == 2:
    #                         progress_percent = (row_num / total_rows) * 100 if total_rows > 0 else 0
    #                         print(f"📊 Progress: {row_num}/{total_rows} rows ({progress_percent:.1f}%) - {processed_rows} successful, {error_rows} errors")
                        
    #                     if len(row) < 2:
    #                         print(f"⚠️ Row {row_num}: insufficient columns, skipping")
    #                         error_rows += 1
    #                         self.update_progress(
    #                             status='processing',  # Keep status as processing
    #                             error_rows=error_rows
    #                         )
    #                         continue
                        
    #                     # Create dictionary from row using cleaned header
    #                     row_dict = {}
    #                     for i, field in enumerate(cleaned_header):
    #                         if i < len(row):
    #                             row_dict[field] = row[i]
                        
    #                     # Extract data using cleaned field names
    #                     departure_iata_raw = row_dict.get('departure_iata', '').strip().upper()
    #                     destination_iata_raw = row_dict.get('destination_iata', '').strip().upper()
                        
    #                     # Validate airport codes (SIMPLIFIED - just check format)
    #                     departure = self._validate_airport_code(departure_iata_raw)
    #                     destination = self._validate_airport_code(destination_iata_raw)
                        
    #                     if not departure or not destination:
    #                         print(f"⚠️ Row {row_num}: invalid airport codes '{departure_iata_raw}' -> '{destination_iata_raw}', skipping")
    #                         error_rows += 1
    #                         self.update_progress(
    #                             status='processing',  # Keep status as processing
    #                             error_rows=error_rows
    #                         )
    #                         continue
                        
    #                     if departure == destination:
    #                         print(f"⚠️ Row {row_num}: same airport {departure}, skipping")
    #                         error_rows += 1
    #                         self.update_progress(
    #                             status='processing',  # Keep status as processing
    #                             error_rows=error_rows
    #                         )
    #                         continue
                        
    #                     # USE BATCH PARAMETERS INSTEAD OF CSV VALUES
    #                     # Override CSV values with batch parameters
    #                     passengers = batch_params['passengers']
    #                     cabin_class = batch_params['cabinClass']
    #                     round_trip = batch_params['roundTrip']
                        
    #                     print(f"🛫 Processing row {row_num}: {departure} -> {destination} with params: {passengers}pax, {cabin_class}, {round_trip and 'round trip' or 'one way'}")
                        
    #                     # Use direct function call from app.py
    #                     from app import get_icao_emissions
    #                     result = get_icao_emissions(
    #                         departure=departure,
    #                         destination=destination,
    #                         passengers=passengers,
    #                         round_trip=round_trip,
    #                         cabin_class=cabin_class
    #                     )
                        
    #                     if result:
    #                         # Create flight info
    #                         flight_info = f"{departure} to {destination} - {result.get('distance_km', 0)}km"
    #                         if round_trip:
    #                             flight_info += " (Round Trip)"
    #                         flight_info += f" • {cabin_class.replace('_', ' ').title()}"
                            
    #                         # FIXED: Use EnhancedFlightCalculation for automation database
    #                         from database.models import FlightCalculation as EnhancedFlightCalculation
                            
    #                         # Get airport IDs
    #                         departure_airport_id = self._get_airport_id(departure)
    #                         destination_airport_id = self._get_airport_id(destination)
                            
    #                         # Create calculation
    #                         try:
    #                             calculation_data = {
    #                                 'passengers': passengers,
    #                                 'round_trip': round_trip,
    #                                 'cabin_class': cabin_class,
    #                                 'fuel_burn_kg': float(result.get('fuel_burn_kg', 0)),
    #                                 'total_co2_kg': float(result.get('total_co2_kg', 0)),
    #                                 'co2_per_passenger_kg': float(result.get('co2_per_passenger_kg', 0)),
    #                                 'co2_tonnes': float(result.get('co2_tonnes', 0)),
    #                                 'distance_km': float(result.get('distance_km', 0)),
    #                                 'distance_miles': float(result.get('distance_miles', 0)),
    #                                 'flight_info': flight_info,
    #                                 'calculation_method': result.get('data_source', 'DIRECT_CALL'),
    #                             }
                                
    #                             # Add airport IDs if we have them
    #                             if departure_airport_id:
    #                                 calculation_data['departure_airport_id'] = departure_airport_id
    #                             if destination_airport_id:
    #                                 calculation_data['destination_airport_id'] = destination_airport_id
                                
    #                             calculation = EnhancedFlightCalculation(**calculation_data)
    #                             self.db.add(calculation)
                                
    #                             # Commit every batch_size rows
    #                             if processed_rows % batch_size == 0:
    #                                 self.db.commit()
    #                                 batch_count += 1
    #                                 print(f"💾 Committed batch {batch_count} ({processed_rows} total processed)")
                                
    #                             processed_rows += 1
    #                             # UPDATE PROGRESS WITH PROCESSED ROWS - KEEP STATUS AS 'processing'
    #                             self.update_progress(
    #                                 status='processing',  # Keep status as processing
    #                                 processed_rows=processed_rows,
    #                                 progress_percent=(row_num / total_rows * 100) if total_rows > 0 else 0,
    #                                 message=f'Processed {processed_rows} rows successfully'
    #                             )
    #                             results.append({
    #                                 'row': row_num,
    #                                 'departure': departure,
    #                                 'destination': destination,
    #                                 'success': True,
    #                                 'calculation_id': calculation.id,
    #                                 'batch_params_applied': batch_params  # Track which params were used
    #                             })
    #                             print(f"✅ Row {row_num} processed successfully - ID: {calculation.id}")
                                
    #                         except Exception as db_error:
    #                             self.db.rollback()
    #                             error_rows += 1
    #                             self.update_progress(
    #                                 status='processing',  # Keep status as processing even on errors
    #                                 error_rows=error_rows
    #                             )
    #                             print(f"❌ Database error for {departure}->{destination}: {db_error}")
    #                             continue
                                
    #                     else:
    #                         error_rows += 1
    #                         self.update_progress(
    #                             status='processing',  # Keep status as processing
    #                             error_rows=error_rows
    #                         )
    #                         results.append({
    #                             'row': row_num,
    #                             'success': False,
    #                             'error': 'Calculation failed'
    #                         })
    #                         print(f"❌ Row {row_num} calculation failed")
                            
    #                 except Exception as e:
    #                     error_rows += 1
    #                     self.update_progress(
    #                         status='processing',  # Keep status as processing even on exceptions
    #                         error_rows=error_rows
    #                     )
    #                     print(f"❌ Row {row_num} error: {str(e)}")
    #                     self.db.rollback()
    #                     continue
            
    #         # Final commit
    #         try:
    #             self.db.commit()
    #             print("💾 Final commit completed")
    #         except Exception as e:
    #             self.db.rollback()
    #             print(f"❌ Final commit error: {e}")
            
    #         print(f"🎉 Processing complete: {processed_rows} successful, {error_rows} errors")
            
    #         # Calculate success rate BEFORE using it
    #         success_rate = (processed_rows / (processed_rows + error_rows)) * 100 if (processed_rows + error_rows) > 0 else 0
            
    #         # CRITICAL: UPDATE PROGRESS TO COMPLETED
    #         self.update_progress(
    #             status='completed',  # FINALLY set to completed
    #             message=f'Processing completed: {processed_rows} successful, {error_rows} errors',
    #             processed_rows=processed_rows,
    #             error_rows=error_rows,
    #             progress_percent=100
    #         )
            
    #         # Return result with batch params info
    #         return {
    #             'success': True,
    #             'processed_rows': processed_rows,
    #             'error_rows': error_rows,
    #             'total_rows': processed_rows + error_rows,
    #             'results': results,
    #             'original_filename': original_filename,
    #             'success_rate': round(success_rate, 1),
    #             'batch_params_used': batch_params  # Include which params were used
    #         }
            
    #     except Exception as e:
    #         print(f"💥 File processing error: {str(e)}")
    #         self.db.rollback()
    #         self.update_progress(
    #             status='failed',  # Set to failed on exception
    #             message=f'Processing failed: {str(e)}',
    #             error_rows=error_rows + 1
    #         )
    #         return {
    #             'success': False,
    #             'error': str(e),
    #             'processed_rows': 0,
    #             'error_rows': 0
    #         }