-- Adds error_report: unified table for system errors (captured automatically
-- on 500s), user-submitted bug reports, and feature requests. See schema.sql
-- for the authoritative column list.

CREATE TABLE `error_report` (
  `id`            INT NOT NULL AUTO_INCREMENT,
  `reportID`      VARCHAR(36) NOT NULL,
  `type`          ENUM('system_error','bug_report','feature_request') NOT NULL,
  `status`        ENUM('new','in_progress','resolved','wont_fix','duplicate') NOT NULL DEFAULT 'new',
  `priority`      ENUM('low','medium','high','critical') NOT NULL DEFAULT 'medium',
  `title`         VARCHAR(255) NOT NULL,
  `description`   TEXT,
  `admin_notes`   TEXT,
  `userID`        VARCHAR(36) DEFAULT NULL,
  `username`      VARCHAR(50) DEFAULT NULL,
  `url`           VARCHAR(512) DEFAULT NULL,
  `http_method`   VARCHAR(10) DEFAULT NULL,
  `http_status`   INT DEFAULT NULL,
  `stack_trace`   TEXT,
  `request_data`  TEXT,
  `user_agent`    VARCHAR(512) DEFAULT NULL,
  `ip`            VARCHAR(45) DEFAULT NULL,
  `created`       DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by`    VARCHAR(36) DEFAULT NULL,
  `resolved_at`   DATETIME DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `reportID` (`reportID`),
  KEY `idx_error_report_type_status` (`type`, `status`),
  KEY `idx_error_report_userID` (`userID`),
  CONSTRAINT `error_report_ibfk_1` FOREIGN KEY (`userID`) REFERENCES `user` (`userID`) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
