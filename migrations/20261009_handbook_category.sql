-- Clear the "Chapter N" category on General Handbook sources: titles now start
-- with the section reference ("38.2.1 ..."), and pages print category in front
-- of the title. study_source is insert-only. Safe to re-run.
INSERT INTO study_source (sourceID, collectionID, userID, category, title, subtitle, author, url,
                          audio_url, audio_length, order_by, scheduled_date, created, created_by)
SELECT s.sourceID, s.collectionID, s.userID, NULL, s.title, s.subtitle,
       s.author, s.url, s.audio_url, s.audio_length, s.order_by, s.scheduled_date, NOW(), s.created_by
FROM study_source s
WHERE s.collectionID = '49dafe5a-1bf9-4ecb-9a18-2ea91b608c5f'
  AND s.id = (SELECT MAX(s2.id) FROM study_source s2 WHERE s2.sourceID = s.sourceID)
  AND s.title IS NOT NULL
  AND s.category IS NOT NULL;
