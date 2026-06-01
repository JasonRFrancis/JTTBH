-- Smart subscription filters and personal calendar scheduling

-- Add smart filter columns to study_subscription (direct ALTER — not insert-only)
ALTER TABLE study_subscription
  ADD COLUMN filter_author        VARCHAR(500) DEFAULT NULL,
  ADD COLUMN filter_category      VARCHAR(500) DEFAULT NULL,
  ADD COLUMN sort_order           ENUM('natural','newest','oldest') NOT NULL DEFAULT 'natural',
  ADD COLUMN limit_count           INT DEFAULT NULL,
  ADD COLUMN start_offset          INT NOT NULL DEFAULT 0,
  ADD COLUMN `repeat`              TINYINT NOT NULL DEFAULT 1,
  ADD COLUMN use_personal_schedule TINYINT NOT NULL DEFAULT 0;

-- Personal calendar scheduling by subscriber
CREATE TABLE IF NOT EXISTS study_schedule (
  id             INT NOT NULL AUTO_INCREMENT,
  scheduleID     VARCHAR(36) NOT NULL,
  userID         VARCHAR(36) NOT NULL,
  sourceID       VARCHAR(36) NOT NULL,
  scheduled_date DATE NOT NULL,
  created        DATETIME NOT NULL,
  created_by     VARCHAR(36) NOT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_user_source  (userID, sourceID),
  UNIQUE KEY uq_schedule_id  (scheduleID),
  KEY idx_schedule_user_date (userID, scheduled_date),
  CONSTRAINT fk_schedule_user FOREIGN KEY (userID) REFERENCES `user` (userID) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
