from django.db import migrations


forwards_sql = """
-- Procedure: Admin Verify User
CREATE PROCEDURE `sp_AdminVerifyUser`(IN p_customer_id BIGINT)
BEGIN
    DECLARE v_license_number VARCHAR(20);
    SELECT license_number INTO v_license_number FROM rental_customer WHERE id = p_customer_id;

    IF v_license_number IS NULL OR CHAR_LENGTH(v_license_number) <> 15 THEN
        SIGNAL SQLSTATE '45000'
        SET MESSAGE_TEXT = 'Cannot verify: User''s license number is missing or is not 15 characters.';
    ELSE
        UPDATE rental_customer SET is_verified = TRUE WHERE id = p_customer_id;
    END IF;
END;

-- Procedure: Admin Unverify User
DROP PROCEDURE IF EXISTS `sp_AdminUnverifyUser`;
CREATE PROCEDURE `sp_AdminUnverifyUser`(
    IN p_customer_id BIGINT,
    IN p_admin_id INT
)
BEGIN
    UPDATE rental_customer SET is_verified = FALSE WHERE id = p_customer_id;

    INSERT INTO admin_audit_log (admin_id, action_performed, target_customer_id)
    VALUES (p_admin_id, CONCAT('Manually un-verified customer #', p_customer_id), p_customer_id);
END;

-- Procedure: Bulk Update Verification Status
DROP PROCEDURE IF EXISTS `sp_AdminBulkUpdateVerificationStatus`;
CREATE PROCEDURE `sp_AdminBulkUpdateVerificationStatus`(
    IN p_customer_ids TEXT,
    IN p_is_verified_status BOOLEAN,
    IN p_admin_id INT
)
BEGIN
    DECLARE current_customer_id BIGINT;
    DECLARE done INT DEFAULT FALSE;
    DECLARE customer_cursor CURSOR FOR 
        SELECT id FROM rental_customer WHERE FIND_IN_SET(id, p_customer_ids);
    DECLARE CONTINUE HANDLER FOR NOT FOUND SET done = TRUE;

    OPEN customer_cursor;
    read_loop: LOOP
        FETCH customer_cursor INTO current_customer_id;
        IF done THEN
            LEAVE read_loop;
        END IF;
        UPDATE rental_customer SET is_verified = p_is_verified_status WHERE id = current_customer_id;

        -- Log this action in the admin audit log
        INSERT INTO admin_audit_log (admin_id, action_performed, target_customer_id)
        VALUES (p_admin_id, CONCAT('Bulk updated verification status for customer #', current_customer_id, ' to: ', IF(p_is_verified_status, 'Verified', 'Unverified')), current_customer_id);
    END LOOP;
    CLOSE customer_cursor;
END;

-- Procedure: Update User Profile
CREATE PROCEDURE `sp_UpdateUserProfile`(
    IN p_customer_id BIGINT,
    IN p_first_name VARCHAR(150),
    IN p_last_name VARCHAR(150),
    IN p_phone VARCHAR(15),
    IN p_address TEXT,
    IN p_city VARCHAR(50),
    IN p_state VARCHAR(50),
    IN p_zip_code VARCHAR(10),
    IN p_date_of_birth DATE,
    IN p_license_number VARCHAR(20)
    IN p_is_subscribed BOOLEAN
)
BEGIN
    DECLARE v_user_id BIGINT;
    DECLARE v_old_license_number VARCHAR(20);
    DECLARE v_is_verified_status BOOLEAN;

    SELECT user_id INTO v_user_id FROM rental_customer WHERE id = p_customer_id;
    SELECT license_number, is_verified INTO v_old_license_number, v_is_verified_status FROM rental_customer WHERE id = p_customer_id;

    -- Definitive auto-verification logic. This covers all cases.
    -- If the new license number is valid (15 chars), the user should be verified.
    IF (p_license_number IS NOT NULL AND CHAR_LENGTH(p_license_number) = 15) THEN
        SET v_is_verified_status = TRUE;
    -- Otherwise, if the license number has been changed (or removed), force re-verification.
    ELSEIF (p_license_number <> v_old_license_number) OR (p_license_number IS NULL AND v_old_license_number IS NOT NULL) THEN
        SET v_is_verified_status = FALSE;
    END IF;

    START TRANSACTION;
    UPDATE auth_user SET first_name = p_first_name, last_name = p_last_name WHERE id = v_user_id;
    UPDATE rental_customer 
    SET first_name = p_first_name, last_name = p_last_name, phone = p_phone, address = p_address, city = p_city, state = p_state, zip_code = p_zip_code, date_of_birth = p_date_of_birth, license_number = p_license_number, is_subscribed_to_newsletter = p_is_subscribed, is_verified = v_is_verified_status
    WHERE id = p_customer_id;
    COMMIT;
END;
"""

reverse_sql = """
DROP PROCEDURE IF EXISTS `sp_AdminVerifyUser`;
DROP PROCEDURE IF EXISTS `sp_AdminUnverifyUser`;
DROP PROCEDURE IF EXISTS `sp_AdminBulkUpdateVerificationStatus`;
DROP PROCEDURE IF EXISTS `sp_UpdateUserProfile`;
"""

class Migration(migrations.Migration):

    dependencies = [
        ('rental', '0021_vehicle_status_trigger'),
    ]

    operations = [
        migrations.RunSQL(forwards_sql, reverse_sql=reverse_sql),
    ]