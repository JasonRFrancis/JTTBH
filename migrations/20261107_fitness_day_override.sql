-- 20261107_fitness_day_override.sql
-- Per-date exercise skips/additions on top of the weekly program. Safe to re-run.
-- Insert-only: latest row per (userID, override_date, exerciseID) is current; action NULL = cleared.

CREATE TABLE IF NOT EXISTS `fitness_dayOverride` (
  `id`            INT NOT NULL AUTO_INCREMENT,
  `userID`        VARCHAR(36) NOT NULL,
  `override_date` DATE NOT NULL,
  `exerciseID`    VARCHAR(36) NOT NULL,
  `action`        ENUM('skip','add') DEFAULT NULL,
  `created`       DATETIME NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_user_date` (`userID`, `override_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Per-day exercise skips/additions';
