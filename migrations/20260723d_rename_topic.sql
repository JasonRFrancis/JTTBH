-- Idempotent-in-intent migration: topics are now shared across the study
-- and quote features (and possibly more later), so they move out of the
-- study_* namespace into their own table.

RENAME TABLE `study_topic` TO `topic`;
