from django.db import migrations


forwards_sql = """
-- Indexes
CREATE INDEX `idx_customer_status` ON `rental_customer`(`is_verified`);
CREATE INDEX `idx_customer_license` ON `rental_customer`(`license_number`);
CREATE UNIQUE INDEX `idx_customer_referral_code` ON `rental_customer`(`referral_code`);

-- Check Constraint
ALTER TABLE `rental_customer` ADD CONSTRAINT `chk_license_length` CHECK (license_number IS NULL OR CHAR_LENGTH(license_number) = 15);
"""

reverse_sql = """
-- Note: Dropping indexes and constraints requires knowing their names.
-- The following syntax is for MySQL 8+ and is safer.
ALTER TABLE `rental_customer` DROP INDEX IF EXISTS `idx_customer_status`;
ALTER TABLE `rental_customer` DROP INDEX IF EXISTS `idx_customer_license`;
ALTER TABLE `rental_customer` DROP INDEX IF EXISTS `idx_customer_referral_code`;
ALTER TABLE `rental_customer` DROP CONSTRAINT IF EXISTS `chk_license_length`;
"""

class Migration(migrations.Migration):

    dependencies = [
        ('rental', '0022_user_management_procedures'),
    ]

    operations = [
        migrations.RunSQL(forwards_sql, reverse_sql=reverse_sql),
    ]