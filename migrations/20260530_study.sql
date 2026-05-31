-- Study feature: collections, sources, subscriptions
-- Idempotent: uses CREATE TABLE IF NOT EXISTS

CREATE TABLE IF NOT EXISTS study_collection (
  id            INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  collectionID  VARCHAR(36) NOT NULL,
  userID        VARCHAR(36) NOT NULL,
  name          VARCHAR(200) DEFAULT NULL,
  description   TEXT,
  mode          ENUM('rate', 'calendar') NOT NULL DEFAULT 'rate',
  created       DATETIME,
  created_by    VARCHAR(36),
  KEY idx_collection_id (collectionID),
  KEY idx_collection_user (userID)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS study_source (
  id            INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  sourceID      VARCHAR(36) NOT NULL,
  collectionID  VARCHAR(36) NOT NULL,
  userID        VARCHAR(36) NOT NULL,
  category      VARCHAR(100),
  title         VARCHAR(500) DEFAULT NULL,
  subtitle      VARCHAR(500),
  author        VARCHAR(200),
  url           VARCHAR(1000),
  audio_url     VARCHAR(1000),
  audio_length  VARCHAR(20),
  order_by      INT NOT NULL DEFAULT 0,
  scheduled_date DATE,
  created       DATETIME,
  created_by    VARCHAR(36),
  KEY idx_source_id (sourceID),
  KEY idx_source_collection (collectionID)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;

-- Direct DELETE (not insert-only); UNIQUE on (userID, collectionID) prevents duplicate subscriptions
CREATE TABLE IF NOT EXISTS study_subscription (
  id              INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
  subscriptionID  VARCHAR(36) NOT NULL,
  userID          VARCHAR(36) NOT NULL,
  collectionID    VARCHAR(36) NOT NULL,
  per_day         INT NOT NULL DEFAULT 1,
  start_date      DATE,
  created         DATETIME,
  created_by      VARCHAR(36),
  UNIQUE KEY uq_subscription_id (subscriptionID),
  UNIQUE KEY uq_user_collection (userID, collectionID)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
