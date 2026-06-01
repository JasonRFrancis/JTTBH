-- Allow multiple subscriptions per collection (for smart subscriptions with different filters)
-- and add an optional user-defined name to each subscription.

ALTER TABLE study_subscription
  DROP INDEX uq_user_collection,
  ADD COLUMN name VARCHAR(200) DEFAULT NULL;
