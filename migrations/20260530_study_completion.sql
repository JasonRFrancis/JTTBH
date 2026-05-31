-- Study completion tracking: records which sources a user has completed per day
-- Idempotent: uses CREATE TABLE IF NOT EXISTS

CREATE TABLE IF NOT EXISTS study_completion (
  id              INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  completionID    VARCHAR(36) NOT NULL,
  userID          VARCHAR(36) NOT NULL,
  sourceID        VARCHAR(36) NOT NULL,
  completed_date  DATE NOT NULL,
  created         DATETIME,
  created_by      VARCHAR(36),
  UNIQUE KEY uq_completion_id (completionID),
  UNIQUE KEY uq_user_source_date (userID, sourceID, completed_date),
  KEY idx_user_date (userID, completed_date)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
