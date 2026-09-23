--
-- 20260923_bookmark_dedupe.sql
-- 1. Strip the `ref=sidebar` query param from every bookmark URL
--    (same rule as _clean_url in app/routes/bookmark.py).
-- 2. Merge duplicate (userID, url) bookmarks into the oldest row:
--    created = most recent save, favorite/read_later = any, read = all,
--    tags/notes kept from the oldest row unless empty; category
--    memberships moved to the kept row. Then delete the extras.
--

START TRANSACTION;

UPDATE bookmark
   SET url = REGEXP_REPLACE(
               REGEXP_REPLACE(url, '[?&]ref=sidebar(?=#|$)', ''),
               '([?&])ref=sidebar&', '$1')
 WHERE url REGEXP '[?&]ref=sidebar(&|#|$)';

CREATE TEMPORARY TABLE bm_keep AS
SELECT userID, url,
       MIN(id)         AS keep_id,
       MAX(created)    AS created,
       MAX(favorite)   AS favorite,
       MAX(read_later) AS read_later,
       MIN(`read`)     AS `read`,
       MAX(tags)       AS tags,
       MAX(notes)      AS notes
  FROM bookmark
 GROUP BY userID, url
HAVING COUNT(*) > 1;

UPDATE bookmark b
  JOIN bm_keep k ON b.id = k.keep_id
   SET b.created    = k.created,
       b.favorite   = k.favorite,
       b.read_later = k.read_later,
       b.`read`     = k.`read`,
       b.tags       = COALESCE(b.tags, k.tags),
       b.notes      = COALESCE(b.notes, k.notes);

-- Move category memberships to the kept row (IGNORE skips ones it already has;
-- the leftovers are removed by ON DELETE CASCADE below).
UPDATE IGNORE bookmark_category_item ci
  JOIN bookmark b  ON b.bookmarkID = ci.bookmarkID
  JOIN bm_keep  k  ON k.userID = b.userID AND k.url = b.url AND b.id <> k.keep_id
  JOIN bookmark kb ON kb.id = k.keep_id
   SET ci.bookmarkID = kb.bookmarkID;

DELETE b FROM bookmark b
  JOIN bm_keep k ON k.userID = b.userID AND k.url = b.url AND b.id <> k.keep_id;

DROP TEMPORARY TABLE bm_keep;

COMMIT;
