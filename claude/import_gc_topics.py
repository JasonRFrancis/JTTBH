#!/usr/bin/env python3
"""
Seed topic with the master list of General Conference topics.

Source: https://www.churchofjesuschrist.org/study/general-conference/topics?lang=eng
The page is a client-rendered SPA with no usable server HTML/JSON API, so the
list below was captured once via a real browser session (Playwright) reading
each topic link's rendered text — casing is verbatim from the church's site.

Idempotent — safe to re-run (INSERT IGNORE against the UNIQUE(name) constraint).

Run from project root:
    python3 claude/import_gc_topics.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import create_app
from app.services.database import db_manager

TOPICS = [
    'Aaronic Priesthood', 'abortion', 'abuse', 'accountability', 'activation',
    'Adam and Eve', 'addiction', 'adversity', 'agency', 'angels', 'anger',
    'animals', 'answering questions', 'anxiety', 'apathy', 'apostasy',
    'Articles of Faith', 'athletics', 'Atonement', 'Atonement of Jesus Christ',
    'attitude', 'authority', 'balance', 'baptism', 'belonging', 'Bible',
    'bishops', 'blessings', 'Book of Mormon', 'Brigham Young', 'brotherhood',
    'bullying', 'callings', 'character', 'charity', 'chastening', 'children',
    'choices', 'Christianity', 'Christmas', 'Church activity',
    'Church attendance', 'Church callings', 'Church doctrine', 'Church growth',
    'Church history', 'Church leaders', 'Church leadership', 'Church meetings',
    'Church membership', 'Church organization', 'commandments', 'commitment',
    'communication', 'compassion', 'confidence', 'confirmation', 'conscience',
    'consecration', 'contention', 'conversion', 'convert retention', 'councils',
    'couple missionaries', 'courage', 'covenants', 'covetousness', 'Creation',
    'creativity', 'criticism', 'curriculum', 'dating', 'death', 'dedication',
    'depression', 'diligence', 'disabilities', 'discipleship',
    'disciplinary councils', 'discipline', 'dispensations', 'diversity',
    'divine nature', 'divorce', 'Doctrine and Covenants', 'duty', 'Easter',
    'education', 'elderly', 'employment', 'endurance', 'environment',
    'eternal life', 'evil', 'example', 'excellence', 'exodus',
    'Ezra Taft Benson', 'faith', 'Fall', 'false doctrines', 'family',
    'family history', 'family home evening', 'fasting', 'fatherhood', 'fear',
    'fellowshipping', 'financial management', 'First Presidency',
    'First Vision', 'foreordination', 'forgiveness', 'freedom', 'friendship',
    'gambling', 'gathering', 'general conference', 'generosity',
    'gifts of the Spirit', 'goals', 'God the Father', 'Godhead',
    'good Samaritan', 'Gordon B. Hinckley', 'gospel', 'government', 'grace',
    'gratitude', 'greed', 'habits', 'happiness', 'Harold B. Lee', 'healing',
    'health', 'Heavenly Father', 'Heavenly Mother', 'heavenly parents',
    'heroes', 'holidays', 'holiness', 'Holy Ghost', 'holy land', 'home',
    'home teaching', 'homosexuality', 'honesty', 'hope', 'house of Israel',
    'Howard W. Hunter', 'humanitarian aid', 'humility', 'humor', 'hymns',
    'idol worship', 'individual worth', 'inspiration', 'institute',
    'integrity', 'Jesus Christ', 'Joseph Smith', 'joy', 'judging', 'justice',
    'kindness', 'kingdom of God', 'knowledge', 'languages', 'last days',
    'laws', 'leadership', 'learning', 'Light of Christ', 'listening',
    'literacy', 'literature', 'loneliness', 'love', 'loyalty', 'marriage',
    'media', 'meekness', 'Melchizedek Priesthood', 'mental health',
    'mental illness', 'mercy', 'military', 'ministering', 'miracles',
    'mission of the Church', 'missionary service', 'missionary work',
    'modesty', 'morality', 'mortality', 'motherhood', 'music', 'name of Church',
    'Native Americans', 'neighbors', 'New Testament', 'nonmembers',
    'obedience', 'offense', 'Old Testament', 'opposition', 'optimism',
    'ordinances', 'parables', 'parenthood', 'parents', 'Passover', 'patience',
    'patriarchal blessings', 'patriotism', 'peace', 'peacemaking',
    'peer pressure', 'perseverance', 'perspective', 'pioneers',
    'plan of salvation', 'pornography', 'poverty', 'power', 'prayer',
    'prejudice', 'premortal existence', 'preparation', 'pride', 'priesthood',
    'priesthood authority', 'priesthood blessings', 'priesthood keys',
    'priesthood power', 'priesthood quorums', 'Primary', 'principles',
    'priorities', 'profanity', 'promptings', 'prophecy', 'prophets', 'purity',
    'Quorum of the Twelve Apostles', 'Quorums of Seventy', 'redemption',
    'Relief Society', 'religion', 'religious freedom', 'repentance', 'respect',
    'responsibility', 'Restoration', 'Resurrection', 'revelation', 'reverence',
    'righteousness', 'Russell M. Nelson', 'Sabbath', 'sacrament',
    'sacrament meeting', 'sacredness', 'sacrifice', 'safety', 'Satan',
    'Scouting', 'scripture study', 'scriptures', 'sealings', 'Second Coming',
    'self-control', 'self-esteem', 'self-reliance', 'seminary',
    'senior missionaries', 'service', 'sexual purity', 'sharing', 'sin',
    'single adults', 'single members', 'sisterhood', 'social services',
    'Spencer W. Kimball', 'spirit world', 'spiritual gifts',
    'spiritual growth', 'spirituality', 'standards', 'stress', 'success',
    'suicide', 'Sunday School', 'sustaining', 'symbols', 'Tabernacle Choir',
    'talents', 'teaching', 'technology', 'Temple Square', 'temple work',
    'temples', 'temptation', 'testimony', 'Thomas S. Monson',
    'time management', 'tithing', 'tolerance', 'traditions', 'trust', 'truth',
    'U.S. Constitution', 'understanding', 'unity', 'values', 'violence',
    'virtue', 'visiting teaching', 'wealth', 'welfare', 'Wilford Woodruff',
    'wisdom', 'womanhood', 'women', 'Word of Wisdom', 'work', 'worldliness',
    'worship', 'worthiness', 'young adults', 'young single adults',
    'Young Women', 'youth', 'Zion',
]


def main():
    app = create_app()
    with app.app_context():
        row = db_manager.execute_one(
            "SELECT userID FROM `user` WHERE admin = 1 LIMIT 1", ())
        if not row:
            print("ERROR: no admin user found in database")
            sys.exit(1)
        admin_id = row['userID']

        added = 0
        for name in TOPICS:
            result = db_manager.execute_insert(
                "INSERT IGNORE INTO topic (name, created, created_by) VALUES (%s, NOW(), %s)",
                (name, admin_id),
            )
            if result:
                added += 1

        total = db_manager.execute_one("SELECT COUNT(*) AS c FROM topic", ())['c']
        print(f"Added {added} new topics. Total in topic: {total}")


if __name__ == '__main__':
    main()
