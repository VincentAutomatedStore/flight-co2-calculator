-- SQLite Database Schema
-- Generated: 2025-11-15T11:48:26.078319
-- Database: flight_calculator.db

-- Table: airports
CREATE TABLE airports (
	id INTEGER NOT NULL, 
	iata_code VARCHAR(3) NOT NULL, 
	icao_code VARCHAR(4), 
	name VARCHAR(200) NOT NULL, 
	city VARCHAR(100) NOT NULL, 
	country VARCHAR(100) NOT NULL, 
	latitude FLOAT, 
	longitude FLOAT, 
	timezone VARCHAR(50), 
	search_field VARCHAR(300), 
	created_at DATETIME, 
	updated_at DATETIME, 
	PRIMARY KEY (id)
);

CREATE UNIQUE INDEX ix_airports_icao_code ON airports (icao_code);
CREATE UNIQUE INDEX ix_airports_iata_code ON airports (iata_code);

-- Table: flight_calculations
CREATE TABLE flight_calculations (
	id INTEGER NOT NULL, 
	departure_airport_id INTEGER NOT NULL, 
	destination_airport_id INTEGER NOT NULL, 
	passengers INTEGER NOT NULL, 
	round_trip BOOLEAN NOT NULL, 
	cabin_class VARCHAR(20) NOT NULL, 
	distance_km FLOAT NOT NULL, 
	distance_miles FLOAT NOT NULL, 
	fuel_burn_kg FLOAT NOT NULL, 
	total_co2_kg FLOAT NOT NULL, 
	co2_per_passenger_kg FLOAT NOT NULL, 
	co2_tonnes FLOAT NOT NULL, 
	calculation_method VARCHAR(50), 
	flight_info TEXT, 
	created_at DATETIME, 
	created_by VARCHAR(100), 
	PRIMARY KEY (id), 
	FOREIGN KEY(departure_airport_id) REFERENCES airports (id), 
	FOREIGN KEY(destination_airport_id) REFERENCES airports (id)
);


