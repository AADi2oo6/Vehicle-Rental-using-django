from django.db import migrations

# This SQL statement creates a VIEW that joins three tables together.
# A VIEW is like a virtual, read-only table that simplifies complex queries.
CREATE_VIEW_SQL = """
CREATE OR REPLACE VIEW vw_detailed_reviews AS
SELECT
    fr.id AS review_id,
    fr.rating,
    fr.review_text,
    fr.review_date,
    c.first_name,
    c.last_name,
    c.profile_picture,
    v.make AS vehicle_make,
    v.model AS vehicle_model
FROM
    rental_feedbackreview fr
JOIN
    rental_customer c ON fr.customer_id = c.id
JOIN
    rental_vehicle v ON fr.vehicle_id = v.id
WHERE
    fr.is_public = TRUE;
"""

# This SQL statement is used to remove the VIEW if we ever need to reverse the migration.
DROP_VIEW_SQL = "DROP VIEW IF EXISTS vw_detailed_reviews;"

class Migration(migrations.Migration):

    dependencies = [
        # Make sure this points to your previous migration file (the trigger one)
        ('rental', '0016_alter_customer_password_alter_payment_payment_status_and_more'), 
    ]

    operations = [
        migrations.RunSQL(CREATE_VIEW_SQL, reverse_sql=DROP_VIEW_SQL),
    ]
