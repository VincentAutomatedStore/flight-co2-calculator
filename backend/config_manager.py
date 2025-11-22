import json
import os
from typing import Dict, Any
from config import Config

class ConfigManager:
    """Manages configuration loading and saving"""
    
    def __init__(self, config_file: str = "config.json"):
        self.config_file = config_file
        self.config = Config()
    
    def load_config(self) -> bool:
        """Load configuration from file"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                self.config.update_from_dict(config_data)
                print(f"✅ Configuration loaded from {self.config_file}")
                return True
            else:
                print(f"⚠️  Config file {self.config_file} not found, using defaults")
                return False
        except Exception as e:
            print(f"❌ Error loading config: {e}")
            return False
    
    def save_config(self, config_dict: Dict[str, Any]) -> bool:
        """Save configuration to file"""
        try:
            with open(self.config_file, 'w') as f:
                json.dump(config_dict, f, indent=4)
            self.config.update_from_dict(config_dict)
            print(f"✅ Configuration saved to {self.config_file}")
            return True
        except Exception as e:
            print(f"❌ Error saving config: {e}")
            return False
    
    def get_config_dict(self) -> Dict[str, Any]:
        """Get current configuration as dictionary"""
        return {
            "database": {
                "dialect": self.config.database.dialect,
                "host": self.config.database.host,
                "port": self.config.database.port,
                "username": self.config.database.username,
                "password": self.config.database.password,
                "database": self.config.database.database,
                "driver": self.config.database.driver
            }
        }
    
    def test_connection(self) -> bool:
        """Test database connection"""
        try:
            from sqlalchemy import create_engine, text
            engine = create_engine(self.config.database.connection_string)
            with engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            print("✅ Database connection test successful")
            return True
        except Exception as e:
            print(f"❌ Database connection test failed: {e}")
            return False