from django.db import migrations


update_vehicle_status_trigger = """
CREATE TRIGGER update_vehicle_status_on_booking_change
AFTER UPDATE ON rental_rentalbooking
FOR EACH ROW
BEGIN
    -- When a booking becomes Active, mark the vehicle as Rented.
    IF NEW.booking_status = 'Active' AND OLD.booking_status <> 'Active' THEN
        UPDATE rental_vehicle SET status = 'Rented' WHERE id = NEW.vehicle_id;
    -- When a booking is Completed or Cancelled, mark the vehicle as Available.
    ELSEIF (NEW.booking_status = 'Completed' OR NEW.booking_status = 'Cancelled') AND OLD.booking_status NOT IN ('Completed', 'Cancelled') THEN
        UPDATE rental_vehicle SET status = 'Available' WHERE id = NEW.vehicle_id;
    END IF;
END;
"""

drop_update_vehicle_status_trigger = "DROP TRIGGER IF EXISTS update_vehicle_status_on_booking_change;"


class Migration(migrations.Migration):

    dependencies = [
        ('rental', '0020_customer_integrity_triggers'),
    ]

    operations = [
        migrations.RunSQL(update_vehicle_status_trigger, reverse_sql=drop_update_vehicle_status_trigger),
    ]