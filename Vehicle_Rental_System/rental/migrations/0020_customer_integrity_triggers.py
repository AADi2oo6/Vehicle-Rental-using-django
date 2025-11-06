from django.db import migrations


forwards_sql = """
-- Create the audit table, ensuring customer_id matches rental_customer.id
CREATE TABLE IF NOT EXISTS `audit_user_changes` (
  `id` INT AUTO_INCREMENT PRIMARY KEY,
  `customer_id` BIGINT NOT NULL,
  `changed_field` VARCHAR(50) NOT NULL,
  `old_value` TEXT,
  `new_value` TEXT,
  `timestamp` DATETIME DEFAULT CURRENT_TIMESTAMP,
  FOREIGN KEY (`customer_id`) REFERENCES `rental_customer`(`id`) ON DELETE CASCADE
);

-- Trigger: BEFORE INSERT on rental_customer
CREATE TRIGGER `trg_Customer_Before_Insert`
BEFORE INSERT ON `rental_customer`
FOR EACH ROW
BEGIN
    -- Age Check
    IF TIMESTAMPDIFF(YEAR, NEW.date_of_birth, CURDATE()) < 18 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'User must be at least 18 years old to register.';
    END IF;
    -- Generate unique referral code
    IF NEW.referral_code IS NULL OR NEW.referral_code = '' THEN
        SET NEW.referral_code = SUBSTRING(MD5(RAND()), 1, 8);
    END IF;
    -- Default Status
    SET NEW.is_verified = FALSE;
END;

-- Trigger: AFTER INSERT on rental_customer
CREATE TRIGGER `trg_Customer_After_Insert`
AFTER INSERT ON `rental_customer`
FOR EACH ROW UPDATE `dashboard_analytics` SET total_customers = total_customers + 1 WHERE id = 1;

-- Trigger: BEFORE UPDATE on rental_customer
CREATE TRIGGER `trg_Customer_Before_Update`
BEFORE UPDATE ON `rental_customer`
FOR EACH ROW
BEGIN
    IF NEW.date_of_birth <> OLD.date_of_birth AND TIMESTAMPDIFF(YEAR, NEW.date_of_birth, CURDATE()) < 18 THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'User must be at least 18 years old.';
    END IF;
    IF NEW.referral_code <> OLD.referral_code THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Referral code cannot be changed.';
    END IF;
    -- License Re-Verification
    IF NEW.license_number <> OLD.license_number THEN
        SET NEW.is_verified = FALSE;
    END IF;
END;

-- Trigger: AFTER UPDATE on rental_customer
CREATE TRIGGER `trg_Customer_After_Update`
AFTER UPDATE ON `rental_customer`
FOR EACH ROW
BEGIN
    IF OLD.phone <> NEW.phone THEN
        INSERT INTO audit_user_changes(customer_id, changed_field, old_value, new_value) VALUES (NEW.id, 'phone', OLD.phone, NEW.phone);
    END IF;
    IF OLD.address <> NEW.address THEN
        INSERT INTO audit_user_changes(customer_id, changed_field, old_value, new_value) VALUES (NEW.id, 'address', OLD.address, NEW.address);
    END IF;
    IF OLD.license_number <> NEW.license_number THEN
        INSERT INTO audit_user_changes(customer_id, changed_field, old_value, new_value) VALUES (NEW.id, 'license_number', OLD.license_number, NEW.license_number);
    END IF;

    -- Admin Audit for status changes
    IF OLD.is_verified <> NEW.is_verified THEN
        INSERT INTO admin_audit_log(action_performed, target_customer_id)
        VALUES (CONCAT('Account status changed from ', IF(OLD.is_verified, "'Verified'", "'Not Verified'"), ' to ', IF(NEW.is_verified, "'Verified'", "'Not Verified'")), NEW.id);
    END IF;
END;

-- Trigger: BEFORE DELETE on rental_customer
CREATE TRIGGER `trg_Customer_Before_Delete`
BEFORE DELETE ON `rental_customer`
FOR EACH ROW
BEGIN
    -- Deletion Block for verified accounts
    IF OLD.is_verified = TRUE THEN
        SIGNAL SQLSTATE '45000' SET MESSAGE_TEXT = 'Verified accounts cannot be deleted.';
    END IF;
END;

-- Trigger: AFTER DELETE on rental_customer
CREATE TRIGGER `trg_Customer_After_Delete`
AFTER DELETE ON `rental_customer`
FOR EACH ROW UPDATE `dashboard_analytics` SET total_customers = total_customers - 1 WHERE id = 1;
"""

reverse_sql = """
DROP TRIGGER IF EXISTS `trg_Customer_After_Insert`;
DROP TRIGGER IF EXISTS `trg_Customer_After_Delete`;
DROP TRIGGER IF EXISTS `trg_Customer_Before_Insert`;
DROP TRIGGER IF EXISTS `trg_Customer_Before_Update`;
DROP TRIGGER IF EXISTS `trg_Customer_After_Update`;
DROP TRIGGER IF EXISTS `trg_Customer_Before_Delete`;
DROP TABLE IF EXISTS `audit_user_changes`;
"""

class Migration(migrations.Migration):

    dependencies = [
        ('rental', '0019_log_booking_completion_trigger'),
    ]

    operations = [
        migrations.RunSQL(forwards_sql, reverse_sql=reverse_sql),
    ]