-- migrations/20260623_shared_list.sql
-- Collaborative shared lists: three new tables.

CREATE TABLE IF NOT EXISTS shared_list (
    id       INT          NOT NULL AUTO_INCREMENT,
    listID   VARCHAR(36)  NOT NULL,
    ownerID  VARCHAR(36)  NOT NULL,
    name     VARCHAR(100) NOT NULL,
    created  DATETIME     NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id),
    UNIQUE KEY uk_listID (listID),
    INDEX idx_owner (ownerID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS shared_list_member (
    id           INT                                  NOT NULL AUTO_INCREMENT,
    listID       VARCHAR(36)                          NOT NULL,
    userID       VARCHAR(36)                          NOT NULL,
    permission   ENUM('view','edit')                  NOT NULL DEFAULT 'view',
    invited_by   VARCHAR(36)                          NOT NULL,
    status       ENUM('pending','accepted','declined') NOT NULL DEFAULT 'pending',
    show_in_todo TINYINT(1)                           NOT NULL DEFAULT 0,
    created      DATETIME                             NOT NULL DEFAULT NOW(),
    PRIMARY KEY (id),
    UNIQUE KEY uk_list_user (listID, userID),
    INDEX idx_user   (userID),
    INDEX idx_listID (listID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

CREATE TABLE IF NOT EXISTS shared_list_item (
    id           INT          NOT NULL AUTO_INCREMENT,
    itemID       VARCHAR(36)  NOT NULL,
    listID       VARCHAR(36)  NOT NULL,
    userID       VARCHAR(36)  NOT NULL,
    title        VARCHAR(255),
    position     INT          NOT NULL DEFAULT 0,
    completed    DATETIME     NULL,
    completed_by VARCHAR(36)  NULL,
    created      DATETIME     NOT NULL DEFAULT NOW(),
    created_by   VARCHAR(36)  NOT NULL,
    PRIMARY KEY (id),
    INDEX idx_list (listID),
    INDEX idx_item (itemID)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
