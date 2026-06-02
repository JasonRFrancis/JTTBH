-- Add favorite flag to bookmark
ALTER TABLE bookmark ADD COLUMN favorite TINYINT(1) NOT NULL DEFAULT 0 AFTER `read`;

-- Categories (direct UPDATE, not insert-only)
CREATE TABLE IF NOT EXISTS bookmark_category (
  id INT NOT NULL AUTO_INCREMENT,
  categoryID VARCHAR(36) NOT NULL,
  userID VARCHAR(36) NOT NULL,
  name VARCHAR(200) NOT NULL,
  position INT NOT NULL DEFAULT 0,
  criteria TEXT DEFAULT NULL,
  created DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_by VARCHAR(36) DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_categoryID (categoryID),
  KEY idx_bcat_user (userID),
  CONSTRAINT fk_bcat_user FOREIGN KEY (userID) REFERENCES `user` (userID) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- Category membership (direct INSERT/DELETE)
CREATE TABLE IF NOT EXISTS bookmark_category_item (
  id INT NOT NULL AUTO_INCREMENT,
  categoryID VARCHAR(36) NOT NULL,
  bookmarkID VARCHAR(36) NOT NULL,
  userID VARCHAR(36) NOT NULL,
  position INT NOT NULL DEFAULT 0,
  created DATETIME DEFAULT CURRENT_TIMESTAMP,
  created_by VARCHAR(36) DEFAULT NULL,
  PRIMARY KEY (id),
  UNIQUE KEY uq_cat_bm (categoryID, bookmarkID),
  KEY idx_catitem_cat (categoryID),
  KEY idx_catitem_bm (bookmarkID),
  CONSTRAINT fk_catitem_cat FOREIGN KEY (categoryID) REFERENCES bookmark_category (categoryID) ON DELETE CASCADE,
  CONSTRAINT fk_catitem_bm FOREIGN KEY (bookmarkID) REFERENCES bookmark (bookmarkID) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
