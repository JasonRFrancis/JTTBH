-- 20261006_journal_template.sql
-- Journal templates: user-defined question form, answers stored as one JSON body per day. Safe to re-run.

CREATE TABLE IF NOT EXISTS `journal_template` (
  `id`         INT NOT NULL AUTO_INCREMENT,
  `userID`     VARCHAR(36) NOT NULL,
  `body`       TEXT NOT NULL COMMENT 'Template markup; latest row per user is current',
  `created`    DATETIME DEFAULT CURRENT_TIMESTAMP,
  `created_by` VARCHAR(36) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_template_user` (`userID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

CREATE TABLE IF NOT EXISTS `journal_entry` (
  `id`         INT NOT NULL AUTO_INCREMENT,
  `entryID`    VARCHAR(36) NOT NULL,
  `userID`     VARCHAR(36) NOT NULL,
  `answered`   DATE NOT NULL,
  `body`       JSON NOT NULL COMMENT '[{type,label,options,value}] — self-describing; latest row per (userID, answered) is current',
  `created`    DATETIME DEFAULT CURRENT_TIMESTAMP,
  `created_by` VARCHAR(36) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_entry_user_date` (`userID`, `answered`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
