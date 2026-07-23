-- Idempotent migration: master list of study topics (tag vocabulary).
-- Flat, admin-managed reference list — same shape as fitness_exercise:
-- direct UPDATE/DELETE, no insert-only versioning.

CREATE TABLE `study_topic` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(200) NOT NULL,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_topic_name` (`name`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
