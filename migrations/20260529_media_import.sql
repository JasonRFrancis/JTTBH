-- Media import: movies, shows, and games.
-- Fixes: Tatsuo→Tetsuo, Tinker Tailer→Tinker Tailor.
-- Deduplicates overlaps between sections.
-- Idempotent: skips titles already present for this user.

-- Add 'game' to the media.kind ENUM.
ALTER TABLE media
  MODIFY COLUMN kind ENUM('book','movie','show','podcast','game') NOT NULL DEFAULT 'book';

SET @user_id = (SELECT userID FROM `user` WHERE username = 'jason' LIMIT 1);

-- Movies
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, 'b8784061-9ed6-4f0c-9674-d814f848d2e5', 'Kung Fu Hustle', 'movie', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Kung Fu Hustle' AND kind = 'movie' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '69987f88-1d49-46ad-abfc-4fdb22fa913a', 'The Host', 'movie', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Host' AND kind = 'movie' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '0c306ad0-3c7c-4e99-92ec-3c07f4c348bf', 'My Sassy Girl', 'movie', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'My Sassy Girl' AND kind = 'movie' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '36cbfb1e-5558-4e81-9b39-24b6839e6b10', 'The Tale of Princess Kaguya', 'movie', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Tale of Princess Kaguya' AND kind = 'movie' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, 'b6b4a3d2-a463-4fc7-828a-249315a7e316', 'Children of Men', 'movie', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Children of Men' AND kind = 'movie' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '42db47d6-b038-4240-91c6-995d7d795c4a', 'Dog Day Afternoon', 'movie', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Dog Day Afternoon' AND kind = 'movie' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, 'd9059bc4-aee1-44c9-96ef-9d5b4d783bcf', 'Tetsuo: The Iron Man', 'movie', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Tetsuo: The Iron Man' AND kind = 'movie' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '7aa55591-93a9-430b-9267-1fdb9d1870aa', 'Tinker Tailor Soldier Spy', 'movie', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Tinker Tailor Soldier Spy' AND kind = 'movie' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, 'd2a9e20b-f64b-4416-a281-df74ae44eeb9', 'Krull', 'movie', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Krull' AND kind = 'movie' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '9a62a46c-1110-4d31-9651-84421ccc26f0', 'Silent Friend', 'movie', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Silent Friend' AND kind = 'movie' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '381b7a41-299f-4453-869a-f3ef64fd90bc', 'In the Mood for Love', 'movie', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'In the Mood for Love' AND kind = 'movie' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '5589097a-0ace-4d98-8d66-cb240266ee39', 'Let the Right One In', 'movie', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Let the Right One In' AND kind = 'movie' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '9d296566-0c4d-464d-8ebc-f587ba8185ff', 'Sisu', 'movie', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Sisu' AND kind = 'movie' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '75c7e6c4-a04b-459a-988f-0a3fd585a2c4', 'Yi Yi', 'movie', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Yi Yi' AND kind = 'movie' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '366175f8-0419-4aab-84a0-d1529d8b243f', 'The Assessment', 'movie', 'want', 'Hulu', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Assessment' AND kind = 'movie' AND title IS NOT NULL);

-- Shows
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '6ea8cbdc-80cb-4956-95de-b3051aff7db9', 'Can You Keep a Secret?', 'show', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Can You Keep a Secret?' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, 'cadc1e3d-9e03-4ffd-8065-fa3b88f4a252', 'How to Get to Heaven from Belfast', 'show', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'How to Get to Heaven from Belfast' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '1b26adeb-b04c-4a55-8fe1-330f7ade117d', 'Good Fortune', 'show', 'want', 'Netflix', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Good Fortune' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '08ad64a6-8150-452e-b319-9870b762a0b0', 'DTF: St. Louis', 'show', 'want', 'HBO', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'DTF: St. Louis' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, 'dbf7b0c9-ebb3-47d5-82ab-9bd6217f3f90', 'The Day of the Jackal', 'show', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Day of the Jackal' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '8313fa8a-10fe-4a24-b5d3-ed58ff198628', 'Mrs. Davis', 'show', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Mrs. Davis' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, 'a27f80f5-e138-46f1-997a-0c86bee33b19', 'Inside the Manosphere', 'show', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Inside the Manosphere' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '0e3f5ade-4e97-4f11-af8d-5fc0dd56bf96', 'Killjoys', 'show', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Killjoys' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, 'f1b713bb-5e9a-41dc-8d47-ce18663714e6', 'The Beast In Me', 'show', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Beast In Me' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '72f5d104-4fc0-4517-9f61-fd4744dea269', 'Sally Wainwright''s Riot Women', 'show', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Sally Wainwright''s Riot Women' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '6d9314a3-e0c1-47f6-b735-28ffec30877b', 'Death by Lightning', 'show', 'want', 'Netflix', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Death by Lightning' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, 'c5302476-a8cf-4329-81db-154618152643', 'A Killer Paradox', 'show', 'want', 'Netflix', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'A Killer Paradox' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, 'e8612ab2-74c7-4c4d-a7bd-774d32b3bcbd', 'Pluribus', 'show', 'want', 'Apple TV+', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Pluribus' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, 'ccf78a07-8923-4b95-bf0c-c9847acdc914', 'Slow Horses', 'show', 'want', 'Apple TV+', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Slow Horses' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, 'fab033cf-c5f8-4ce9-9ffa-26cdac534373', 'The Diplomat', 'show', 'want', 'Netflix', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Diplomat' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '8a3cc82d-05d3-4075-bb4e-7f6fde2e08b5', 'Down Cemetery Road', 'show', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Down Cemetery Road' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '9aa1c9d5-b79a-4ba2-8b9f-d33660fcef69', 'Karma', 'show', 'want', 'Netflix', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Karma' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, 'a6b7952f-5748-43ba-bbb4-f7b2422d193b', 'Alice in Borderland', 'show', 'want', 'Netflix', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Alice in Borderland' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, 'a7f0bfef-bee4-4164-801b-83e8edc18b56', 'The Last Frontier', 'show', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Last Frontier' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, 'b84f7a53-7311-4bec-b33c-6bff2dea0a47', 'All of Us Are Dead', 'show', 'want', 'Netflix', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'All of Us Are Dead' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '558b253c-f652-4c63-9756-737263710cb8', 'Black Summer', 'show', 'want', 'Netflix', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Black Summer' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '54a42fee-e0b0-4041-8de6-beb4c04aba6b', 'Neglected Waters', 'show', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Neglected Waters' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '602eb92b-fba0-453e-8ab4-30894f6173cd', 'Formula 1: Drive to Survive', 'show', 'want', 'Netflix', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Formula 1: Drive to Survive' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '8f63e8cf-fe32-4657-99e9-b59fa8b371c9', 'Paris Has Fallen', 'show', 'want', 'Hulu', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Paris Has Fallen' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, 'd574eff9-8912-45bd-a9c9-05ee805d1fa6', 'The Åre Murders', 'show', 'want', 'Netflix', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Åre Murders' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, 'd683951d-68db-42b1-8147-895e573a00b4', 'My Name', 'show', 'want', 'Netflix', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'My Name' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, 'ddd6b985-ba96-4b11-acba-30a9a9575782', 'Trigger', 'show', 'want', 'Netflix', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Trigger' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '30554f5d-454a-4a20-ab39-2563d0210dda', 'Rage', 'show', 'want', 'HBO Max', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Rage' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, 'c0a02c04-10d2-4a26-81f3-1f4d3bda4b6e', 'Nine Puzzles', 'show', 'want', 'Hulu', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Nine Puzzles' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '5e6b4f0d-46e0-4bd5-af5f-4b8718e86adb', 'The Trunk', 'show', 'want', 'Netflix', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Trunk' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '26c747c1-0fae-413b-a060-c5e09af46699', 'Ludwig', 'show', 'want', 'BritBox', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Ludwig' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '6513b6ad-3438-4c98-8fb4-974799d6b798', 'Extracurricular', 'show', 'want', 'Netflix', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Extracurricular' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '7d41078a-dce8-4d3b-9ebb-3c4b66862ec3', 'ZeroZeroZero', 'show', 'want', 'Amazon Prime', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'ZeroZeroZero' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '7371a03b-8ccc-426e-9760-f3b58e6b04b1', 'Deli Boys', 'show', 'want', 'Hulu', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Deli Boys' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '2091250f-01e3-411c-93e3-80ac06b2e3bc', 'Adolescence', 'show', 'want', 'Netflix', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Adolescence' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '3d11488f-70f8-4dfc-8d79-25f274a2c19e', 'Such Brave Girls', 'show', 'want', 'Hulu', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Such Brave Girls' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, 'f84292d3-f936-4644-9cdb-43dec5cf09c7', 'The American Revolution', 'show', 'want', 'PBS', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The American Revolution' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '60c70633-b9a4-4433-b6ab-c066bc64ff74', 'Kingdom', 'show', 'want', 'Netflix', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Kingdom' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '48506cb8-5ef0-44a1-b722-b0e9bbf77395', 'Dept. Q', 'show', 'want', 'Netflix', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Dept. Q' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '1b398469-b7cc-4ac3-b552-8d28dfdba328', 'Asura', 'show', 'want', 'Netflix', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Asura' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '6edd2d97-72d3-4639-b340-ccc6f326db32', 'The Bear', 'show', 'want', 'FX', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Bear' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, 'a425b8e0-1b25-43fb-975a-82bb78c008d0', 'Families Like Ours', 'show', 'want', 'Netflix', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Families Like Ours' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '7b3bec3b-b33b-4cc0-b2ac-14dc9bfa3a78', 'The Studio', 'show', 'want', 'Apple TV+', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Studio' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '21a41898-fabe-49b3-92f7-cd7460826fec', 'Severance', 'show', 'want', 'Apple TV+', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Severance' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '8a170e10-54e2-4511-9aa8-0569937e00bd', 'Bait', 'show', 'want', 'Amazon Prime', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Bait' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, 'bb320fbf-af9a-4f84-9aa2-b4eb246ea067', 'Detective Hole', 'show', 'want', 'Netflix', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Detective Hole' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '998fa4a8-047c-4346-9ce6-4ded4ff2e78a', 'Privilèges', 'show', 'want', 'HBO', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Privilèges' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '300b79dd-daf2-416a-a95c-2b1b6f147b46', 'The Lady', 'show', 'want', 'BritBox', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Lady' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '09afe27c-39c6-4acd-892f-027a11380f56', 'The Audacity', 'show', 'want', 'HBO', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Audacity' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '60a484bf-b8d3-43a7-b7f2-49ad4fe1e5cb', 'Maximum Pleasure Guaranteed', 'show', 'want', 'Apple TV+', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Maximum Pleasure Guaranteed' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '784fb9c5-cbde-4950-a01a-97c0e9d95588', 'The Expanse', 'show', 'want', 'Amazon Prime', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Expanse' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, 'a2fa1d20-490d-4ee0-9f6a-5b1b63ecb5fd', 'Fallout', 'show', 'want', 'Amazon Prime', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Fallout' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, 'aa7a87ce-ea83-4363-b82e-464371bdc87a', 'The Boys', 'show', 'want', 'Amazon Prime', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Boys' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '53da6064-9aa8-4caa-9d65-1585681c9a7f', 'Battlestar Galactica', 'show', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Battlestar Galactica' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '70dd1ab2-6182-4340-9679-4340e1f80c4b', 'Outer Range', 'show', 'want', 'Amazon Prime', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Outer Range' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, 'c7f01a69-8513-4967-98c5-e4debfbbb449', 'Upload', 'show', 'want', 'Amazon Prime', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Upload' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '80377685-0583-49c0-92cc-1cfa83824766', 'The Peripheral', 'show', 'want', 'Amazon Prime', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Peripheral' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '9667d181-b3c4-458e-b56a-ac50ce1834d1', 'Monarch: Legacy of Monsters', 'show', 'want', 'Apple TV+', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Monarch: Legacy of Monsters' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, 'ab91b5ac-c0fd-40d6-b1fa-02317d86d5fd', 'The Man in the High Castle', 'show', 'want', 'Amazon Prime', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Man in the High Castle' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '5f3cd334-fbcb-4bf7-830c-7b065015b573', 'Tales from the Loop', 'show', 'want', 'Amazon Prime', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Tales from the Loop' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '8c47dc6d-eb06-4e7c-b85d-f50990f14847', 'Farscape', 'show', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Farscape' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, 'fa641edd-017f-45a8-9049-caf4f044b840', 'Orphan Black', 'show', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Orphan Black' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, 'facc7a54-200d-4268-a7c2-b8818f985a8b', 'Night Sky', 'show', 'want', 'Amazon Prime', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Night Sky' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '1759c98d-572e-491d-8da3-a540d9ec7436', 'The 100', 'show', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The 100' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, 'a54dbad7-22ae-4bab-9721-98e5ff94abb1', 'Person of Interest', 'show', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Person of Interest' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, 'df01667f-5d7e-4db3-9a67-d5d54f47fbe1', 'Babylon 5', 'show', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Babylon 5' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, 'e88dc85e-6aa6-4b71-a987-5f570b55b7e5', 'Electric Dreams', 'show', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Electric Dreams' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '2ddd4416-333f-4c57-968f-6a409bc09ff3', 'Humans', 'show', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Humans' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '6cdf8a64-ed73-494e-8b34-323a6f05d438', 'Counterpart', 'show', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Counterpart' AND kind = 'show' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '1d38c480-74d5-4fec-9108-cbd2100fda3c', 'Devs', 'show', 'want', 'Hulu', NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Devs' AND kind = 'show' AND title IS NOT NULL);

-- Games
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, 'e4395cd4-7256-4adb-b7ea-442ee5f901b7', 'Hard Stuck', 'game', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Hard Stuck' AND kind = 'game' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '0e18d818-524e-4052-865d-ccc653d0c7af', 'Project Werewulf', 'game', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Project Werewulf' AND kind = 'game' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '9f4a2007-08b6-4812-a335-db50b24b0cb4', 'Umbranomicon', 'game', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Umbranomicon' AND kind = 'game' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, 'e4e2a466-f0b8-4e96-ab1a-cd104db1b305', 'Operation: Lovecraft', 'game', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Operation: Lovecraft' AND kind = 'game' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '4d1d0061-bfb2-4d8c-8400-990283bfe570', 'Together BnB', 'game', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Together BnB' AND kind = 'game' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '7579f294-5147-49e5-b150-108904c51a26', 'Queen''s Loyalty', 'game', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Queen''s Loyalty' AND kind = 'game' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '283c0c56-a2c3-4778-801c-a1151f603d2a', 'Vindictus: Defying Fate', 'game', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Vindictus: Defying Fate' AND kind = 'game' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, 'e7533256-3469-45c9-acf1-e8e3c619fb7b', 'The Parasites', 'game', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Parasites' AND kind = 'game' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '672f8bd3-fe1d-4447-ba84-d92130a76568', 'The Killing Antidote', 'game', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'The Killing Antidote' AND kind = 'game' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, 'a4de72a0-22e5-4ac5-bfd4-e2a373732c3c', 'Kingdom Come: Deliverance 2', 'game', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Kingdom Come: Deliverance 2' AND kind = 'game' AND title IS NOT NULL);
INSERT INTO media (userID, mediaID, title, kind, status, streaming, creator, created, created_by)
  SELECT @user_id, '5e8a1c2d-5e3a-4fe6-b20b-9776030d90a3', 'Libertine: King of Hearts', 'game', 'want', NULL, NULL, NOW(), @user_id
  WHERE NOT EXISTS (SELECT 1 FROM media WHERE userID = @user_id AND title = 'Libertine: King of Hearts' AND kind = 'game' AND title IS NOT NULL);
