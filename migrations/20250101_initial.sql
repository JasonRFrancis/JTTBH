-- Migration: Initial schema baseline
-- Date: 2025-01-01
-- 
-- This file documents the initial schema. The actual schema is in schema.sql
-- at the project root. Run the initial setup with:
--
--   mysql -u jttbh -p jttbh < schema.sql
--
-- NOTE: The book table has a foreign key referencing 'users' (plural) which
-- is a bug -- it should reference 'user' (singular). Until fixed in schema.sql,
-- apply this correction:

-- Forward migration (run after schema.sql if the FK error occurs)
-- ALTER TABLE book DROP FOREIGN KEY books_ibfk_1;
-- ALTER TABLE book ADD CONSTRAINT books_ibfk_1 
--   FOREIGN KEY (userID) REFERENCES user(userID) ON DELETE CASCADE;

-- Rollback
-- No rollback needed for initial schema
