import os
from dataclasses import dataclass
from typing import Optional

@dataclass
class DatabaseConfig:
    """Database configuration settings"""
    dialect: str = "sqlite"
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    database: str = "flight_calculator"
    driver: str = "ODBC Driver 17 for SQL Server"
    extra: Optional[str] = None
    
    @property
    def connection_string(self):
        if self.dialect == "sqlite":
            return f"sqlite:///{self.database}.db"
        elif self.dialect == "mssql":
            # Build connection string with optional extra parameters
            base_conn = f"mssql+pyodbc://"
            
            # Add credentials if provided
            if self.username and self.password:
                base_conn += f"{self.username}:{self.password}@"
            else:
                base_conn += "@"  # Windows authentication
            
            # Add server and database
            base_conn += f"{self.host}:{self.port}/{self.database}"
            
            # Add driver and extra parameters
            params = f"driver={self.driver}"
            if self.extra:
                params += f"&{self.extra}"
            
            return f"{base_conn}?{params}"
        else:
            raise ValueError(f"Unsupported database dialect: {self.dialect}")

class Config:
    """Main configuration class"""
    
    def __init__(self):
        self.database = DatabaseConfig()
        self._load_from_env()
    
    def _load_from_env(self):
        """Load configuration from environment variables"""
        # Database configuration
        self.database.dialect = os.getenv('DB_DIALECT', 'sqlite')
        self.database.host = os.getenv('DB_HOST')
        self.database.port = int(os.getenv('DB_PORT', '1433'))
        self.database.username = os.getenv('DB_USERNAME')
        self.database.password = os.getenv('DB_PASSWORD')
        self.database.database = os.getenv('DB_NAME', 'flight_calculator')
        self.database.driver = os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')
        self.database.extra = os.getenv('DB_EXTRA')
    
    def update_from_dict(self, config_dict: dict):
        """Update configuration from dictionary"""
        if 'database' in config_dict:
            db_config = config_dict['database']
            for key, value in db_config.items():
                if hasattr(self.database, key):
                    setattr(self.database, key, value)

# Global config instance
config = Config()