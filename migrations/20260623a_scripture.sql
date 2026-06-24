-- migrations/20260623a_scripture.sql
-- Scripture memorization feature: two new tables.

CREATE TABLE IF NOT EXISTS scripture (
    id          INT          NOT NULL AUTO_INCREMENT,
    scriptureID VARCHAR(36)  NOT NULL,
    userID      VARCHAR(36)  NOT NULL,
    reference   VARCHAR(150),
    text        TEXT,
    summary     TEXT,
    created     DATETIME     NOT NULL DEFAULT NOW(),
    created_by  VARCHAR(36),
    PRIMARY KEY (id),
    INDEX idx_scripture_user (userID, scriptureID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- Tracks spaced-repetition state per scripture per mode.
-- Direct UPDATE (not insert-only) because this is mutable review state.
CREATE TABLE IF NOT EXISTS scripture_review (
    id            INT                                    NOT NULL AUTO_INCREMENT,
    scriptureID   VARCHAR(36)                            NOT NULL,
    userID        VARCHAR(36)                            NOT NULL,
    mode          ENUM('reference','familiar','verbatim') NOT NULL,
    ease_factor   DECIMAL(4,2)                           NOT NULL DEFAULT 2.50,
    interval_days INT                                    NOT NULL DEFAULT 1,
    repetitions   INT                                    NOT NULL DEFAULT 0,
    next_review   DATE                                   NOT NULL,
    last_reviewed DATETIME,
    PRIMARY KEY (id),
    UNIQUE KEY uk_review (scriptureID, userID, mode),
    INDEX idx_review_user_date (userID, next_review)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
