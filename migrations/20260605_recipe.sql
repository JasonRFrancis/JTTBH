-- Recipe tracker feature
-- recipe: insert-only, soft-delete via title IS NULL
-- recipe_image: direct INSERT/DELETE

CREATE TABLE IF NOT EXISTS recipe (
  id          INT UNSIGNED NOT NULL AUTO_INCREMENT,
  recipeID    VARCHAR(36)  NOT NULL,
  userID      VARCHAR(36)  NOT NULL,
  title       VARCHAR(500) DEFAULT NULL,
  source      TEXT,
  type        VARCHAR(100),
  servings    VARCHAR(100),
  prep_time   VARCHAR(100),
  cook_time   VARCHAR(100),
  ingredients TEXT,
  directions  TEXT,
  notes       TEXT,
  position    INT NOT NULL DEFAULT 0,
  created     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  created_by  VARCHAR(36),
  PRIMARY KEY (id),
  KEY idx_recipe_user (userID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS recipe_image (
  id        INT UNSIGNED NOT NULL AUTO_INCREMENT,
  imageID   VARCHAR(36)  NOT NULL,
  recipeID  VARCHAR(36)  NOT NULL,
  userID    VARCHAR(36)  NOT NULL,
  url       TEXT         NOT NULL,
  caption   VARCHAR(500),
  position  INT NOT NULL DEFAULT 0,
  created   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (id),
  UNIQUE KEY uq_image (imageID),
  KEY idx_image_recipe (recipeID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
