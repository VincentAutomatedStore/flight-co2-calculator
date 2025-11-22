import schedule
import time
import threading
import logging
import os
import shutil
from datetime import datetime
from glob import glob
from sqlalchemy.orm import Session
from services.batch_service import DirectBatchService as BatchService
from .config import SchedulerConfig

logger = logging.getLogger(__name__)

class SimpleScheduler:
    """
    Simple scheduler for processing CSV files on daily, weekly, or monthly basis
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.batch_service = BatchService(db)
        self.is_running = False
        self.scheduler_thread = None
        self.processing_lock = threading.Lock()  # Add lock to prevent concurrent processing
        self.processed_files_cache = set()  # Track processed files to prevent reprocessing
        self.last_run_time = None
        self.next_run_time = None
        self.current_batch_params = None  # Store current batch parameters
        
        # Ensure directories exist
        SchedulerConfig.ensure_directories()
        
        logger.info("SimpleScheduler initialized")
    
    def _safe_move_file(self, source_path, target_dir, new_filename):
        """Safely move a file with proper error handling"""
        try:
            # Ensure source exists
            if not os.path.exists(source_path):
                logger.error(f"❌ Source file not found: {source_path}")
                return False
                
            # Ensure target directory exists
            os.makedirs(target_dir, exist_ok=True)
            
            target_path = os.path.join(target_dir, new_filename)
            
            # Move the file
            shutil.move(source_path, target_path)
            logger.info(f"✅ File moved successfully: {source_path} -> {target_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Failed to move file {source_path}: {e}")
            return False

    def process_pending_files(self, force_process=False):
        """Process all CSV files in the scheduled directory - UPDATED WITH FORCE PROCESS"""
        # Use lock to prevent concurrent processing
        if not self.processing_lock.acquire(blocking=False):
            logger.info("Processing already in progress, skipping...")
            return
            
        try:
            pattern = os.path.join(SchedulerConfig.SCHEDULED_DIR, SchedulerConfig.CSV_PATTERN)
            csv_files = glob(pattern)
            
            if not csv_files:
                logger.debug("No CSV files found to process")
                return
            
            # If force_process is True, process ALL files regardless of cache
            if force_process:
                logger.info("🔄 Force processing all files (ignoring cache)")
                new_csv_files = csv_files
            else:
                # Filter out files that have already been processed in this session
                new_csv_files = [f for f in csv_files if os.path.basename(f) not in self.processed_files_cache]
            
            if not new_csv_files:
                logger.debug("No new CSV files to process (all files already processed)")
                return
            
            logger.info(f"Found {len(new_csv_files)} new CSV file(s) to process")
            
            for csv_file in new_csv_files:
                self._process_single_file(csv_file)
                
            self.last_run_time = datetime.now()
                
        except Exception as e:
            logger.error(f"Error in process_pending_files: {str(e)}")
        finally:
            self.processing_lock.release()
    
    def _process_single_file(self, file_path: str):
        """Process a single CSV file and move it to appropriate directory"""
        filename = os.path.basename(file_path)
        
        try:
            logger.info(f"🔄 Processing file: {filename}")
            logger.info(f"📋 Using batch parameters: {self.current_batch_params}")
            
            # Process the CSV file with batch parameters
            result = self.batch_service.process_flight_csv(
                file_path, 
                batch_params=self.current_batch_params  # PASS BATCH PARAMS
            )
            
            # Add to processed cache to prevent reprocessing in automated runs
            self.processed_files_cache.add(filename)
            
            # Determine destination directory based on success rate
            successful = result.get('processed_rows', 0)
            failed = result.get('error_rows', 0)
            total = successful + failed
            
            if total == 0:
                # No rows processed, move to errors
                destination_dir = SchedulerConfig.ERRORS_DIR
                logger.warning(f"No rows processed in {filename}, moving to errors")
            elif failed == 0:
                # All rows processed successfully
                destination_dir = SchedulerConfig.PROCESSED_DIR
                logger.info(f"✅ Successfully processed {filename}: {successful} calculations")
            else:
                # Some rows failed
                success_rate = (successful / total) * 100
                if success_rate >= 50:  # More than 50% success
                    destination_dir = SchedulerConfig.PROCESSED_DIR
                    logger.info(f"⚠️ Partially processed {filename}: {successful} success, {failed} failures (moved to processed)")
                else:
                    destination_dir = SchedulerConfig.ERRORS_DIR
                    logger.warning(f"❌ Poor success rate for {filename}: {successful} success, {failed} failures (moved to errors)")
            
            # Move file to appropriate directory using safe method
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            new_filename = f"{timestamp}_{filename}"
            
            if self._safe_move_file(file_path, destination_dir, new_filename):
                logger.info(f"📁 Moved {filename} to {destination_dir}")
                
                # Save processing result
                result_file = os.path.join(destination_dir, f"{timestamp}_{filename}.result.json")
                import json
                with open(result_file, 'w') as f:
                    json.dump(result, f, indent=2)
            else:
                logger.error(f"❌ Failed to move file {filename}")
            
        except Exception as e:
            logger.error(f"❌ Failed to process file {file_path}: {str(e)}")
            
            # Add to processed cache even if failed to prevent infinite retry
            self.processed_files_cache.add(filename)
            
            # Move to errors directory using safe method
            try:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                error_filename = f"{timestamp}_{filename}"
                
                if self._safe_move_file(file_path, SchedulerConfig.ERRORS_DIR, error_filename):
                    logger.info(f"📁 Moved failed file to errors directory: {error_filename}")
                else:
                    logger.error(f"❌ Failed to move error file: {file_path}")
            except Exception as move_error:
                logger.error(f"❌ Failed to move error file: {move_error}")
    
    def trigger_manual_run(self):
        """Manually trigger processing of pending files - UPDATED TO FORCE PROCESS"""
        logger.info("🔧 Manual processing triggered - FORCING REPROCESSING")
        
        # Use default batch params if none set
        if not self.current_batch_params:
            self.current_batch_params = {
                'passengers': 1,
                'cabinClass': 'economy',
                'roundTrip': False
            }
        
        # For manual runs, force processing of ALL files regardless of cache
        return self.process_pending_files(force_process=True)
    
    def clear_processed_cache(self):
        """Clear the processed files cache (useful for testing)"""
        cache_size = len(self.processed_files_cache)
        self.processed_files_cache.clear()
        logger.info(f"🧹 Cleared processed files cache ({cache_size} files)")
        return cache_size
    
    def start_daily(self, hour: int = 2, minute: int = 0):
        """Start daily processing at specified time"""
        schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(self.process_pending_files)
        self.next_run_time = f"Daily at {hour:02d}:{minute:02d}"
        logger.info(f"⏰ Daily schedule set for {hour:02d}:{minute:02d}")
    
    def start_weekly(self, day: str = "monday", hour: int = 2, minute: int = 0):
        """Start weekly processing on specified day and time"""
        getattr(schedule.every(), day).at(f"{hour:02d}:{minute:02d}").do(self.process_pending_files)
        self.next_run_time = f"Weekly on {day} at {hour:02d}:{minute:02d}"
        logger.info(f"⏰ Weekly schedule set for every {day} at {hour:02d}:{minute:02d}")
    
    def start_monthly(self, day: int = 1, hour: int = 2, minute: int = 0):
        """Start monthly processing on specified day of month and time"""
        def monthly_job():
            if datetime.now().day == day:
                self.process_pending_files()
        
        schedule.every().day.at(f"{hour:02d}:{minute:02d}").do(monthly_job)
        self.next_run_time = f"Monthly on day {day} at {hour:02d}:{minute:02d}"
        logger.info(f"⏰ Monthly schedule set for day {day} at {hour:02d}:{minute:02d}")
    
    def start_scheduler(self):
        """Start the scheduler thread"""
        if self.is_running:
            logger.warning("⚠️ Scheduler is already running")
            return
        
        self.is_running = True
        
        def run_scheduler():
            logger.info("🔌 Scheduler thread started")
            while self.is_running:
                try:
                    schedule.run_pending()
                except Exception as e:
                    logger.error(f"❌ Scheduler error: {e}")
                time.sleep(60)  # Check every minute
        
        self.scheduler_thread = threading.Thread(target=run_scheduler)
        self.scheduler_thread.daemon = True
        self.scheduler_thread.start()
        
        logger.info("✅ Scheduler started")
    
    def stop_scheduler(self):
        """Stop the scheduler"""
        self.is_running = False
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=10)
        logger.info("🛑 Scheduler stopped")
    
    def get_cache_info(self):
        """Get information about processed files cache"""
        return {
            'cache_size': len(self.processed_files_cache),
            'processed_files': list(self.processed_files_cache),
            'last_run': self.last_run_time.isoformat() if self.last_run_time else 'Never',
            'next_run': self.next_run_time or 'Not scheduled'
        }