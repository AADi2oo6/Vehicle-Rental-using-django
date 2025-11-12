from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('rental', '0044_add_trigger_type_to_activitylog'),
    ]

    operations = [
        # Drop and recreate the BEFORE INSERT trigger to include Razorpay as a valid payment method
        migrations.RunSQL(
            """
            DROP TRIGGER IF EXISTS tr_payment_before_insert;
            """,
            reverse_sql="SELECT 1;"
        ),
        
        # Create updated BEFORE INSERT trigger
        migrations.RunSQL(
            """
            CREATE TRIGGER tr_payment_before_insert
            BEFORE INSERT ON rental_payment
            FOR EACH ROW
            BEGIN
                -- Validate payment method
                IF NEW.payment_method NOT IN ('Credit Card', 'Debit Card', 'Net Banking', 'UPI', 'Cash', 'Razorpay') THEN
                    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid payment method';
                END IF;
                
                -- Validate amount for completed payments
                IF NEW.payment_status = 'Completed' AND (NEW.amount IS NULL OR NEW.amount <= 0) THEN
                    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Completed payments must have a positive amount';
                END IF;
                
                -- Set transaction ID requirement
                IF NEW.payment_status = 'Completed' AND (NEW.transaction_id IS NULL OR NEW.transaction_id = '') THEN
                    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'A completed payment must have a transaction ID.';
                END IF;
            END;
            """,
            reverse_sql="DROP TRIGGER IF EXISTS tr_payment_before_insert;"
        ),
    ]