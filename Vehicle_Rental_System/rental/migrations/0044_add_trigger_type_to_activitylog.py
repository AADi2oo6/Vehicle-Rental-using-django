from django.db import migrations

class Migration(migrations.Migration):
    dependencies = [
        ('rental', '0043_customer_is_subscribed_to_newsletter_and_more'),
    ]

    operations = [
        # Add trigger_type column to activity log table
        migrations.RunSQL(
            """
            ALTER TABLE rental_activitylog 
            ADD COLUMN trigger_type VARCHAR(20) NULL AFTER action_type
            """,
            reverse_sql="ALTER TABLE rental_activitylog DROP COLUMN trigger_type"
        ),
        
        # Update existing triggers to populate the trigger_type column
        migrations.RunSQL(
            """
            DROP TRIGGER IF EXISTS tr_payment_before_insert;
            DROP TRIGGER IF EXISTS tr_payment_after_insert;
            DROP TRIGGER IF EXISTS tr_payment_after_update;
            DROP TRIGGER IF EXISTS tr_payment_before_delete;
            """,
            reverse_sql="SELECT 1;"
        ),
        
        # Create new triggers with trigger_type population
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
        
        migrations.RunSQL(
            """
            CREATE TRIGGER tr_payment_after_insert
            AFTER INSERT ON rental_payment
            FOR EACH ROW
            BEGIN
                INSERT INTO rental_activitylog (action_type, trigger_type, details, timestamp, customer_id)
                VALUES (
                    'PAYMENT_CREATED',
                    'INSERT',
                    CONCAT('Payment ID: ', NEW.id, ', Amount: ', NEW.amount, ', Method: ', NEW.payment_method, ', Status: ', NEW.payment_status),
                    NOW(6),
                    NEW.customer_id
                );
            END;
            """,
            reverse_sql="DROP TRIGGER IF EXISTS tr_payment_after_insert;"
        ),
        
        migrations.RunSQL(
            """
            CREATE TRIGGER tr_payment_after_update
            AFTER UPDATE ON rental_payment
            FOR EACH ROW
            BEGIN
                -- Log status changes
                IF OLD.payment_status != NEW.payment_status THEN
                    INSERT INTO rental_activitylog (action_type, trigger_type, details, timestamp, customer_id)
                    VALUES (
                        'PAYMENT_STATUS_CHANGED',
                        'UPDATE',
                        CONCAT('Payment ID: ', NEW.id, ', Status changed from ', OLD.payment_status, ' to ', NEW.payment_status),
                        NOW(6),
                        NEW.customer_id
                    );
                END IF;
                
                -- Log amount changes
                IF OLD.amount != NEW.amount THEN
                    INSERT INTO rental_activitylog (action_type, trigger_type, details, timestamp, customer_id)
                    VALUES (
                        'PAYMENT_AMOUNT_CHANGED',
                        'UPDATE',
                        CONCAT('Payment ID: ', NEW.id, ', Amount changed from ', OLD.amount, ' to ', NEW.amount),
                        NOW(6),
                        NEW.customer_id
                    );
                END IF;
            END;
            """,
            reverse_sql="DROP TRIGGER IF EXISTS tr_payment_after_update;"
        ),
        
        migrations.RunSQL(
            """
            CREATE TRIGGER tr_payment_before_delete
            BEFORE DELETE ON rental_payment
            FOR EACH ROW
            BEGIN
                -- Prevent deletion of completed payments
                IF OLD.payment_status = 'Completed' THEN
                    INSERT INTO rental_activitylog (action_type, trigger_type, details, timestamp, customer_id)
                    VALUES (
                        'PAYMENT_DELETE_ATTEMPT',
                        'DELETE',
                        CONCAT('Attempted deletion of completed payment ID: ', OLD.id, ' by user'),
                        NOW(6),
                        OLD.customer_id
                    );
                    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot delete completed payments';
                END IF;
                
                -- Log deletion attempts for other payments
                INSERT INTO rental_activitylog (action_type, trigger_type, details, timestamp, customer_id)
                VALUES (
                    'PAYMENT_DELETE_ATTEMPT',
                    'DELETE',
                    CONCAT('Deleted payment ID: ', OLD.id),
                    NOW(6),
                    OLD.customer_id
                );
            END;
            """,
            reverse_sql="DROP TRIGGER IF EXISTS tr_payment_before_delete;"
        ),
    ]