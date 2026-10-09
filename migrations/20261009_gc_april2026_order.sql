-- April 2026 GC: talk prefixes are session digit + talk number ('210' = 2.10).
-- The scraper read '210' as session 21, mislabelling it and sorting it after
-- session 5. Renumber the conference as YYYYMM*1000 + session*100 + talk (the
-- scraper's new scheme) and fix the label. study_source is insert-only.
-- Safe to re-run: rows already renumbered and labelled are skipped.
INSERT INTO study_source (sourceID, collectionID, userID, category, title, subtitle, author, url,
                          audio_url, audio_length, order_by, scheduled_date, created, created_by)
SELECT sourceID, collectionID, userID,
       IF(category REGEXP '^Session [0-9]{2}$',
          ELT(LEFT(prefix, 1), 'Saturday Morning Session', 'Saturday Afternoon Session',
              'Saturday Evening Session', 'Sunday Morning Session', 'Sunday Afternoon Session'),
          category),
       title, subtitle, author, url, audio_url, audio_length, new_order, scheduled_date, NOW(), created_by
FROM (
    SELECT s.*, p.prefix, 202604000 + LEFT(p.prefix, 1) * 100 + SUBSTRING(p.prefix, 2) AS new_order
    FROM study_source s
    JOIN (SELECT id, REGEXP_SUBSTR(SUBSTRING_INDEX(url, '/', -1), '^[0-9]+') AS prefix FROM study_source) p
      ON p.id = s.id
    WHERE s.collectionID = (SELECT c.collectionID FROM study_collection c WHERE c.name = 'General Conference'
                            AND c.id = (SELECT MAX(c2.id) FROM study_collection c2 WHERE c2.collectionID = c.collectionID)
                            LIMIT 1)
      AND s.url LIKE '%/general-conference/2026/04/%'
      AND s.id = (SELECT MAX(s2.id) FROM study_source s2 WHERE s2.sourceID = s.sourceID)
      AND s.title IS NOT NULL
) t
WHERE prefix IS NOT NULL AND (order_by <> new_order OR category REGEXP '^Session [0-9]{2}$');
