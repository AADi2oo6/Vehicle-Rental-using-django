from django.db import migrations

# --- THIS IS THE RAW SQL FOR YOUR TEACHER ---
# DBMS Concept: Database Trigger (AFTER UPDATE)
# Purpose: Creates a secure, automatic audit log for any changes to customer data.
# This trigger runs *after* an UPDATE on rental_customer. It compares OLD and NEW
# values and builds a detailed log string of what changed.

CREATE_AUDIT_TRIGGER_SQL = """
CREATE TRIGGER trg_customer_profile_update
AFTER UPDATE ON rental_customer
FOR EACH ROW
BEGIN
    DECLARE changes_details TEXT;
    SET changes_details = '';

    -- Check each field for changes
    IF OLD.first_name != NEW.first_name THEN
        SET changes_details = CONCAT(changes_details, 'First Name: ''', OLD.first_name, ''' -> ''', NEW.first_name, '''. ');
    END IF;
    IF OLD.last_name != NEW.last_name THEN
        SET changes_details = CONCAT(changes_details, 'Last Name: ''', OLD.last_name, ''' -> ''', NEW.last_name, '''. ');
    END IF;
    IF OLD.phone != NEW.phone THEN
        SET changes_details = CONCAT(changes_details, 'Phone: ''', OLD.phone, ''' -> ''', NEW.phone, '''. ');
    END IF;
    IF IFNULL(OLD.address, '') != IFNULL(NEW.address, '') THEN
        SET changes_details = CONCAT(changes_details, 'Address: ''', IFNULL(OLD.address, 'NULL'), ''' -> ''', IFNULL(NEW.address, 'NULL'), '''. ');
    END IF;
    IF IFNULL(OLD.city, '') != IFNULL(NEW.city, '') THEN
        SET changes_details = CONCAT(changes_details, 'City: ''', IFNULL(OLD.city, 'NULL'), ''' -> ''', IFNULL(NEW.city, 'NULL'), '''. ');
    END IF;
    IF IFNULL(OLD.state, '') != IFNULL(NEW.state, '') THEN
        SET changes_details = CONCAT(changes_details, 'State: ''', IFNULL(OLD.state, 'NULL'), ''' -> ''', IFNULL(NEW.state, 'NULL'), '''. ');
    END IF;
    IF IFNULL(OLD.zip_code, '') != IFNULL(NEW.zip_code, '') THEN
        SET changes_details = CONCAT(changes_details, 'Zip: ''', IFNULL(OLD.zip_code, 'NULL'), ''' -> ''', IFNULL(NEW.zip_code, 'NULL'), '''. ');
    END IF;
    IF IFNULL(OLD.license_number, '') != IFNULL(NEW.license_number, '') THEN
        SET changes_details = CONCAT(changes_details, 'License: ''', IFNULL(OLD.license_number, 'NULL'), ''' -> ''', IFNULL(NEW.license_number, 'NULL'), '''. ');
    END IF;

    -- If any changes were detected, insert a log record
    IF changes_details != '' THEN
        INSERT INTO rental_activitylog (customer_id, action_type, details, timestamp)
        VALUES (NEW.id, 'PROFILE_UPDATE', CONCAT('Trigger audit: ', changes_details), NOW());
    END IF;
END;
"""

DROP_AUDIT_TRIGGER_SQL = "DROP TRIGGER IF EXISTS trg_customer_profile_update;"

class Migration(migrations.Migration):

    dependencies = [
        ('rental', '0019_detailedreview_alter_customer_password'),
    ]

    operations = [
        migrations.RunSQL(CREATE_AUDIT_TRIGGER_SQL, reverse_sql=DROP_AUDIT_TRIGGER_SQL),
    ]
