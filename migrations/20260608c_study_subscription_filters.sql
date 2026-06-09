ALTER TABLE study_subscription
  ADD COLUMN filter_has_audio TINYINT      NOT NULL DEFAULT 0,
  ADD COLUMN filter_title     VARCHAR(300) DEFAULT NULL;
