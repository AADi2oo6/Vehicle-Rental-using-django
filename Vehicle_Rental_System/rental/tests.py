from django.test import TestCase, TransactionTestCase
from django.db import IntegrityError
from .models import Customer, Vehicle, RentalBooking
from django.contrib.auth.models import User
from datetime import date, timedelta

class TriggerTestCase(TransactionTestCase):
    """
    Test case for database triggers.
    We use TransactionTestCase because it does not wrap tests in a transaction,
    allowing us to test the effects of database-level integrity errors like those from triggers.
    """

    def setUp(self):
        """Set up data for the tests."""
        self.user = User.objects.create_user(username='testuser', password='password')
        # The Customer is created automatically by a post_save signal on the User model.
        # We just need to fetch it here instead of creating it again.
        self.customer = Customer.objects.get(user=self.user)

        self.vehicle = Vehicle.objects.create(
            vehicle_number='TS-TEST-01', make='TestMake', model='TestModel', year=2024,
            vehicle_type='Car', fuel_type='Petrol', seating_capacity=4, transmission='Automatic',
            insurance_expiry='2025-12-31'
        )

    def test_prevent_customer_deletion_with_active_bookings_trigger(self):
        """
        Verify that a customer with an 'Active' or 'Confirmed' booking cannot be deleted.
        """
        # Create a confirmed booking
        booking = RentalBooking.objects.create(
            customer=self.customer, vehicle=self.vehicle, booking_status='Confirmed',
            total_amount=100, security_deposit=50
        )

        # Expect an IntegrityError when trying to delete the customer
        with self.assertRaises(IntegrityError, msg="Trigger should prevent deletion of customer with active bookings."):
            self.customer.delete()

        # Now, change the booking status to 'Completed'
        booking.booking_status = 'Completed'
        booking.save()

        # The deletion should now succeed
        self.customer.delete()
        self.assertFalse(Customer.objects.filter(id=self.customer.id).exists(), "Customer should be deleted after booking is completed.")

    def test_update_vehicle_status_on_booking_delete_trigger(self):
        """Verify that deleting a booking sets the vehicle status back to 'Available'."""
        self.vehicle.status = 'Rented'
        self.vehicle.save()

        booking = RentalBooking.objects.create(customer=self.customer, vehicle=self.vehicle, total_amount=100, security_deposit=50)

        # Delete the booking, which should fire the trigger
        booking.delete()

        # Refresh the vehicle object from the database to get the updated status
        self.vehicle.refresh_from_db()
        self.assertEqual(self.vehicle.status, 'Available', "Vehicle status should be reset to 'Available' after booking deletion.")

    def test_age_check_trigger_on_create(self):
        """Verify that creating a customer younger than 18 is blocked by the INSERT trigger."""
        underage_dob = date.today() - timedelta(days=17 * 365) # Approx. 17 years old
        
        # We must create a user first, as Customer has a foreign key to it.
        user = User.objects.create_user(username='underage_user', password='password')
        
        # Now, directly attempt to create a Customer with an invalid DOB.
        # This will correctly test the BEFORE INSERT trigger.
        with self.assertRaises(IntegrityError, msg="Database should prevent creating a customer under 18."):
            Customer.objects.create(
                user=user, first_name="Underage", last_name="Test", 
                email="underage@test.com", date_of_birth=underage_dob
            )

    def test_age_check_trigger_on_update(self):
        """Verify that updating a customer to be younger than 18 is blocked by the UPDATE trigger."""
        underage_dob = date.today() - timedelta(days=17 * 365)
        self.customer.date_of_birth = underage_dob
        with self.assertRaises(IntegrityError, msg="Database should prevent updating a customer to be under 18."):
            self.customer.save()
