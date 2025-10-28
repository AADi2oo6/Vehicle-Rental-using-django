# Car Rental System - Fixed Data Insertion Script for MySQL
import mysql.connector
from datetime import datetime, date, timedelta
import random

# Database connection configuration
DB_CONFIG = {
    'host': 'localhost',
    'database': 'cp',
    'user': 'root',
    'password': 'vedantiasatkar1523@'
}

# Customer Data (20 customers from various Indian cities)
customers_data = [
    {
        'first_name': 'Arjun', 'last_name': 'Sharma', 'email': 'arjun.sharma@gmail.com',
        'phone': '+91-9876543210', 'address': '123 MG Road', 'city': 'Mumbai',
        'state': 'Maharashtra', 'zip_code': '400001', 'license_number': 'MH1220190123456',
        'date_of_birth': '1990-05-15', 'credit_score': 750
    },
    {
        'first_name': 'Priya', 'last_name': 'Singh', 'email': 'priya.singh@yahoo.com',
        'phone': '+91-9876543211', 'address': '45 Connaught Place', 'city': 'New Delhi',
        'state': 'Delhi', 'zip_code': '110001', 'license_number': 'DL1120190234567',
        'date_of_birth': '1985-08-22', 'credit_score': 680
    },
    {
        'first_name': 'Rajesh', 'last_name': 'Kumar', 'email': 'rajesh.kumar@hotmail.com',
        'phone': '+91-9876543212', 'address': '78 Brigade Road', 'city': 'Bangalore',
        'state': 'Karnataka', 'zip_code': '560001', 'license_number': 'KA0320190345678',
        'date_of_birth': '1988-12-10', 'credit_score': 720
    },
    {
        'first_name': 'Sneha', 'last_name': 'Patel', 'email': 'sneha.patel@gmail.com',
        'phone': '+91-9876543213', 'address': '12 Law Garden', 'city': 'Ahmedabad',
        'state': 'Gujarat', 'zip_code': '380009', 'license_number': 'GJ0120190456789',
        'date_of_birth': '1992-03-18', 'credit_score': 690
    },
    {
        'first_name': 'Vikram', 'last_name': 'Reddy', 'email': 'vikram.reddy@outlook.com',
        'phone': '+91-9876543214', 'address': '34 Banjara Hills', 'city': 'Hyderabad',
        'state': 'Telangana', 'zip_code': '500034', 'license_number': 'TS0720190567890',
        'date_of_birth': '1987-11-25', 'credit_score': 760
    },
    {
        'first_name': 'Ananya', 'last_name': 'Nair', 'email': 'ananya.nair@gmail.com',
        'phone': '+91-9876543215', 'address': '56 Marine Drive', 'city': 'Kochi',
        'state': 'Kerala', 'zip_code': '682001', 'license_number': 'KL0720190678901',
        'date_of_birth': '1991-07-14', 'credit_score': 710
    },
    {
        'first_name': 'Rohit', 'last_name': 'Gupta', 'email': 'rohit.gupta@yahoo.com',
        'phone': '+91-9876543216', 'address': '89 Park Street', 'city': 'Kolkata',
        'state': 'West Bengal', 'zip_code': '700016', 'license_number': 'WB0220190789012',
        'date_of_birth': '1989-01-30', 'credit_score': 640
    },
    {
        'first_name': 'Kavya', 'last_name': 'Iyer', 'email': 'kavya.iyer@gmail.com',
        'phone': '+91-9876543217', 'address': '23 T Nagar', 'city': 'Chennai',
        'state': 'Tamil Nadu', 'zip_code': '600017', 'license_number': 'TN0320190890123',
        'date_of_birth': '1993-09-08', 'credit_score': 700
    },
    {
        'first_name': 'Amit', 'last_name': 'Joshi', 'email': 'amit.joshi@hotmail.com',
        'phone': '+91-9876543218', 'address': '67 Civil Lines', 'city': 'Pune',
        'state': 'Maharashtra', 'zip_code': '411001', 'license_number': 'MH1420190901234',
        'date_of_birth': '1986-04-12', 'credit_score': 780
    },
    {
        'first_name': 'Ritu', 'last_name': 'Agarwal', 'email': 'ritu.agarwal@gmail.com',
        'phone': '+91-9876543219', 'address': '90 Pink City', 'city': 'Jaipur',
        'state': 'Rajasthan', 'zip_code': '302001', 'license_number': 'RJ1420191012345',
        'date_of_birth': '1994-06-20', 'credit_score': 660
    },
    {
        'first_name': 'Sanjay', 'last_name': 'Verma', 'email': 'sanjay.verma@outlook.com',
        'phone': '+91-9876543220', 'address': '45 Hazratganj', 'city': 'Lucknow',
        'state': 'Uttar Pradesh', 'zip_code': '226001', 'license_number': 'UP3220191123456',
        'date_of_birth': '1983-10-05', 'credit_score': 720
    },
    {
        'first_name': 'Meera', 'last_name': 'Chopra', 'email': 'meera.chopra@gmail.com',
        'phone': '+91-9876543221', 'address': '78 Sector 17', 'city': 'Chandigarh',
        'state': 'Chandigarh', 'zip_code': '160017', 'license_number': 'CH0120191234567',
        'date_of_birth': '1990-12-28', 'credit_score': 690
    },
    {
        'first_name': 'Deepak', 'last_name': 'Thakur', 'email': 'deepak.thakur@yahoo.com',
        'phone': '+91-9876543222', 'address': '12 Mall Road', 'city': 'Shimla',
        'state': 'Himachal Pradesh', 'zip_code': '171001', 'license_number': 'HP0220191345678',
        'date_of_birth': '1987-02-14', 'credit_score': 740
    },
    {
        'first_name': 'Pooja', 'last_name': 'Rao', 'email': 'pooja.rao@gmail.com',
        'phone': '+91-9876543223', 'address': '34 Koregaon Park', 'city': 'Pune',
        'state': 'Maharashtra', 'zip_code': '411001', 'license_number': 'MH1420191456789',
        'date_of_birth': '1991-11-16', 'credit_score': 670
    },
    {
        'first_name': 'Arun', 'last_name': 'Menon', 'email': 'arun.menon@hotmail.com',
        'phone': '+91-9876543224', 'address': '56 Thiruvananthapuram', 'city': 'Trivandrum',
        'state': 'Kerala', 'zip_code': '695001', 'license_number': 'KL1420191567890',
        'date_of_birth': '1985-08-03', 'credit_score': 710
    },
    {
        'first_name': 'Sunita', 'last_name': 'Bansal', 'email': 'sunita.bansal@outlook.com',
        'phone': '+91-9876543225', 'address': '89 CP', 'city': 'New Delhi',
        'state': 'Delhi', 'zip_code': '110001', 'license_number': 'DL1120191678901',
        'date_of_birth': '1989-05-27', 'credit_score': 650
    },
    {
        'first_name': 'Kiran', 'last_name': 'Desai', 'email': 'kiran.desai@gmail.com',
        'phone': '+91-9876543226', 'address': '23 Navrangpura', 'city': 'Ahmedabad',
        'state': 'Gujarat', 'zip_code': '380009', 'license_number': 'GJ0120191789012',
        'date_of_birth': '1992-01-11', 'credit_score': 680
    },
    {
        'first_name': 'Ravi', 'last_name': 'Chandra', 'email': 'ravi.chandra@yahoo.com',
        'phone': '+91-9876543227', 'address': '67 Jubilee Hills', 'city': 'Hyderabad',
        'state': 'Telangana', 'zip_code': '500033', 'license_number': 'TS0720191890123',
        'date_of_birth': '1988-07-19', 'credit_score': 730
    },
    {
        'first_name': 'Nisha', 'last_name': 'Sinha', 'email': 'nisha.sinha@gmail.com',
        'phone': '+91-9876543228', 'address': '90 Salt Lake', 'city': 'Kolkata',
        'state': 'West Bengal', 'zip_code': '700064', 'license_number': 'WB0220191901234',
        'date_of_birth': '1993-04-23', 'credit_score': 690
    },
    {
        'first_name': 'Manish', 'last_name': 'Jain', 'email': 'manish.jain@hotmail.com',
        'phone': '+91-9876543229', 'address': '45 Anna Nagar', 'city': 'Chennai',
        'state': 'Tamil Nadu', 'zip_code': '600040', 'license_number': 'TN0320192012345',
        'date_of_birth': '1986-09-15', 'credit_score': 750
    }
]

# Vehicle Data (15 vehicles with Indian popular car models)
vehicles_data = [
    {
        'vehicle_number': 'MH12AB1234', 'make': 'Maruti Suzuki', 'model': 'Swift',
        'year': 2021, 'color': 'White', 'vehicle_type': 'Car', 'fuel_type': 'Petrol',
        'seating_capacity': 5, 'transmission': 'Manual', 'daily_rate': 1200.00,
        'mileage': 18.50, 'insurance_expiry': '2025-12-31', 'last_service_date': '2024-10-15'
    },
    {
        'vehicle_number': 'DL8CAB5678', 'make': 'Hyundai', 'model': 'Creta',
        'year': 2022, 'color': 'Silver', 'vehicle_type': 'SUV', 'fuel_type': 'Diesel',
        'seating_capacity': 7, 'transmission': 'Automatic', 'daily_rate': 2500.00,
        'mileage': 16.80, 'insurance_expiry': '2025-11-20', 'last_service_date': '2024-11-01'
    },
    {
        'vehicle_number': 'KA03CD9012', 'make': 'Tata', 'model': 'Nexon',
        'year': 2023, 'color': 'Blue', 'vehicle_type': 'SUV', 'fuel_type': 'Electric',
        'seating_capacity': 5, 'transmission': 'Automatic', 'daily_rate': 2200.00,
        'mileage': 312.00, 'insurance_expiry': '2026-03-15', 'last_service_date': '2024-09-20'
    },
    {
        'vehicle_number': 'GJ01EF3456', 'make': 'Honda', 'model': 'City',
        'year': 2021, 'color': 'Red', 'vehicle_type': 'Car', 'fuel_type': 'Petrol',
        'seating_capacity': 5, 'transmission': 'Automatic', 'daily_rate': 1800.00,
        'mileage': 17.80, 'insurance_expiry': '2025-08-10', 'last_service_date': '2024-10-30'
    },
    {
        'vehicle_number': 'TS07GH7890', 'make': 'Toyota', 'model': 'Innova Crysta',
        'year': 2020, 'color': 'Grey', 'vehicle_type': 'SUV', 'fuel_type': 'Diesel',
        'seating_capacity': 8, 'transmission': 'Manual', 'daily_rate': 3000.00,
        'mileage': 15.60, 'insurance_expiry': '2025-07-25', 'last_service_date': '2024-11-05'
    },
    {
        'vehicle_number': 'KL07IJ1234', 'make': 'Mahindra', 'model': 'XUV300',
        'year': 2022, 'color': 'Black', 'vehicle_type': 'SUV', 'fuel_type': 'Diesel',
        'seating_capacity': 5, 'transmission': 'Manual', 'daily_rate': 2000.00,
        'mileage': 20.00, 'insurance_expiry': '2026-01-18', 'last_service_date': '2024-10-12'
    },
    {
        'vehicle_number': 'WB02KL5678', 'make': 'Maruti Suzuki', 'model': 'Alto K10',
        'year': 2023, 'color': 'Yellow', 'vehicle_type': 'Car', 'fuel_type': 'Petrol',
        'seating_capacity': 5, 'transmission': 'Manual', 'daily_rate': 1000.00,
        'mileage': 24.70, 'insurance_expiry': '2026-04-20', 'last_service_date': '2024-09-15'
    },
    {
        'vehicle_number': 'TN03MN9012', 'make': 'Hyundai', 'model': 'Verna',
        'year': 2021, 'color': 'White', 'vehicle_type': 'Car', 'fuel_type': 'Petrol',
        'seating_capacity': 5, 'transmission': 'Automatic', 'daily_rate': 1900.00,
        'mileage': 18.45, 'insurance_expiry': '2025-09-30', 'last_service_date': '2024-10-25'
    },
    {
        'vehicle_number': 'MH14OP3456', 'make': 'Kia', 'model': 'Seltos',
        'year': 2022, 'color': 'Orange', 'vehicle_type': 'SUV', 'fuel_type': 'Petrol',
        'seating_capacity': 5, 'transmission': 'Automatic', 'daily_rate': 2300.00,
        'mileage': 16.80, 'insurance_expiry': '2025-12-05', 'last_service_date': '2024-11-10'
    },
    {
        'vehicle_number': 'RJ14QR7890', 'make': 'Maruti Suzuki', 'model': 'Ertiga',
        'year': 2020, 'color': 'Silver', 'vehicle_type': 'Van', 'fuel_type': 'Petrol',
        'seating_capacity': 7, 'transmission': 'Manual', 'daily_rate': 2100.00,
        'mileage': 19.34, 'insurance_expiry': '2025-06-15', 'last_service_date': '2024-10-20'
    },
    {
        'vehicle_number': 'UP32ST1234', 'make': 'Honda', 'model': 'Amaze',
        'year': 2023, 'color': 'Blue', 'vehicle_type': 'Car', 'fuel_type': 'Petrol',
        'seating_capacity': 5, 'transmission': 'Manual', 'daily_rate': 1500.00,
        'mileage': 19.50, 'insurance_expiry': '2026-02-28', 'last_service_date': '2024-09-30'
    },
    {
        'vehicle_number': 'CH01UV5678', 'make': 'Bajaj', 'model': 'Pulsar NS200',
        'year': 2022, 'color': 'Black', 'vehicle_type': 'Motorcycle', 'fuel_type': 'Petrol',
        'seating_capacity': 2, 'transmission': 'Manual', 'daily_rate': 500.00,
        'mileage': 35.00, 'insurance_expiry': '2025-10-12', 'last_service_date': '2024-11-01'
    },
    {
        'vehicle_number': 'HP02WX9012', 'make': 'Royal Enfield', 'model': 'Classic 350',
        'year': 2021, 'color': 'Green', 'vehicle_type': 'Motorcycle', 'fuel_type': 'Petrol',
        'seating_capacity': 2, 'transmission': 'Manual', 'daily_rate': 800.00,
        'mileage': 40.00, 'insurance_expiry': '2025-05-18', 'last_service_date': '2024-10-08'
    },
    {
        'vehicle_number': 'MH14YZ3456', 'make': 'Tata', 'model': 'Harrier',
        'year': 2023, 'color': 'Red', 'vehicle_type': 'SUV', 'fuel_type': 'Diesel',
        'seating_capacity': 5, 'transmission': 'Automatic', 'daily_rate': 2800.00,
        'mileage': 16.35, 'insurance_expiry': '2026-01-10', 'last_service_date': '2024-11-12'
    },
    {
        'vehicle_number': 'KL14AB7890', 'make': 'Force', 'model': 'Traveller',
        'year': 2020, 'color': 'White', 'vehicle_type': 'Van', 'fuel_type': 'Diesel',
        'seating_capacity': 12, 'transmission': 'Manual', 'daily_rate': 3500.00,
        'mileage': 12.50, 'insurance_expiry': '2025-08-20', 'last_service_date': '2024-10-18'
    }
]

# Rental Booking Data (15 bookings)
rental_bookings_data = [
    {
        'customer_id': 1, 'vehicle_id': 1, 'pickup_date': '2024-11-01', 'return_date': '2024-11-05',
        'actual_return_date': '2024-11-05', 'pickup_location': 'Mumbai Airport',
        'return_location': 'Mumbai Airport', 'daily_rate': 1200.00, 'total_amount': 4800.00,
        'security_deposit': 5000.00, 'booking_status': 'Completed'
    },
    {
        'customer_id': 2, 'vehicle_id': 2, 'pickup_date': '2024-11-10', 'return_date': '2024-11-15',
        'pickup_location': 'New Delhi Railway Station', 'return_location': 'IGI Airport Delhi',
        'daily_rate': 2500.00, 'total_amount': 12500.00, 'security_deposit': 10000.00,
        'booking_status': 'Active'
    },
    {
        'customer_id': 3, 'vehicle_id': 3, 'pickup_date': '2024-11-20', 'return_date': '2024-11-25',
        'pickup_location': 'Bangalore City Center', 'return_location': 'Bangalore City Center',
        'daily_rate': 2200.00, 'total_amount': 11000.00, 'security_deposit': 8000.00,
        'booking_status': 'Confirmed'
    },
    {
        'customer_id': 4, 'vehicle_id': 4, 'pickup_date': '2024-10-15', 'return_date': '2024-10-18',
        'actual_return_date': '2024-10-18', 'pickup_location': 'Ahmedabad Central',
        'return_location': 'Ahmedabad Central', 'daily_rate': 1800.00, 'total_amount': 5400.00,
        'security_deposit': 6000.00, 'booking_status': 'Completed'
    },
    {
        'customer_id': 5, 'vehicle_id': 5, 'pickup_date': '2024-11-12', 'return_date': '2024-11-17',
        'pickup_location': 'Hyderabad Airport', 'return_location': 'Hyderabad Airport',
        'daily_rate': 3000.00, 'total_amount': 15000.00, 'security_deposit': 12000.00,
        'booking_status': 'Active'
    },
    {
        'customer_id': 6, 'vehicle_id': 6, 'pickup_date': '2024-09-20', 'return_date': '2024-09-23',
        'actual_return_date': '2024-09-24', 'pickup_location': 'Kochi Marine Drive',
        'return_location': 'Kochi Marine Drive', 'daily_rate': 2000.00, 'total_amount': 8000.00,
        'security_deposit': 7000.00, 'booking_status': 'Completed'
    },
    {
        'customer_id': 7, 'vehicle_id': 7, 'pickup_date': '2024-11-08', 'return_date': '2024-11-12',
        'pickup_location': 'Kolkata Howrah', 'return_location': 'Kolkata Howrah',
        'daily_rate': 1000.00, 'total_amount': 4000.00, 'security_deposit': 3000.00,
        'booking_status': 'Active'
    },
    {
        'customer_id': 8, 'vehicle_id': 8, 'pickup_date': '2024-11-25', 'return_date': '2024-11-30',
        'pickup_location': 'Chennai Central Station', 'return_location': 'Chennai Airport',
        'daily_rate': 1900.00, 'total_amount': 9500.00, 'security_deposit': 8000.00,
        'booking_status': 'Confirmed'
    },
    {
        'customer_id': 9, 'vehicle_id': 9, 'pickup_date': '2024-10-01', 'return_date': '2024-10-07',
        'actual_return_date': '2024-10-07', 'pickup_location': 'Pune Station',
        'return_location': 'Pune Airport', 'daily_rate': 2300.00, 'total_amount': 13800.00,
        'security_deposit': 10000.00, 'booking_status': 'Completed'
    },
    {
        'customer_id': 10, 'vehicle_id': 10, 'pickup_date': '2024-11-15', 'return_date': '2024-11-20',
        'pickup_location': 'Jaipur City Palace', 'return_location': 'Jaipur Airport',
        'daily_rate': 2100.00, 'total_amount': 10500.00, 'security_deposit': 8000.00,
        'booking_status': 'Confirmed'
    },
    {
        'customer_id': 11, 'vehicle_id': 11, 'pickup_date': '2024-08-15', 'return_date': '2024-08-18',
        'actual_return_date': '2024-08-18', 'pickup_location': 'Lucknow Charbagh',
        'return_location': 'Lucknow Charbagh', 'daily_rate': 1500.00, 'total_amount': 4500.00,
        'security_deposit': 5000.00, 'booking_status': 'Completed'
    },
    {
        'customer_id': 12, 'vehicle_id': 12, 'pickup_date': '2024-11-05', 'return_date': '2024-11-08',
        'pickup_location': 'Chandigarh Sector 17', 'return_location': 'Chandigarh Airport',
        'daily_rate': 500.00, 'total_amount': 1500.00, 'security_deposit': 2000.00,
        'booking_status': 'Active'
    },
    {
        'customer_id': 13, 'vehicle_id': 13, 'pickup_date': '2024-07-10', 'return_date': '2024-07-15',
        'actual_return_date': '2024-07-15', 'pickup_location': 'Shimla Mall Road',
        'return_location': 'Shimla Mall Road', 'daily_rate': 800.00, 'total_amount': 4000.00,
        'security_deposit': 3000.00, 'booking_status': 'Completed'
    },
    {
        'customer_id': 14, 'vehicle_id': 14, 'pickup_date': '2024-11-18', 'return_date': '2024-11-22',
        'pickup_location': 'Pune Koregaon Park', 'return_location': 'Mumbai Airport',
        'daily_rate': 2800.00, 'total_amount': 11200.00, 'security_deposit': 12000.00,
        'booking_status': 'Confirmed'
    },
    {
        'customer_id': 15, 'vehicle_id': 15, 'pickup_date': '2024-09-01', 'return_date': '2024-09-05',
        'actual_return_date': '2024-09-05', 'pickup_location': 'Trivandrum Central',
        'return_location': 'Kochi Airport', 'daily_rate': 3500.00, 'total_amount': 14000.00,
        'security_deposit': 15000.00, 'booking_status': 'Completed'
    }
]

# Payment Data (20 payments)
payments_data = [
    {'booking_id': 1, 'customer_id': 1, 'amount': 2400.00, 'payment_method': 'UPI', 'payment_type': 'Advance', 'transaction_id': 'UPI2024110112345', 'reference_number': 'REF001'},
    {'booking_id': 1, 'customer_id': 1, 'amount': 2400.00, 'payment_method': 'Credit Card', 'payment_type': 'Full Payment', 'transaction_id': 'CC2024110512346', 'reference_number': 'REF002'},
    {'booking_id': 1, 'customer_id': 1, 'amount': 5000.00, 'payment_method': 'Credit Card', 'payment_type': 'Security Deposit', 'transaction_id': 'CC2024110512347', 'reference_number': 'REF003'},
    {'booking_id': 4, 'customer_id': 4, 'amount': 5400.00, 'payment_method': 'UPI', 'payment_type': 'Full Payment', 'transaction_id': 'UPI2024101512352', 'reference_number': 'REF008'},
    {'booking_id': 6, 'customer_id': 6, 'amount': 8000.00, 'payment_method': 'Net Banking', 'payment_type': 'Full Payment', 'transaction_id': 'NB2024092012356', 'reference_number': 'REF012'},
    {'booking_id': 9, 'customer_id': 9, 'amount': 13800.00, 'payment_method': 'Net Banking', 'payment_type': 'Full Payment', 'transaction_id': 'NB2024100112362', 'reference_number': 'REF018'},
    {'booking_id': 11, 'customer_id': 11, 'amount': 4500.00, 'payment_method': 'Cash', 'payment_type': 'Full Payment', 'transaction_id': None, 'reference_number': 'CASH001'},
    {'booking_id': 13, 'customer_id': 13, 'amount': 4000.00, 'payment_method': 'Debit Card', 'payment_type': 'Full Payment', 'transaction_id': 'DC2024071012368', 'reference_number': 'REF024'},
    {'booking_id': 15, 'customer_id': 15, 'amount': 14000.00, 'payment_method': 'Net Banking', 'payment_type': 'Full Payment', 'transaction_id': 'NB2024090112372', 'reference_number': 'REF028'},
    {'booking_id': 2, 'customer_id': 2, 'amount': 6250.00, 'payment_method': 'Net Banking', 'payment_type': 'Advance', 'transaction_id': 'NB2024111012348', 'reference_number': 'REF004'},
    {'booking_id': 3, 'customer_id': 3, 'amount': 5500.00, 'payment_method': 'UPI', 'payment_type': 'Advance', 'transaction_id': 'UPI2024112012350', 'reference_number': 'REF006'},
    {'booking_id': 5, 'customer_id': 5, 'amount': 7500.00, 'payment_method': 'Credit Card', 'payment_type': 'Advance', 'transaction_id': 'CC2024111212354', 'reference_number': 'REF010'},
    {'booking_id': 7, 'customer_id': 7, 'amount': 2000.00, 'payment_method': 'UPI', 'payment_type': 'Advance', 'transaction_id': 'UPI2024110812358', 'reference_number': 'REF014'},
    {'booking_id': 8, 'customer_id': 8, 'amount': 4750.00, 'payment_method': 'Credit Card', 'payment_type': 'Advance', 'transaction_id': 'CC2024112512360', 'reference_number': 'REF016'},
    {'booking_id': 10, 'customer_id': 10, 'amount': 5250.00, 'payment_method': 'UPI', 'payment_type': 'Advance', 'transaction_id': 'UPI2024111512364', 'reference_number': 'REF020'},
    {'booking_id': 12, 'customer_id': 12, 'amount': 750.00, 'payment_method': 'UPI', 'payment_type': 'Advance', 'transaction_id': 'UPI2024110512366', 'reference_number': 'REF022'},
    {'booking_id': 14, 'customer_id': 14, 'amount': 5600.00, 'payment_method': 'Credit Card', 'payment_type': 'Advance', 'transaction_id': 'CC2024111812370', 'reference_number': 'REF026'},
    {'booking_id': 6, 'customer_id': 6, 'amount': 2000.00, 'payment_method': 'Cash', 'payment_type': 'Fine', 'transaction_id': None, 'reference_number': 'FINE001'}
]

# Maintenance Records Data (15 records)
maintenance_records_data = [
    {'maintenance_id': 1, 'vehicle_id': 1, 'maintenance_date': '2024-10-15', 'maintenance_type': 'Regular Service', 'description': 'Engine oil change, air filter replacement, brake inspection', 'service_provider': 'Maruti Service Center Mumbai', 'status': 'Completed'},
    {'maintenance_id': 2, 'vehicle_id': 2, 'maintenance_date': '2024-11-01', 'maintenance_type': 'Regular Service', 'description': 'Full service including engine, transmission, and brake system check', 'service_provider': 'Hyundai Service Delhi', 'status': 'Completed'},
    {'maintenance_id': 3, 'vehicle_id': 3, 'maintenance_date': '2024-09-20', 'maintenance_type': 'Inspection', 'description': 'Electric vehicle battery health check and software update', 'service_provider': 'Tata Motors Bangalore', 'status': 'Completed'},
    {'maintenance_id': 4, 'vehicle_id': 4, 'maintenance_date': '2024-10-30', 'maintenance_type': 'Regular Service', 'description': 'Routine maintenance with transmission fluid change', 'service_provider': 'Honda Service Ahmedabad', 'status': 'Completed'},
    {'maintenance_id': 5, 'vehicle_id': 5, 'maintenance_date': '2024-11-05', 'maintenance_type': 'Repair', 'description': 'AC compressor repair and coolant top-up', 'service_provider': 'Toyota Service Hyderabad', 'status': 'Completed'},
    {'maintenance_id': 6, 'vehicle_id': 6, 'maintenance_date': '2024-10-12', 'maintenance_type': 'Regular Service', 'description': 'Complete service with diesel filter replacement', 'service_provider': 'Mahindra Service Kochi', 'status': 'Completed'},
    {'maintenance_id': 7, 'vehicle_id': 7, 'maintenance_date': '2024-09-15', 'maintenance_type': 'Tire Change', 'description': 'All four tires replaced due to wear and tear', 'service_provider': 'MRF Tire Shop Kolkata', 'status': 'Completed'},
    {'maintenance_id': 8, 'vehicle_id': 8, 'maintenance_date': '2024-10-25', 'maintenance_type': 'Regular Service', 'description': 'Engine service with timing belt inspection', 'service_provider': 'Hyundai Service Chennai', 'status': 'Completed'},
    {'maintenance_id': 9, 'vehicle_id': 9, 'maintenance_date': '2024-11-10', 'maintenance_type': 'Regular Service', 'description': 'Complete SUV service with suspension check', 'service_provider': 'Kia Service Pune', 'status': 'Completed'},
    {'maintenance_id': 10, 'vehicle_id': 10, 'maintenance_date': '2024-10-20', 'maintenance_type': 'Cleaning', 'description': 'Deep interior and exterior cleaning with wax coating', 'service_provider': 'Auto Spa Jaipur', 'status': 'Completed'},
    {'maintenance_id': 11, 'vehicle_id': 11, 'maintenance_date': '2024-09-30', 'maintenance_type': 'Regular Service', 'description': 'Basic service with battery check', 'service_provider': 'Honda Service Lucknow', 'status': 'Completed'},
    {'maintenance_id': 12, 'vehicle_id': 12, 'maintenance_date': '2024-11-01', 'maintenance_type': 'Regular Service', 'description': 'Motorcycle chain cleaning and engine tune-up', 'service_provider': 'Bajaj Service Chandigarh', 'status': 'Completed'},
    {'maintenance_id': 13, 'vehicle_id': 13, 'maintenance_date': '2024-10-08', 'maintenance_type': 'Regular Service', 'description': 'Royal Enfield complete engine service', 'service_provider': 'Royal Enfield Shimla', 'status': 'Completed'},
    {'maintenance_id': 14, 'vehicle_id': 14, 'maintenance_date': '2024-11-12', 'maintenance_type': 'Inspection', 'description': 'Pre-delivery inspection and minor adjustments', 'service_provider': 'Tata Motors Pune', 'status': 'Completed'},
    {'maintenance_id': 15, 'vehicle_id': 15, 'maintenance_date': '2024-10-18', 'maintenance_type': 'Repair', 'description': 'Diesel engine repair and clutch adjustment', 'service_provider': 'Force Motors Kochi', 'status': 'Completed'}
]

maintenance_details_data = [
    {'maintenance_id': 1, 'mileage_at_service': 45000.00, 'parts_replaced': 'Engine oil, Air filter, Spark plugs', 'cost': 3500.00, 'technician_name': 'Ravi Kumar'},
    {'maintenance_id': 2, 'mileage_at_service': 38000.00, 'parts_replaced': 'Engine oil, Oil filter, Brake pads', 'cost': 4200.00, 'technician_name': 'Suresh Singh'},
    {'maintenance_id': 3, 'mileage_at_service': 25000.00, 'parts_replaced': 'None - Software update only', 'cost': 2800.00, 'technician_name': 'Prakash Reddy'},
    {'maintenance_id': 4, 'mileage_at_service': 42000.00, 'parts_replaced': 'Transmission fluid, Cabin filter', 'cost': 3800.00, 'technician_name': 'Kiran Patel'},
    {'maintenance_id': 5, 'mileage_at_service': 55000.00, 'parts_replaced': 'AC compressor, Coolant', 'cost': 8500.00, 'technician_name': 'Venkat Rao'},
    {'maintenance_id': 6, 'mileage_at_service': 35000.00, 'parts_replaced': 'Diesel filter, Engine oil, Air filter', 'cost': 4000.00, 'technician_name': 'Anil Nair'},
    {'maintenance_id': 7, 'mileage_at_service': 32000.00, 'parts_replaced': 'All 4 tires - MRF ZLX 175/65 R14', 'cost': 12000.00, 'technician_name': 'Dipak Das'},
    {'maintenance_id': 8, 'mileage_at_service': 40000.00, 'parts_replaced': 'Engine oil, Oil filter, Fuel filter', 'cost': 3600.00, 'technician_name': 'Tamil Selvan'},
    {'maintenance_id': 9, 'mileage_at_service': 28000.00, 'parts_replaced': 'Engine oil, Shock absorbers', 'cost': 4500.00, 'technician_name': 'Rahul Joshi'},
    {'maintenance_id': 10, 'mileage_at_service': 48000.00, 'parts_replaced': 'None - Cleaning service only', 'cost': 1200.00, 'technician_name': 'Mohan Sharma'},
    {'maintenance_id': 11, 'mileage_at_service': 35000.00, 'parts_replaced': 'Engine oil, Battery terminals cleaned', 'cost': 2800.00, 'technician_name': 'Ashok Verma'},
    {'maintenance_id': 12, 'mileage_at_service': 15000.00, 'parts_replaced': 'Chain lubricant, Spark plug', 'cost': 800.00, 'technician_name': 'Gurpreet Singh'},
    {'maintenance_id': 13, 'mileage_at_service': 18000.00, 'parts_replaced': 'Engine oil, Oil filter, Chain', 'cost': 1500.00, 'technician_name': 'Himanshu Thakur'},
    {'maintenance_id': 14, 'mileage_at_service': 8000.00, 'parts_replaced': 'None - Inspection only', 'cost': 1800.00, 'technician_name': 'Sachin Patil'},
    {'maintenance_id': 15, 'mileage_at_service': 85000.00, 'parts_replaced': 'Clutch plate, Pressure plate, Engine gaskets', 'cost': 15000.00, 'technician_name': 'Biju Thomas'}
]

maintenance_costs_data = [
    {'maintenance_id': 1, 'cost': 3500.00, 'next_service_date': '2025-04-15'},
    {'maintenance_id': 2, 'cost': 4200.00, 'next_service_date': '2025-05-01'},
    {'maintenance_id': 3, 'cost': 2800.00, 'next_service_date': '2025-03-20'},
    {'maintenance_id': 4, 'cost': 3800.00, 'next_service_date': '2025-04-30'},
    {'maintenance_id': 5, 'cost': 8500.00, 'next_service_date': '2025-02-05'},
    {'maintenance_id': 6, 'cost': 4000.00, 'next_service_date': '2025-04-12'},
    {'maintenance_id': 7, 'cost': 12000.00, 'next_service_date': '2025-03-15'},
    {'maintenance_id': 8, 'cost': 3600.00, 'next_service_date': '2025-04-25'},
    {'maintenance_id': 9, 'cost': 4500.00, 'next_service_date': '2025-05-10'},
    {'maintenance_id': 10, 'cost': 1200.00, 'next_service_date': None},
    {'maintenance_id': 11, 'cost': 2800.00, 'next_service_date': '2025-03-30'},
    {'maintenance_id': 12, 'cost': 800.00, 'next_service_date': '2025-02-01'},
    {'maintenance_id': 13, 'cost': 1500.00, 'next_service_date': '2025-01-08'},
    {'maintenance_id': 14, 'cost': 1800.00, 'next_service_date': '2025-02-12'},
    {'maintenance_id': 15, 'cost': 15000.00, 'next_service_date': '2025-01-18'}
]

# Feedback Reviews Data (10 reviews)
feedback_reviews_data = [
    {'customer_id': 1, 'vehicle_id': 1, 'booking_id': 1, 'rating': 5, 'review_text': 'Excellent service! The Maruti Swift was in perfect condition and very fuel efficient. Pickup and drop were smooth. Highly recommended!', 'service_rating': 5, 'vehicle_condition_rating': 5},
    {'customer_id': 4, 'vehicle_id': 4, 'booking_id': 4, 'rating': 4, 'review_text': 'Good experience overall. Honda City was comfortable for our Ahmedabad trip. Only minor issue was the AC took time to cool initially.', 'service_rating': 4, 'vehicle_condition_rating': 4},
    {'customer_id': 6, 'vehicle_id': 6, 'booking_id': 6, 'rating': 3, 'review_text': 'Average experience. The XUV300 had some rattling noise but drove well. Late return penalty was fair. Service could be improved.', 'service_rating': 3, 'vehicle_condition_rating': 3},
    {'customer_id': 9, 'vehicle_id': 9, 'booking_id': 9, 'rating': 5, 'review_text': 'Outstanding! Kia Seltos was brand new condition. Perfect for our Pune-Mumbai trip. Staff was very professional and courteous.', 'service_rating': 5, 'vehicle_condition_rating': 5},
    {'customer_id': 11, 'vehicle_id': 11, 'booking_id': 11, 'rating': 4, 'review_text': 'Honda Amaze was economical and reliable. Good mileage for city driving in Lucknow. Booking process was simple and quick.', 'service_rating': 4, 'vehicle_condition_rating': 4},
    {'customer_id': 13, 'vehicle_id': 13, 'booking_id': 13, 'rating': 5, 'review_text': 'Royal Enfield Classic 350 was amazing for Shimla hills! Perfect bike for mountain roads. Great experience overall.', 'service_rating': 5, 'vehicle_condition_rating': 5},
    {'customer_id': 15, 'vehicle_id': 15, 'booking_id': 15, 'rating': 4, 'review_text': 'Force Traveller was spacious and comfortable for our group travel from Trivandrum to Kochi. Driver was experienced.', 'service_rating': 4, 'vehicle_condition_rating': 4},
    {'customer_id': 2, 'vehicle_id': 2, 'booking_id': 2, 'rating': 5, 'review_text': 'Hyundai Creta exceeded expectations! Smooth ride, excellent features, and punctual service. Will definitely book again.', 'service_rating': 5, 'vehicle_condition_rating': 5},
    {'customer_id': 3, 'vehicle_id': 3, 'booking_id': 3, 'rating': 4, 'review_text': 'Tata Nexon electric was great! Silent operation and eco-friendly. Charging infrastructure support was helpful.', 'service_rating': 4, 'vehicle_condition_rating': 4},
    {'customer_id': 5, 'vehicle_id': 5, 'booking_id': 5, 'rating': 4, 'review_text': 'Toyota Innova Crysta was perfect for family trip. Spacious and comfortable. Good service from the team.', 'service_rating': 4, 'vehicle_condition_rating': 4}
]

def insert_data():
    """Insert all data into the MySQL database"""
    try:
        # Connect to MySQL database
        connection = mysql.connector.connect(**DB_CONFIG)
        cursor = connection.cursor()

        # Insert Customers
        print("Inserting customer data...")
        c_query = """
        INSERT INTO rental_customer (first_name, last_name, email, phone, address, city, state, zip_code, license_number, date_of_birth, credit_score, is_verified)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        for customer in customers_data:
            c_values = (
                customer['first_name'], customer['last_name'], customer['email'], customer['phone'],
                customer['address'], customer['city'], customer['state'], customer['zip_code'],
                customer.get('license_number'), customer['date_of_birth'], customer.get('credit_score'),
                bool(customer.get('license_number'))
            )
            cursor.execute(c_query, c_values)
        connection.commit()
        print(f"{cursor.rowcount} customers inserted.")

        # Insert Vehicles
        print("\n2. Inserting Vehicle data...")
        vehicle_insert_query = """
        INSERT INTO rental_vehicle (vehicle_number, make, model, year, color, vehicle_type, fuel_type, 
        seating_capacity, transmission, hourly_rate, mileage, insurance_expiry, last_service_date, 
        status, created_date, vehicle_picture) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        for vehicle in vehicles_data:
            hourly_rate = vehicle['daily_rate'] / 24  # Calculate hourly rate from daily rate
            vehicle_values = (
                vehicle['vehicle_number'], vehicle['make'], vehicle['model'], vehicle['year'],
                vehicle['color'], vehicle['vehicle_type'], vehicle['fuel_type'], vehicle['seating_capacity'],
                vehicle['transmission'], hourly_rate, vehicle['mileage'], vehicle['insurance_expiry'],
                vehicle['last_service_date'], 'Available', datetime.now(), 'vehicle_pics/default.jpg'
            )
            cursor.execute(v_query, v_values)
        connection.commit()
        print(f"{cursor.rowcount} vehicles inserted.")

        # Insert Rental Bookings
        print("\n3. Inserting Rental Booking data...")
        booking_insert_query = """
        INSERT INTO rental_rentalbooking (customer_id, vehicle_id, booking_date, pickup_datetime, return_datetime, 
        actual_return_datetime, pickup_location, return_location, hourly_rate, total_amount, security_deposit, 
        booking_status, special_requests, created_by) 
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        for booking in rental_bookings_data:
            hourly_rate = booking['daily_rate'] / 24 # Calculate hourly rate
            pickup_datetime = f"{booking['pickup_date']} 10:00:00" # Add a default time
            return_datetime = f"{booking['return_date']} 10:00:00" # Add a default time
            booking_values = (
                booking['customer_id'], booking['vehicle_id'], datetime.now(), pickup_datetime,
                return_datetime, booking.get('actual_return_date'), booking['pickup_location'],
                booking['return_location'], hourly_rate, booking['total_amount'],
                booking['security_deposit'], booking['booking_status'], None, 'System'
            )
            cursor.execute(rb_query, rb_values)
        connection.commit()
        print(f"{cursor.rowcount} rental bookings inserted.")

        # Insert Payments
        print("Inserting payment data...")
        p_query = """
        INSERT INTO rental_payment (booking_id, customer_id, amount, payment_method, payment_type, transaction_id, reference_number, payment_status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """
        for payment in payments_data:
            p_values = (
                payment['booking_id'], payment['customer_id'], payment['amount'],
                payment['payment_method'], payment['payment_type'], payment.get('transaction_id'),
                payment.get('reference_number'), 'Completed'
            )
            cursor.execute(p_query, p_values)
        connection.commit()
        print(f"{cursor.rowcount} payments inserted.")

        # Merge and Insert Maintenance Records
        print("Inserting maintenance record data...")
        merged_maintenance_data = []
        for i in range(len(maintenance_records_data)):
            record = maintenance_records_data[i]
            details = maintenance_details_data[i]
            costs = maintenance_costs_data[i]
            if record['maintenance_id'] == details['maintenance_id'] == costs['maintenance_id']:
                merged_maintenance_data.append({
                    'vehicle_id': record['vehicle_id'],
                    'maintenance_date': record['maintenance_date'],
                    'maintenance_type': record['maintenance_type'],
                    'description': record['description'],
                    'service_provider': record['service_provider'],
                    'status': record['status'],
                    'mileage_at_service': details['mileage_at_service'],
                    'parts_replaced': details['parts_replaced'],
                    'cost': details['cost'],
                    'technician_name': details['technician_name'],
                    'next_service_date': costs['next_service_date']
                })

        mr_query = """
        INSERT INTO rental_maintenancerecord (vehicle_id, maintenance_date, maintenance_type, description, cost, service_provider, next_service_date, mileage_at_service, parts_replaced, technician_name, status)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        """
        for record in merged_maintenance_data:
            mr_values = (
                record['vehicle_id'], record['maintenance_date'], record['maintenance_type'],
                record['description'], record['cost'], record['service_provider'],
                record.get('next_service_date'), record.get('mileage_at_service'),
                record.get('parts_replaced'), record.get('technician_name'), record['status']
            )
            cursor.execute(mr_query, mr_values)
        connection.commit()
        print(f"{cursor.rowcount} maintenance records inserted.")

        # Insert Feedback Reviews
        print("Inserting feedback review data...")
        fr_query = """
        INSERT INTO rental_feedbackreview (customer_id, vehicle_id, booking_id, rating, review_text, service_rating, vehicle_condition_rating)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        for review in feedback_reviews_data:
            fr_values = (
                review['customer_id'], review['vehicle_id'], review['booking_id'],
                review['rating'], review.get('review_text'), review.get('service_rating'),
                review.get('vehicle_condition_rating')
            )
            cursor.execute(fr_query, fr_values)
        connection.commit()
        print(f"{cursor.rowcount} feedback reviews inserted.")

        print("Data insertion completed successfully!")

    except mysql.connector.Error as err:
        print(f"Error: {err}")
        if 'connection' in locals() and connection.is_connected():
            connection.rollback()
    finally:
        if 'connection' in locals() and connection.is_connected():
            cursor.close()
            connection.close()
            print("MySQL connection is closed.")

if __name__ == "__main__":
    insert_data()