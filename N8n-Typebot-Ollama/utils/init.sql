CREATE DATABASE IF NOT EXISTS `messaging_session`
CHARACTER SET utf8mb4
COLLATE utf8mb4_0900_ai_ci;

USE `messaging_session`;

CREATE TABLE IF NOT EXISTS `sessions` (
    `session_id` VARCHAR(50) NOT NULL,
    `session_date` DATE NOT NULL,
    `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `disposition_code` VARCHAR(255) NULL DEFAULT NULL,
    `ai_summary` TEXT NULL DEFAULT NULL,
    `interaction_score` INT NULL DEFAULT NULL,
    `sf_synced` TINYINT NULL DEFAULT 0,
    `ai_disposition_code` VARCHAR(255) NULL DEFAULT NULL,
    `property` VARCHAR(100) NULL DEFAULT NULL,
    `is_sale` TINYINT(1) NULL DEFAULT 0,
    `handled_by_bot` TINYINT(1) NULL DEFAULT 1 COMMENT '1 = Resuelto por bot, 0 = Requiere humano',
    `escalated_to_human` TINYINT(1) NULL DEFAULT 0 COMMENT '1 = Escalado a Salesforce, 0 = Atendido en bot',
    PRIMARY KEY (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `messages` (
    `id` INT NOT NULL AUTO_INCREMENT,
    `session_id` VARCHAR(50) NULL DEFAULT NULL,
    `timestamp_str` VARCHAR(50) NULL DEFAULT NULL,
    `sender_type` ENUM('CLIENTE', 'AGENTE', 'SISTEMA') NOT NULL,
    `sender_name` VARCHAR(255) NULL DEFAULT NULL,
    `message_text` TEXT NULL DEFAULT NULL,
    `updated_at` TIMESTAMP NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    `extracted_urls` TEXT NULL DEFAULT NULL,
    PRIMARY KEY (`id`),
    INDEX `idx_sender_type` (`sender_type`),
    INDEX `idx_session_id` (`session_id`),
    CONSTRAINT `fk_messages_sessions` 
        FOREIGN KEY (`session_id`) 
        REFERENCES `sessions` (`session_id`) 
        ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
