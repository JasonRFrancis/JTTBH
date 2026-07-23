-- Idempotent migration: allow study_subscription to exist without a collection
-- (cross-collection "subscribe by author" subscriptions), and give it its own
-- delivery mode since author-subscriptions have no collection to borrow `mode` from.

ALTER TABLE `study_subscription`
  MODIFY COLUMN `collectionID` varchar(36) NULL;

ALTER TABLE `study_subscription`
  ADD COLUMN `mode` enum('rate','calendar') NOT NULL DEFAULT 'rate' AFTER `collectionID`;
