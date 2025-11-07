from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rental', '0034_payment_indexes'),
    ]

    operations = [
        # This migration is intentionally left empty as the indexes already exist
        # We're just marking it as applied to avoid future conflicts
        migrations.RunSQL(
            "SELECT 1;",  # No-op SQL
            reverse_sql="SELECT 1;"
        ),
    ]