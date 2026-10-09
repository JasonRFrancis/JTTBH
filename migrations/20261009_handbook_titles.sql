-- Prefix General Handbook source titles with their handbook reference
-- ("Introduction" -> "37.0 Introduction"). study_source is insert-only.
-- Safe to re-run: rows whose title already starts with the reference are skipped.
INSERT INTO study_source (sourceID, collectionID, userID, category, title, subtitle, author, url,
                          audio_url, audio_length, order_by, scheduled_date, created, created_by)
SELECT s.sourceID, s.collectionID, s.userID, s.category, CONCAT(s.subtitle, ' ', s.title), s.subtitle,
       s.author, s.url, s.audio_url, s.audio_length, s.order_by, s.scheduled_date, NOW(), s.created_by
FROM study_source s
WHERE s.collectionID = '49dafe5a-1bf9-4ecb-9a18-2ea91b608c5f'
  AND s.id = (SELECT MAX(s2.id) FROM study_source s2 WHERE s2.sourceID = s.sourceID)
  AND s.title IS NOT NULL
  AND s.subtitle IS NOT NULL
  AND s.title NOT LIKE CONCAT(s.subtitle, ' %');

-- Then clear subtitle (the reference now lives in the title and the daily page
-- showed it twice). Must run after the statement above, which keys on subtitle.
INSERT INTO study_source (sourceID, collectionID, userID, category, title, subtitle, author, url,
                          audio_url, audio_length, order_by, scheduled_date, created, created_by)
SELECT s.sourceID, s.collectionID, s.userID, s.category, s.title, NULL,
       s.author, s.url, s.audio_url, s.audio_length, s.order_by, s.scheduled_date, NOW(), s.created_by
FROM study_source s
WHERE s.collectionID = '49dafe5a-1bf9-4ecb-9a18-2ea91b608c5f'
  AND s.id = (SELECT MAX(s2.id) FROM study_source s2 WHERE s2.sourceID = s.sourceID)
  AND s.title IS NOT NULL
  AND s.subtitle IS NOT NULL
  AND s.title LIKE CONCAT(s.subtitle, ' %');
