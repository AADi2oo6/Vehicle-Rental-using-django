from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rental', '0037_add_payment_indexes'),
    ]

    operations = [
        # Drop existing triggers if they exist
        migrations.RunSQL(
            """
            DROP TRIGGER IF EXISTS tr_payment_before_insert;
            DROP TRIGGER IF EXISTS tr_payment_after_insert;
            DROP TRIGGER IF EXISTS tr_payment_after_update;
            DROP TRIGGER IF EXISTS tr_payment_before_delete;
            """,
            reverse_sql="SELECT 1;"
        ),
        
        # Create BEFORE INSERT trigger - Validate amount/status before inserting
        migrations.RunSQL(
            """
            CREATE TRIGGER tr_payment_before_insert
            BEFORE INSERT ON rental_payment
            FOR EACH ROW
            BEGIN
                -- Validate amount is not negative
                IF NEW.amount < 0 THEN
                    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Payment amount cannot be negative';
                END IF;
                
                -- Validate payment status is valid
                IF NEW.payment_status NOT IN ('Pending', 'Completed', 'Failed', 'Refunded') THEN
                    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid payment status';
                END IF;
                
                -- Validate payment method is valid
                IF NEW.payment_method NOT IN ('Cash', 'Credit Card', 'Debit Card', 'UPI', 'Net Banking') THEN
                    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Invalid payment method';
                END IF;
                
                -- Set default processed_by if not provided
                IF NEW.processed_by IS NULL OR NEW.processed_by = '' THEN
                    SET NEW.processed_by = 'System';
                END IF;
            END;
            """,
            reverse_sql="DROP TRIGGER IF EXISTS tr_payment_before_insert;"
        ),
        
        # Create AFTER INSERT trigger - Log or update related tables (bookings, analytics)
        migrations.RunSQL(
            """
            CREATE TRIGGER tr_payment_after_insert
            AFTER INSERT ON rental_payment
            FOR EACH ROW
            BEGIN
                -- Update booking status if payment is completed and it's a full payment
                IF NEW.payment_status = 'Completed' AND NEW.payment_type = 'Full Payment' THEN
                    UPDATE rental_rentalbooking 
                    SET booking_status = 'Confirmed' 
                    WHERE id = NEW.booking_id;
                END IF;
                
                -- Log the payment insertion into activity log
                INSERT INTO rental_activitylog (customer_id, action_type, details, timestamp)
                VALUES (
                    NEW.customer_id, 
                    'PAYMENT_CREATED', 
                    CONCAT('Payment ID ', NEW.id, ' created for booking ', NEW.booking_id, ' with amount ', NEW.amount),
                    NOW()
                );
            END;
            """,
            reverse_sql="DROP TRIGGER IF EXISTS tr_payment_after_insert;"
        ),
        
        # Create AFTER UPDATE trigger - Track changes in payment status or amount
        migrations.RunSQL(
            """
            CREATE TRIGGER tr_payment_after_update
            AFTER UPDATE ON rental_payment
            FOR EACH ROW
            BEGIN
                -- Track payment status changes
                IF OLD.payment_status != NEW.payment_status THEN
                    -- Log status change
                    INSERT INTO rental_activitylog (customer_id, action_type, details, timestamp)
                    VALUES (
                        NEW.customer_id,
                        'PAYMENT_STATUS_CHANGED',
                        CONCAT('Payment ID ', NEW.id, ' status changed from ', OLD.payment_status, ' to ', NEW.payment_status),
                        NOW()
                    );
                    
                    -- Update booking status based on payment status
                    IF NEW.payment_status = 'Completed' THEN
                        UPDATE rental_rentalbooking 
                        SET booking_status = 'Confirmed' 
                        WHERE id = NEW.booking_id;
                    ELSEIF NEW.payment_status = 'Refunded' THEN
                        UPDATE rental_rentalbooking 
                        SET booking_status = 'Cancelled' 
                        WHERE id = NEW.booking_id;
                    END IF;
                END IF;
                
                -- Track payment amount changes
                IF OLD.amount != NEW.amount THEN
                    INSERT INTO rental_activitylog (customer_id, action_type, details, timestamp)
                    VALUES (
                        NEW.customer_id,
                        'PAYMENT_AMOUNT_CHANGED',
                        CONCAT('Payment ID ', NEW.id, ' amount changed from ', OLD.amount, ' to ', NEW.amount),
                        NOW()
                    );
                END IF;
            END;
            """,
            reverse_sql="DROP TRIGGER IF EXISTS tr_payment_after_update;"
        ),
        
        # Create BEFORE DELETE trigger - Prevent deleting completed transactions
        migrations.RunSQL(
            """
            CREATE TRIGGER tr_payment_before_delete
            BEFORE DELETE ON rental_payment
            FOR EACH ROW
            BEGIN
                -- Prevent deletion of completed payments
                IF OLD.payment_status = 'Completed' THEN
                    SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Cannot delete completed payments';
                END IF;
                
                -- Log the deletion attempt
                INSERT INTO rental_activitylog (customer_id, action_type, details, timestamp)
                VALUES (
                    OLD.customer_id,
                    'PAYMENT_DELETE_ATTEMPT',
                    CONCAT('Attempt to delete Payment ID ', OLD.id, ' with status ', OLD.payment_status),
                    NOW()
                );
            END;
            """,
            reverse_sql="DROP TRIGGER IF EXISTS tr_payment_before_delete;"
        ),
    ]