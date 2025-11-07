from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rental', '0033_payment_status_views'),
    ]

    operations = [
        # Drop existing views first
        migrations.RunSQL(
            """
            DROP VIEW IF EXISTS vw_completed_payments;
            DROP VIEW IF EXISTS vw_pending_payments;
            DROP VIEW IF EXISTS vw_refunded_payments;
            DROP VIEW IF EXISTS vw_failed_payments;
            """,
            reverse_sql="SELECT 1"
        ),
        
        # Recreate views with optimized queries
        migrations.RunSQL(
            """
            CREATE VIEW vw_completed_payments AS
            SELECT 
                id,
                booking_id,
                customer_id,
                payment_date,
                amount,
                payment_method,
                payment_type,
                transaction_id,
                payment_status,
                reference_number,
                notes,
                processed_by
            FROM rental_payment
            WHERE payment_status = 'Completed'
            ORDER BY payment_date DESC
            """,
            reverse_sql="DROP VIEW IF EXISTS vw_completed_payments"
        ),
        
        migrations.RunSQL(
            """
            CREATE VIEW vw_pending_payments AS
            SELECT 
                id,
                booking_id,
                customer_id,
                payment_date,
                amount,
                payment_method,
                payment_type,
                transaction_id,
                payment_status,
                reference_number,
                notes,
                processed_by
            FROM rental_payment
            WHERE payment_status = 'Pending'
            ORDER BY payment_date DESC
            """,
            reverse_sql="DROP VIEW IF EXISTS vw_pending_payments"
        ),
        
        migrations.RunSQL(
            """
            CREATE VIEW vw_refunded_payments AS
            SELECT 
                id,
                booking_id,
                customer_id,
                payment_date,
                amount,
                payment_method,
                payment_type,
                transaction_id,
                payment_status,
                reference_number,
                notes,
                processed_by
            FROM rental_payment
            WHERE payment_status = 'Refunded'
            ORDER BY payment_date DESC
            """,
            reverse_sql="DROP VIEW IF EXISTS vw_refunded_payments"
        ),
        
        migrations.RunSQL(
            """
            CREATE VIEW vw_failed_payments AS
            SELECT 
                id,
                booking_id,
                customer_id,
                payment_date,
                amount,
                payment_method,
                payment_type,
                transaction_id,
                payment_status,
                reference_number,
                notes,
                processed_by
            FROM rental_payment
            WHERE payment_status = 'Failed'
            ORDER BY payment_date DESC
            """,
            reverse_sql="DROP VIEW IF EXISTS vw_failed_payments"
        ),
    ]