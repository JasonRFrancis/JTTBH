-- API key table for Hermes Agent and future programmatic access.
-- Keys are stored as SHA-256 hashes only; the raw key is shown once on creation.
-- This table uses direct UPDATE (exception to insert-only) for last_used/revoked_at.

CREATE TABLE IF NOT EXISTS api_key (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    key_hash    VARCHAR(64)  NOT NULL COMMENT 'SHA-256 hex of the raw bearer token',
    name        VARCHAR(255) NOT NULL COMMENT 'Human label, e.g. hermes-agent',
    user_id     VARCHAR(36)  NOT NULL COMMENT 'FK -> user.userID',
    perm_read   INT          NOT NULL DEFAULT 0,
    perm_write  INT          NOT NULL DEFAULT 0,
    last_used   DATETIME     NULL,
    created_at  DATETIME     NOT NULL DEFAULT NOW(),
    revoked_at  DATETIME     NULL,
    UNIQUE KEY uq_key_hash (key_hash),
    INDEX      idx_user_id  (user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
