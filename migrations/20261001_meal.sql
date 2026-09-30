-- 20261001_meal.sql
-- Meal / macro tracker backed by Open Food Facts. Safe to re-run.
-- Recipe ↔ food links live in recipe.ingredients JSON (keys foodID, grams); no recipe DDL needed.

CREATE TABLE IF NOT EXISTS `food` (
  `id`        INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `foodID`    VARCHAR(36)  NOT NULL,
  `code`      VARCHAR(32)  DEFAULT NULL COMMENT 'Barcode; NULL for custom foods without one',
  `userID`    VARCHAR(36)  DEFAULT NULL COMMENT 'Owner of a custom food; NULL for OFF cache rows',
  `name`      VARCHAR(500) NOT NULL,
  `brand`     VARCHAR(255) DEFAULT NULL,
  `serving_g` DECIMAL(8,2) DEFAULT NULL,
  `kcal`      DECIMAL(8,2) DEFAULT NULL COMMENT 'All nutrients per 100 g',
  `protein`   DECIMAL(8,2) DEFAULT NULL,
  `carbs`     DECIMAL(8,2) DEFAULT NULL,
  `fat`       DECIMAL(8,2) DEFAULT NULL,
  `fiber`     DECIMAL(8,2) DEFAULT NULL,
  `sugar`     DECIMAL(8,2) DEFAULT NULL,
  `sodium`    DECIMAL(8,3) DEFAULT NULL COMMENT 'grams, as OFF stores it',
  `source`    ENUM('off','custom') NOT NULL,
  `fetched`   DATETIME DEFAULT NULL,
  `created`   DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_food` (`foodID`),
  UNIQUE KEY `uq_food_code` (`code`),
  KEY `idx_food_name` (`name`(100))
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `meal` (
  `id`       INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `mealID`   VARCHAR(36)  NOT NULL,
  `userID`   VARCHAR(36)  NOT NULL,
  `name`     VARCHAR(100) DEFAULT NULL COMMENT 'NULL = soft deleted',
  `eaten_at` DATETIME     NOT NULL COMMENT 'user-local time',
  `created`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_meal_user_time` (`userID`, `eaten_at`),
  KEY `idx_meal_id` (`mealID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS `meal_item` (
  `id`       INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `itemID`   VARCHAR(36)  NOT NULL,
  `mealID`   VARCHAR(36)  NOT NULL,
  `userID`   VARCHAR(36)  NOT NULL,
  `label`    VARCHAR(500) DEFAULT NULL COMMENT 'NULL = soft deleted',
  `recipeID` VARCHAR(36)  DEFAULT NULL,
  `foodID`   VARCHAR(36)  DEFAULT NULL,
  `quantity` DECIMAL(8,2) NOT NULL DEFAULT 1,
  `unit`     ENUM('serving','g') NOT NULL,
  `kcal`     DECIMAL(8,2) DEFAULT NULL COMMENT 'Snapshot at log time',
  `protein`  DECIMAL(8,2) DEFAULT NULL,
  `carbs`    DECIMAL(8,2) DEFAULT NULL,
  `fat`      DECIMAL(8,2) DEFAULT NULL,
  `created`  DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_meal_item_meal` (`mealID`),
  KEY `idx_meal_item_id` (`itemID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

INSERT INTO `user_permissionAccess` (access, name, resource, description, created, created_by)
SELECT 131072, 'Meal', 'meal', 'Meal / macro tracker', NOW(), '58ec8c11-e060-4367-93cf-91a6cc28db8c'
WHERE NOT EXISTS (SELECT 1 FROM `user_permissionAccess` WHERE access = 131072);
