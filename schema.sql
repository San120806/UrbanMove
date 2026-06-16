-- Create database if not exists (handled by docker, but safe fallback)
CREATE DATABASE IF NOT EXISTS urbanmove_db;
USE urbanmove_db;

-- --------------------------------------------------------
-- Table: drivers
-- --------------------------------------------------------
DROP TABLE IF EXISTS rides;
DROP TABLE IF EXISTS reports;
DROP TABLE IF EXISTS drivers;

CREATE TABLE drivers (
    driver_id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    city VARCHAR(50) NOT NULL,
    vehicle_type VARCHAR(50) NOT NULL,
    status ENUM('Active', 'Offline', 'Suspended') DEFAULT 'Offline',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- Table: rides
-- --------------------------------------------------------
CREATE TABLE rides (
    ride_id INT AUTO_INCREMENT PRIMARY KEY,
    driver_id INT NULL,
    pickup_location VARCHAR(100) NOT NULL,
    drop_location VARCHAR(100) NOT NULL,
    fare DECIMAL(10, 2) NOT NULL,
    status ENUM('Completed', 'Ongoing', 'Cancelled') DEFAULT 'Ongoing',
    ride_date DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_ride_driver FOREIGN KEY (driver_id) 
        REFERENCES drivers(driver_id) 
        ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

-- --------------------------------------------------------
-- Table: reports
-- --------------------------------------------------------
CREATE TABLE reports (
    report_id INT AUTO_INCREMENT PRIMARY KEY,
    report_name VARCHAR(100) NOT NULL,
    report_type VARCHAR(50) NOT NULL,
    generated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    file_path VARCHAR(255) NULL,
    records_count INT DEFAULT 0
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;


-- --------------------------------------------------------
-- Seeding Mock Data
-- --------------------------------------------------------

-- Seed drivers
INSERT INTO drivers (driver_id, name, city, vehicle_type, status) VALUES
(1, 'John Doe', 'Chicago', 'SUV', 'Active'),
(2, 'Jane Smith', 'New York', 'Sedan', 'Active'),
(3, 'Bob Johnson', 'San Francisco', 'Bike', 'Offline'),
(4, 'Alice Brown', 'Los Angeles', 'SUV-XL', 'Suspended'),
(5, 'David Wilson', 'Boston', 'Sedan', 'Active'),
(6, 'Sarah Miller', 'Seattle', 'Bike', 'Active'),
(7, 'James Taylor', 'New York', 'SUV', 'Offline'),
(8, 'Emily Davis', 'Chicago', 'Sedan', 'Active'),
(9, 'Michael Clark', 'San Francisco', 'SUV', 'Active'),
(10, 'Jessica White', 'Los Angeles', 'Sedan', 'Offline');

-- Seed rides (spread across early to mid June 2026 to populate charts nicely)
INSERT INTO rides (ride_id, driver_id, pickup_location, drop_location, fare, status, ride_date) VALUES
(1, 1, 'O Hare Airport', 'Downtown Chicago', 45.00, 'Completed', '2026-06-01 08:30:00'),
(2, 2, 'Times Square', 'JFK Airport', 65.50, 'Completed', '2026-06-01 10:15:00'),
(3, 3, 'Fishermans Wharf', 'Union Square', 12.00, 'Completed', '2026-06-02 14:00:00'),
(4, 5, 'Boston Common', 'Harvard Square', 22.50, 'Completed', '2026-06-03 09:45:00'),
(5, 6, 'Space Needle', 'Capitol Hill', 15.00, 'Cancelled', '2026-06-03 18:20:00'),
(6, 1, 'Navy Pier', 'Lincoln Park', 18.25, 'Completed', '2026-06-04 11:30:00'),
(7, 8, 'Wrigley Field', 'Loop', 25.00, 'Completed', '2026-06-05 19:10:00'),
(8, 2, 'Brooklyn Bridge', 'Manhattan', 35.00, 'Completed', '2026-06-06 08:00:00'),
(9, 9, 'Golden Gate Park', 'SOMA', 28.50, 'Completed', '2026-06-07 15:30:00'),
(10, 5, 'MIT Campus', 'Back Bay', 18.00, 'Completed', '2026-06-07 17:45:00'),
(11, 6, 'Pike Place Market', 'Ballard', 19.50, 'Completed', '2026-06-08 12:15:00'),
(12, 1, 'Downtown Chicago', 'O Hare Airport', 42.00, 'Completed', '2026-06-09 06:30:00'),
(13, 2, 'Central Park', 'Wall Street', 28.00, 'Completed', '2026-06-09 16:40:00'),
(14, 8, 'Loop', 'Hyde Park', 32.00, 'Completed', '2026-06-10 13:00:00'),
(15, 9, 'Mission District', 'Marina', 22.00, 'Cancelled', '2026-06-11 21:00:00'),
(16, 5, 'Logan Airport', 'Downtown Boston', 38.50, 'Completed', '2026-06-12 11:15:00'),
(17, 6, 'University District', 'Fremont', 14.00, 'Completed', '2026-06-13 15:50:00'),
(18, 9, 'SOMA', 'Oakland', 55.00, 'Completed', '2026-06-14 18:30:00'),
(19, 2, 'Times Square', 'LaGuardia Airport', 45.00, 'Ongoing', '2026-06-15 10:00:00'),
(20, 8, 'Navy Pier', 'O Hare Airport', 48.00, 'Ongoing', '2026-06-15 11:30:00'),
(21, 1, 'Loop', 'Wrigley Field', 24.50, 'Completed', '2026-06-16 09:00:00'),
(22, 6, 'Capitol Hill', 'South Lake Union', 11.50, 'Ongoing', '2026-06-16 11:45:00');

-- Seed reports
INSERT INTO reports (report_id, report_name, report_type, generated_at, file_path, records_count) VALUES
(1, 'System Boot Analytics', 'System', '2026-06-01 00:00:00', NULL, 0),
(2, 'Weekly Ops Audit - Week 22', 'Revenue', '2026-06-07 23:59:59', '/static/exports/weekly_ops_w22.csv', 10),
(3, 'Weekly Ops Audit - Week 23', 'Revenue', '2026-06-14 23:59:59', '/static/exports/weekly_ops_w23.csv', 8);
