-- Quote tracker table
-- Insert-only: body = NULL means soft-deleted

CREATE TABLE IF NOT EXISTS quote (
  id         INT NOT NULL AUTO_INCREMENT,
  quoteID    VARCHAR(36) NOT NULL,
  userID     VARCHAR(36) NOT NULL,
  body       TEXT DEFAULT NULL,
  author     VARCHAR(255) DEFAULT NULL,
  title      VARCHAR(500) DEFAULT NULL,
  source     VARCHAR(1000) DEFAULT NULL,
  tags       VARCHAR(500) DEFAULT NULL,
  created    DATETIME NOT NULL,
  created_by VARCHAR(36) NOT NULL,
  PRIMARY KEY (id),
  KEY idx_quote_id (quoteID),
  KEY idx_quote_user (userID),
  CONSTRAINT fk_quote_user FOREIGN KEY (userID) REFERENCES user (userID) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
