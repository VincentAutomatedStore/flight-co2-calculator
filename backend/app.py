from flask import Flask, request, jsonify
from flask_cors import CORS
from models import db, FlightCalculation
import math
import requests
from datetime import datetime, timedelta
import threading
import time
import os
from automation.scheduler import SimpleScheduler
from services.batch_service import BatchService
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import logging
import json
from datetime import timedelta
from flask import Flask, request, jsonify, render_template, current_app
import pandas as pd
import io
from flask import send_file
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
import sqlite3
from werkzeug.utils import secure_filename

logger = logging.getLogger(__name__)

# Import new config system with error handling
try:
    from config_manager import ConfigManager
    CONFIG_MANAGER_AVAILABLE = True
    print("✅ Configuration system available")
except ImportError as e:
    print(f"❌ Configuration system not available: {e}")
    CONFIG_MANABER_AVAILABLE = False
    # Fallback to SQLite
    class SimpleConfig:
        def __init__(self):
            self.database = type('obj', (object,), {
                'connection_string': 'sqlite:///flight_calculator.db'
            })
    
    class SimpleConfigManager:
        def __init__(self):
            self.config = SimpleConfig()
        
        def load_config(self):
            return True
        
        def get_config_dict(self):
            return {"database": {"dialect": "sqlite"}}
        
        def save_config(self, config_dict):
            return True
        
        def test_connection(self):
            return True
    
    ConfigManager = SimpleConfigManager

app = Flask(__name__)

# Initialize configuration manager
config_manager = ConfigManager()
config_manager.load_config()

# Set database URI from config
app.config['SQLALCHEMY_DATABASE_URI'] = config_manager.config.database.connection_string
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Enable CORS for all routes
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"], supports_credentials=True)

# Add CORS headers to all responses
@app.after_request
def after_request(response):
    response.headers.add('Access-Control-Allow-Origin', 'http://localhost:3000')
    response.headers.add('Access-Control-Allow-Headers', 'Content-Type,Authorization')
    response.headers.add('Access-Control-Allow-Methods', 'GET,PUT,POST,DELETE,OPTIONS')
    response.headers.add('Access-Control-Allow-Credentials', 'true')
    return response
    
db.init_app(app)

# Enhanced features setup - SINGLE INITIALIZATION BLOCK
ENHANCED_FEATURES_AVAILABLE = False
enhanced_engine = None
EnhancedSessionLocal = None
EnhancedFlightCalculation = None
Airport = None
CalculationService = None
AirportService = None

try:
    from database.models import Base, Airport as EnhancedAirport, FlightCalculation as EnhancedFlightCalc
    from services.calculation_service import CalculationService as CalcService
    from services.airport_service import AirportService as AirportServ
    ENHANCED_FEATURES_AVAILABLE = True
    
    # Set the imported classes
    Airport = EnhancedAirport
    EnhancedFlightCalculation = EnhancedFlightCalc
    CalculationService = CalcService
    AirportService = AirportServ
    
    print("✅ Enhanced features are available")
    
    # Use the SAME connection string for both databases
    enhanced_connection_string = config_manager.config.database.connection_string
    enhanced_engine = create_engine(enhanced_connection_string)
    EnhancedSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=enhanced_engine)
    
    # For SQL Server, we need to handle identity columns
    if 'mssql' in config_manager.config.database.connection_string:
        from sqlalchemy import event
        from sqlalchemy import Integer
        
        @event.listens_for(Base.metadata, "column_reflect")
        def column_reflect(inspector, table, column_info):
            # Add autoincrement for SQL Server identity columns
            if column_info.get('autoincrement', False) and column_info['type'].__class__ == Integer:
                column_info['autoincrement'] = 'auto'

except ImportError as e:
    print(f"❌ Enhanced features not available: {e}")
    ENHANCED_FEATURES_AVAILABLE = False

# SINGLE DATABASE INITIALIZATION BLOCK
with app.app_context():
    # Basic database (SQLite) - using models.py
    db.create_all()
    print("✅ Basic database tables created")
    
    # Enhanced database (SQLite or SQL Server) - using database.models
    if ENHANCED_FEATURES_AVAILABLE:
        try:
            # This will create tables only if they don't exist
            Base.metadata.create_all(bind=enhanced_engine)
            print("✅ Enhanced database tables checked/created")
        except Exception as e:
            print(f"⚠️ Enhanced database table creation: {e}")
            ENHANCED_FEATURES_AVAILABLE = False
    
    # Initialize batch service and attach to app
    try:
        from services.batch_service import DirectBatchService
        app.batch_service = DirectBatchService(db.session)
        print("✅ Batch service initialized")
    except Exception as e:
        print(f"❌ Failed to initialize batch service: {e}")
        # Create a fallback batch service
        class FallbackBatchService:
            def __init__(self):
                self.current_progress = {
                    'status': 'idle',
                    'message': 'Batch service not available',
                    'current_row': 0,
                    'total_rows': 0,
                    'processed_rows': 0,
                    'error_rows': 0,
                    'progress_percent': 0
                }
        app.batch_service = FallbackBatchService()

# Enhanced database session dependency
def get_enhanced_db():
    """Dependency for enhanced database session"""
    if not ENHANCED_FEATURES_AVAILABLE:
        return None
    enhanced_db = EnhancedSessionLocal()
    try:
        yield enhanced_db
    finally:
        enhanced_db.close()

# =============================================================================
# AIRPORTS DATA - From shared file
# =============================================================================

try:
    from shared_airports import airports as AIRPORTS_DATA
    print(f"✅ Successfully loaded {len(AIRPORTS_DATA)} airports from shared file")
except ImportError as e:
    print(f"❌ Could not import airports from shared_airports.py: {e}")
    print("⚠️  Creating empty airports list - airport relationships may not work")
    AIRPORTS_DATA = []

# =============================================================================
# UPDATED ICAO CALCULATION FUNCTIONS WITH BETTER ERROR HANDLING
# =============================================================================

def update_sqlite_schema():
    """Add missing columns to SQLite database"""
    try:
        with app.app_context():
            # Check if we're using SQLite
            if 'sqlite' in app.config['SQLALCHEMY_DATABASE_URI']:
                print("🔧 Updating SQLite schema...")
                
                # Add missing columns if they don't exist
                with db.engine.connect() as conn:
                    # Check if calculation_method column exists
                    result = conn.execute(text("PRAGMA table_info(flight_calculations)"))
                    columns = [row[1] for row in result]
                    
                    missing_columns = []
                    if 'calculation_method' not in columns:
                        missing_columns.append("ADD COLUMN calculation_method VARCHAR(50)")
                    if 'departure_airport_id' not in columns:
                        missing_columns.append("ADD COLUMN departure_airport_id INTEGER")
                    if 'destination_airport_id' not in columns:
                        missing_columns.append("ADD COLUMN destination_airport_id INTEGER")
                    if 'created_by' not in columns:
                        missing_columns.append("ADD COLUMN created_by VARCHAR(100)")
                    
                    if missing_columns:
                        for column_sql in missing_columns:
                            try:
                                conn.execute(text(f"ALTER TABLE flight_calculations {column_sql}"))
                                print(f"✅ Added column: {column_sql}")
                            except Exception as e:
                                print(f"⚠️ Could not add column: {e}")
                    
                    print("✅ SQLite schema updated")
                    
    except Exception as e:
        print(f"❌ Error updating SQLite schema: {e}")

# Call schema update after db creation
with app.app_context():
    update_sqlite_schema()
    
# =============================================================================
# AUTOMATION SCHEDULER SETUP
# =============================================================================

# Initialize automation scheduler
automation_scheduler = None

if ENHANCED_FEATURES_AVAILABLE:
    def init_automation():
        global automation_scheduler
        try:
            # Get a database session
            with next(get_enhanced_db()) as db:
                automation_scheduler = SimpleScheduler(db)
                # Start with daily schedule at 2 AM as default
                automation_scheduler.start_daily(hour=2, minute=0)
                automation_scheduler.start_scheduler()
                print("✅ Automation scheduler started successfully")
        except Exception as e:
            print(f"❌ Failed to start automation scheduler: {e}")
    
    # Start automation in a background thread (with delay to let app fully initialize)
    def delayed_automation_start():
        time.sleep(5)  # Wait 5 seconds for app to be fully ready
        init_automation()
    
    automation_thread = threading.Thread(target=delayed_automation_start)
    automation_thread.daemon = True
    automation_thread.start()
else:
    print("⚠️  Enhanced features not available - automation disabled")

# =============================================================================
# CORE CALCULATION ENDPOINTS (KEEP THESE - THEY'RE ESSENTIAL)
# =============================================================================

@app.route('/api/calculate', methods=['POST', 'OPTIONS'])
def calculate_emissions_route():
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        
        departure = data.get('departure', '').strip()
        destination = data.get('destination', '').strip()
        passengers = int(data.get('passengers', 1))
        round_trip = bool(data.get('round_trip', False))
        cabin_class = data.get('cabin_class', 'economy')
        
        if not departure or not destination:
            return jsonify({'error': 'Departure and destination are required'}), 400
        
        if passengers < 1:
            return jsonify({'error': 'Number of passengers must be at least 1'}), 400
        
        # Get emissions data
        results = get_icao_emissions(departure, destination, passengers, round_trip, cabin_class)
        
        # Create flight info string
        flight_info = f"{departure} to {destination} - {results['distance_km']}km"
        if round_trip:
            flight_info += " (Round Trip)"
        flight_info += f" • {cabin_class.replace('_', ' ').title()}"
        
        # Save to database - ONLY SET COLUMNS THAT EXIST
        calculation = FlightCalculation(
            departure=departure,
            destination=destination,
            passengers=passengers,
            round_trip=round_trip,
            cabin_class=cabin_class,
            fuel_burn_kg=results['fuel_burn_kg'],
            total_co2_kg=results['total_co2_kg'],
            co2_per_passenger_kg=results['co2_per_passenger_kg'],
            co2_tonnes=results['co2_tonnes'],
            distance_km=results['distance_km'],
            distance_miles=results['distance_miles'],
            flight_info=flight_info
        )
        
        db.session.add(calculation)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'results': {
                **results,
                'flight_info': flight_info,
                'id': calculation.id
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@app.route('/api/results', methods=['GET'])
def get_results():
    try:
        calculations = FlightCalculation.query.order_by(FlightCalculation.created_at.desc()).all()
        
        results = []
        for calc in calculations:
            results.append({
                'id': calc.id,
                'departure': calc.departure,
                'destination': calc.destination,
                'passengers': calc.passengers,
                'round_trip': calc.round_trip,
                'cabin_class': calc.cabin_class,
                'fuel_burn_kg': calc.fuel_burn_kg,
                'total_co2_kg': calc.total_co2_kg,
                'co2_per_passenger_kg': calc.co2_per_passenger_kg,
                'co2_tonnes': calc.co2_tonnes,
                'distance_km': calc.distance_km,
                'distance_miles': calc.distance_miles,
                'flight_info': calc.flight_info,
                'created_at': calc.created_at.isoformat()
            })
        
        return jsonify(results)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/delete/<int:calculation_id>', methods=['DELETE', 'OPTIONS'])
def delete_calculation(calculation_id):
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        calculation = FlightCalculation.query.get_or_404(calculation_id)
        db.session.delete(calculation)
        db.session.commit()
        
        return jsonify({'success': True})
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =============================================================================
# ESSENTIAL AUTOMATION ENDPOINTS (KEEP THESE)
# =============================================================================

@app.route('/api/v2/automation/status', methods=['GET'])
def automation_status():
    """Get automation scheduler status"""
    global automation_scheduler
    
    status = {
        'scheduler_running': automation_scheduler and getattr(automation_scheduler, 'is_running', False),
        'enhanced_features': ENHANCED_FEATURES_AVAILABLE,
        'last_run': getattr(automation_scheduler, 'last_run_time', 'Never') if automation_scheduler else 'No scheduler',
        'files_processed': 0
    }
    
    # Count files in directories
    for dir_type in ['scheduled', 'processed', 'errors']:
        dir_path = f'data/{dir_type}'
        if os.path.exists(dir_path):
            csv_files = [f for f in os.listdir(dir_path) if f.endswith('.csv')]
            status[f'{dir_type}_files'] = len(csv_files)
        else:
            status[f'{dir_type}_files'] = 0
    
    return jsonify(status)

@app.route('/api/force-refresh', methods=['POST'])
def force_refresh():
    """Force frontend to refresh data"""
    try:
        # Return latest calculation count or timestamp
        count = FlightCalculation.query.count()
        latest = FlightCalculation.query.order_by(FlightCalculation.created_at.desc()).first()
        
        return jsonify({
            'status': 'refresh_triggered',
            'total_calculations': count,
            'latest_timestamp': latest.created_at.isoformat() if latest else None,
            'message': 'Data updated - refresh your frontend'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/check-updates')
def check_updates():
    """Check if there are new calculations"""
    count = FlightCalculation.query.count()
    latest = FlightCalculation.query.order_by(FlightCalculation.created_at.desc()).first()
    
    return jsonify({
        'total_calculations': count,
        'latest_timestamp': latest.created_at.isoformat() if latest else None,
        'needs_refresh': True  # Always return true for now
    })

@app.route('/api/v2/automation/cancel', methods=['POST'])
def cancel_processing():
    """Cancel current batch processing"""
    try:
        # Add your cancellation logic here
        # This might involve setting a flag that your batch service checks
        return jsonify({'success': True, 'message': 'Processing cancelled'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500
    
# =============================================================================
# AUTOMATION CONTROL ENDPOINTS
# =============================================================================

@app.route('/api/v2/automation/trigger', methods=['POST', 'OPTIONS'])
def trigger_automation():
    """Manually trigger automation processing with batch parameters"""
    if request.method == 'OPTIONS':
        return '', 200
        
    global automation_scheduler
    
    if not automation_scheduler:
        return jsonify({'error': 'Automation scheduler not available'}), 400
    
    try:
        # Get batch parameters from request
        data = request.get_json() or {}
        batch_params = data.get('batch_params', {
            'passengers': 1,
            'cabinClass': 'economy', 
            'roundTrip': False
        })
        
        print(f"🎯 Triggering automation with batch params: {batch_params}")
        
        # Store batch parameters in scheduler for processing
        automation_scheduler.current_batch_params = batch_params
        
        result = automation_scheduler.trigger_manual_run()
        return jsonify({
            'success': True, 
            'message': 'Manual processing triggered',
            'batch_params': batch_params,
            'result': result
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v2/automation/process-now', methods=['POST', 'OPTIONS'])
def process_now():
    """Alternative endpoint to trigger processing"""
    if request.method == 'OPTIONS':
        return '', 200
        
    return trigger_automation()

@app.route('/api/v2/automation/force-process', methods=['POST', 'OPTIONS'])
def force_process_automation():
    """Force process any pending automation files"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        if not ENHANCED_FEATURES_AVAILABLE:
            return jsonify({'error': 'Enhanced features not available'}), 400
        
        global automation_scheduler
        
        if not automation_scheduler:
            return jsonify({'error': 'Automation scheduler not available'}), 400
        
        # Manually trigger processing
        result = automation_scheduler.trigger_manual_run()
        
        return jsonify({
            'success': True,
            'message': 'Manual processing triggered',
            'result': result
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v2/automation/progress')
def get_batch_progress():
    """Get current batch processing progress - SIMPLIFIED VERSION"""
    # For now, return idle status
    # You can enhance this later to track actual progress
    return jsonify({
        'status': 'idle',
        'message': 'No active processing'
    })

@app.route('/api/v2/automation/progress', methods=['GET'])
def get_automation_progress():
    """Get current batch processing progress"""
    try:
        # Get the batch service from current_app
        if hasattr(current_app, 'batch_service') and current_app.batch_service:
            progress = current_app.batch_service.current_progress
            print(f"📊 Progress API returning: {progress['status']} - {progress.get('message', '')}")
            return jsonify(progress)
        else:
            # Fallback if no batch service available
            return jsonify({
                'status': 'idle',
                'message': 'Batch service not initialized',
                'current_row': 0,
                'total_rows': 0,
                'processed_rows': 0,
                'error_rows': 0,
                'progress_percent': 0
            })
    except Exception as e:
        print(f"❌ Error getting progress: {e}")
        return jsonify({
            'status': 'error',
            'message': f'Error getting progress: {str(e)}',
            'current_row': 0,
            'total_rows': 0,
            'processed_rows': 0,
            'error_rows': 0,
            'progress_percent': 0
        }), 500

# =============================================================================
# AUTOMATION DEBUG ENDPOINTS
# =============================================================================

@app.route('/api/v2/automation/debug-processing', methods=['GET'])
def debug_automation_processing():
    """Debug endpoint to check automation processing status"""
    try:
        if not ENHANCED_FEATURES_AVAILABLE:
            return jsonify({'error': 'Enhanced features not available'}), 400
        
        debug_info = {
            'scheduler_status': {},
            'file_processing': {},
            'database_counts': {},
            'issues': []
        }
        
        # Check scheduler status
        global automation_scheduler
        if automation_scheduler:
            debug_info['scheduler_status'] = {
                'running': getattr(automation_scheduler, 'is_running', False),
                'last_run': getattr(automation_scheduler, 'last_run_time', 'Unknown'),
                'next_run': getattr(automation_scheduler, 'next_run_time', 'Unknown')
            }
        else:
            debug_info['scheduler_status'] = {'running': False, 'error': 'Scheduler not initialized'}
            debug_info['issues'].append('Automation scheduler not initialized')
        
        # Check file directories
        directories = ['data/scheduled', 'data/processed', 'data/errors']
        for dir_path in directories:
            if os.path.exists(dir_path):
                files = [f for f in os.listdir(dir_path) if f.endswith('.csv')]
                debug_info['file_processing'][dir_path] = {
                    'exists': True,
                    'file_count': len(files),
                    'files': files[:10]  # First 10 files
                }
            else:
                debug_info['file_processing'][dir_path] = {'exists': False, 'file_count': 0}
                debug_info['issues'].append(f'Directory {dir_path} does not exist')
        
        # Check database counts
        with next(get_enhanced_db()) as db:
            # Total calculations count
            total_calcs = db.query(EnhancedFlightCalculation).count()
            debug_info['database_counts']['total_calculations'] = total_calcs
            
            # Recent calculations (last hour)
            one_hour_ago = datetime.utcnow() - timedelta(hours=1)
            recent_calcs = db.query(EnhancedFlightCalculation).filter(
                EnhancedFlightCalculation.created_at >= one_hour_ago
            ).count()
            debug_info['database_counts']['recent_calculations'] = recent_calcs
            
        return jsonify(debug_info)
        
    except Exception as e:
        import traceback
        return jsonify({
            'error': str(e),
            'traceback': traceback.format_exc()
        }), 500

def get_scheduled_directory():
    """Get the scheduled directory path that works locally and on Railway"""
    base_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(base_dir, 'data')
    scheduled_dir = os.path.join(data_dir, 'scheduled')
    
    # Create directory if it doesn't exist
    os.makedirs(scheduled_dir, exist_ok=True)
    
    return scheduled_dir

@app.route('/api/v2/automation/upload-csv', methods=['POST'])
def upload_csv_for_processing():
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if file and file.filename.endswith('.csv'):
            # Use the dynamic path function instead of hardcoded path
            scheduled_dir = get_scheduled_directory()
            os.makedirs(scheduled_dir, exist_ok=True)
            
            # Create a safe filename
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            original_name = secure_filename(file.filename)
            filename = f"{timestamp}_{original_name}"
            file_path = os.path.join(scheduled_dir, filename)
            
            # Save the file
            file.save(file_path)
            
            # Validate CSV structure
            try:
                import pandas as pd
                df = pd.read_csv(file_path)
                required_columns = ['departure_iata', 'destination_iata']
                
                if not all(col in df.columns for col in required_columns):
                    # Clean up invalid file
                    os.remove(file_path)
                    return jsonify({
                        'error': f'CSV must contain columns: {required_columns}. Found: {list(df.columns)}'
                    }), 400
                
                row_count = len(df)
                
                return jsonify({
                    'success': True,
                    'message': f'File {original_name} uploaded successfully with {row_count} routes',
                    'file_path': file_path,
                    'filename': filename,
                    'row_count': row_count,
                    'next_processing': 'Will be processed within 1 minute by automation'
                })
                
            except Exception as csv_error:
                # Clean up invalid file
                if os.path.exists(file_path):
                    os.remove(file_path)
                return jsonify({'error': f'Invalid CSV file: {str(csv_error)}'}), 400
            
        else:
            return jsonify({'error': 'Only CSV files allowed'}), 400
            
    except Exception as e:
        logger.error(f"❌ CSV upload error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v2/automation/uploaded-files', methods=['GET'])
def get_uploaded_files():
    """Get list of uploaded CSV files"""
    try:
        scheduled_dir = 'data/scheduled'
        if not os.path.exists(scheduled_dir):
            return jsonify({'files': [], 'total': 0})
        
        csv_files = []
        for filename in os.listdir(scheduled_dir):
            if filename.endswith('.csv'):
                file_path = os.path.join(scheduled_dir, filename)
                file_stats = os.stat(file_path)
                csv_files.append({
                    'filename': filename,
                    'upload_time': datetime.fromtimestamp(file_stats.st_mtime).isoformat(),
                    'size_kb': round(file_stats.st_size / 1024, 2)
                })
        
        # Sort by upload time (newest first)
        csv_files.sort(key=lambda x: x['upload_time'], reverse=True)
        
        return jsonify({
            'files': csv_files,
            'total': len(csv_files)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v2/automation/clear-processed', methods=['POST', 'OPTIONS'])
def clear_processed_files():
    """Clear processed files to test fresh processing"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        processed_dir = 'data/processed'
        if os.path.exists(processed_dir):
            # Move files to a backup directory instead of deleting
            from datetime import datetime
            backup_dir = 'data/backup_' + datetime.now().strftime('%Y%m%d_%H%M%S')
            os.makedirs(backup_dir, exist_ok=True)
            
            moved_files = []
            for file in os.listdir(processed_dir):
                if file.endswith('.csv'):
                    src = os.path.join(processed_dir, file)
                    dst = os.path.join(backup_dir, file)
                    os.rename(src, dst)
                    moved_files.append(file)
            
            return jsonify({
                'success': True,
                'message': f'Moved {len(moved_files)} files to backup',
                'backup_dir': backup_dir,
                'moved_files': moved_files
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Processed directory does not exist'
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# =============================================================================
# BATCH PROCESSING ENDPOINTS
# =============================================================================

@app.route('/api/v2/automation/process-csv', methods=['POST', 'OPTIONS'])
def process_csv_manual():
    """Manually process a specific CSV file"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        file_path = data.get('file_path', '').strip()
        
        if not file_path:
            return jsonify({'error': 'File path is required'}), 400
        
        # Use the get_enhanced_db function
        with next(get_enhanced_db()) as db:
            batch_service = BatchService(db)
            result = batch_service.process_flight_csv(file_path)
            
            return jsonify({
                'success': True,
                'result': result
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v2/automation/process-with-direct', methods=['POST', 'GET'])
def process_with_direct():
    """Process all scheduled files using DirectFixedBatchService"""
    try:
        if not ENHANCED_FEATURES_AVAILABLE:
            return jsonify({'error': 'Enhanced features not available'}), 400
        
        from services.batch_service import DirectFixedBatchService
        
        scheduled_dir = 'data/scheduled'
        processed_dir = 'data/processed'
        
        # Ensure directories exist
        for directory in [scheduled_dir, processed_dir]:
            os.makedirs(directory, exist_ok=True)
        
        # Get all CSV files
        csv_files = [f for f in os.listdir(scheduled_dir) if f.endswith('.csv')]
        
        if not csv_files:
            return jsonify({
                'success': True,
                'message': 'No files to process',
                'files_processed': 0
            })
        
        processing_results = []
        
        with next(get_enhanced_db()) as db:
            direct_service = DirectFixedBatchService(db)
            
            for filename in csv_files:
                file_path = os.path.join(scheduled_dir, filename)
                print(f"🔄 Processing {filename} with DirectFixedBatchService")
                
                result = direct_service.process_flight_csv(file_path)
                
                # Move to processed if successful
                if result.get('success'):
                    processed_path = os.path.join(processed_dir, filename)
                    import shutil
                    shutil.move(file_path, processed_path)
                    result['file_moved'] = True
                else:
                    result['file_moved'] = False
                
                processing_results.append({
                    'file': filename,
                    'result': result
                })
        
        return jsonify({
            'success': True,
            'message': f'Processed {len(csv_files)} files with DirectFixedBatchService',
            'files_processed': len(csv_files),
            'processing_results': processing_results
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

def clean_csv_header(header):
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

def validate_airport_code(code):
    """Validate airport IATA code"""
    if not code or not isinstance(code, str):
        return False
    code = code.strip().upper()
    # Valid IATA codes are 3 letters
    if len(code) != 3 or not code.isalpha():
        return False
    return True

def get_airport_by_iata_enhanced(iata_code):
    """Enhanced airport lookup with better validation"""
    if not validate_airport_code(iata_code):
        return None
    
    iata_code = iata_code.upper().strip()
    
    # First try enhanced database
    if ENHANCED_FEATURES_AVAILABLE:
        try:
            with next(get_enhanced_db()) as db:
                airport = db.query(Airport).filter(Airport.iata_code == iata_code).first()
                if airport:
                    return airport
        except Exception as e:
            print(f"❌ Database error getting airport {iata_code}: {e}")
    
    # Fallback to AIRPORTS_DATA
    for airport in AIRPORTS_DATA:
        if airport.get('code') == iata_code:
            # Create a simple airport object
            class SimpleAirport:
                def __init__(self, data):
                    self.iata_code = data.get('code')
                    self.name = data.get('name', 'Unknown Airport')
                    self.city = data.get('city', 'Unknown')
                    self.country = data.get('country', 'Unknown')
                    self.latitude = data.get('latitude')
                    self.longitude = data.get('longitude')
            
            return SimpleAirport(airport)
    
    print(f"❌ Airport not found in database: {iata_code}")
    return None

# =============================================================================
# HELPER FUNCTIONS
# =============================================================================

def get_airport_by_iata(iata_code):
    """Get airport by IATA code from database or airports data"""
    if not iata_code or iata_code == 'Unknown':
        return None
    
    iata_code = iata_code.upper().strip()
    
    # First try enhanced database
    if ENHANCED_FEATURES_AVAILABLE:
        try:
            with next(get_enhanced_db()) as db:
                airport = db.query(Airport).filter(Airport.iata_code == iata_code).first()
                if airport:
                    return airport
        except Exception as e:
            print(f"❌ Database error getting airport {iata_code}: {e}")
    
    # Fallback to AIRPORTS_DATA
    for airport in AIRPORTS_DATA:
        if airport.get('code') == iata_code:
            # Create a simple airport object
            class SimpleAirport:
                def __init__(self, data):
                    self.iata_code = data.get('code')
                    self.name = data.get('name', 'Unknown Airport')
                    self.city = data.get('city', 'Unknown')
                    self.country = data.get('country', 'Unknown')
                    self.latitude = data.get('latitude')
                    self.longitude = data.get('longitude')
            
            return SimpleAirport(airport)
    
    print(f"❌ Airport not found: {iata_code}")
    return None

def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate great circle distance between two points using Haversine formula"""
    try:
        # Convert coordinates to floats
        lat1 = float(lat1) if lat1 else 0
        lon1 = float(lon1) if lon1 else 0
        lat2 = float(lat2) if lat2 else 0
        lon2 = float(lon2) if lon2 else 0
        
        # If any coordinates are missing, return 0
        if lat1 == 0 and lon1 == 0 or lat2 == 0 and lon2 == 0:
            return 0
        
        # Haversine formula
        R = 6371  # Earth's radius in kilometers
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon/2) * math.sin(delta_lon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        distance_km = R * c
        return distance_km
        
    except Exception as e:
        print(f"❌ Distance calculation error: {e}")
        return 0

def get_airport_by_code(code):
    """Alias for get_airport_by_iata for compatibility"""
    return get_airport_by_iata(code)

def extract_airport_code(text):
    """Extract 3-letter airport code from text"""
    if not text:
        return "Unknown"
    
    # Clean the text
    text = str(text).strip().upper()
    
    # If it's already a 3-letter code, return it
    if len(text) == 3 and text.isalpha():
        return text
    
    # Look for 3-letter codes in the text
    import re
    matches = re.findall(r'\b[A-Z]{3}\b', text)
    if matches:
        return matches[0]
    
    return "Unknown"

def get_icao_emissions_with_session(departure, destination, passengers, round_trip, cabin_class):
    """Alternative approach using session to maintain cookies"""
    
    ICAO_API_URL = "https://icec.icao.int/Home/PassengerCompute"
    
    try:
        # Create a session to handle cookies
        session = requests.Session()
        
        # First, visit the calculator page to get session cookies
        print("🔄 Getting session cookies from ICAO...")
        session.get("https://icec.icao.int/calculator", timeout=10)
        
        # Prepare request data
        icao_data = {
            "AirportCodeDeparture": departure.upper(),
            "AirportCodeDestination": [destination.upper()],
            "CabinClass": "",
            "Departure": f"{departure.upper()} Airport", 
            "Destination": [f"{destination.upper()} Airport"],
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
        
        print(f"🔍 Calling ICAO API for {departure} -> {destination}")
        response = session.post(ICAO_API_URL, json=icao_data, headers=headers, timeout=30)
        
        print(f"📡 ICAO API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            icao_result = response.json()
            print("✅ ICAO API call successful with session")
            return parse_icao_response(icao_result, departure, destination, passengers, round_trip, cabin_class)
        else:
            print(f"❌ ICAO API returned status {response.status_code}")
            return get_fallback_icao_data(departure, destination, passengers, round_trip, cabin_class)
            
    except Exception as e:
        print(f"❌ ICAO API session error: {e}")
        return get_fallback_icao_data(departure, destination, passengers, round_trip, cabin_class)

# =============================================================================
# AUTOMATION ENDPOINTS FOR FRONTEND
# =============================================================================

@app.route('/api/v2/automation/results', methods=['GET'])
def get_automation_results():
    """Get automation results - works with both SQLite and SQL Server - FIXED VERBOSE LOGGING"""
    try:
        if not ENHANCED_FEATURES_AVAILABLE:
            return jsonify({"error": "Enhanced features not available", "results": []}), 400
            
        with next(get_enhanced_db()) as db:
            # Use the same FlightCalculation model for both databases
            calculations = db.query(EnhancedFlightCalculation)\
                .order_by(EnhancedFlightCalculation.created_at.desc())\
                .all()
            
            # Only log on first call or when count changes significantly
            static_count = getattr(get_automation_results, '_last_count', 0)
            if len(calculations) != static_count:
                print(f"🔍 Found {len(calculations)} calculations in automation database")
                get_automation_results._last_count = len(calculations)
            
            results = []
            for calc in calculations:
                try:
                    # Use the model's to_dict method (works for both schemas)
                    result = calc.to_dict()
                    results.append(result)
                    # REMOVED: The verbose "✅ Processed: X -> Y" logging for each calculation
                    
                except Exception as e:
                    print(f"❌ Error processing calculation {calc.id}: {e}")
                    continue
            
            # Only log success message occasionally
            import random
            if random.random() < 0.1:  # 10% chance to log
                print(f"🎯 Successfully processed {len(results)} calculations for API response")
                
            return jsonify(results)
            
    except Exception as e:
        print(f"💥 Error in automation results: {e}")
        return jsonify({"error": str(e), "results": []}), 500
    
@app.route('/api/v2/automation/airports-list', methods=['GET'])
def get_automation_airports_list():
    """Get airports list - works with both SQLite and SQL Server"""
    try:
        if not ENHANCED_FEATURES_AVAILABLE:
            return jsonify({'error': 'Enhanced features not available'}), 400
            
        with next(get_enhanced_db()) as db:
            try:
                # Try to use the Airport model
                airports = db.query(Airport).order_by(Airport.iata_code).all()
                airports_list = [airport.to_dict() for airport in airports]
                
            except Exception as model_error:
                print(f"⚠️ Model query failed, trying raw SQL: {model_error}")
                # Fallback to raw SQL
                try:
                    # Detect database type and use appropriate query
                    if 'sqlite' in str(db.bind.url).lower():
                        result = db.execute(text("""
                            SELECT iata_code, name, city, country, latitude, longitude
                            FROM airports 
                            ORDER BY iata_code
                        """))
                    else:
                        # SQL Server
                        result = db.execute(text("""
                            SELECT iata_code, name, city, country, latitude, longitude, search_field
                            FROM airports 
                            ORDER BY iata_code
                        """))
                    
                    airports_list = []
                    for row in result:
                        if len(row) >= 6:  # SQLite has 6 columns
                            airport_data = {
                                'iata_code': row[0],
                                'name': row[1] or f"{row[0]} Airport",
                                'city': row[2] or 'Unknown',
                                'country': row[3] or 'Unknown',
                                'latitude': row[4],
                                'longitude': row[5],
                                'search': f"{row[2] or 'Unknown'}, {row[3] or 'Unknown'} ({row[0]})"
                            }
                        else:  # SQL Server has more columns
                            airport_data = {
                                'iata_code': row[0],
                                'name': row[1] or f"{row[0]} Airport",
                                'city': row[2] or 'Unknown',
                                'country': row[3] or 'Unknown',
                                'latitude': row[4],
                                'longitude': row[5],
                                'search': row[6] or f"{row[2] or 'Unknown'}, {row[3] or 'Unknown'} ({row[0]})"
                            }
                        airports_list.append(airport_data)
                        
                except Exception as sql_error:
                    return jsonify({'error': f'Both model and SQL queries failed: {sql_error}'}), 500
            
            return jsonify({
                'success': True,
                'total_airports': len(airports_list),
                'airports': airports_list
            })
                
    except Exception as e:
        print(f"❌ Error in automation airports list: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v2/automation/export', methods=['POST', 'OPTIONS'])
def export_automation_results():
    """Export automation results in various formats"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        export_format = data.get('format', 'csv')
        results_data = data.get('data', [])
        filters = data.get('filters', {})
        batch_params = data.get('batchParams', {})
        
        if not results_data:
            return jsonify({'error': 'No data to export'}), 400
        
        # Convert to DataFrame for easier manipulation
        df = pd.DataFrame(results_data)
        
        # Add metadata columns
        df['export_timestamp'] = datetime.now().isoformat()
        df['batch_parameters'] = json.dumps(batch_params)
        
        if export_format == 'csv':
            return export_csv(df, filters, batch_params)
        elif export_format == 'excel':
            return export_excel(df, filters, batch_params)
        elif export_format == 'pdf':
            return export_pdf(df, filters, batch_params)
        elif export_format == 'sql':
            return export_sql_server(df, filters, batch_params)
        else:
            return jsonify({'error': 'Unsupported export format'}), 400
            
    except Exception as e:
        logger.error(f"❌ Export error: {str(e)}")
        return jsonify({'error': str(e)}), 500

def export_csv(df, filters, batch_params):
    """Export results as CSV"""
    try:
        # Create output
        output = io.StringIO()
        
        # Add metadata header
        output.write("# Flight CO2 Calculator - Export Data\n")
        output.write(f"# Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        output.write(f"# Batch Parameters: {json.dumps(batch_params, indent=2)}\n")
        output.write(f"# Filters Applied: {json.dumps(filters, indent=2)}\n")
        output.write("# \n")
        
        # Write data
        df.to_csv(output, index=False)
        
        # Prepare response
        output.seek(0)
        return send_file(
            io.BytesIO(output.getvalue().encode('utf-8')),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'flight_emissions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
        )
    except Exception as e:
        logger.error(f"❌ CSV export error: {str(e)}")
        raise

def export_excel(df, filters, batch_params):
    """Export results as Excel file"""
    try:
        output = io.BytesIO()
        
        # Create Excel writer
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Main data sheet
            df.to_excel(writer, sheet_name='Emissions Data', index=False)
            
            # Metadata sheet
            metadata = pd.DataFrame({
                'Field': ['Export Date', 'Total Records', 'Batch Parameters', 'Applied Filters'],
                'Value': [
                    datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                    len(df),
                    json.dumps(batch_params, indent=2),
                    json.dumps(filters, indent=2)
                ]
            })
            metadata.to_excel(writer, sheet_name='Metadata', index=False)
            
            # Summary statistics sheet
            summary_data = {
                'Metric': [
                    'Total Calculations',
                    'Average CO2 per Passenger (kg)',
                    'Total CO2 Emitted (kg)',
                    'Average Distance (km)',
                    'Most Common Cabin Class'
                ],
                'Value': [
                    len(df),
                    df['co2_per_passenger_kg'].mean(),
                    df['total_co2_kg'].sum(),
                    df['distance_km'].mean(),
                    df['cabin_class'].mode().iloc[0] if not df['cabin_class'].empty else 'N/A'
                ]
            }
            summary_df = pd.DataFrame(summary_data)
            summary_df.to_excel(writer, sheet_name='Summary', index=False)
        
        output.seek(0)
        return send_file(
            output,
            mimetype='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            as_attachment=True,
            download_name=f'flight_emissions_{datetime.now().strftime("%Y%m%d_%H%M%S")}.xlsx'
        )
    except Exception as e:
        logger.error(f"❌ Excel export error: {str(e)}")
        # Fallback to CSV if Excel fails
        return export_csv(df, filters, batch_params)

def export_single_page_pdf(df, filters, batch_params):
    """Export results as PDF report with full data table"""
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title = Paragraph("Flight CO2 Emissions Report", styles['Title'])
        elements.append(title)
        
        # Metadata
        metadata_text = f"""
        <b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>
        <b>Total Records:</b> {len(df)}<br/>
        <b>Batch Parameters:</b> {json.dumps(batch_params)}<br/>
        <b>Filters Applied:</b> {json.dumps(filters)}
        """
        metadata = Paragraph(metadata_text, styles['Normal'])
        elements.append(metadata)
        
        elements.append(Paragraph("<br/><b>Summary Statistics:</b>", styles['Heading2']))
        
        # Summary table
        summary_data = [
            ['Metric', 'Value'],
            ['Total Calculations', str(len(df))],
            ['Average CO2 per Passenger (kg)', f"{df['co2_per_passenger_kg'].mean():.2f}"],
            ['Total CO2 Emitted (kg)', f"{df['total_co2_kg'].sum():.0f}"],
            ['Average Distance (km)', f"{df['distance_km'].mean():.0f}"],
            ['Most Common Cabin Class', df['cabin_class'].mode().iloc[0] if not df['cabin_class'].empty else 'N/A']
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(summary_table)
        
        # NEW: Full Data Table
        elements.append(Paragraph("<br/><b>Detailed Flight Data:</b>", styles['Heading2']))
        
        # Prepare data for the table - limit columns for readability
        table_data = [['Route', 'Passengers', 'Cabin', 'Distance (km)', 'CO2 (kg)', 'Date']]
        
        for _, row in df.iterrows():
            # Format the data for PDF display
            route = f"{row.get('departure', '')} → {row.get('destination', '')}"
            passengers = str(row.get('passengers', ''))
            cabin_class = str(row.get('cabin_class', '')).replace('_', ' ').title()
            distance = f"{row.get('distance_km', 0):.0f}"
            co2 = f"{row.get('co2_per_passenger_kg', 0):.0f}"
            
            # Format date
            created_at = row.get('created_at', '')
            if created_at:
                try:
                    # Handle different date formats
                    if 'T' in str(created_at):
                        date_obj = datetime.fromisoformat(str(created_at).replace('Z', '+00:00'))
                    else:
                        date_obj = datetime.strptime(str(created_at), '%Y-%m-%d %H:%M:%S')
                    date_str = date_obj.strftime('%Y-%m-%d')
                except:
                    date_str = str(created_at)[:10]
            else:
                date_str = 'N/A'
                
            table_data.append([route, passengers, cabin_class, distance, co2, date_str])
        
        # Create the main data table
        data_table = Table(table_data)
        
        # Style the data table
        data_table.setStyle(TableStyle([
            # Header style
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            
            # Data rows style
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 8),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            
            # Column specific styles
            ('ALIGN', (3, 1), (4, -1), 'RIGHT'),  # Distance and CO2 right-aligned
            ('ALIGN', (1, 1), (1, -1), 'CENTER'),  # Passengers centered
        ]))
        
        elements.append(data_table)
        
        # NEW: Additional detailed information for larger datasets
        if len(df) > 10:
            elements.append(Paragraph("<br/><b>Additional Statistics:</b>", styles['Heading3']))
            
            # Cabin class distribution
            cabin_stats = df['cabin_class'].value_counts()
            cabin_text = "<b>Cabin Class Distribution:</b><br/>"
            for cabin, count in cabin_stats.items():
                cabin_text += f"• {cabin.replace('_', ' ').title()}: {count} flights ({count/len(df)*100:.1f}%)<br/>"
            
            cabin_para = Paragraph(cabin_text, styles['Normal'])
            elements.append(cabin_para)
            
            # Round trip statistics
            if 'round_trip' in df.columns:
                round_trip_stats = df['round_trip'].value_counts()
                trip_text = "<b>Trip Type:</b><br/>"
                for is_round, count in round_trip_stats.items():
                    trip_type = "Round Trip" if is_round else "One Way"
                    trip_text += f"• {trip_type}: {count} flights ({count/len(df)*100:.1f}%)<br/>"
                
                trip_para = Paragraph(trip_text, styles['Normal'])
                elements.append(trip_para)
        
        # NEW: Environmental Impact Context
        elements.append(Paragraph("<br/><b>Environmental Impact Context:</b>", styles['Heading3']))
        
        total_co2_tonnes = df['total_co2_kg'].sum() / 1000
        trees_needed = total_co2_tonnes * 50  # Rough estimate: 1 tree absorbs ~20kg CO2 per year
        
        impact_text = f"""
        <b>Total CO2 Emissions:</b> {total_co2_tonnes:.1f} tonnes<br/>
        <b>Tree Equivalent:</b> Approximately {trees_needed:.0f} trees needed to absorb this CO2 annually<br/>
        <b>Car Equivalent:</b> Like driving a car for {(total_co2_tonnes / 4.6 * 12):.1f} months<br/>
        <i>Note: Based on average car emissions of 4.6 tonnes CO2 per year</i>
        """
        
        impact_para = Paragraph(impact_text, styles['Normal'])
        elements.append(impact_para)
        
        # Footer with page numbers
        def add_page_number(canvas, doc):
            canvas.saveState()
            canvas.setFont('Helvetica', 8)
            canvas.drawRightString(doc.pagesize[0] - 50, 30, f"Page {doc.page}")
            canvas.drawString(50, 30, f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
            canvas.restoreState()
        
        # Build PDF
        doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'flight_emissions_complete_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        )
    except Exception as e:
        logger.error(f"❌ PDF export error: {e}")
        # Fallback to CSV if PDF fails
        return export_csv(df, filters, batch_params)

def export_pdf(df, filters, batch_params):
    """Export results as PDF report with full data table and pagination"""
    try:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        elements = []
        styles = getSampleStyleSheet()
        
        # Title
        title = Paragraph("Flight CO2 Emissions Report", styles['Title'])
        elements.append(title)
        
        # Metadata
        metadata_text = f"""
        <b>Generated:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br/>
        <b>Total Records:</b> {len(df)}<br/>
        <b>Batch Parameters:</b> {json.dumps(batch_params)}<br/>
        <b>Filters Applied:</b> {json.dumps(filters)}
        """
        metadata = Paragraph(metadata_text, styles['Normal'])
        elements.append(metadata)
        
        # Summary section
        elements.append(Paragraph("<br/><b>Summary Statistics:</b>", styles['Heading2']))
        
        summary_data = [
            ['Metric', 'Value'],
            ['Total Calculations', str(len(df))],
            ['Average CO2 per Passenger (kg)', f"{df['co2_per_passenger_kg'].mean():.2f}"],
            ['Total CO2 Emitted (kg)', f"{df['total_co2_kg'].sum():.0f}"],
            ['Average Distance (km)', f"{df['distance_km'].mean():.0f}"],
            ['Most Common Cabin Class', df['cabin_class'].mode().iloc[0] if not df['cabin_class'].empty else 'N/A']
        ]
        
        summary_table = Table(summary_data)
        summary_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        elements.append(summary_table)
        
        # Full Data Table with pagination
        elements.append(Paragraph("<br/><b>Detailed Flight Data:</b>", styles['Heading2']))
        
        # Prepare all data rows
        all_table_data = [['Route', 'Passengers', 'Cabin', 'Distance (km)', 'CO2 (kg)', 'Date', 'Round Trip']]
        
        for _, row in df.iterrows():
            route = f"{row.get('departure', '')} → {row.get('destination', '')}"
            passengers = str(row.get('passengers', ''))
            cabin_class = str(row.get('cabin_class', '')).replace('_', ' ').title()
            distance = f"{row.get('distance_km', 0):.0f}"
            co2 = f"{row.get('co2_per_passenger_kg', 0):.0f}"
            round_trip = 'Yes' if row.get('round_trip') else 'No'
            
            # Format date
            created_at = row.get('created_at', '')
            date_str = format_date_for_pdf(created_at)
                
            all_table_data.append([route, passengers, cabin_class, distance, co2, date_str, round_trip])
        
        # Split data into chunks for better PDF rendering
        rows_per_page = 25  # Adjust based on your needs
        total_rows = len(all_table_data)
        
        for i in range(1, total_rows, rows_per_page):
            end_idx = min(i + rows_per_page, total_rows)
            page_data = all_table_data[0:1] + all_table_data[i:end_idx]  # Keep header + data
            
            # Add page break for subsequent pages
            if i > 1:
                elements.append(Paragraph(f"<br/><i>Continued... (Page {i//rows_per_page + 1})</i>", styles['Italic']))
            
            data_table = Table(page_data, repeatRows=1)  # Repeat header on each page
            
            # Style the table
            data_table.setStyle(TableStyle([
                # Header style
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1e40af')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 8),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
                
                # Data rows style
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
                ('ALIGN', (0, 1), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 1), (-1, -1), 7),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f8fafc')]),
            ]))
            
            elements.append(data_table)
        
        # Environmental impact section
        elements.append(Paragraph("<br/><b>Environmental Impact Analysis:</b>", styles['Heading2']))
        
        total_co2_tonnes = df['total_co2_kg'].sum() / 1000
        trees_needed = total_co2_tonnes * 50  # 1 tree absorbs ~20kg CO2 per year
        
        impact_text = f"""
        <b>Carbon Footprint Summary:</b><br/>
        • Total CO2 Emissions: <b>{total_co2_tonnes:,.1f} tonnes</b><br/>
        • Tree Equivalent: <b>{trees_needed:,.0f} trees</b> needed annually to absorb this CO2<br/>
        • Car Equivalent: Like driving a car for <b>{(total_co2_tonnes / 4.6 * 12):.1f} months</b><br/>
        • Flight Distance Total: <b>{df['distance_km'].sum():,.0f} km</b><br/>
        <br/>
        <i>Calculation notes:<br/>
        - Average car emissions: 4.6 tonnes CO2 per year<br/>
        - Tree absorption: ~20kg CO2 per tree per year<br/>
        - Based on ICAO carbon calculation methodology</i>
        """
        
        impact_para = Paragraph(impact_text, styles['Normal'])
        elements.append(impact_para)
        
        # Footer function
        def add_page_number(canvas, doc):
            canvas.saveState()
            canvas.setFont('Helvetica', 8)
            canvas.setFillColor(colors.grey)
            canvas.drawRightString(doc.pagesize[0] - 50, 30, f"Page {doc.page}")
            canvas.drawString(50, 30, f"Flight CO2 Calculator - {datetime.now().strftime('%Y-%m-%d')}")
            canvas.restoreState()
        
        # Build PDF
        doc.build(elements, onFirstPage=add_page_number, onLaterPages=add_page_number)
        buffer.seek(0)
        
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'flight_emissions_detailed_report_{datetime.now().strftime("%Y%m%d_%H%M%S")}.pdf'
        )
        
    except Exception as e:
        logger.error(f"❌ PDF export error: {e}")
        import traceback
        logger.error(f"PDF error details: {traceback.format_exc()}")
        return export_csv(df, filters, batch_params)

@app.route('/api/v2/automation/delete-multiple', methods=['DELETE', 'OPTIONS'])
def delete_multiple_calculations():
    """Delete multiple calculations by IDs"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        calculation_ids = data.get('calculation_ids', [])
        
        if not calculation_ids:
            return jsonify({'error': 'No calculation IDs provided'}), 400
        
        logger.info(f"🔄 Deleting {len(calculation_ids)} calculations")
        
        if not ENHANCED_FEATURES_AVAILABLE:
            return jsonify({'error': 'Enhanced features not available'}), 400
            
        with next(get_enhanced_db()) as db:
            from database.models import FlightCalculation as EnhancedFlightCalculation
            
            # Delete calculations
            delete_count = db.query(EnhancedFlightCalculation)\
                .filter(EnhancedFlightCalculation.id.in_(calculation_ids))\
                .delete(synchronize_session=False)
            
            db.commit()
            
            logger.info(f"✅ Successfully deleted {delete_count} calculations")
            
            return jsonify({
                'success': True,
                'deleted_count': delete_count,
                'requested_ids': calculation_ids
            })
            
    except Exception as e:
        logger.error(f"❌ Delete multiple error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v2/automation/delete-all', methods=['DELETE', 'OPTIONS'])
def delete_all_calculations():
    """Delete all calculations from the automation database"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        logger.info("🔄 Deleting ALL calculations")
        
        if not ENHANCED_FEATURES_AVAILABLE:
            return jsonify({'error': 'Enhanced features not available'}), 400
            
        with next(get_enhanced_db()) as db:
            from database.models import FlightCalculation as EnhancedFlightCalculation
            
            # Get count before deletion for reporting
            total_count = db.query(EnhancedFlightCalculation).count()
            
            # Delete all calculations
            delete_count = db.query(EnhancedFlightCalculation).delete()
            db.commit()
            
            logger.info(f"✅ Successfully deleted {delete_count} calculations (of {total_count} total)")
            
            return jsonify({
                'success': True,
                'deleted_count': delete_count,
                'total_count': total_count
            })
            
    except Exception as e:
        logger.error(f"❌ Delete all error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v2/automation/delete-by-filters', methods=['DELETE', 'OPTIONS'])
def delete_by_filters():
    """Delete calculations based on filters"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        filters = data.get('filters', {})
        
        logger.info(f"🔄 Deleting calculations with filters: {filters}")
        
        if not ENHANCED_FEATURES_AVAILABLE:
            return jsonify({'error': 'Enhanced features not available'}), 400
            
        with next(get_enhanced_db()) as db:
            from database.models import FlightCalculation as EnhancedFlightCalculation
            from sqlalchemy import and_, or_
            
            query = db.query(EnhancedFlightCalculation)
            
            # Apply filters
            if filters.get('date_range'):
                start_date = filters['date_range'].get('start')
                end_date = filters['date_range'].get('end')
                if start_date:
                    query = query.filter(EnhancedFlightCalculation.created_at >= start_date)
                if end_date:
                    query = query.filter(EnhancedFlightCalculation.created_at <= end_date)
            
            if filters.get('cabin_class'):
                query = query.filter(EnhancedFlightCalculation.cabin_class == filters['cabin_class'])
            
            if filters.get('data_source'):
                query = query.filter(EnhancedFlightCalculation.calculation_method == filters['data_source'])
            
            # Get count before deletion
            count_before = query.count()
            
            # Perform deletion
            delete_count = query.delete(synchronize_session=False)
            db.commit()
            
            logger.info(f"✅ Successfully deleted {delete_count} calculations with filters")
            
            return jsonify({
                'success': True,
                'deleted_count': delete_count,
                'filters_applied': filters,
                'matched_count': count_before
            })
            
    except Exception as e:
        logger.error(f"❌ Delete by filters error: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v2/automation/delete-older-than', methods=['DELETE', 'OPTIONS'])
def delete_older_than():
    """Delete calculations older than specified days"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        data = request.get_json()
        days = data.get('days', 30)
        
        logger.info(f"🔄 Deleting calculations older than {days} days")
        
        if not ENHANCED_FEATURES_AVAILABLE:
            return jsonify({'error': 'Enhanced features not available'}), 400
            
        with next(get_enhanced_db()) as db:
            from database.models import FlightCalculation as EnhancedFlightCalculation
            from datetime import datetime, timedelta
            
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            
            # Get count before deletion
            count_before = db.query(EnhancedFlightCalculation)\
                .filter(EnhancedFlightCalculation.created_at < cutoff_date)\
                .count()
            
            # Perform deletion
            delete_count = db.query(EnhancedFlightCalculation)\
                .filter(EnhancedFlightCalculation.created_at < cutoff_date)\
                .delete(synchronize_session=False)
            
            db.commit()
            
            logger.info(f"✅ Successfully deleted {delete_count} calculations older than {days} days")
            
            return jsonify({
                'success': True,
                'deleted_count': delete_count,
                'cutoff_date': cutoff_date.isoformat(),
                'days_old': days,
                'matched_count': count_before
            })
            
    except Exception as e:
        logger.error(f"❌ Delete older than error: {str(e)}")
        return jsonify({'error': str(e)}), 500

def format_date_for_pdf(date_value):
    """Helper function to format dates for PDF display"""
    if not date_value or pd.isna(date_value):
        return 'N/A'
    
    try:
        if isinstance(date_value, str):
            if 'T' in date_value:
                date_obj = datetime.fromisoformat(date_value.replace('Z', '+00:00'))
            else:
                date_obj = datetime.strptime(date_value, '%Y-%m-%d %H:%M:%S')
        elif isinstance(date_value, datetime):
            date_obj = date_value
        else:
            return str(date_value)[:10]
            
        return date_obj.strftime('%Y-%m-%d')
    except:
        return str(date_value)[:10]

def export_sql_server(df, filters, batch_params):
    """Export results as SQL Server INSERT statements"""
    try:
        # Generate SQL Server INSERT statements from the DataFrame
        insert_statements = []
        table_name = "flight_calculations"
        
        # SQL Server compatible column mapping
        column_mapping = {
            'id': 'id',
            'departure': 'departure',
            'destination': 'destination', 
            'passengers': 'passengers',
            'round_trip': 'round_trip',
            'cabin_class': 'cabin_class',
            'fuel_burn_kg': 'fuel_burn_kg',
            'total_co2_kg': 'total_co2_kg',
            'co2_per_passenger_kg': 'co2_per_passenger_kg',
            'co2_tonnes': 'co2_tonnes',
            'distance_km': 'distance_km',
            'distance_miles': 'distance_miles',
            'flight_info': 'flight_info',
            'created_at': 'created_at',
            'calculation_method': 'calculation_method',
            'data_source': 'data_source'
        }
        
        for _, row in df.iterrows():
            values = []
            columns_used = []
            
            for df_col, sql_col in column_mapping.items():
                if df_col in row:
                    value = row[df_col]
                    columns_used.append(f"[{sql_col}]")
                    
                    if pd.isna(value) or value is None:
                        values.append("NULL")
                    elif isinstance(value, str):
                        # Escape single quotes for SQL
                        escaped_value = value.replace("'", "''")
                        values.append(f"'{escaped_value}'")
                    elif isinstance(value, (int, float)):
                        values.append(str(value))
                    elif isinstance(value, bool):
                        values.append("1" if value else "0")
                    else:
                        # Convert any other type to string
                        values.append(f"'{str(value)}'")
            
            columns_str = ", ".join(columns_used)
            values_str = ", ".join(values)
            
            insert_stmt = f"INSERT INTO [{table_name}] ({columns_str}) VALUES ({values_str});"
            insert_statements.append(insert_stmt)
        
        # Generate the complete SQL file content
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sql_content = generate_sql_file_content(insert_statements, len(df), filters, batch_params, timestamp)
        
        return jsonify({
            'sql_content': sql_content,
            'filename': f'flight_calculations_sql_server_{timestamp}.sql',
            'row_count': len(insert_statements),
            'timestamp': timestamp
        })
        
    except Exception as e:
        logger.error(f"❌ SQL Server export error: {str(e)}")
        return jsonify({'error': str(e)}), 500

def generate_sql_file_content(insert_statements, row_count, filters, batch_params, timestamp):
    """Generate complete SQL file with headers and metadata"""
    
    sql_content = f"""-- SQL Server INSERT statements for table: flight_calculations
-- Generated by Flight CO2 Calculator
-- Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- Total Rows: {row_count}
-- Batch Parameters: {json.dumps(batch_params, indent=2)}
-- Filters Applied: {json.dumps(filters, indent=2)}
-- File Generated: {timestamp}

-- Enable identity insert to preserve original IDs (if needed)
SET IDENTITY_INSERT [flight_calculations] ON;

-- Insert statements
"""

    # Add all INSERT statements
    for stmt in insert_statements:
        sql_content += stmt + "\n"

    sql_content += """
-- Disable identity insert after import
SET IDENTITY_INSERT [flight_calculations] OFF;

-- Verification query
SELECT 
    COUNT(*) as TotalRows,
    AVG(total_co2_kg) as AvgCO2,
    SUM(total_co2_kg) as TotalCO2
FROM [flight_calculations];

-- Export completed successfully
"""

    return sql_content

# Optional: Add direct SQLite to SQL Server export endpoint
@app.route('/api/v2/automation/export-sqlite-to-sqlserver', methods=['POST', 'OPTIONS'])
def export_sqlite_to_sqlserver():
    """Export directly from SQLite database to SQL Server INSERT scripts"""
    if request.method == 'OPTIONS':
        return '', 200
        
    try:
        # Get the SQLite database path from config
        sqlite_db_path = 'flight_calculator.db'  # Adjust path as needed
        
        if not os.path.exists(sqlite_db_path):
            return jsonify({'error': 'SQLite database not found'}), 404
        
        # Connect to SQLite database
        sqlite_conn = sqlite3.connect(sqlite_db_path)
        sqlite_cursor = sqlite_conn.cursor()
        
        # Get table structure
        sqlite_cursor.execute("PRAGMA table_info(flight_calculations)")
        columns_info = sqlite_cursor.fetchall()
        columns = [row[1] for row in columns_info]
        
        # Get all data
        sqlite_cursor.execute("SELECT * FROM flight_calculations")
        rows = sqlite_cursor.fetchall()
        
        # Generate SQL Server INSERT statements
        insert_statements = []
        table_name = "flight_calculations"
        
        for row in rows:
            values = []
            for i, value in enumerate(row):
                col_name = columns[i]
                
                if value is None:
                    values.append("NULL")
                elif isinstance(value, str):
                    escaped_value = value.replace("'", "''")
                    values.append(f"'{escaped_value}'")
                elif isinstance(value, int):
                    values.append(str(value))
                elif isinstance(value, float):
                    values.append(str(value))
                elif isinstance(value, datetime):
                    values.append(f"'{value.isoformat()}'")
                elif isinstance(value, bool):
                    values.append("1" if value else "0")
                else:
                    values.append(f"'{str(value)}'")
            
            columns_str = ", ".join([f"[{col}]" for col in columns])
            values_str = ", ".join(values)
            
            insert_stmt = f"INSERT INTO [{table_name}] ({columns_str}) VALUES ({values_str});"
            insert_statements.append(insert_stmt)
        
        sqlite_conn.close()
        
        # Generate complete SQL file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        sql_content = generate_complete_sql_export(insert_statements, len(rows), columns_info, timestamp)
        
        # Return as downloadable file
        return send_file(
            io.BytesIO(sql_content.encode('utf-8')),
            mimetype='application/sql',
            as_attachment=True,
            download_name=f'sqlserver_export_complete_{timestamp}.sql'
        )
        
    except Exception as e:
        logger.error(f"❌ SQLite to SQL Server export error: {str(e)}")
        return jsonify({'error': str(e)}), 500

def generate_complete_sql_export(insert_statements, row_count, columns_info, timestamp):
    """Generate complete SQL export with metadata and summary"""
    
    has_identity = any(col[5] > 0 for col in columns_info if col[1] == 'id')
    
    sql_content = f"""-- SQL Server Migration Script
-- Flight CO2 Calculator Database Export
-- Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
-- Source: SQLite database
-- Target: SQL Server
-- Total Rows: {row_count}
-- File: {timestamp}

-- Create table if not exists (adjust data types as needed)
IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='flight_calculations' AND xtype='U')
CREATE TABLE [flight_calculations] (
    [id] INT PRIMARY KEY,
    [departure] NVARCHAR(100) NOT NULL,
    [destination] NVARCHAR(100) NOT NULL,
    [passengers] INT NOT NULL,
    [round_trip] BIT NOT NULL,
    [cabin_class] NVARCHAR(50) NOT NULL,
    [fuel_burn_kg] FLOAT NOT NULL,
    [total_co2_kg] FLOAT NOT NULL,
    [co2_per_passenger_kg] FLOAT NOT NULL,
    [co2_tonnes] FLOAT NOT NULL,
    [distance_km] FLOAT NOT NULL,
    [distance_miles] FLOAT NOT NULL,
    [flight_info] NVARCHAR(200),
    [created_at] DATETIME2,
    [calculation_method] NVARCHAR(50),
    [data_source] NVARCHAR(50)
);

"""

    if has_identity:
        sql_content += "-- Enable identity insert to preserve original IDs\n"
        sql_content += "SET IDENTITY_INSERT [flight_calculations] ON;\n\n"

    # Add INSERT statements
    sql_content += "-- Data insertion\n"
    for stmt in insert_statements:
        sql_content += stmt + "\n"

    if has_identity:
        sql_content += "\n-- Disable identity insert\n"
        sql_content += "SET IDENTITY_INSERT [flight_calculations] OFF;\n"

    # Add verification and summary
    sql_content += f"""
-- Verification and summary
SELECT 
    'Migration Summary' as Info,
    COUNT(*) as TotalRowsImported,
    GETDATE() as ImportDate,
    '{row_count}' as ExpectedRows
FROM [flight_calculations];

-- Data summary
SELECT 
    cabin_class,
    COUNT(*) as Count,
    AVG(total_co2_kg) as AvgCO2,
    SUM(total_co2_kg) as TotalCO2
FROM [flight_calculations]
GROUP BY cabin_class;

-- Migration completed successfully
"""

    return sql_content

@app.route('/api/v2/automation/cleanup', methods=['POST'])
def cleanup_automation():
    """Clean up automation state and stop current processing"""
    try:
        global automation_scheduler
        
        if automation_scheduler:
            # Clear processed files cache
            cache_size = automation_scheduler.clear_processed_cache()
            
            # Stop any ongoing processing
            automation_scheduler.is_running = False
            
            return jsonify({
                'success': True,
                'message': 'Automation cleanup completed',
                'cache_cleared': cache_size,
                'scheduler_stopped': True
            })
        else:
            return jsonify({
                'success': True,
                'message': 'No scheduler running',
                'cache_cleared': 0,
                'scheduler_stopped': False
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/v2/automation/populate-airports', methods=['POST'])
def populate_airports():
    """Populate airport data from frontend airports array"""
    try:
        if not ENHANCED_FEATURES_AVAILABLE:
            return jsonify({'error': 'Enhanced features not available'}), 400
        
        if not AIRPORTS_DATA:
            return jsonify({
                'success': False, 
                'error': 'No airports data available. Please check if airports.js is accessible.'
            }), 400
                
        with next(get_enhanced_db()) as db:
            airport_service = AirportService(db)
            
            airports_created = 0
            airports_updated = 0
            airports_skipped = 0
            airports_with_errors = 0
            
            for i, airport_data in enumerate(AIRPORTS_DATA):
                try:
                    # Validate required fields - use iata_code instead of code
                    if not airport_data.get('code'):
                        print(f"⚠️ Skipping airport without code at index {i}")
                        airports_skipped += 1
                        continue
                    
                    # Check if airport exists using iata_code
                    existing = airport_service.get_airport_by_code(airport_data['code'])
                    
                    # Prepare airport data with correct field names
                    iata_code = airport_data['code']
                    name = airport_data.get('name', f"{iata_code} Airport")
                    city = airport_data.get('city', 'Unknown')
                    country = airport_data.get('country', 'Unknown')
                    
                    # Handle coordinate conversion - convert to float or None
                    latitude = airport_data.get('latitude')
                    if latitude is None or latitude == '':
                        latitude = None  # Use None instead of empty string
                    else:
                        try:
                            latitude = float(latitude)
                        except (ValueError, TypeError):
                            latitude = None
                    
                    longitude = airport_data.get('longitude')
                    if longitude is None or longitude == '':
                        longitude = None  # Use None instead of empty string
                    else:
                        try:
                            longitude = float(longitude)
                        except (ValueError, TypeError):
                            longitude = None
                    
                    # Use search field or create default
                    search = airport_data.get('search', f"{city}, {country} ({iata_code})")
                    
                    if not existing:
                        # Create the airport with correct field names
                        new_airport = Airport(
                            iata_code=iata_code,
                            name=name,
                            city=city,
                            country=country,
                            latitude=latitude,
                            longitude=longitude,
                            search=search
                        )
                        db.add(new_airport)
                        airports_created += 1
                        print(f"✅ Created airport: {iata_code}")
                    else:
                        # Update existing airport - always update since we want to populate coordinates
                        existing.name = name
                        existing.city = city
                        existing.country = country
                        existing.latitude = latitude
                        existing.longitude = longitude
                        existing.search = search
                        airports_updated += 1
                        print(f"🔄 Updated airport: {iata_code}")
                            
                except Exception as e:
                    print(f"❌ Error processing airport {airport_data.get('code', 'Unknown')} at index {i}: {str(e)}")
                    airports_with_errors += 1
                    continue
                
                # Commit in batches to avoid memory issues
                if (airports_created + airports_updated) % 100 == 0:
                    db.commit()
                    print(f"🔄 Committed {airports_created + airports_updated} airports so far...")
            
            db.commit()
            
            return jsonify({
                'success': True,
                'message': f'Airports populated: {airports_created} created, {airports_updated} updated, {airports_skipped} skipped, {airports_with_errors} errors',
                'airports_created': airports_created,
                'airports_updated': airports_updated,
                'airports_skipped': airports_skipped,
                'airports_with_errors': airports_with_errors,
                'total_processed': len(AIRPORTS_DATA)
            })
                
    except Exception as e:
        print(f"❌ Error in populate_airports: {e}")
        import traceback
        print(f"🔍 Full traceback: {traceback.format_exc()}")
        return jsonify({'error': str(e)}), 500

# =============================================================================
# ICAO CALCULATION FUNCTIONS (KEEP THESE)
# =============================================================================

# WITH NO FALLBACK IF ICAO FAILES
def get_icao_emissions(departure, destination, passengers, round_trip, cabin_class):
    """Get real emissions data from ICAO API - STRICT MODE: No fallbacks"""
    
    ICAO_API_URL = "https://icec.icao.int/Home/PassengerCompute"
    
    try:
        print(f"🎯 Starting ICAO API call for {departure} -> {destination}")
        
        # CORRECTED: Map cabin class to ICAO numeric format
        cabin_class_mapping = {
            "economy": 0,        # ICAO uses 0 for Economy
            "premium_economy": 1, # ICAO uses 1 for Premium Economy
            "business": 2,        # ICAO uses 2 for Business
            "first": 3            # ICAO uses 3 for First
        }
        
        icao_cabin_class = cabin_class_mapping.get(cabin_class, 0)
        
        # Get airport names from database or use fallback
        dep_airport = get_airport_by_iata(departure)
        dest_airport = get_airport_by_iata(destination)
        
        departure_name = f"{departure.upper()} Airport"
        destination_name = f"{destination.upper()} Airport"
        
        if dep_airport and hasattr(dep_airport, 'name') and dep_airport.name:
            departure_name = dep_airport.name
        if dest_airport and hasattr(dest_airport, 'name') and dest_airport.name:
            destination_name = dest_airport.name
        
        # CORRECTED: Prepare proper ICAO API payload
        icao_data = {
            "AirportCodeDeparture": departure.upper(),
            "AirportCodeDestination": [destination.upper()],
            "CabinClass": icao_cabin_class,  # Now sending numeric value
            "Departure": departure_name,      # Full airport name
            "Destination": [destination_name], # Full airport name in array
            "IsRoundTrip": round_trip,
            "NumberOfPassenger": passengers
        }

        print(f"📤 Payload: {icao_data}")
        
        # Headers that match what the ICAO website sends
        headers = {
            "Content-Type": "application/json; charset=UTF-8",
            "Accept": "application/json, text/javascript, */*; q=0.01",
            "X-Requested-With": "XMLHttpRequest",
            "Origin": "https://icec.icao.int",
            "Referer": "https://icec.icao.int/calculator",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
            "Sec-Ch-Ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors", 
            "Sec-Fetch-Site": "same-origin"
        }
        
        print("🔄 Sending request to ICAO API...")
        
        response = requests.post(
            ICAO_API_URL, 
            json=icao_data, 
            headers=headers,
            timeout=30
        )
        
        print(f"📡 ICAO API Response Status: {response.status_code}")
        
        if response.status_code == 200:
            # Check if response is HTML instead of JSON
            if response.text.strip().startswith('<!DOCTYPE html>') or response.text.strip().startswith('<html'):
                print(f"❌ ICAO API returned HTML instead of JSON for {departure}->{destination}")
                print(f"📄 Response preview: {response.text[:200]}...")
                # STRICT MODE: Don't fallback, raise exception
                raise Exception(f"ICAO API returned HTML instead of JSON")
            
            try:
                icao_result = response.json()
                print("✅ ICAO API call successful, parsing response...")
                return parse_icao_response(icao_result, departure, destination, passengers, round_trip, cabin_class)
            except json.JSONDecodeError as e:
                print(f"❌ JSON decode error for {departure}->{destination}: {e}")
                print(f"📄 Response text: {response.text[:500]}...")
                # STRICT MODE: Don't fallback, raise exception
                raise Exception(f"ICAO API returned invalid JSON: {e}")
        else:
            print(f"❌ ICAO API returned status {response.status_code}")
            print(f"Response text: {response.text[:500]}...")
            # STRICT MODE: Don't fallback, raise exception
            raise Exception(f"ICAO API returned status {response.status_code}")
            
    except requests.exceptions.Timeout:
        print("❌ ICAO API timeout")
        raise Exception("ICAO API timeout - no fallback calculation performed")
    except requests.exceptions.ConnectionError:
        print("❌ ICAO API connection error")
        raise Exception("ICAO API connection error - no fallback calculation performed")
    except Exception as e:
        print(f"❌ ICAO API error: {e}")
        import traceback
        print(f"Full traceback: {traceback.format_exc()}")
        # STRICT MODE: Re-raise the exception instead of falling back
        raise

# # WITH FALLBACK IF ICAO FAILES
# def get_icao_emissions(departure, destination, passengers, round_trip, cabin_class):
#     """Get real emissions data from ICAO API with better error handling"""
    
#     ICAO_API_URL = "https://icec.icao.int/Home/PassengerCompute"
    
#     try:
#         print(f"🎯 Starting ICAO API call for {departure} -> {destination}")
        
#         # CORRECTED: Map cabin class to ICAO numeric format
#         cabin_class_mapping = {
#             "economy": 0,        # ICAO uses 0 for Economy
#             "premium_economy": 1, # ICAO uses 1 for Premium Economy
#             "business": 2,        # ICAO uses 2 for Business
#             "first": 3            # ICAO uses 3 for First
#         }
        
#         icao_cabin_class = cabin_class_mapping.get(cabin_class, 0)
        
#         # Get airport names from database or use fallback
#         dep_airport = get_airport_by_iata(departure)
#         dest_airport = get_airport_by_iata(destination)
        
#         departure_name = f"{departure.upper()} Airport"
#         destination_name = f"{destination.upper()} Airport"
        
#         if dep_airport and hasattr(dep_airport, 'name') and dep_airport.name:
#             departure_name = dep_airport.name
#         if dest_airport and hasattr(dest_airport, 'name') and dest_airport.name:
#             destination_name = dest_airport.name
        
#         # CORRECTED: Prepare proper ICAO API payload
#         icao_data = {
#             "AirportCodeDeparture": departure.upper(),
#             "AirportCodeDestination": [destination.upper()],
#             "CabinClass": icao_cabin_class,  # Now sending numeric value
#             "Departure": departure_name,      # Full airport name
#             "Destination": [destination_name], # Full airport name in array
#             "IsRoundTrip": round_trip,
#             "NumberOfPassenger": passengers
#         }

#         print(f"📤 Payload: {icao_data}")
        
#         # Headers that match what the ICAO website sends
#         headers = {
#             "Content-Type": "application/json; charset=UTF-8",
#             "Accept": "application/json, text/javascript, */*; q=0.01",
#             "X-Requested-With": "XMLHttpRequest",
#             "Origin": "https://icec.icao.int",
#             "Referer": "https://icec.icao.int/calculator",
#             "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/141.0.0.0 Safari/537.36",
#             "Sec-Ch-Ua": '"Google Chrome";v="141", "Not?A_Brand";v="8", "Chromium";v="141"',
#             "Sec-Ch-Ua-Mobile": "?0",
#             "Sec-Ch-Ua-Platform": '"Windows"',
#             "Sec-Fetch-Dest": "empty",
#             "Sec-Fetch-Mode": "cors", 
#             "Sec-Fetch-Site": "same-origin"
#         }
        
#         print("🔄 Sending request to ICAO API...")
        
#         response = requests.post(
#             ICAO_API_URL, 
#             json=icao_data, 
#             headers=headers,
#             timeout=30
#         )
        
#         print(f"📡 ICAO API Response Status: {response.status_code}")
        
#         if response.status_code == 200:
#             # Check if response is HTML instead of JSON
#             if response.text.strip().startswith('<!DOCTYPE html>') or response.text.strip().startswith('<html'):
#                 print(f"❌ ICAO API returned HTML instead of JSON for {departure}->{destination}")
#                 print(f"📄 Response preview: {response.text[:200]}...")
#                 return get_fallback_icao_data(departure, destination, passengers, round_trip, cabin_class)
            
#             try:
#                 icao_result = response.json()
#                 print("✅ ICAO API call successful, parsing response...")
#                 return parse_icao_response(icao_result, departure, destination, passengers, round_trip, cabin_class)
#             except json.JSONDecodeError as e:
#                 print(f"❌ JSON decode error for {departure}->{destination}: {e}")
#                 print(f"📄 Response text: {response.text[:500]}...")
#                 return get_fallback_icao_data(departure, destination, passengers, round_trip, cabin_class)
#         else:
#             print(f"❌ ICAO API returned status {response.status_code}")
#             print(f"Response text: {response.text[:500]}...")
#             return get_fallback_icao_data(departure, destination, passengers, round_trip, cabin_class)
            
#     except requests.exceptions.Timeout:
#         print("❌ ICAO API timeout")
#         return get_fallback_icao_data(departure, destination, passengers, round_trip, cabin_class)
#     except requests.exceptions.ConnectionError:
#         print("❌ ICAO API connection error")
#         return get_fallback_icao_data(departure, destination, passengers, round_trip, cabin_class)
#     except Exception as e:
#         print(f"❌ ICAO API error: {e}")
#         import traceback
#         print(f"Full traceback: {traceback.format_exc()}")
#         return get_fallback_icao_data(departure, destination, passengers, round_trip, cabin_class)

def parse_icao_response(icao_response, departure, destination, passengers, round_trip, cabin_class):
    """Parse the ICAO API response into our format"""
    
    print("🔍 Parsing ICAO API response...")
    
    # Find the correct result based on cabin class
    cabin_class_mapping = {
        "economy": 0,
        "premium_economy": 1, 
        "business": 2,
        "first": 3
    }

    icao_cabin_class = cabin_class_mapping.get(cabin_class, 0)

    # Find the result for our cabin class
    result_summary = None
    for summary in icao_response.get('resultSummary', []):
        if summary.get('cabinClass') == icao_cabin_class and summary.get('isClassFound', False):
            result_summary = summary
            break
    
    # If exact cabin class not found, use economy (class 0) as fallback
    if not result_summary:
        for summary in icao_response.get('resultSummary', []):
            if summary.get('cabinClass') == 0 and summary.get('isClassFound', False):
                result_summary = summary
                break
    
    if not result_summary:
        print("❌ No valid results found in ICAO response")
        raise ValueError("No valid results found in ICAO response")
    
    print(f"✅ Found result summary for cabin class {icao_cabin_class}")
    
    # Calculate totals from legs
    total_co2 = 0
    total_fuel = 0
    total_distance = 0
    
    for leg in result_summary.get('details', []):
        total_co2 += leg.get('co2', 0)
        total_fuel += leg.get('avgFuel', 0)
        total_distance += leg.get('tripDistance', 0)
    
    print(f"📊 Raw totals - CO2: {total_co2}, Fuel: {total_fuel}, Distance: {total_distance}")
    
    # ICAO gives per-passenger CO2 directly in their API response
    co2_per_passenger = total_co2
    total_co2_for_passengers = co2_per_passenger * passengers
    
    # Calculate fuel allocation per passenger (derived from CO2)
    fuel_per_passenger = total_co2 / 3.16  # Convert CO2 back to fuel using ICAO factor
    total_fuel_for_passengers = fuel_per_passenger * passengers

    print(f"🎯 Final calculation - CO2 per passenger: {co2_per_passenger}, Fuel per passenger: {fuel_per_passenger}")

    result = {
        'fuel_burn_kg': round(total_fuel_for_passengers),
        'total_co2_kg': round(total_co2_for_passengers),
        'co2_per_passenger_kg': round(co2_per_passenger),
        'co2_tonnes': round(total_co2_for_passengers / 1000, 3),
        'distance_km': round(total_distance),
        'distance_miles': round(total_distance * 0.621371),
        'cabin_class': cabin_class,
        'data_source': 'ICAO_API',
        'aircraft_fuel_total_kg': round(total_fuel),
        'aircraft_co2_total_kg': round(total_co2 * 3.16),
        'avg_seats': result_summary['details'][0].get('avgSeats', 242) if result_summary.get('details') else 242,
        'fleet': result_summary['details'][0].get('fleet', '') if result_summary.get('details') else ''
    }
    
    print(f"✅ Parsed result: {result}")
    return result

def get_fallback_icao_data(departure, destination, passengers, round_trip, cabin_class):
    """Fallback calculation when ICAO API is unavailable"""
    # Use our previous accurate calculation as fallback
    distance_km = calculate_great_circle_distance(departure, destination)
    
    if distance_km == 0:
        # Use average distance if calculation fails
        distance_km = 1000
    
    CO2_PER_KG_FUEL = 3.16
    BASE_FUEL_PER_PAX_KM = 0.01766
    
    cabin_multipliers = {
        "economy": 1.0,
        "premium_economy": 1.3,
        "business": 1.8,
        "first": 2.5
    }
    
    multiplier = cabin_multipliers.get(cabin_class.lower(), 1.0)
    
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
        'data_source': 'FALLBACK_CALCULATION'
    }

def calculate_great_circle_distance(departure, destination):
    """Calculate great circle distance between airports in km using Haversine formula"""
    try:
        # Extract airport codes (handle cases like "JFK" or "New York (JFK)")
        dep_code = departure.upper()[-3:] if '(' in departure else departure.upper()
        dest_code = destination.upper()[-3:] if '(' in destination else destination.upper()
        
        # Get coordinates
        lat1, lon1 = get_airport_coordinates(dep_code)
        lat2, lon2 = get_airport_coordinates(dest_code)
        
        # If coordinates not found, return 0
        if lat1 == 0 and lon1 == 0 or lat2 == 0 and lon2 == 0:
            print(f"Warning: Coordinates not found for {dep_code} or {dest_code}")
            return 0
        
        # Haversine formula
        R = 6371  # Earth's radius in km
        
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        delta_lat = math.radians(lat2 - lat1)
        delta_lon = math.radians(lon2 - lon1)
        
        a = (math.sin(delta_lat/2) * math.sin(delta_lat/2) + 
             math.cos(lat1_rad) * math.cos(lat2_rad) * 
             math.sin(delta_lon/2) * math.sin(delta_lon/2))
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
        
        distance_km = R * c
        return distance_km
        
    except Exception as e:
        print(f"Distance calculation error: {e}")
        return 0

def get_airport_coordinates(airport_code):
    """Get airport coordinates from ICAO database or fallback"""
    # First try to get from your enhanced database
    if ENHANCED_FEATURES_AVAILABLE:
        try:
            with next(get_enhanced_db()) as db:
                airport_service = AirportService(db)
                airport = airport_service.get_airport_by_code(airport_code)
                if airport and airport.latitude and airport.longitude:
                    return (airport.latitude, airport.longitude)
        except:
            pass
    
    # Fallback to our airports data
    for airport in AIRPORTS_DATA:
        if airport['code'] == airport_code.upper():
            return (airport['latitude'], airport['longitude'])
    
    return (0, 0)

# =============================================================================
# BASIC TEST ENDPOINTS (KEEP THESE)
# =============================================================================

@app.route('/api/test', methods=['GET'])
def test_route():
    return jsonify({'message': 'Backend is working!'})

@app.route('/api/v2/automation/debug-model', methods=['GET'])
def debug_model_structure():
    """Debug the EnhancedFlightCalculation model structure"""
    try:
        if not ENHANCED_FEATURES_AVAILABLE:
            return jsonify({'error': 'Enhanced features not available'}), 400
        
        from database.models import FlightCalculation as EnhancedFlightCalculation
        import inspect
        
        model_info = {
            'model_name': 'EnhancedFlightCalculation',
            'columns': [],
            'methods': []
        }
        
        # Get column information
        for column in EnhancedFlightCalculation.__table__.columns:
            model_info['columns'].append({
                'name': column.name,
                'type': str(column.type),
                'nullable': column.nullable,
                'primary_key': column.primary_key
            })
        
        # Get methods
        for name, value in inspect.getmembers(EnhancedFlightCalculation):
            if not name.startswith('_') and inspect.ismethod(value):
                model_info['methods'].append(name)
        
        return jsonify(model_info)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500
    
@app.route('/api/v2/automation/debug-status', methods=['GET'])
def debug_automation_status():
    """Comprehensive debug endpoint to check automation status"""
    try:
        global automation_scheduler
        
        debug_info = {
            'scheduler': {},
            'database': {},
            'files': {},
            'endpoints': {}
        }
        
        # Check scheduler status
        if automation_scheduler:
            debug_info['scheduler'] = {
                'is_running': automation_scheduler.is_running,
                'last_run_time': str(getattr(automation_scheduler, 'last_run_time', 'Never')),
                'processed_files_cache': list(getattr(automation_scheduler, 'processed_files_cache', set())),
                'cache_size': len(getattr(automation_scheduler, 'processed_files_cache', set()))
            }
        else:
            debug_info['scheduler'] = {'error': 'Scheduler not initialized'}
        
        # Check database counts
        try:
            with next(get_enhanced_db()) as db:
                from database.models import FlightCalculation as EnhancedFlightCalculation
                total_calculations = db.query(EnhancedFlightCalculation).count()
                
                # Recent calculations (last 10 minutes)
                ten_minutes_ago = datetime.utcnow() - timedelta(minutes=10)
                recent_calculations = db.query(EnhancedFlightCalculation)\
                    .filter(EnhancedFlightCalculation.created_at >= ten_minutes_ago)\
                    .count()
                
                debug_info['database'] = {
                    'total_calculations': total_calculations,
                    'recent_calculations': recent_calculations,
                    'enhanced_features_available': ENHANCED_FEATURES_AVAILABLE
                }
        except Exception as e:
            debug_info['database'] = {'error': str(e)}
        
        # Check file system
        try:
            scheduled_files = []
            processed_files = []
            
            if os.path.exists('data/scheduled'):
                scheduled_files = [f for f in os.listdir('data/scheduled') if f.endswith('.csv')]
            
            if os.path.exists('data/processed'):
                processed_files = [f for f in os.listdir('data/processed') if f.endswith('.csv')]
            
            debug_info['files'] = {
                'scheduled_files': scheduled_files,
                'processed_files': processed_files[:10],  # First 10 only
                'scheduled_dir_exists': os.path.exists('data/scheduled'),
                'processed_dir_exists': os.path.exists('data/processed')
            }
        except Exception as e:
            debug_info['files'] = {'error': str(e)}
        
        # Test batch service directly
        try:
            if ENHANCED_FEATURES_AVAILABLE and automation_scheduler:
                from services.batch_service import DirectFixedBatchService
                with next(get_enhanced_db()) as db:
                    test_service = DirectFixedBatchService(db)
                    debug_info['batch_service'] = {
                        'available': True,
                        'service_type': str(type(test_service))
                    }
            else:
                debug_info['batch_service'] = {'available': False}
        except Exception as e:
            debug_info['batch_service'] = {'error': str(e)}
        
        return jsonify(debug_info)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/v2/automation/test-single-calculation', methods=['POST'])
def test_single_calculation():
    """Test a single calculation to verify the database is working"""
    try:
        if not ENHANCED_FEATURES_AVAILABLE:
            return jsonify({'error': 'Enhanced features not available'}), 400
        
        with next(get_enhanced_db()) as db:
            from database.models import FlightCalculation as EnhancedFlightCalculation
            
            # Create a simple test calculation
            test_calculation = EnhancedFlightCalculation(
                departure='TEST',
                destination='TEST',
                passengers=1,
                round_trip=True,
                cabin_class='economy',
                fuel_burn_kg=100.0,
                total_co2_kg=200.0,
                co2_per_passenger_kg=200.0,
                co2_tonnes=0.2,
                distance_km=1000.0,
                distance_miles=621.0,
                flight_info='TEST to TEST - 1000km (Round Trip) • Economy',
                calculation_method='TEST'
            )
            
            db.add(test_calculation)
            db.commit()
            
            # Verify it was saved
            saved_calc = db.query(EnhancedFlightCalculation)\
                .filter(EnhancedFlightCalculation.departure == 'TEST')\
                .first()
            
            return jsonify({
                'success': True,
                'message': 'Test calculation saved successfully',
                'calculation_id': saved_calc.id if saved_calc else None,
                'test_data_saved': saved_calc is not None
            })
            
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/')
def home():
    return jsonify({'message': 'Flight CO₂ Calculator API - ICAO Methodology'})
    
if __name__ == '__main__':
    app.run(debug=True, port=8080, host='0.0.0.0')
