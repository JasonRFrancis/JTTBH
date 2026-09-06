-- 20260906_project_agent.sql
-- Agent collaboration surface for the Projects feature.
--   * project.parentID / project.status  (insert-only, carried forward)
--   * project_task     – the agent's checkable plan (insert-only, sentinel title NULL)
--   * project_message  – two-way thread (append-only; only `resolution` is UPDATEd)

ALTER TABLE `project`
  ADD COLUMN `parentID` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL
    COMMENT 'set = this project is a subproject of parentID' AFTER `userID`,
  ADD COLUMN `status` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL
    COMMENT 'active | blocked | awaiting_review | done (NULL = active)' AFTER `next_step`,
  ADD KEY `idx_parentID` (`parentID`);

CREATE TABLE `project_task` (
  `id` int NOT NULL AUTO_INCREMENT,
  `taskID` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `projectID` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'NULL = soft deleted',
  `done` tinyint(1) DEFAULT '0',
  `position` int DEFAULT '0',
  `note` text COLLATE utf8mb4_unicode_ci,
  `created` datetime DEFAULT CURRENT_TIMESTAMP,
  `created_by` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `idx_taskID` (`taskID`),
  KEY `idx_projectID` (`projectID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;

CREATE TABLE `project_message` (
  `id` int NOT NULL AUTO_INCREMENT,
  `messageID` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `projectID` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `author` enum('user','agent') COLLATE utf8mb4_unicode_ci NOT NULL,
  `kind` varchar(20) COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'question|progress|proposal|guidance',
  `body` text COLLATE utf8mb4_unicode_ci,
  `meta` text COLLATE utf8mb4_unicode_ci COMMENT 'JSON; proposal title/description',
  `resolution` varchar(20) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'proposal only: approved|dismissed',
  `created` datetime DEFAULT CURRENT_TIMESTAMP,
  `created_by` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id` (`id`),
  KEY `idx_projectID` (`projectID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
