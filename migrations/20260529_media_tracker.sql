-- Media Tracker
-- Creates media and media_episode tables; migrates existing book data.
-- Idempotent: safe to re-run.

CREATE TABLE IF NOT EXISTS `media` (
  `id`          INT          NOT NULL AUTO_INCREMENT,
  `mediaID`     VARCHAR(36)  NOT NULL,
  `userID`      VARCHAR(36)  NOT NULL,
  `title`       VARCHAR(500) DEFAULT NULL,      -- NULL = soft-deleted
  `kind`        ENUM('book','movie','show','podcast') NOT NULL DEFAULT 'book',
  `creator`     VARCHAR(255) DEFAULT NULL,      -- author / director / host
  `status`      ENUM('want','in_progress','done','dismiss') NOT NULL DEFAULT 'want',
  `rating`      TINYINT      DEFAULT NULL,      -- 1–5
  `review`      TEXT         DEFAULT NULL,
  `external_id` VARCHAR(500) DEFAULT NULL,      -- TMDB int ID or RSS feed URL
  `cover_url`   VARCHAR(500) DEFAULT NULL,
  `streaming`   VARCHAR(255) DEFAULT NULL,      -- e.g. "Netflix, Hulu"
  `next_date`   DATE         DEFAULT NULL,      -- next episode / sequel release
  `started`     DATE         DEFAULT NULL,
  `finished`    DATE         DEFAULT NULL,
  `created`     DATETIME     NOT NULL,
  `created_by`  VARCHAR(36)  NOT NULL,
  PRIMARY KEY (`id`),
  KEY `mediaID` (`mediaID`),
  KEY `userID`  (`userID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- media_episode: direct UPDATE for `seen` (not insert-only).
-- One row per episode per media item.
CREATE TABLE IF NOT EXISTS `media_episode` (
  `id`             INT          NOT NULL AUTO_INCREMENT,
  `episodeID`      VARCHAR(36)  NOT NULL,
  `mediaID`        VARCHAR(36)  NOT NULL,
  `title`          VARCHAR(500) DEFAULT NULL,
  `season`         SMALLINT     DEFAULT NULL,   -- NULL for podcasts
  `episode_number` SMALLINT     DEFAULT NULL,
  `air_date`       DATE         DEFAULT NULL,
  `seen`           TINYINT      NOT NULL DEFAULT 0,
  `description`    TEXT         DEFAULT NULL,
  `external_id`    VARCHAR(500) DEFAULT NULL,   -- TMDB episode ID or RSS guid
  `created`        DATETIME     NOT NULL,
  `created_by`     VARCHAR(36)  NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `episodeID` (`episodeID`),
  KEY `mediaID` (`mediaID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Migrate existing book rows (latest per bookID, not deleted).
-- NOT EXISTS guard makes this idempotent.
INSERT INTO media
  (mediaID, userID, title, kind, creator, status, rating, review,
   started, finished, created, created_by)
SELECT
  b.bookID,
  b.userID,
  b.title,
  'book',
  b.author,
  CASE b.status
    WHEN 'want_to_read' THEN 'want'
    WHEN 'reading'      THEN 'in_progress'
    WHEN 'completed'    THEN 'done'
    ELSE                     'dismiss'
  END,
  b.rating,
  COALESCE(b.review, b.notes),
  b.started,
  b.finished,
  b.created,
  b.created_by
FROM book b
WHERE b.id = (SELECT MAX(b2.id) FROM book b2 WHERE b2.bookID = b.bookID)
  AND b.title IS NOT NULL
  AND NOT EXISTS (SELECT 1 FROM media m WHERE m.mediaID = b.bookID);
