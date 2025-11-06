from django.db import migrations

# This SQL defines the trigger to be created.
# It automatically logs an activity when a booking is marked as 'Completed'.
create_trigger_sql = """
CREATE TRIGGER log_booking_completion
AFTER UPDATE ON rental_rentalbooking
FOR EACH ROW
BEGIN
    -- Check if the status is changing TO 'Completed' from something else
    IF NEW.booking_status = 'Completed' AND OLD.booking_status <> 'Completed' THEN
        INSERT INTO rental_customeractivitylog (customer_id, activity_type, description, timestamp)
        VALUES (NEW.customer_id, 'Booking Completed', CONCAT('Booking #', NEW.id, ' marked as completed.'), NOW());
    END IF;
END;
"""

# This SQL is for reversing the migration (i.e., dropping the trigger).
drop_trigger_sql = "DROP TRIGGER IF EXISTS log_booking_completion;"

class Migration(migrations.Migration):

    dependencies = [
        ('rental', '0015_customer_is_subscribed_to_newsletter_and_more'),
    ]

    operations = [
        migrations.RunSQL(create_trigger_sql, reverse_sql=drop_trigger_sql),
    ]