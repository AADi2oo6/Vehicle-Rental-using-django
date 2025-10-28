-- CREATE DATABASE IF NOT EXISTS DBMS_CP;

-- 1. CUSTOMERS Table
CREATE TABLE CUSTOMERS (
    customer_id INT PRIMARY KEY AUTO_INCREMENT,
    first_name VARCHAR(50) NOT NULL,
    last_name VARCHAR(50) NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    phone VARCHAR(15) NOT NULL,
    address TEXT,
    city VARCHAR(50),
    state VARCHAR(50),
    zip_code VARCHAR(10),
    license_number VARCHAR(20) UNIQUE NOT NULL,
    date_of_birth DATE NOT NULL,
    registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    credit_score INT CHECK (credit_score >= 300 AND credit_score <= 850),
    profile_picture VARCHAR(255) DEFAULT 'none'
);


-- 2. VEHICLES Table
CREATE TABLE VEHICLES (
    vehicle_id INT PRIMARY KEY AUTO_INCREMENT,
    vehicle_number VARCHAR(20) UNIQUE NOT NULL,
    make VARCHAR(50) NOT NULL,
    model VARCHAR(50) NOT NULL,
    year INT NOT NULL CHECK (year >= 1980),
    color VARCHAR(30),
    vehicle_type ENUM('Car', 'SUV', 'Truck', 'Motorcycle', 'Van') NOT NULL,
    fuel_type ENUM('Petrol', 'Diesel', 'Electric', 'Hybrid') NOT NULL,
    seating_capacity INT NOT NULL,
    transmission ENUM('Manual', 'Automatic') NOT NULL,
    daily_rate DECIMAL(10,2) NOT NULL CHECK (daily_rate > 0),
    mileage DECIMAL(8,2),
    insurance_expiry DATE NOT NULL,
    last_service_date DATE,
    status ENUM('Available', 'Rented', 'Maintenance', 'Retired') DEFAULT 'Available',
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    vehicle_picture VARCHAR(255) DEFAULT 'none'

);

-- 3. RENTAL_BOOKINGS Table
CREATE TABLE RENTAL_BOOKINGS (
    booking_id INT PRIMARY KEY AUTO_INCREMENT,
    customer_id INT NOT NULL,
    vehicle_id INT NOT NULL,
    booking_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    pickup_date DATE NOT NULL,
    return_date DATE NOT NULL,
    actual_return_date DATE,
    pickup_location VARCHAR(100) NOT NULL,
    return_location VARCHAR(100) NOT NULL,
    total_days INT GENERATED ALWAYS AS (DATEDIFF(return_date, pickup_date)) STORED,
    daily_rate DECIMAL(10,2) NOT NULL,
    total_amount DECIMAL(12,2) NOT NULL,
    security_deposit DECIMAL(10,2) NOT NULL,
    booking_status ENUM('Confirmed', 'Active', 'Completed', 'Cancelled') DEFAULT 'Confirmed',
    special_requests TEXT,
    created_by VARCHAR(50) DEFAULT 'System',
    FOREIGN KEY (customer_id) REFERENCES CUSTOMERS(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (vehicle_id) REFERENCES VEHICLES(vehicle_id) ON DELETE CASCADE,
    CHECK (return_date > pickup_date),
    CHECK (total_amount > 0)
);

-- 4. PAYMENTS Table

CREATE TABLE PAYMENTS (
    payment_id INT PRIMARY KEY AUTO_INCREMENT,
    booking_id INT NOT NULL,
    customer_id INT NOT NULL,
    payment_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    amount DECIMAL(12,2) NOT NULL CHECK (amount > 0),
    payment_method ENUM('Cash', 'Credit Card', 'Debit Card', 'UPI', 'Net Banking') NOT NULL,
    payment_type ENUM('Advance', 'Full Payment', 'Security Deposit', 'Fine', 'Refund') NOT NULL,
    transaction_id VARCHAR(50) UNIQUE,
    payment_status ENUM('Pending', 'Completed', 'Failed', 'Refunded') DEFAULT 'Completed',
    reference_number VARCHAR(50),
    notes TEXT,
    processed_by VARCHAR(50) DEFAULT 'System',
    FOREIGN KEY (booking_id) REFERENCES RENTAL_BOOKINGS(booking_id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES CUSTOMERS(customer_id) ON DELETE CASCADE
);


-- 5. FEEDBACK_REVIEWS Table
CREATE TABLE FEEDBACK_REVIEWS (
    review_id INT PRIMARY KEY AUTO_INCREMENT,
    booking_id INT NOT NULL,
    customer_id INT NOT NULL,
    vehicle_id INT NOT NULL,
    rating INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    review_text TEXT,
    service_rating INT CHECK (service_rating >= 1 AND service_rating <= 5),
    vehicle_condition_rating INT CHECK (vehicle_condition_rating >= 1 AND vehicle_condition_rating <= 5),
    review_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_public BOOLEAN DEFAULT TRUE,
    response_from_admin TEXT,
    response_date TIMESTAMP NULL,
    FOREIGN KEY (booking_id) REFERENCES RENTAL_BOOKINGS(booking_id) ON DELETE CASCADE,
    FOREIGN KEY (customer_id) REFERENCES CUSTOMERS(customer_id) ON DELETE CASCADE,
    FOREIGN KEY (vehicle_id) REFERENCES VEHICLES(vehicle_id) ON DELETE CASCADE
);
-- 6. Core maintenance record table
CREATE TABLE MAINTENANCE_RECORDS (
    maintenance_id INT PRIMARY KEY AUTO_INCREMENT,
    vehicle_id INT NOT NULL,
    maintenance_date DATE NOT NULL,
    maintenance_type ENUM('Regular Service', 'Repair', 'Inspection', 'Cleaning', 'Tire Change') NOT NULL,
    description TEXT NOT NULL,
    service_provider VARCHAR(100),
    status ENUM('Scheduled', 'In Progress', 'Completed', 'Cancelled') DEFAULT 'Completed',
    created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (vehicle_id) REFERENCES VEHICLES(vehicle_id) ON DELETE CASCADE
);

-- 7. Crew-specific details (staff input)
CREATE TABLE MAINTENANCE_DETAILS (
    maintenance_id INT PRIMARY KEY,
    mileage_at_service DECIMAL(8,2),
    parts_replaced TEXT,
    cost DECIMAL(10,2) NOT NULL CHECK (cost >= 0),
    technician_name VARCHAR(50),
    FOREIGN KEY (maintenance_id) REFERENCES MAINTENANCE_RECORDS(maintenance_id) ON DELETE CASCADE
);

-- 8. Admin accounting table
CREATE TABLE MAINTENANCE_COSTS (
    maintenance_id INT PRIMARY KEY,
    cost DECIMAL(10,2) NOT NULL CHECK (cost >= 0),
    next_service_date DATE,
    FOREIGN KEY (maintenance_id) REFERENCES MAINTENANCE_RECORDS(maintenance_id) ON DELETE CASCADE
);
