-- Increase user_preference.value from varchar(100) to varchar(500).
-- Required for storing API keys and other longer preference values.
ALTER TABLE user_preference
  MODIFY COLUMN value VARCHAR(500);
