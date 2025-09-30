from django.db import migrations

CREATE_TRIGGER_SQL = """
CREATE TRIGGER prevent_booking_overlap
BEFORE INSERT ON rental_rentalbooking
FOR EACH ROW
BEGIN
    DECLARE conflict_count INT;

    -- Check for any existing bookings that conflict with the new booking's time slot
    SELECT COUNT(*) INTO conflict_count
    FROM rental_rentalbooking
    WHERE
        vehicle_id = NEW.vehicle_id AND
        NEW.pickup_datetime < return_datetime AND
        NEW.return_datetime > pickup_datetime;

    -- If a conflict is found (count > 0), raise an error
    IF conflict_count > 0 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Booking conflict: The selected time slot is unavailable for this vehicle.';
    END IF;
END;
"""

DROP_TRIGGER_SQL = "DROP TRIGGER IF EXISTS prevent_booking_overlap;"

class Migration(migrations.Migration):

    dependencies = [
        ('rental', '0014_alter_customer_password'),
    ]

    operations = [
        migrations.RunSQL(CREATE_TRIGGER_SQL, reverse_sql=DROP_TRIGGER_SQL),
    ]
