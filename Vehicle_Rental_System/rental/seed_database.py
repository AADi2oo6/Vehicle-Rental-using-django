import random
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.db import transaction
from django.contrib.auth.models import User
from rental.models import Customer, Vehicle, RentalBooking, Payment, MaintenanceRecord, FeedbackReview

# To make this command self-contained and robust, the data has been moved directly
# into this file from the external `car_rental_data_insertion.py`.
# This removes the dependency on `sys.path` and the external `SQL_Queris` folder.

from decimal import Decimal

# --- Data from SQL_Queris/car_rental_data_insertion.py ---
customers_data = [{'first_name': 'Arjun', 'last_name': 'Sharma', 'email': 'arjun.sharma@gmail.com', 'phone': '+91-9876543210', 'address': '123 MG Road', 'city': 'Mumbai', 'state': 'Maharashtra', 'zip_code': '400001', 'license_number': 'MH1220190123456', 'date_of_birth': '1990-05-15', 'credit_score': 750}, {'first_name': 'Priya', 'last_name': 'Singh', 'email': 'priya.singh@yahoo.com', 'phone': '+91-9876543211', 'address': '45 Connaught Place', 'city': 'New Delhi', 'state': 'Delhi', 'zip_code': '110001', 'license_number': 'DL1120190234567', 'date_of_birth': '1985-08-22', 'credit_score': 680}, {'first_name': 'Rajesh', 'last_name': 'Kumar', 'email': 'rajesh.kumar@hotmail.com', 'phone': '+91-9876543212', 'address': '78 Brigade Road', 'city': 'Bangalore', 'state': 'Karnataka', 'zip_code': '560001', 'license_number': 'KA0320190345678', 'date_of_birth': '1988-12-10', 'credit_score': 720}, {'first_name': 'Sneha', 'last_name': 'Patel', 'email': 'sneha.patel@gmail.com', 'phone': '+91-9876543213', 'address': '12 Law Garden', 'city': 'Ahmedabad', 'state': 'Gujarat', 'zip_code': '380009', 'license_number': 'GJ0120190456789', 'date_of_birth': '1992-03-18', 'credit_score': 690}, {'first_name': 'Vikram', 'last_name': 'Reddy', 'email': 'vikram.reddy@outlook.com', 'phone': '+91-9876543214', 'address': '34 Banjara Hills', 'city': 'Hyderabad', 'state': 'Telangana', 'zip_code': '500034', 'license_number': 'TS0720190567890', 'date_of_birth': '1987-11-25', 'credit_score': 760}, {'first_name': 'Ananya', 'last_name': 'Nair', 'email': 'ananya.nair@gmail.com', 'phone': '+91-9876543215', 'address': '56 Marine Drive', 'city': 'Kochi', 'state': 'Kerala', 'zip_code': '682001', 'license_number': 'KL0720190678901', 'date_of_birth': '1991-07-14', 'credit_score': 710}, {'first_name': 'Rohit', 'last_name': 'Gupta', 'email': 'rohit.gupta@yahoo.com', 'phone': '+91-9876543216', 'address': '89 Park Street', 'city': 'Kolkata', 'state': 'West Bengal', 'zip_code': '700016', 'license_number': 'WB0220190789012', 'date_of_birth': '1989-01-30', 'credit_score': 640}, {'first_name': 'Kavya', 'last_name': 'Iyer', 'email': 'kavya.iyer@gmail.com', 'phone': '+91-9876543217', 'address': '23 T Nagar', 'city': 'Chennai', 'state': 'Tamil Nadu', 'zip_code': '600017', 'license_number': 'TN0320190890123', 'date_of_birth': '1993-09-08', 'credit_score': 700}, {'first_name': 'Amit', 'last_name': 'Joshi', 'email': 'amit.joshi@hotmail.com', 'phone': '+91-9876543218', 'address': '67 Civil Lines', 'city': 'Pune', 'state': 'Maharashtra', 'zip_code': '411001', 'license_number': 'MH1420190901234', 'date_of_birth': '1986-04-12', 'credit_score': 780}, {'first_name': 'Ritu', 'last_name': 'Agarwal', 'email': 'ritu.agarwal@gmail.com', 'phone': '+91-9876543219', 'address': '90 Pink City', 'city': 'Jaipur', 'state': 'Rajasthan', 'zip_code': '302001', 'license_number': 'RJ1420191012345', 'date_of_birth': '1994-06-20', 'credit_score': 660}, {'first_name': 'Sanjay', 'last_name': 'Verma', 'email': 'sanjay.verma@outlook.com', 'phone': '+91-9876543220', 'address': '45 Hazratganj', 'city': 'Lucknow', 'state': 'Uttar Pradesh', 'zip_code': '226001', 'license_number': 'UP3220191123456', 'date_of_birth': '1983-10-05', 'credit_score': 720}, {'first_name': 'Meera', 'last_name': 'Chopra', 'email': 'meera.chopra@gmail.com', 'phone': '+91-9876543221', 'address': '78 Sector 17', 'city': 'Chandigarh', 'state': 'Chandigarh', 'zip_code': '160017', 'license_number': 'CH0120191234567', 'date_of_birth': '1990-12-28', 'credit_score': 690}, {'first_name': 'Deepak', 'last_name': 'Thakur', 'email': 'deepak.thakur@yahoo.com', 'phone': '+91-9876543222', 'address': '12 Mall Road', 'city': 'Shimla', 'state': 'Himachal Pradesh', 'zip_code': '171001', 'license_number': 'HP0220191345678', 'date_of_birth': '1987-02-14', 'credit_score': 740}, {'first_name': 'Pooja', 'last_name': 'Rao', 'email': 'pooja.rao@gmail.com', 'phone': '+91-9876543223', 'address': '34 Koregaon Park', 'city': 'Pune', 'state': 'Maharashtra', 'zip_code': '411001', 'license_number': 'MH1420191456789', 'date_of_birth': '1991-11-16', 'credit_score': 670}, {'first_name': 'Arun', 'last_name': 'Menon', 'email': 'arun.menon@hotmail.com', 'phone': '+91-9876543224', 'address': '56 Thiruvananthapuram', 'city': 'Trivandrum', 'state': 'Kerala', 'zip_code': '695001', 'license_number': 'KL1420191567890', 'date_of_birth': '1985-08-03', 'credit_score': 710}, {'first_name': 'Sunita', 'last_name': 'Bansal', 'email': 'sunita.bansal@outlook.com', 'phone': '+91-9876543225', 'address': '89 CP', 'city': 'New Delhi', 'state': 'Delhi', 'zip_code': '110001', 'license_number': 'DL1120191678901', 'date_of_birth': '1989-05-27', 'credit_score': 650}, {'first_name': 'Kiran', 'last_name': 'Desai', 'email': 'kiran.desai@gmail.com', 'phone': '+91-9876543226', 'address': '23 Navrangpura', 'city': 'Ahmedabad', 'state': 'Gujarat', 'zip_code': '380009', 'license_number': 'GJ0120191789012', 'date_of_birth': '1992-01-11', 'credit_score': 680}, {'first_name': 'Ravi', 'last_name': 'Chandra', 'email': 'ravi.chandra@yahoo.com', 'phone': '+91-9876543227', 'address': '67 Jubilee Hills', 'city': 'Hyderabad', 'state': 'Telangana', 'zip_code': '500033', 'license_number': 'TS0720191890123', 'date_of_birth': '1988-07-19', 'credit_score': 730}, {'first_name': 'Nisha', 'last_name': 'Sinha', 'email': 'nisha.sinha@gmail.com', 'phone': '+91-9876543228', 'address': '90 Salt Lake', 'city': 'Kolkata', 'state': 'West Bengal', 'zip_code': '700064', 'license_number': 'WB0220191901234', 'date_of_birth': '1993-04-23', 'credit_score': 690}, {'first_name': 'Manish', 'last_name': 'Jain', 'email': 'manish.jain@hotmail.com', 'phone': '+91-9876543229', 'address': '45 Anna Nagar', 'city': 'Chennai', 'state': 'Tamil Nadu', 'zip_code': '600040', 'license_number': 'TN0320192012345', 'date_of_birth': '1986-09-15', 'credit_score': 750}]
vehicles_data = [{'vehicle_number': 'MH12AB1234', 'make': 'Maruti Suzuki', 'model': 'Swift', 'year': 2021, 'color': 'White', 'vehicle_type': 'Car', 'fuel_type': 'Petrol', 'seating_capacity': 5, 'transmission': 'Manual', 'daily_rate': 1200.0, 'mileage': 18.5, 'insurance_expiry': '2025-12-31', 'last_service_date': '2024-10-15'}, {'vehicle_number': 'DL8CAB5678', 'make': 'Hyundai', 'model': 'Creta', 'year': 2022, 'color': 'Silver', 'vehicle_type': 'SUV', 'fuel_type': 'Diesel', 'seating_capacity': 7, 'transmission': 'Automatic', 'daily_rate': 2500.0, 'mileage': 16.8, 'insurance_expiry': '2025-11-20', 'last_service_date': '2024-11-01'}, {'vehicle_number': 'KA03CD9012', 'make': 'Tata', 'model': 'Nexon', 'year': 2023, 'color': 'Blue', 'vehicle_type': 'SUV', 'fuel_type': 'Electric', 'seating_capacity': 5, 'transmission': 'Automatic', 'daily_rate': 2200.0, 'mileage': 312.0, 'insurance_expiry': '2026-03-15', 'last_service_date': '2024-09-20'}, {'vehicle_number': 'GJ01EF3456', 'make': 'Honda', 'model': 'City', 'year': 2021, 'color': 'Red', 'vehicle_type': 'Car', 'fuel_type': 'Petrol', 'seating_capacity': 5, 'transmission': 'Automatic', 'daily_rate': 1800.0, 'mileage': 17.8, 'insurance_expiry': '2025-08-10', 'last_service_date': '2024-10-30'}, {'vehicle_number': 'TS07GH7890', 'make': 'Toyota', 'model': 'Innova Crysta', 'year': 2020, 'color': 'Grey', 'vehicle_type': 'SUV', 'fuel_type': 'Diesel', 'seating_capacity': 8, 'transmission': 'Manual', 'daily_rate': 3000.0, 'mileage': 15.6, 'insurance_expiry': '2025-07-25', 'last_service_date': '2024-11-05'}, {'vehicle_number': 'KL07IJ1234', 'make': 'Mahindra', 'model': 'XUV300', 'year': 2022, 'color': 'Black', 'vehicle_type': 'SUV', 'fuel_type': 'Diesel', 'seating_capacity': 5, 'transmission': 'Manual', 'daily_rate': 2000.0, 'mileage': 20.0, 'insurance_expiry': '2026-01-18', 'last_service_date': '2024-10-12'}, {'vehicle_number': 'WB02KL5678', 'make': 'Maruti Suzuki', 'model': 'Alto K10', 'year': 2023, 'color': 'Yellow', 'vehicle_type': 'Car', 'fuel_type': 'Petrol', 'seating_capacity': 5, 'transmission': 'Manual', 'daily_rate': 1000.0, 'mileage': 24.7, 'insurance_expiry': '2026-04-20', 'last_service_date': '2024-09-15'}, {'vehicle_number': 'TN03MN9012', 'make': 'Hyundai', 'model': 'Verna', 'year': 2021, 'color': 'White', 'vehicle_type': 'Car', 'fuel_type': 'Petrol', 'seating_capacity': 5, 'transmission': 'Automatic', 'daily_rate': 1900.0, 'mileage': 18.45, 'insurance_expiry': '2025-09-30', 'last_service_date': '2024-10-25'}, {'vehicle_number': 'MH14OP3456', 'make': 'Kia', 'model': 'Seltos', 'year': 2022, 'color': 'Orange', 'vehicle_type': 'SUV', 'fuel_type': 'Petrol', 'seating_capacity': 5, 'transmission': 'Automatic', 'daily_rate': 2300.0, 'mileage': 16.8, 'insurance_expiry': '2025-12-05', 'last_service_date': '2024-11-10'}, {'vehicle_number': 'RJ14QR7890', 'make': 'Maruti Suzuki', 'model': 'Ertiga', 'year': 2020, 'color': 'Silver', 'vehicle_type': 'Van', 'fuel_type': 'Petrol', 'seating_capacity': 7, 'transmission': 'Manual', 'daily_rate': 2100.0, 'mileage': 19.34, 'insurance_expiry': '2025-06-15', 'last_service_date': '2024-10-20'}, {'vehicle_number': 'UP32ST1234', 'make': 'Honda', 'model': 'Amaze', 'year': 2023, 'color': 'Blue', 'vehicle_type': 'Car', 'fuel_type': 'Petrol', 'seating_capacity': 5, 'transmission': 'Manual', 'daily_rate': 1500.0, 'mileage': 19.5, 'insurance_expiry': '2026-02-28', 'last_service_date': '2024-09-30'}, {'vehicle_number': 'CH01UV5678', 'make': 'Bajaj', 'model': 'Pulsar NS200', 'year': 2022, 'color': 'Black', 'vehicle_type': 'Motorcycle', 'fuel_type': 'Petrol', 'seating_capacity': 2, 'transmission': 'Manual', 'daily_rate': 500.0, 'mileage': 35.0, 'insurance_expiry': '2025-10-12', 'last_service_date': '2024-11-01'}, {'vehicle_number': 'HP02WX9012', 'make': 'Royal Enfield', 'model': 'Classic 350', 'year': 2021, 'color': 'Green', 'vehicle_type': 'Motorcycle', 'fuel_type': 'Petrol', 'seating_capacity': 2, 'transmission': 'Manual', 'daily_rate': 800.0, 'mileage': 40.0, 'insurance_expiry': '2025-05-18', 'last_service_date': '2024-10-08'}, {'vehicle_number': 'MH14YZ3456', 'make': 'Tata', 'model': 'Harrier', 'year': 2023, 'color': 'Red', 'vehicle_type': 'SUV', 'fuel_type': 'Diesel', 'seating_capacity': 5, 'transmission': 'Automatic', 'daily_rate': 2800.0, 'mileage': 16.35, 'insurance_expiry': '2026-01-10', 'last_service_date': '2024-11-12'}, {'vehicle_number': 'KL14AB7890', 'make': 'Force', 'model': 'Traveller', 'year': 2020, 'color': 'White', 'vehicle_type': 'Van', 'fuel_type': 'Diesel', 'seating_capacity': 12, 'transmission': 'Manual', 'daily_rate': 3500.0, 'mileage': 12.5, 'insurance_expiry': '2025-08-20', 'last_service_date': '2024-10-18'}]
rental_bookings_data = [{'customer_id': 1, 'vehicle_id': 1, 'pickup_date': '2024-11-01', 'return_date': '2024-11-05', 'actual_return_date': '2024-11-05', 'pickup_location': 'Mumbai Airport', 'return_location': 'Mumbai Airport', 'daily_rate': 1200.0, 'total_amount': 4800.0, 'security_deposit': 5000.0, 'booking_status': 'Completed'}, {'customer_id': 2, 'vehicle_id': 2, 'pickup_date': '2024-11-10', 'return_date': '2024-11-15', 'pickup_location': 'New Delhi Railway Station', 'return_location': 'IGI Airport Delhi', 'daily_rate': 2500.0, 'total_amount': 12500.0, 'security_deposit': 10000.0, 'booking_status': 'Active'}, {'customer_id': 3, 'vehicle_id': 3, 'pickup_date': '2024-11-20', 'return_date': '2024-11-25', 'pickup_location': 'Bangalore City Center', 'return_location': 'Bangalore City Center', 'daily_rate': 2200.0, 'total_amount': 11000.0, 'security_deposit': 8000.0, 'booking_status': 'Confirmed'}, {'customer_id': 4, 'vehicle_id': 4, 'pickup_date': '2024-10-15', 'return_date': '2024-10-18', 'actual_return_date': '2024-10-18', 'pickup_location': 'Ahmedabad Central', 'return_location': 'Ahmedabad Central', 'daily_rate': 1800.0, 'total_amount': 5400.0, 'security_deposit': 6000.0, 'booking_status': 'Completed'}, {'customer_id': 5, 'vehicle_id': 5, 'pickup_date': '2024-11-12', 'return_date': '2024-11-17', 'pickup_location': 'Hyderabad Airport', 'return_location': 'Hyderabad Airport', 'daily_rate': 3000.0, 'total_amount': 15000.0, 'security_deposit': 12000.0, 'booking_status': 'Active'}, {'customer_id': 6, 'vehicle_id': 6, 'pickup_date': '2024-09-20', 'return_date': '2024-09-23', 'actual_return_date': '2024-09-24', 'pickup_location': 'Kochi Marine Drive', 'return_location': 'Kochi Marine Drive', 'daily_rate': 2000.0, 'total_amount': 8000.0, 'security_deposit': 7000.0, 'booking_status': 'Completed'}, {'customer_id': 7, 'vehicle_id': 7, 'pickup_date': '2024-11-08', 'return_date': '2024-11-12', 'pickup_location': 'Kolkata Howrah', 'return_location': 'Kolkata Howrah', 'daily_rate': 1000.0, 'total_amount': 4000.0, 'security_deposit': 3000.0, 'booking_status': 'Active'}, {'customer_id': 8, 'vehicle_id': 8, 'pickup_date': '2024-11-25', 'return_date': '2024-11-30', 'pickup_location': 'Chennai Central Station', 'return_location': 'Chennai Airport', 'daily_rate': 1900.0, 'total_amount': 9500.0, 'security_deposit': 8000.0, 'booking_status': 'Confirmed'}, {'customer_id': 9, 'vehicle_id': 9, 'pickup_date': '2024-10-01', 'return_date': '2024-10-07', 'actual_return_date': '2024-10-07', 'pickup_location': 'Pune Station', 'return_location': 'Pune Airport', 'daily_rate': 2300.0, 'total_amount': 13800.0, 'security_deposit': 10000.0, 'booking_status': 'Completed'}, {'customer_id': 10, 'vehicle_id': 10, 'pickup_date': '2024-11-15', 'return_date': '2024-11-20', 'pickup_location': 'Jaipur City Palace', 'return_location': 'Jaipur Airport', 'daily_rate': 2100.0, 'total_amount': 10500.0, 'security_deposit': 8000.0, 'booking_status': 'Confirmed'}, {'customer_id': 11, 'vehicle_id': 11, 'pickup_date': '2024-08-15', 'return_date': '2024-08-18', 'actual_return_date': '2024-08-18', 'pickup_location': 'Lucknow Charbagh', 'return_location': 'Lucknow Charbagh', 'daily_rate': 1500.0, 'total_amount': 4500.0, 'security_deposit': 5000.0, 'booking_status': 'Completed'}, {'customer_id': 12, 'vehicle_id': 12, 'pickup_date': '2024-11-05', 'return_date': '2024-11-08', 'pickup_location': 'Chandigarh Sector 17', 'return_location': 'Chandigarh Airport', 'daily_rate': 500.0, 'total_amount': 1500.0, 'security_deposit': 2000.0, 'booking_status': 'Active'}, {'customer_id': 13, 'vehicle_id': 13, 'pickup_date': '2024-07-10', 'return_date': '2024-07-15', 'actual_return_date': '2024-07-15', 'pickup_location': 'Shimla Mall Road', 'return_location': 'Shimla Mall Road', 'daily_rate': 800.0, 'total_amount': 4000.0, 'security_deposit': 3000.0, 'booking_status': 'Completed'}, {'customer_id': 14, 'vehicle_id': 14, 'pickup_date': '2024-11-18', 'return_date': '2024-11-22', 'pickup_location': 'Pune Koregaon Park', 'return_location': 'Mumbai Airport', 'daily_rate': 2800.0, 'total_amount': 11200.0, 'security_deposit': 12000.0, 'booking_status': 'Confirmed'}, {'customer_id': 15, 'vehicle_id': 15, 'pickup_date': '2024-09-01', 'return_date': '2024-09-05', 'actual_return_date': '2024-09-05', 'pickup_location': 'Trivandrum Central', 'return_location': 'Kochi Airport', 'daily_rate': 3500.0, 'total_amount': 14000.0, 'security_deposit': 15000.0, 'booking_status': 'Completed'}]
payments_data = [{'booking_id': 1, 'customer_id': 1, 'amount': 2400.0, 'payment_method': 'UPI', 'payment_type': 'Advance', 'transaction_id': 'UPI2024110112345', 'reference_number': 'REF001'}, {'booking_id': 1, 'customer_id': 1, 'amount': 2400.0, 'payment_method': 'Credit Card', 'payment_type': 'Full Payment', 'transaction_id': 'CC2024110512346', 'reference_number': 'REF002'}, {'booking_id': 1, 'customer_id': 1, 'amount': 5000.0, 'payment_method': 'Credit Card', 'payment_type': 'Security Deposit', 'transaction_id': 'CC2024110512347', 'reference_number': 'REF003'}, {'booking_id': 4, 'customer_id': 4, 'amount': 5400.0, 'payment_method': 'UPI', 'payment_type': 'Full Payment', 'transaction_id': 'UPI2024101512352', 'reference_number': 'REF008'}, {'booking_id': 6, 'customer_id': 6, 'amount': 8000.0, 'payment_method': 'Net Banking', 'payment_type': 'Full Payment', 'transaction_id': 'NB2024092012356', 'reference_number': 'REF012'}, {'booking_id': 9, 'customer_id': 9, 'amount': 13800.0, 'payment_method': 'Net Banking', 'payment_type': 'Full Payment', 'transaction_id': 'NB2024100112362', 'reference_number': 'REF018'}, {'booking_id': 11, 'customer_id': 11, 'amount': 4500.0, 'payment_method': 'Cash', 'payment_type': 'Full Payment', 'transaction_id': None, 'reference_number': 'CASH001'}, {'booking_id': 13, 'customer_id': 13, 'amount': 4000.0, 'payment_method': 'Debit Card', 'payment_type': 'Full Payment', 'transaction_id': 'DC2024071012368', 'reference_number': 'REF024'}, {'booking_id': 15, 'customer_id': 15, 'amount': 14000.0, 'payment_method': 'Net Banking', 'payment_type': 'Full Payment', 'transaction_id': 'NB2024090112372', 'reference_number': 'REF028'}, {'booking_id': 2, 'customer_id': 2, 'amount': 6250.0, 'payment_method': 'Net Banking', 'payment_type': 'Advance', 'transaction_id': 'NB2024111012348', 'reference_number': 'REF004'}, {'booking_id': 3, 'customer_id': 3, 'amount': 5500.0, 'payment_method': 'UPI', 'payment_type': 'Advance', 'transaction_id': 'UPI2024112012350', 'reference_number': 'REF006'}, {'booking_id': 5, 'customer_id': 5, 'amount': 7500.0, 'payment_method': 'Credit Card', 'payment_type': 'Advance', 'transaction_id': 'CC2024111212354', 'reference_number': 'REF010'}, {'booking_id': 7, 'customer_id': 7, 'amount': 2000.0, 'payment_method': 'UPI', 'payment_type': 'Advance', 'transaction_id': 'UPI2024110812358', 'reference_number': 'REF014'}, {'booking_id': 8, 'customer_id': 8, 'amount': 4750.0, 'payment_method': 'Credit Card', 'payment_type': 'Advance', 'transaction_id': 'CC2024112512360', 'reference_number': 'REF016'}, {'booking_id': 10, 'customer_id': 10, 'amount': 5250.0, 'payment_method': 'UPI', 'payment_type': 'Advance', 'transaction_id': 'UPI2024111512364', 'reference_number': 'REF020'}, {'booking_id': 12, 'customer_id': 12, 'amount': 750.0, 'payment_method': 'UPI', 'payment_type': 'Advance', 'transaction_id': 'UPI2024110512366', 'reference_number': 'REF022'}, {'booking_id': 14, 'customer_id': 14, 'amount': 5600.0, 'payment_method': 'Credit Card', 'payment_type': 'Advance', 'transaction_id': 'CC2024111812370', 'reference_number': 'REF026'}, {'booking_id': 6, 'customer_id': 6, 'amount': 2000.0, 'payment_method': 'Cash', 'payment_type': 'Fine', 'transaction_id': None, 'reference_number': 'FINE001'}]
maintenance_records_data = [{'maintenance_id': 1, 'vehicle_id': 1, 'maintenance_date': '2024-10-15', 'maintenance_type': 'Regular Service', 'description': 'Engine oil change, air filter replacement, brake inspection', 'service_provider': 'Maruti Service Center Mumbai', 'status': 'Completed'}, {'maintenance_id': 2, 'vehicle_id': 2, 'maintenance_date': '2024-11-01', 'maintenance_type': 'Regular Service', 'description': 'Full service including engine, transmission, and brake system check', 'service_provider': 'Hyundai Service Delhi', 'status': 'Completed'}, {'maintenance_id': 3, 'vehicle_id': 3, 'maintenance_date': '2024-09-20', 'maintenance_type': 'Inspection', 'description': 'Electric vehicle battery health check and software update', 'service_provider': 'Tata Motors Bangalore', 'status': 'Completed'}, {'maintenance_id': 4, 'vehicle_id': 4, 'maintenance_date': '2024-10-30', 'maintenance_type': 'Regular Service', 'description': 'Routine maintenance with transmission fluid change', 'service_provider': 'Honda Service Ahmedabad', 'status': 'Completed'}, {'maintenance_id': 5, 'vehicle_id': 5, 'maintenance_date': '2024-11-05', 'maintenance_type': 'Repair', 'description': 'AC compressor repair and coolant top-up', 'service_provider': 'Toyota Service Hyderabad', 'status': 'Completed'}, {'maintenance_id': 6, 'vehicle_id': 6, 'maintenance_date': '2024-10-12', 'maintenance_type': 'Regular Service', 'description': 'Complete service with diesel filter replacement', 'service_provider': 'Mahindra Service Kochi', 'status': 'Completed'}, {'maintenance_id': 7, 'vehicle_id': 7, 'maintenance_date': '2024-09-15', 'maintenance_type': 'Tire Change', 'description': 'All four tires replaced due to wear and tear', 'service_provider': 'MRF Tire Shop Kolkata', 'status': 'Completed'}, {'maintenance_id': 8, 'vehicle_id': 8, 'maintenance_date': '2024-10-25', 'maintenance_type': 'Regular Service', 'description': 'Engine service with timing belt inspection', 'service_provider': 'Hyundai Service Chennai', 'status': 'Completed'}, {'maintenance_id': 9, 'vehicle_id': 9, 'maintenance_date': '2024-11-10', 'maintenance_type': 'Regular Service', 'description': 'Complete SUV service with suspension check', 'service_provider': 'Kia Service Pune', 'status': 'Completed'}, {'maintenance_id': 10, 'vehicle_id': 10, 'maintenance_date': '2024-10-20', 'maintenance_type': 'Cleaning', 'description': 'Deep interior and exterior cleaning with wax coating', 'service_provider': 'Auto Spa Jaipur', 'status': 'Completed'}, {'maintenance_id': 11, 'vehicle_id': 11, 'maintenance_date': '2024-09-30', 'maintenance_type': 'Regular Service', 'description': 'Basic service with battery check', 'service_provider': 'Honda Service Lucknow', 'status': 'Completed'}, {'maintenance_id': 12, 'vehicle_id': 12, 'maintenance_date': '2024-11-01', 'maintenance_type': 'Regular Service', 'description': 'Motorcycle chain cleaning and engine tune-up', 'service_provider': 'Bajaj Service Chandigarh', 'status': 'Completed'}, {'maintenance_id': 13, 'vehicle_id': 13, 'maintenance_date': '2024-10-08', 'maintenance_type': 'Regular Service', 'description': 'Royal Enfield complete engine service', 'service_provider': 'Royal Enfield Shimla', 'status': 'Completed'}, {'maintenance_id': 14, 'vehicle_id': 14, 'maintenance_date': '2024-11-12', 'maintenance_type': 'Inspection', 'description': 'Pre-delivery inspection and minor adjustments', 'service_provider': 'Tata Motors Pune', 'status': 'Completed'}, {'maintenance_id': 15, 'vehicle_id': 15, 'maintenance_date': '2024-10-18', 'maintenance_type': 'Repair', 'description': 'Diesel engine repair and clutch adjustment', 'service_provider': 'Force Motors Kochi', 'status': 'Completed'}]
feedback_reviews_data = [{'customer_id': 1, 'vehicle_id': 1, 'booking_id': 1, 'rating': 5, 'review_text': 'Excellent service! The Maruti Swift was in perfect condition and very fuel efficient. Pickup and drop were smooth. Highly recommended!', 'service_rating': 5, 'vehicle_condition_rating': 5}, {'customer_id': 4, 'vehicle_id': 4, 'booking_id': 4, 'rating': 4, 'review_text': 'Good experience overall. Honda City was comfortable for our Ahmedabad trip. Only minor issue was the AC took time to cool initially.', 'service_rating': 4, 'vehicle_condition_rating': 4}, {'customer_id': 6, 'vehicle_id': 6, 'booking_id': 6, 'rating': 3, 'review_text': 'Average experience. The XUV300 had some rattling noise but drove well. Late return penalty was fair. Service could be improved.', 'service_rating': 3, 'vehicle_condition_rating': 3}, {'customer_id': 9, 'vehicle_id': 9, 'booking_id': 9, 'rating': 5, 'review_text': 'Outstanding! Kia Seltos was brand new condition. Perfect for our Pune-Mumbai trip. Staff was very professional and courteous.', 'service_rating': 5, 'vehicle_condition_rating': 5}, {'customer_id': 11, 'vehicle_id': 11, 'booking_id': 11, 'rating': 4, 'review_text': 'Honda Amaze was economical and reliable. Good mileage for city driving in Lucknow. Booking process was simple and quick.', 'service_rating': 4, 'vehicle_condition_rating': 4}, {'customer_id': 13, 'vehicle_id': 13, 'booking_id': 13, 'rating': 5, 'review_text': 'Royal Enfield Classic 350 was amazing for Shimla hills! Perfect bike for mountain roads. Great experience overall.', 'service_rating': 5, 'vehicle_condition_rating': 5}, {'customer_id': 15, 'vehicle_id': 15, 'booking_id': 15, 'rating': 4, 'review_text': 'Force Traveller was spacious and comfortable for our group travel from Trivandrum to Kochi. Driver was experienced.', 'service_rating': 4, 'vehicle_condition_rating': 4}, {'customer_id': 2, 'vehicle_id': 2, 'booking_id': 2, 'rating': 5, 'review_text': 'Hyundai Creta exceeded expectations! Smooth ride, excellent features, and punctual service. Will definitely book again.', 'service_rating': 5, 'vehicle_condition_rating': 5}, {'customer_id': 3, 'vehicle_id': 3, 'booking_id': 3, 'rating': 4, 'review_text': 'Tata Nexon electric was great! Silent operation and eco-friendly. Charging infrastructure support was helpful.', 'service_rating': 4, 'vehicle_condition_rating': 4}, {'customer_id': 5, 'vehicle_id': 5, 'booking_id': 5, 'rating': 4, 'review_text': 'Toyota Innova Crysta was perfect for family trip. Spacious and comfortable. Good service from the team.', 'service_rating': 4, 'vehicle_condition_rating': 4}]

class Command(BaseCommand):
    help = 'Seeds the database with initial data for the Velo-Rent application.'

    @transaction.atomic
    def handle(self, *args, **kwargs):
        self.stdout.write(self.style.SUCCESS('Starting database seeding process...'))

        # --- Clean up existing data to prevent duplicates ---
        self.stdout.write('Deleting existing data...')
        User.objects.filter(is_superuser=False).delete()
        # Deleting users will cascade-delete Customers due to OneToOneField.
        # Customer.objects.all().delete() 
        Vehicle.objects.all().delete()
        RentalBooking.objects.all().delete()
        Payment.objects.all().delete()
        MaintenanceRecord.objects.all().delete()
        FeedbackReview.objects.all().delete()
        self.stdout.write(self.style.SUCCESS('Existing data cleared.'))

        # --- 1. Create Users and Customers ---
        self.stdout.write('Creating users and customers...')
        customer_map = {}
        for i, customer_data in enumerate(customers_data, 1):
            try:
                # Create the Django User first
                user = User.objects.create_user(
                    username=customer_data['email'],
                    email=customer_data['email'],
                    password='password123',  # Set a default password
                    first_name=customer_data['first_name'],
                    last_name=customer_data['last_name']
                )

                # The post_save signal will create the Customer profile.
                # We just need to update it with the remaining data.
                customer = Customer.objects.get(user=user)
                customer.phone = customer_data['phone']
                customer.address = customer_data['address']
                customer.city = customer_data['city']
                customer.state = customer_data['state']
                customer.zip_code = customer_data['zip_code']
                customer.license_number = customer_data.get('license_number')
                customer.date_of_birth = customer_data['date_of_birth']
                customer.credit_score = customer_data.get('credit_score')
                
                # The license trigger will handle verification, but we can set it here too for clarity
                if customer.license_number and len(customer.license_number) == 15:
                    customer.is_verified = True
                
                customer.save()
                customer_map[i] = customer # Map old ID to new customer object

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error creating customer {customer_data['email']}: {e}"))
        self.stdout.write(self.style.SUCCESS(f'{len(customer_map)} customers created.'))

        # --- 2. Create Vehicles ---
        self.stdout.write('Creating vehicles...')
        vehicle_map = {}
        for i, vehicle_data in enumerate(vehicles_data, 1):
            vehicle = Vehicle.objects.create(
                vehicle_number=vehicle_data['vehicle_number'],
                make=vehicle_data['make'],
                model=vehicle_data['model'],
                year=vehicle_data['year'],
                color=vehicle_data['color'],
                vehicle_type=vehicle_data['vehicle_type'],
                fuel_type=vehicle_data['fuel_type'],
                seating_capacity=vehicle_data['seating_capacity'],
                transmission=vehicle_data['transmission'],
                hourly_rate=Decimal(vehicle_data['daily_rate']) / Decimal('24.0'), # Use Decimal for precision
                mileage=vehicle_data['mileage'],
                insurance_expiry=vehicle_data['insurance_expiry'],
                last_service_date=vehicle_data['last_service_date'],
                status='Available'
            )
            vehicle_map[i] = vehicle
        self.stdout.write(self.style.SUCCESS(f'{len(vehicle_map)} vehicles created.'))

        # --- 3. Create Rental Bookings ---
        self.stdout.write('Creating rental bookings...')
        booking_map = {}
        for i, booking_data in enumerate(rental_bookings_data, 1):
            customer = customer_map.get(booking_data['customer_id'])
            vehicle = vehicle_map.get(booking_data['vehicle_id'])
            if customer and vehicle:
                booking = RentalBooking.objects.create(
                    customer=customer,
                    vehicle=vehicle,
                    pickup_datetime=f"{booking_data['pickup_date']} 00:00:00",
                    return_datetime=f"{booking_data['return_date']} 00:00:00",
                    actual_return_datetime=f"{booking_data['actual_return_date']} 00:00:00" if 'actual_return_date' in booking_data else None,
                    pickup_location=booking_data['pickup_location'],
                    return_location=booking_data['return_location'],
                    hourly_rate=Decimal(booking_data['daily_rate']) / Decimal('24.0'),
                    total_amount=booking_data['total_amount'],
                    security_deposit=booking_data['security_deposit'],
                    booking_status=booking_data['booking_status']
                )
                booking_map[i] = booking
        self.stdout.write(self.style.SUCCESS(f'{len(booking_map)} bookings created.'))

        # --- 4. Create Payments ---
        self.stdout.write('Creating payments...')
        for payment_data in payments_data:
            booking = booking_map.get(payment_data['booking_id'])
            customer = customer_map.get(payment_data['customer_id'])
            if booking and customer:
                Payment.objects.create(
                    booking=booking,
                    customer=customer,
                    amount=payment_data['amount'],
                    payment_method=payment_data['payment_method'],
                    payment_type=payment_data['payment_type'],
                    transaction_id=payment_data.get('transaction_id'),
                    reference_number=payment_data.get('reference_number'),
                    payment_status='Completed'
                )
        self.stdout.write(self.style.SUCCESS('Payments created.'))

        # --- 5. Create Maintenance Records ---
        self.stdout.write('Creating maintenance records...')
        for i, record_data in enumerate(maintenance_records_data, 1):
            vehicle = vehicle_map.get(record_data['vehicle_id'])
            if vehicle:
                MaintenanceRecord.objects.create(
                    vehicle=vehicle,
                    maintenance_date=record_data['maintenance_date'],
                    maintenance_type=record_data['maintenance_type'],
                    description=record_data['description'],
                    cost=random.randint(2000, 8000), # Simplified cost
                    service_provider=record_data['service_provider'],
                    status=record_data['status']
                )
        self.stdout.write(self.style.SUCCESS('Maintenance records created.'))

        # --- 6. Create Feedback Reviews ---
        self.stdout.write('Creating feedback reviews...')
        for review_data in feedback_reviews_data:
            customer = customer_map.get(review_data['customer_id'])
            vehicle = vehicle_map.get(review_data['vehicle_id'])
            booking = booking_map.get(review_data['booking_id'])
            if customer and vehicle and booking:
                FeedbackReview.objects.create(
                    customer=customer,
                    vehicle=vehicle,
                    booking=booking,
                    rating=review_data['rating'],
                    review_text=review_data.get('review_text'),
                    service_rating=review_data.get('service_rating'),
                    vehicle_condition_rating=review_data.get('vehicle_condition_rating')
                )
        self.stdout.write(self.style.SUCCESS('Feedback reviews created.'))

        self.stdout.write(self.style.SUCCESS('Database seeding completed successfully!'))