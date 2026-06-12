-- Fix: Replace Accompaniment audio URLs with Vocal for LDS CDN sources.
-- Idempotent: REPLACE on a non-matching string is a no-op.

-- Pattern 1: ldscdn.org URLs with -Accompaniment.mp3 (title-case)
UPDATE study_source
SET audio_url = REPLACE(audio_url, '-Accompaniment.mp3', '-Vocal.mp3')
WHERE audio_url LIKE '%ldscdn%' AND audio_url LIKE '%-Accompaniment.mp3';

-- Pattern 2: ldscdn.org URLs with -accompaniment.mp3 (lowercase)
UPDATE study_source
SET audio_url = REPLACE(audio_url, '-accompaniment.mp3', '-vocal.mp3')
WHERE audio_url LIKE '%ldscdn%' AND audio_url LIKE '%-accompaniment.mp3';

-- Pattern 3: media2.ldscdn.org /assets/music/ paths (title-case)
UPDATE study_source
SET audio_url = REPLACE(audio_url, '-Accompaniment.mp3', '-Vocal.mp3')
WHERE audio_url LIKE '%media2.ldscdn.org/assets/music/%' AND audio_url LIKE '%-Accompaniment.mp3';

-- Pattern 4: media2.ldscdn.org /assets/music/ paths (lowercase)
UPDATE study_source
SET audio_url = REPLACE(audio_url, '-accompaniment.mp3', '-vocal.mp3')
WHERE audio_url LIKE '%media2.ldscdn.org/assets/music/%' AND audio_url LIKE '%-accompaniment.mp3';
