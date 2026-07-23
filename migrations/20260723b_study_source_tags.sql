-- Idempotent migration: topic tags for study_source items.
-- Many-to-many table keyed on the stable sourceID (study_source is
-- insert-only/versioned, so sourceID isn't a unique key to FK against).

CREATE TABLE `study_source_tag` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sourceID` varchar(36) NOT NULL,
  `tag` varchar(100) NOT NULL,
  `userID` varchar(36) NOT NULL,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_source_tag` (`sourceID`,`tag`),
  KEY `idx_tag_tag` (`tag`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

ALTER TABLE `study_subscription`
  ADD COLUMN `filter_tag` varchar(500) DEFAULT NULL,
  ADD COLUMN `filter_tag_text` varchar(300) DEFAULT NULL;
