-- Import Overcast podcast subscriptions from OPML export.
-- Idempotent: skips any feed URL already present for this user.
-- Run after 20260529_media_tracker.sql.

SET @user_id = (SELECT userID FROM `user` WHERE username = 'jason' LIMIT 1);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, 'ca9190a8-f9f3-4b47-a4da-c602f04c8ab0', 'The Incomparable Mothership', 'podcast', 'want', 'https://feeds.theincomparable.com/theincomparable', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://feeds.theincomparable.com/theincomparable' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '728aa407-1763-4cc7-af90-5ebc76e67768', 'Two-minute Time Lord', 'podcast', 'want', 'https://twominutetimelord.com/feed/podcast/', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://twominutetimelord.com/feed/podcast/' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, 'ed8e468e-b56e-47d8-b19b-7f1b919ce990', 'The History of English Podcast', 'podcast', 'want', 'https://historyofenglishpodcast.com/feed/podcast/', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://historyofenglishpodcast.com/feed/podcast/' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, 'ea9007f5-7593-4bc4-b2f4-2d7a6b0c867d', 'The Talk Show With John Gruber', 'podcast', 'want', 'https://daringfireball.net/thetalkshow/rss', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://daringfireball.net/thetalkshow/rss' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '70be4876-c67b-4866-ad40-45a7b41fab72', 'TALKING POLITICS', 'podcast', 'want', 'https://access.acast.com/rss/9a03fe9e-1ff0-4dcc-b3f6-50bd1f016ea4/', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://access.acast.com/rss/9a03fe9e-1ff0-4dcc-b3f6-50bd1f016ea4/' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, 'ba891260-129a-4be8-b09b-c8351ee87d0d', 'BYU Speeches', 'podcast', 'want', 'https://www.omnycontent.com/d/playlist/0c331867-ade6-4f54-a1a9-aa5d00345817/b0d8b123-6f8f-49b4-ad69-aa70011ce971/379d3bbf-05e6-46c1-921e-aa70011ce976/podcast.rss', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://www.omnycontent.com/d/playlist/0c331867-ade6-4f54-a1a9-aa5d00345817/b0d8b123-6f8f-49b4-ad69-aa70011ce971/379d3bbf-05e6-46c1-921e-aa70011ce976/podcast.rss' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '338066ca-fd0d-490b-ac6a-4b4d6d4cd649', 'Software Engineering Daily', 'podcast', 'want', 'https://softwareengineeringdaily.com/feed/podcast/', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://softwareengineeringdaily.com/feed/podcast/' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, 'cb17d8fc-9903-4ab8-9bca-9fab85ca486e', 'Talk Python To Me', 'podcast', 'want', 'https://talkpython.fm/episodes/rss', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://talkpython.fm/episodes/rss' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '24392ef8-4b99-45b4-a8c4-86abcc18bb72', 'Classic BYU Speeches', 'podcast', 'want', 'https://www.omnycontent.com/d/playlist/0c331867-ade6-4f54-a1a9-aa5d00345817/b6ab73b6-c6a7-489e-b639-aa7100f69ce1/7118aff4-56ad-4def-a7e4-aa7100f69cf3/podcast.rss', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://www.omnycontent.com/d/playlist/0c331867-ade6-4f54-a1a9-aa5d00345817/b6ab73b6-c6a7-489e-b639-aa7100f69ce1/7118aff4-56ad-4def-a7e4-aa7100f69cf3/podcast.rss' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '9557af06-314e-4241-8a42-b1a56855755b', 'Food Labels Revealed', 'podcast', 'want', 'https://feed.podbean.com/foodlabelsrevealed/feed.xml', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://feed.podbean.com/foodlabelsrevealed/feed.xml' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, 'a9877db9-03fa-4cec-8e63-10dd9765c637', 'The President’s Inbox', 'podcast', 'want', 'https://feed.podbean.com/thepresidentsinbox/feed.xml', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://feed.podbean.com/thepresidentsinbox/feed.xml' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, 'e89f909f-667b-4a49-a5b4-3713d0ee62fb', 'Ologies with Alie Ward', 'podcast', 'want', 'https://feeds.simplecast.com/FO6kxYGj', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://feeds.simplecast.com/FO6kxYGj' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '3db3a928-fad0-4eee-955d-ec96ca7bc6a2', 'Tim Goodman''s TV Talk Machine', 'podcast', 'want', 'https://feeds.theincomparable.com/tvtm', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://feeds.theincomparable.com/tvtm' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, 'a7a842a5-8126-4a1b-903b-eee94f70a6b9', 'Stay Tuned with Preet', 'podcast', 'want', 'https://feeds.megaphone.fm/VMP5489734702', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://feeds.megaphone.fm/VMP5489734702' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, 'cf916db2-f132-4dd7-bc1b-6e33d6b9ccad', 'So Very Wrong About Games', 'podcast', 'want', 'https://feeds.megaphone.fm/NSR5899116605', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://feeds.megaphone.fm/NSR5899116605' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '5221c15f-2fbe-46a2-9ab0-5588894fd30b', 'Don''t Let''s Start: A Podcast About They Might Be Giants', 'podcast', 'want', 'https://anchor.fm/s/80d20d4/podcast/rss', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://anchor.fm/s/80d20d4/podcast/rss' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '2724d1bb-c6ac-4ed3-9e26-76eaae0419b5', 'Talking Feds', 'podcast', 'want', 'https://feeds.megaphone.fm/GEMINIMEDIA2127678588', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://feeds.megaphone.fm/GEMINIMEDIA2127678588' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '3a2477a5-64ca-4de5-894f-91018b423b40', 'Articles of Interest', 'podcast', 'want', 'https://feed.articlesofinterest.club/', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://feed.articlesofinterest.club/' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, 'a646dcdf-4e1a-4c74-b6fa-253476e88b90', 'Hearts of the Fathers', 'podcast', 'want', 'https://feeds.buzzsprout.com/271487.rss', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://feeds.buzzsprout.com/271487.rss' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '9d119236-7810-41a1-848d-f38df2688745', 'Sharing Time - A Latter Day Saint Culture Podcast', 'podcast', 'want', 'https://feeds.soundcloud.com/users/soundcloud:users:677867924/sounds.rss', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://feeds.soundcloud.com/users/soundcloud:users:677867924/sounds.rss' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, 'db0e9dd4-ce2f-47a8-9bf5-5fa9b879ae81', 'Langsam Gesprochene Nachrichten | Audios | DW Deutsch lernen', 'podcast', 'want', 'https://rss.dw.com/xml/DKpodcast_lgn_de', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://rss.dw.com/xml/DKpodcast_lgn_de' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '213a217a-3d86-4ea2-8000-562f073fe357', 'Small Things Often', 'podcast', 'want', 'https://feeds.megaphone.fm/smallthingsoften', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://feeds.megaphone.fm/smallthingsoften' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '7f34e230-fed6-4d67-92ad-646926925172', 'Just Julia', 'podcast', 'want', 'https://anchor.fm/s/1abd0758/podcast/rss', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://anchor.fm/s/1abd0758/podcast/rss' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '5d3d7076-8340-477e-84c3-e355b59d1a99', 'Church News', 'podcast', 'want', 'https://feed.cdnstream1.com/zjb/feed/download/41/4c/58/414c58bd-a3af-4d13-ba31-2c53f0322bcc.xml', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://feed.cdnstream1.com/zjb/feed/download/41/4c/58/414c58bd-a3af-4d13-ba31-2c53f0322bcc.xml' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '4779b2f0-4d0a-49c0-a9f8-7e786c3c3ce1', 'EconTalk', 'podcast', 'want', 'https://feeds.simplecast.com/wgl4xEgL', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://feeds.simplecast.com/wgl4xEgL' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '173fe462-1ffd-440a-a6d6-c8007343dd07', 'The Ezra Klein Show', 'podcast', 'want', 'https://feeds.simplecast.com/kEKXbjuJ', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://feeds.simplecast.com/kEKXbjuJ' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '68d53043-5095-47eb-9098-25f734f8e485', 'Rational Security', 'podcast', 'want', 'https://feeds.acast.com/public/shows/60427f9d34b9a27f4b6e3a8d', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://feeds.acast.com/public/shows/60427f9d34b9a27f4b6e3a8d' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, 'd0df9484-6a1e-4d7f-83bc-cb25d5bbc87e', 'What Trump Can Teach Us About Con Law', 'podcast', 'want', 'https://feeds.simplecast.com/jZLi00b4', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://feeds.simplecast.com/jZLi00b4' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, 'b86d7307-5aad-460c-94e4-4d5445942ee5', 'The Lawfare Podcast', 'podcast', 'want', 'https://feeds.acast.com/public/shows/60518a52f69aa815d2dba41c', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://feeds.acast.com/public/shows/60518a52f69aa815d2dba41c' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '63868f3f-5690-4ffe-a17b-55f13304f684', 'Deep Blue', 'podcast', 'want', 'https://www.byuradio.org/rss/showpodcastfeed/7d3b3ccb-fc00-4bac-81f8-98195af1b798', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://www.byuradio.org/rss/showpodcastfeed/7d3b3ccb-fc00-4bac-81f8-98195af1b798' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '7236010e-07aa-4a23-963e-40eafbeba6e1', 'Doctor Who Flashcast', 'podcast', 'want', 'https://feeds.theincomparable.com/dwf', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://feeds.theincomparable.com/dwf' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '5227bb61-f38d-435a-bd64-2d1c01415f74', 'Making Sense with Sam Harris - Invalid feed', 'podcast', 'want', 'https://rss.making-sense.samharris.org/feed/?token=144bf47d-813a-4ad3-9db9-2f712c434b28', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://rss.making-sense.samharris.org/feed/?token=144bf47d-813a-4ad3-9db9-2f712c434b28' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '267c99a2-0942-4a4c-8959-d07545702120', 'Plain English with Derek Thompson', 'podcast', 'want', 'https://feeds.megaphone.fm/plain-english', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://feeds.megaphone.fm/plain-english' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '9b40db6e-5d57-4de6-8cb5-bb8b22c96531', 'Talking Politics: HISTORY OF IDEAS', 'podcast', 'want', 'https://feeds.acast.com/public/shows/7a3c5644-595b-4535-89cb-4df503953241', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://feeds.acast.com/public/shows/7a3c5644-595b-4535-89cb-4df503953241' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '9a1b9149-38e5-4ae9-8130-203fd9f37265', 'Things Fell Apart', 'podcast', 'want', 'https://podcasts.files.bbci.co.uk/m0011cpr.rss', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://podcasts.files.bbci.co.uk/m0011cpr.rss' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, 'c433482d-2238-4792-9477-a16689ad1a80', 'A Podcast Of Unnecessary Detail', 'podcast', 'want', 'https://feeds.acast.com/public/shows/61deed94f2acc80013aab8aa', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://feeds.acast.com/public/shows/61deed94f2acc80013aab8aa' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '8b028f34-2103-4aaa-9175-d93e0488e406', 'Odd Lots', 'podcast', 'want', 'https://www.omnycontent.com/d/playlist/e73c998e-6e60-432f-8610-ae210140c5b1/8a94442e-5a74-4fa2-8b8d-ae27003a8d6b/982f5071-765c-403d-969d-ae27003a8d83/podcast.rss', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://www.omnycontent.com/d/playlist/e73c998e-6e60-432f-8610-ae210140c5b1/8a94442e-5a74-4fa2-8b8d-ae27003a8d6b/982f5071-765c-403d-969d-ae27003a8d83/podcast.rss' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '04650cd0-5383-44b7-aa1c-a771361bf86a', '60 Songs That Explain the ''90s', 'podcast', 'want', 'https://feeds.megaphone.fm/60-songs', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://feeds.megaphone.fm/60-songs' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '4d01f448-6039-4d6f-8ab9-b8438ca3341e', 'Podcast – Ethnic Relations and Migration in the Ancient World: The Websites of Philip A. Harland', 'podcast', 'want', 'https://feeds.feedburner.com/feedburner/APRP', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://feeds.feedburner.com/feedburner/APRP' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '63aceddd-ee2f-4bbb-b08b-956c87bcd5ff', 'The Political Scene | The New Yorker', 'podcast', 'want', 'http://feeds.feedburner.com/tnypoliticalscene', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'http://feeds.feedburner.com/tnypoliticalscene' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '80c1f3bd-f4de-46bf-8d50-93744e0c9991', 'the memory palace', 'podcast', 'want', 'http://feeds.thememorypalace.us/thememorypalace', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'http://feeds.thememorypalace.us/thememorypalace' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, 'f1aa7649-6c85-46b0-8aed-063d458a9adf', 'NT Pod', 'podcast', 'want', 'https://feeds2.feedburner.com/NTPod', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://feeds2.feedburner.com/NTPod' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, 'a5069ce6-a153-4c8b-b36e-de079bff891d', 'The Ancient Tradition', 'podcast', 'want', 'https://rss.buzzsprout.com/2105781.rss', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://rss.buzzsprout.com/2105781.rss' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, 'a7b4ada4-4231-4dcd-ba2b-6d82f48a6092', 'Ones and Tooze', 'podcast', 'want', 'https://feeds.megaphone.fm/FGP6717686883', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://feeds.megaphone.fm/FGP6717686883' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, 'c0a9d7f0-ab72-40bf-9a88-ce8a2876583d', 'The Interpreter Foundation Podcast', 'podcast', 'want', 'https://cms.interpreterfoundation.org/feed/podcast/', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://cms.interpreterfoundation.org/feed/podcast/' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, 'ee01385b-8a95-453b-8dff-a87bcbc676d0', 'The Ancient Tradition: Audio Writ', 'podcast', 'want', 'https://rss.buzzsprout.com/2117748.rss', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://rss.buzzsprout.com/2117748.rss' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '83ced7a3-d104-4b6a-9159-7a7469b5ade2', 'Trump, Inc.', 'podcast', 'want', 'https://feeds.simplecast.com/10jzt1tO', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://feeds.simplecast.com/10jzt1tO' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '6c39a249-fd8c-4ae4-9f98-ada74be672ab', 'The Rest Is History', 'podcast', 'want', 'https://feeds.megaphone.fm/GLT4787413333', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://feeds.megaphone.fm/GLT4787413333' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '23e05da1-dcce-40e8-862f-44e315433234', 'The Bulwark Podcast', 'podcast', 'want', 'https://audioboom.com/channels/5114286.rss', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://audioboom.com/channels/5114286.rss' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '6372c17a-0fa4-461d-abd8-578403c3886b', 'Politix', 'podcast', 'want', 'https://api.substack.com/feed/podcast/2118966.rss', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://api.substack.com/feed/podcast/2118966.rss' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '482e2577-d1d9-4bcd-9147-8cdb486b3104', 'Night Owls', 'podcast', 'want', 'https://rss.buzzsprout.com/2536306.rss', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://rss.buzzsprout.com/2536306.rss' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '980b7879-c48a-40b5-a986-946a8dd1786d', 'Letters from an American', 'podcast', 'want', 'https://api.substack.com/feed/podcast/20533.rss', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://api.substack.com/feed/podcast/20533.rss' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '21ffe319-a825-4e82-abe0-fec8f2cd4201', 'Money Stuff: The Podcast', 'podcast', 'want', 'https://www.omnycontent.com/d/playlist/e73c998e-6e60-432f-8610-ae210140c5b1/ee4336cb-155f-4488-90e0-b1400134e40e/77e6a3a7-290d-4a82-8164-b14001353ef2/podcast.rss', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://www.omnycontent.com/d/playlist/e73c998e-6e60-432f-8610-ae210140c5b1/ee4336cb-155f-4488-90e0-b1400134e40e/77e6a3a7-290d-4a82-8164-b14001353ef2/podcast.rss' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, 'f583afc1-c743-40ce-80c2-326b1ec56b63', 'On the Media', 'podcast', 'want', 'https://feeds.simplecast.com/o4jAFXaw', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://feeds.simplecast.com/o4jAFXaw' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '998a9641-808c-4464-9d95-151b3bed2b7d', 'Risky Business with Nate Silver and Maria Konnikova', 'podcast', 'want', 'https://www.omnycontent.com/d/playlist/e73c998e-6e60-432f-8610-ae210140c5b1/951120d9-cf6e-4224-93d7-b15c014dcea5/eb5e885e-6644-4680-aec4-b15c0150ffc0/podcast.rss', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://www.omnycontent.com/d/playlist/e73c998e-6e60-432f-8610-ae210140c5b1/951120d9-cf6e-4224-93d7-b15c014dcea5/eb5e885e-6644-4680-aec4-b15c0150ffc0/podcast.rss' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '03c4efdc-ce3c-48a6-b944-d0c2bfedd3ed', 'The Daily', 'podcast', 'want', 'https://feeds.simplecast.com/Sl5CSM3S', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://feeds.simplecast.com/Sl5CSM3S' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '03f92d8c-7382-42f6-9315-043dbfc102a0', 'Raging Moderates with Scott Galloway and Jessica Tarlov', 'podcast', 'want', 'https://feeds.megaphone.fm/VMP7229898872', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://feeds.megaphone.fm/VMP7229898872' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, 'ca22c169-ae6e-4fa5-9941-99a5413f31c7', 'Past Present Future', 'podcast', 'want', 'https://feeds.megaphone.fm/ARML2708405200', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://feeds.megaphone.fm/ARML2708405200' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '413868ff-859d-4392-b733-c3c8a9a23fed', 'Marketplace Morning Report', 'podcast', 'want', 'https://feeds.publicradio.org/public_feeds/marketplace-morning-report', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://feeds.publicradio.org/public_feeds/marketplace-morning-report' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '8a6e2e0a-f189-4ffe-b11f-ac339e6389f7', 'The Last Invention', 'podcast', 'want', 'https://feeds.megaphone.fm/thelastinvention', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://feeds.megaphone.fm/thelastinvention' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, 'eb6695ff-72a0-4e6b-b65d-9d0761d85cd9', 'The Anthropocene Reviewed', 'podcast', 'want', 'https://rss.art19.com/the-anthropocene-reviewed', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://rss.art19.com/the-anthropocene-reviewed' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '4646893c-d8dd-44aa-853d-25d81092664c', 'Rachel Maddow Presents: Ultra', 'podcast', 'want', 'https://feeds.simplecast.com/_sWHkul5', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://feeds.simplecast.com/_sWHkul5' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, 'c17f0335-daa6-46b4-9ee8-3cb23617baf1', 'Conversations with Tyler', 'podcast', 'want', 'https://rss.libsyn.com/shows/137081/destinations/850607.xml', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://rss.libsyn.com/shows/137081/destinations/850607.xml' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '43b1b037-e979-48fa-b8f4-baba7af84fba', 'FoundMyFitness', 'podcast', 'want', 'https://rss.libsyn.com/shows/51714/destinations/184296.xml', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://rss.libsyn.com/shows/51714/destinations/184296.xml' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '78938568-3e43-4259-bb47-808b4785cffd', 'Amicus With Dahlia Lithwick | Law, justice, and the courts', 'podcast', 'want', 'https://my.slate.com/podcasts/feeds/amicus/', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://my.slate.com/podcasts/feeds/amicus/' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, 'bc5cb7b0-6b40-4218-8bbe-16b79dd04485', 'The Book Pile', 'podcast', 'want', 'https://rss.buzzsprout.com/1505809.rss', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://rss.buzzsprout.com/1505809.rss' AND title IS NOT NULL);

INSERT INTO media (userID, mediaID, title, kind, status, external_id, created, created_by)
  SELECT @user_id, '60ac17e4-1d7b-43de-9d5d-26ae6d70852d', 'Downstream', 'podcast', 'want', 'https://relay.fm/downstream/feed', NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND external_id = 'https://relay.fm/downstream/feed' AND title IS NOT NULL);
