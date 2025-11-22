-- =============================================
-- Flight CO2 Calculator Database Setup
-- =============================================

-- Create database
IF NOT EXISTS(SELECT name FROM sys.databases WHERE name = 'flight_calculator')
BEGIN
    CREATE DATABASE flight_calculator;
    PRINT '? Database "flight_calculator" created successfully';
END
ELSE
BEGIN
    PRINT '?? Database "flight_calculator" already exists';
END
GO

USE flight_calculator;
GO

-- =============================================
-- Create Tables
-- =============================================

-- Airports table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'airports')
BEGIN
    CREATE TABLE airports (
        id INT IDENTITY(1,1) PRIMARY KEY,
        iata_code NVARCHAR(3) NOT NULL,
        icao_code NVARCHAR(4) NULL,
        name NVARCHAR(200) NOT NULL,
        city NVARCHAR(100) NOT NULL,
        country NVARCHAR(100) NOT NULL,
        latitude FLOAT NULL,
        longitude FLOAT NULL,
        timezone NVARCHAR(50) NULL,
        search_field NVARCHAR(300) NULL,
        created_at DATETIME2 DEFAULT GETUTCDATE(),
        updated_at DATETIME2 DEFAULT GETUTCDATE()
    );
    
    PRINT '? Table "airports" created successfully';
END
ELSE
BEGIN
    PRINT '?? Table "airports" already exists';
END
GO

-- Flight calculations table
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'flight_calculations')
BEGIN
    CREATE TABLE flight_calculations (
        id INT IDENTITY(1,1) PRIMARY KEY,
        departure_airport_id INT NOT NULL,
        destination_airport_id INT NOT NULL,
        passengers INT NOT NULL DEFAULT 1,
        round_trip BIT NOT NULL DEFAULT 0,
        cabin_class NVARCHAR(20) NOT NULL DEFAULT 'economy',
        distance_km FLOAT NOT NULL,
        distance_miles FLOAT NOT NULL,
        fuel_burn_kg FLOAT NOT NULL,
        total_co2_kg FLOAT NOT NULL,
        co2_per_passenger_kg FLOAT NOT NULL,
        co2_tonnes FLOAT NOT NULL,
        calculation_method NVARCHAR(50) DEFAULT 'ICAO',
        flight_info NVARCHAR(MAX) NULL,
        created_at DATETIME2 DEFAULT GETUTCDATE(),
        created_by NVARCHAR(100) NULL
    );
    
    PRINT '? Table "flight_calculations" created successfully';
END
ELSE
BEGIN
    PRINT '?? Table "flight_calculations" already exists';
END
GO

-- =============================================
-- Create Indexes and Constraints
-- =============================================

-- Indexes for airports table
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_airports_iata_code')
    CREATE UNIQUE INDEX IX_airports_iata_code ON airports(iata_code);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_airports_icao_code')
    CREATE INDEX IX_airports_icao_code ON airports(icao_code);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_airports_search_field')
    CREATE INDEX IX_airports_search_field ON airports(search_field);

-- Indexes for flight_calculations table
IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_flight_calculations_departure_id')
    CREATE INDEX IX_flight_calculations_departure_id ON flight_calculations(departure_airport_id);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_flight_calculations_destination_id')
    CREATE INDEX IX_flight_calculations_destination_id ON flight_calculations(destination_airport_id);

IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'IX_flight_calculations_created_at')
    CREATE INDEX IX_flight_calculations_created_at ON flight_calculations(created_at);

-- Foreign key constraints
IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_flight_calculations_departure_airport')
    ALTER TABLE flight_calculations 
    ADD CONSTRAINT FK_flight_calculations_departure_airport 
    FOREIGN KEY (departure_airport_id) REFERENCES airports(id);

IF NOT EXISTS (SELECT * FROM sys.foreign_keys WHERE name = 'FK_flight_calculations_destination_airport')
    ALTER TABLE flight_calculations 
    ADD CONSTRAINT FK_flight_calculations_destination_airport 
    FOREIGN KEY (destination_airport_id) REFERENCES airports(id);

PRINT '? Indexes and constraints created successfully';
GO

-- =============================================
-- Create Sample Data
-- =============================================

-- Insert sample airports
IF NOT EXISTS (SELECT 1 FROM airports WHERE iata_code = 'JFK')
BEGIN
    INSERT INTO airports (iata_code, icao_code, name, city, country, latitude, longitude, timezone, search_field)
    VALUES
        ('JFK', 'KJFK', 'John F Kennedy International Airport', 'New York', 'USA', 40.6398, -73.7789, 'America/New_York', 'New York, USA (JFK)'),
        ('LHR', 'EGLL', 'Heathrow Airport', 'London', 'UK', 51.4700, -0.4543, 'Europe/London', 'London, UK (LHR)'),
        ('LAX', 'KLAX', 'Los Angeles International Airport', 'Los Angeles', 'USA', 33.9416, -118.4085, 'America/Los_Angeles', 'Los Angeles, USA (LAX)'),
        ('NRT', 'RJAA', 'Narita International Airport', 'Tokyo', 'Japan', 35.7647, 140.3864, 'Asia/Tokyo', 'Tokyo, Japan (NRT)'),
        ('CPH', 'EKCH', 'Copenhagen Airport', 'Copenhagen', 'Denmark', 55.6180, 12.6561, 'Europe/Copenhagen', 'Copenhagen, Denmark (CPH)'),
        ('AAL', 'EKYT', 'Aalborg Airport', 'Aalborg', 'Denmark', 57.0928, 9.8492, 'Europe/Copenhagen', 'Aalborg, Denmark (AAL)'),
        ('SFO', 'KSFO', 'San Francisco International Airport', 'San Francisco', 'USA', 37.6190, -122.3748, 'America/Los_Angeles', 'San Francisco, USA (SFO)'),
        ('DXB', 'OMDB', 'Dubai International Airport', 'Dubai', 'UAE', 25.2532, 55.3657, 'Asia/Dubai', 'Dubai, UAE (DXB)'),
        ('CDG', 'LFPG', 'Charles de Gaulle Airport', 'Paris', 'France', 49.0097, 2.5479, 'Europe/Paris', 'Paris, France (CDG)'),
        ('AAD', 'HCAD', 'Adado Airport', 'Adado', 'Somalia', 6.0969, 46.6389, 'Africa/Mogadishu', 'Adado, Somalia (AAD)'),
        ('AAE', 'DABB', 'Rabah Bitat Airport', 'Annaba', 'Algeria', 36.8222, 7.8092, 'Africa/Algiers', 'Annaba, Algeria (AAE)');
    
    PRINT '? Sample airports inserted successfully';
END
ELSE
BEGIN
    PRINT '?? Sample airports already exist';
END
GO

-- =============================================
-- Create Useful Views
-- =============================================

-- View for flight calculations with airport details
IF NOT EXISTS (SELECT * FROM sys.views WHERE name = 'vw_flight_calculations')
BEGIN
    EXEC('CREATE VIEW vw_flight_calculations AS
        SELECT 
            fc.id,
            fc.passengers,
            fc.round_trip,
            fc.cabin_class,
            fc.distance_km,
            fc.distance_miles,
            fc.fuel_burn_kg,
            fc.total_co2_kg,
            fc.co2_per_passenger_kg,
            fc.co2_tonnes,
            fc.calculation_method,
            fc.flight_info,
            fc.created_at,
            fc.created_by,
            
            -- Departure airport details
            dep.iata_code as departure_iata,
            dep.icao_code as departure_icao, 
            dep.name as departure_name,
            dep.city as departure_city,
            dep.country as departure_country,
            dep.search_field as departure_search,
            
            -- Destination airport details
            dest.iata_code as destination_iata,
            dest.icao_code as destination_icao,
            dest.name as destination_name, 
            dest.city as destination_city,
            dest.country as destination_country,
            dest.search_field as destination_search
            
        FROM flight_calculations fc
        INNER JOIN airports dep ON fc.departure_airport_id = dep.id
        INNER JOIN airports dest ON fc.destination_airport_id = dest.id');
    
    PRINT '? View "vw_flight_calculations" created successfully';
END
ELSE
BEGIN
    PRINT '?? View "vw_flight_calculations" already exists';
END
GO

-- =============================================
-- Create Stored Procedures
-- =============================================

-- Stored procedure to add a new flight calculation
IF NOT EXISTS (SELECT * FROM sys.procedures WHERE name = 'sp_add_flight_calculation')
BEGIN
    EXEC('CREATE PROCEDURE sp_add_flight_calculation
        @departure_iata NVARCHAR(3),
        @destination_iata NVARCHAR(3),
        @passengers INT = 1,
        @round_trip BIT = 0,
        @cabin_class NVARCHAR(20) = ''economy'',
        @distance_km FLOAT,
        @distance_miles FLOAT,
        @fuel_burn_kg FLOAT,
        @total_co2_kg FLOAT,
        @co2_per_passenger_kg FLOAT,
        @co2_tonnes FLOAT,
        @calculation_method NVARCHAR(50) = ''ICAO'',
        @flight_info NVARCHAR(MAX) = NULL,
        @created_by NVARCHAR(100) = NULL
    AS
    BEGIN
        DECLARE @departure_id INT, @destination_id INT;
        
        -- Get airport IDs
        SELECT @departure_id = id FROM airports WHERE iata_code = @departure_iata;
        SELECT @destination_id = id FROM airports WHERE iata_code = @destination_iata;
        
        IF @departure_id IS NULL OR @destination_id IS NULL
        BEGIN
            RAISERROR(''Invalid airport codes provided'', 16, 1);
            RETURN;
        END
        
        INSERT INTO flight_calculations (
            departure_airport_id, destination_airport_id, passengers, round_trip, cabin_class,
            distance_km, distance_miles, fuel_burn_kg, total_co2_kg, co2_per_passenger_kg, co2_tonnes,
            calculation_method, flight_info, created_by
        )
        VALUES (
            @departure_id, @destination_id, @passengers, @round_trip, @cabin_class,
            @distance_km, @distance_miles, @fuel_burn_kg, @total_co2_kg, @co2_per_passenger_kg, @co2_tonnes,
            @calculation_method, @flight_info, @created_by
        );
        
        SELECT SCOPE_IDENTITY() as new_calculation_id;
    END');
    
    PRINT '? Stored procedure "sp_add_flight_calculation" created successfully';
END
ELSE
BEGIN
    PRINT '?? Stored procedure "sp_add_flight_calculation" already exists';
END
GO

-- =============================================
-- Database Summary
-- =============================================

PRINT '=============================================';
PRINT 'Flight Calculator Database Setup Complete';
PRINT '=============================================';
PRINT 'Tables created:';
PRINT '  - airports (stores airport information)';
PRINT '  - flight_calculations (stores emission calculations)';
PRINT '';
PRINT 'Sample data: 11 airports inserted';
PRINT 'Views: vw_flight_calculations (joined view)';
PRINT 'Stored procedures: sp_add_flight_calculation';
PRINT '';
PRINT 'Ready to use! ??';
GO