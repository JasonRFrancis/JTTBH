-- MySQL dump 10.13  Distrib 9.3.0, for macos15.2 (arm64)
--
-- Host: localhost    Database: jttbh
-- ------------------------------------------------------
-- Server version 9.3.0

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `api_key`
--

DROP TABLE IF EXISTS `api_key`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `api_key` (
  `id` int NOT NULL AUTO_INCREMENT,
  `keyID` varchar(36) NOT NULL,
  `userID` varchar(36) NOT NULL,
  `key_hash` varchar(128) NOT NULL,
  `key_name` varchar(100) NOT NULL,
  `permissions` text,
  `last_used` datetime DEFAULT NULL,
  `active` tinyint(1) DEFAULT '1',
  `expires` datetime DEFAULT NULL,
  `created` datetime DEFAULT CURRENT_TIMESTAMP,
  `created_by` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  UNIQUE KEY `keyID` (`keyID`),
  KEY `idx_keyID` (`keyID`),
  KEY `idx_key_user` (`userID`),
  KEY `idx_key_hash` (`key_hash`),
  KEY `idx_key_active` (`active`),
  KEY `idx_key_last_used` (`last_used`),
  CONSTRAINT `api_keys_ibfk_1` FOREIGN KEY (`userID`) REFERENCES `user` (`userID`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `appointment`
--

DROP TABLE IF EXISTS `appointment`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `appointment` (
  `id` int NOT NULL AUTO_INCREMENT,
  `appointmentID` varchar(36) NOT NULL,
  `userID` varchar(36) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` text,
  `url` varchar(100) NOT NULL,
  `active` tinyint(1) DEFAULT NULL,
  `location` varchar(200) DEFAULT NULL,
  `type` varchar(50) DEFAULT NULL,
  `color` varchar(20) DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(36) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  UNIQUE KEY `url` (`url`),
  CONSTRAINT `scheduling_profile_ibfk_1` FOREIGN KEY (`userID`) REFERENCES `user` (`userID`)
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `appointment_block`
--

DROP TABLE IF EXISTS `appointment_block`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `appointment_block` (
  `id` int NOT NULL AUTO_INCREMENT,
  `appointmentID` varchar(36) NOT NULL,
  `blockID` varchar(36) NOT NULL,
  `label` varchar(100) NOT NULL,
  `begin` datetime NOT NULL,
  `end` datetime NOT NULL,
  `created` datetime NOT NULL,
  `created_by` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `ix_blockID` (`blockID`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `appointment_invite`
--

DROP TABLE IF EXISTS `appointment_invite`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `appointment_invite` (
  `id` int NOT NULL AUTO_INCREMENT,
  `appointmentID` varchar(36) NOT NULL,
  `blockID` varchar(36) NOT NULL,
  `name` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `instructions` text,
  `begin` datetime NOT NULL,
  `end` datetime NOT NULL,
  `created` datetime NOT NULL,
  `created_by` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `ix_blockID` (`blockID`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `book`
--

DROP TABLE IF EXISTS `book`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `book` (
  `id` int NOT NULL AUTO_INCREMENT,
  `bookID` varchar(36) NOT NULL,
  `userID` varchar(36) NOT NULL,
  `title` varchar(500) DEFAULT NULL COMMENT 'NULL = soft deleted',
  `author` varchar(300) DEFAULT NULL,
  `isbn` varchar(20) DEFAULT NULL,
  `pages` int DEFAULT NULL,
  `tags` varchar(100) DEFAULT NULL,
  `cover` text,
  `status` enum ('want_to_read','reading','completed','dismiss') DEFAULT 'want_to_read',
  `rating` int DEFAULT NULL,
  `review` text,
  `notes` text,
  `started` date DEFAULT NULL,
  `finished` date DEFAULT NULL,
  `created` datetime DEFAULT CURRENT_TIMESTAMP,
  `created_by` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `bookID` (`bookID`),
  KEY `idx_book_user` (`userID`),
  KEY `idx_book_status` (`status`),
  KEY `idx_book_isbn` (`isbn`),
  CONSTRAINT `books_ibfk_1` FOREIGN KEY (`userID`) REFERENCES `user` (`userID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `bookmark`
--

DROP TABLE IF EXISTS `bookmark`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bookmark` (
  `id` int NOT NULL AUTO_INCREMENT,
  `bookmarkID` varchar(36) NOT NULL,
  `userID` varchar(36) NOT NULL,
  `url` text NOT NULL,
  `title` varchar(500) NOT NULL,
  `description` text,
  `tags` text,
  `read_later` tinyint(1) DEFAULT '0',
  `read` tinyint(1) DEFAULT '0',
  `favorite` tinyint(1) NOT NULL DEFAULT '0',
  `notes` text,
  `favicon` text,
  `created` datetime DEFAULT CURRENT_TIMESTAMP,
  `created_by` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  UNIQUE KEY `bookmarkID` (`bookmarkID`),
  KEY `idx_bookmark_user` (`userID`),
  KEY `idx_bookmarks_read_later` (`userID`,`read_later`),
  CONSTRAINT `bookmark_ibfk_1` FOREIGN KEY (`userID`) REFERENCES `user` (`userID`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=363 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `bookmark_content`
--

DROP TABLE IF EXISTS `bookmark_content`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bookmark_content` (
  `id` int NOT NULL AUTO_INCREMENT,
  `bookmarkID` varchar(36) NOT NULL,
  `content_text` longtext,
  `content_html` longtext,
  `extracted` datetime DEFAULT CURRENT_TIMESTAMP,
  `status` varchar(50) DEFAULT 'pending',
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `idx_bookmark_content_uuid` (`bookmarkID`),
  KEY `idx_bookmark_content_status` (`status`),
  CONSTRAINT `bookmark_content_ibfk_1` FOREIGN KEY (`bookmarkID`) REFERENCES `bookmark` (`bookmarkID`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=2 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `bookmark_tag`
--

DROP TABLE IF EXISTS `bookmark_tag`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `bookmark_tag` (
  `id` int NOT NULL AUTO_INCREMENT,
  `userID` varchar(36) NOT NULL,
  `tag` varchar(100) NOT NULL,
  `created` datetime DEFAULT CURRENT_TIMESTAMP,
  `created_by` varchar(36) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  UNIQUE KEY `unique_user_tag` (`userID`,`tag`),
  KEY `idx_bookmark_tags_user` (`userID`),
  KEY `idx_bookmark_tags_name` (`tag`),
  CONSTRAINT `bookmark_tags_ibfk_1` FOREIGN KEY (`userID`) REFERENCES `user` (`userID`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `bookmark_category`
--

DROP TABLE IF EXISTS `bookmark_category`;
CREATE TABLE `bookmark_category` (
  `id` int NOT NULL AUTO_INCREMENT,
  `categoryID` varchar(36) NOT NULL,
  `userID` varchar(36) NOT NULL,
  `name` varchar(200) NOT NULL,
  `position` int NOT NULL DEFAULT '0',
  `criteria` text,
  `created` datetime DEFAULT CURRENT_TIMESTAMP,
  `created_by` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_categoryID` (`categoryID`),
  KEY `idx_bcat_user` (`userID`),
  CONSTRAINT `fk_bcat_user` FOREIGN KEY (`userID`) REFERENCES `user` (`userID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Table structure for table `bookmark_category_item`
--

DROP TABLE IF EXISTS `bookmark_category_item`;
CREATE TABLE `bookmark_category_item` (
  `id` int NOT NULL AUTO_INCREMENT,
  `categoryID` varchar(36) NOT NULL,
  `bookmarkID` varchar(36) NOT NULL,
  `userID` varchar(36) NOT NULL,
  `position` int NOT NULL DEFAULT '0',
  `created` datetime DEFAULT CURRENT_TIMESTAMP,
  `created_by` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_cat_bm` (`categoryID`,`bookmarkID`),
  KEY `idx_catitem_cat` (`categoryID`),
  KEY `idx_catitem_bm` (`bookmarkID`),
  CONSTRAINT `fk_catitem_cat` FOREIGN KEY (`categoryID`) REFERENCES `bookmark_category` (`categoryID`) ON DELETE CASCADE,
  CONSTRAINT `fk_catitem_bm` FOREIGN KEY (`bookmarkID`) REFERENCES `bookmark` (`bookmarkID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

--
-- Table structure for table `chore`
--

DROP TABLE IF EXISTS `chore`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `chore` (
  `id` int NOT NULL AUTO_INCREMENT,
  `choreID` varchar(36) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` varchar(100) NOT NULL,
  `created` datetime DEFAULT CURRENT_TIMESTAMP,
  `created_by` varchar(36) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `idx_chore_name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `chore_assigned`
--

DROP TABLE IF EXISTS `chore_assigned`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `chore_assigned` (
  `id` int NOT NULL AUTO_INCREMENT,
  `householdID` varchar(36) NOT NULL,
  `choreID` varchar(36) NOT NULL,
  `assigned` datetime DEFAULT CURRENT_TIMESTAMP,
  `assigned_to` varchar(36) NOT NULL,
  `completed` datetime DEFAULT CURRENT_TIMESTAMP,
  `completed_by` varchar(36) NOT NULL,
  `created` datetime DEFAULT CURRENT_TIMESTAMP,
  `created_by` varchar(36) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `idx_chore_list_householdID` (`householdID`),
  KEY `idx_chore_list_choreID` (`choreID`),
  KEY `idx_chore_list_assignedTo` (`assigned_to`),
  KEY `idx_chore_list_completed` (`completed`),
  KEY `idx_chore_list_completedBy` (`completed_by`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `chore_list`
--

DROP TABLE IF EXISTS `chore_list`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `chore_list` (
  `id` int NOT NULL AUTO_INCREMENT,
  `choreListID` varchar(36) NOT NULL,
  `householdID` varchar(36) NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` varchar(100) NOT NULL,
  `created` datetime DEFAULT CURRENT_TIMESTAMP,
  `created_by` varchar(36) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `idx_chore_list_householdID` (`householdID`),
  KEY `idx_chore_list_name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `chore_listItem`
--

DROP TABLE IF EXISTS `chore_listItemDay`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `chore_listItemDay` (
  `id` int NOT NULL AUTO_INCREMENT,
  `choreListID` varchar(36) NOT NULL,
  `choreID` varchar(36) NOT NULL,
  `season` tinyint NOT NULL,  -- bitvector: 1 = spring, 2 = summer, 4 = fall, 8 = winter
  `day_of_week` tinyint NOT NULL,  -- bitvector: 1 = Sunday, 2 = Monday, 4 = Tuesday, 8 = Wednesday, 16 = Thursday, 32 = Friday, 64 = Saturday
  `created` datetime DEFAULT CURRENT_TIMESTAMP,
  `created_by` varchar(36) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `idx_chore_list_choreListID` (`choreListID`),
  KEY `idx_chore_list_choreID` (`choreID`),
  KEY `idx_chore_list_season` (`season`),
  KEY `idx_chore_list_day` (`day_of_week`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `chore_listItemMonth`
--

DROP TABLE IF EXISTS `chore_listItemMonth`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `chore_listItemMonth` (
  `id` int NOT NULL AUTO_INCREMENT,
  `choreListID` varchar(36) NOT NULL,
  `choreID` varchar(36) NOT NULL,
  `month` int NOT NULL,  -- bitvector: 1 = January, 2 = February, 4 = March, 8 = April, 16 = May, 32 = June, 64 = July, 128 = August, 256 = September, 512 = October, 1024 = November, 2048 = December
  `day_of_month` tinyint NOT NULL, 
  `created` datetime DEFAULT CURRENT_TIMESTAMP,
  `created_by` varchar(36) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `idx_chore_list_choreListID` (`choreListID`),
  KEY `idx_chore_list_choreID` (`choreID`),
  KEY `idx_chore_list_month` (`month`),
  KEY `idx_chore_list_day` (`day_of_month`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `enum`
--

DROP TABLE IF EXISTS `enum`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `enum` (
  `id` int NOT NULL AUTO_INCREMENT,
  `namespace` varchar(50) NOT NULL,
  `name` varchar(100) NOT NULL,
  `value` int NOT NULL,
  `created` datetime NOT NULL,
  `created_by` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `ix_enum_name` (`name`),
  KEY `ix_enum_value` (`value`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


DROP TABLE IF EXISTS `fitness`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fitness` (
  `id` int NOT NULL AUTO_INCREMENT,
  `fitnessID` varchar(36) NOT NULL,
  `userID` varchar(36) NOT NULL,
  `name` varchar(255) DEFAULT NULL,  -- NULL = soft deleted
  `description` text,
  `start_date` date DEFAULT NULL,
  `active` tinyint(1) NOT NULL DEFAULT 0,
  `created` datetime NOT NULL,
  `created_by` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `idx_fitnessID` (`fitnessID`),
  KEY `idx_userID` (`userID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='User workout programs';
/*!40101 SET character_set_client = @saved_cs_client */;

DROP TABLE IF EXISTS `fitness_bodyWeight`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fitness_bodyWeight` (
  `id` int NOT NULL AUTO_INCREMENT,
  `weightID` varchar(36) NOT NULL,
  `userID` varchar(36) NOT NULL,
  `weight` decimal(5,1) NOT NULL,
  `unit` enum('lbs','kg') NOT NULL DEFAULT 'lbs',
  `recorded` date NOT NULL,
  `created` datetime NOT NULL,
  `created_by` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `idx_weightID` (`weightID`),
  KEY `idx_userID_recorded` (`userID`, `recorded`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

DROP TABLE IF EXISTS `fitness_exercise`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fitness_exercise` (
  `id` int NOT NULL AUTO_INCREMENT,
  `exerciseID` varchar(36) NOT NULL,
  `name` varchar(255) DEFAULT NULL,  -- NULL = soft deleted
  `description` text,
  `equipment_type` enum('weight_machine','hand_weight','bodyweight','cable','other') NOT NULL DEFAULT 'weight_machine',
  `muscle_group` varchar(100) DEFAULT NULL,
  `video_url` varchar(512) DEFAULT NULL,
  `type` enum('machine','hand_weight','bodyweight','cardio','video') NOT NULL DEFAULT 'machine',
  `created` datetime NOT NULL,
  `created_by` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `idx_exerciseID` (`exerciseID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Catalog of all exercises';
/*!40101 SET character_set_client = @saved_cs_client */;

DROP TABLE IF EXISTS `fitness_program`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fitness_program` (
  `id` int NOT NULL AUTO_INCREMENT,
  `programID` varchar(36) NOT NULL,
  `fitnessID` varchar(36) NOT NULL,
  `day_of_week` int NOT NULL,  -- 0=Sunday, 1=Monday, ..., 6=Saturday
  `exerciseID` varchar(36) DEFAULT NULL,  -- NULL = soft deleted
  `order_index` int NOT NULL DEFAULT 0,
  `recommended_weight` decimal(6,2) DEFAULT NULL,
  `recommended_sets` int DEFAULT '3',
  `recommended_reps` int DEFAULT '10',
  `rest_seconds` int DEFAULT 60,
  `notes` text,  -- machine adjustment notes (e.g. "Seat: 5")
  `location` enum('gym','home','other') NOT NULL DEFAULT 'gym',
  `recommended_duration` int DEFAULT NULL,   -- cardio: minutes
  `recommended_speed` decimal(4,2) DEFAULT NULL,  -- cardio: mph
  `recommended_incline` decimal(4,1) DEFAULT NULL, -- cardio: degrees
  `created` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `idx_programID` (`programID`),
  KEY `idx_fitnessID` (`fitnessID`),
  KEY `idx_day` (`day_of_week`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Exercises scheduled per day in a program';
/*!40101 SET character_set_client = @saved_cs_client */;

DROP TABLE IF EXISTS `fitness_log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fitness_log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `logID` varchar(36) NOT NULL,
  `userID` varchar(36) NOT NULL,
  `fitnessID` varchar(36) DEFAULT NULL,
  `log_date` date DEFAULT NULL,  -- NULL = soft deleted
  `start_time` datetime DEFAULT NULL,
  `end_time` datetime DEFAULT NULL,
  `location` enum('gym','home','other') DEFAULT 'gym',
  `notes` text,
  `created` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `idx_logID` (`logID`),
  KEY `idx_userID` (`userID`),
  KEY `idx_date` (`log_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Workout sessions';
/*!40101 SET character_set_client = @saved_cs_client */;

DROP TABLE IF EXISTS `fitness_logSet`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `fitness_logSet` (
  `id` int NOT NULL AUTO_INCREMENT,
  `logSetID` varchar(36) NOT NULL,
  `logID` varchar(36) NOT NULL,
  `exerciseID` varchar(36) DEFAULT NULL,  -- NULL = soft deleted
  `set_number` int NOT NULL,
  `actual_weight` decimal(6,2) DEFAULT NULL,
  `actual_reps` int DEFAULT NULL,
  `notes` text,
  `setup` varchar(255) DEFAULT NULL,      -- machine/cardio: session setup notes
  `duration_minutes` int DEFAULT NULL,    -- cardio: minutes; bodyweight: seconds
  `speed` decimal(4,2) DEFAULT NULL,      -- cardio mph
  `incline` decimal(4,1) DEFAULT NULL,    -- cardio degrees (legacy, preserved)
  `created` datetime NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `idx_logSetID` (`logSetID`),
  KEY `idx_logID` (`logID`),
  KEY `idx_exerciseID` (`exerciseID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='Individual sets performed in workouts';
/*!40101 SET character_set_client = @saved_cs_client */;


-- ============================================================================
-- INITIAL DATA: Populate with common gym exercises
-- ============================================================================

-- LEG MACHINES
INSERT INTO `fitness_exercise` (`id`, `exerciseID`, `name`, `description`, `equipment_type`, `muscle_group`, `video_url`, `created`) VALUES
(1, UUID(), 'Leg Press', 'Compound leg exercise targeting quads, hamstrings, and glutes', 'weight_machine', 'legs', NULL, NOW()),
(2, UUID(), 'Leg Extension', 'Isolation exercise for quadriceps', 'weight_machine', 'legs', NULL, NOW()),
(3, UUID(), 'Leg Curl', 'Isolation exercise for hamstrings', 'weight_machine', 'legs', NULL, NOW()),
(4, UUID(), 'Seated Calf Raise', 'Isolation exercise for calves (soleus)', 'weight_machine', 'legs', NULL, NOW()),
(5, UUID(), 'Standing Calf Raise', 'Isolation exercise for calves (gastrocnemius)', 'weight_machine', 'legs', NULL, NOW()),
(6, UUID(), 'Hip Abductor', 'Isolation exercise for outer thighs and glutes', 'weight_machine', 'legs', NULL, NOW()),
(7, UUID(), 'Hip Adductor', 'Isolation exercise for inner thighs', 'weight_machine', 'legs', NULL, NOW()),
(8, UUID(), 'Hack Squat', 'Compound leg exercise emphasizing quads', 'weight_machine', 'legs', NULL, NOW()),

-- CHEST MACHINES
(9, UUID(), 'Chest Press Machine', 'Compound exercise for chest, shoulders, triceps', 'weight_machine', 'chest', NULL, NOW()),
(10, UUID(), 'Pec Fly Machine', 'Isolation exercise for chest', 'weight_machine', 'chest', NULL, NOW()),
(11, UUID(), 'Incline Chest Press', 'Compound exercise targeting upper chest', 'weight_machine', 'chest', NULL, NOW()),
(12, UUID(), 'Cable Crossover', 'Isolation exercise for chest with constant tension', 'cable', 'chest', NULL, NOW()),

-- BACK MACHINES
(13, UUID(), 'Lat Pulldown', 'Compound exercise for lats and upper back', 'weight_machine', 'back', NULL, NOW()),
(14, UUID(), 'Seated Cable Row', 'Compound exercise for mid-back and lats', 'cable', 'back', NULL, NOW()),
(15, UUID(), 'T-Bar Row', 'Compound exercise for mid-back thickness', 'weight_machine', 'back', NULL, NOW()),
(16, UUID(), 'Back Extension', 'Lower back and glute strengthening', 'weight_machine', 'back', NULL, NOW()),
(17, UUID(), 'Assisted Pull-Up Machine', 'Compound exercise for lats and biceps', 'weight_machine', 'back', NULL, NOW()),

-- SHOULDER MACHINES
(18, UUID(), 'Shoulder Press Machine', 'Compound exercise for shoulders and triceps', 'weight_machine', 'shoulders', NULL, NOW()),
(19, UUID(), 'Lateral Raise Machine', 'Isolation exercise for side delts', 'weight_machine', 'shoulders', NULL, NOW()),
(20, UUID(), 'Rear Delt Fly Machine', 'Isolation exercise for rear delts', 'weight_machine', 'shoulders', NULL, NOW()),

-- ARM MACHINES
(21, UUID(), 'Bicep Curl Machine', 'Isolation exercise for biceps', 'weight_machine', 'arms', NULL, NOW()),
(22, UUID(), 'Tricep Extension Machine', 'Isolation exercise for triceps', 'weight_machine', 'arms', NULL, NOW()),
(23, UUID(), 'Tricep Dip Machine', 'Compound exercise for triceps and chest', 'weight_machine', 'arms', NULL, NOW()),
(24, UUID(), 'Preacher Curl Machine', 'Isolation exercise for biceps', 'weight_machine', 'arms', NULL, NOW()),
(25, UUID(), 'Cable Tricep Pushdown', 'Isolation exercise for triceps', 'cable', 'arms', NULL, NOW()),

-- CORE MACHINES
(26, UUID(), 'Ab Crunch Machine', 'Isolation exercise for abs', 'weight_machine', 'core', NULL, NOW()),
(27, UUID(), 'Torso Rotation Machine', 'Isolation exercise for obliques', 'weight_machine', 'core', NULL, NOW()),
(28, UUID(), 'Cable Woodchop', 'Compound core exercise for obliques', 'cable', 'core', NULL, NOW()),

-- HAND WEIGHT EXERCISES (DUMBBELLS)
(29, UUID(), 'Dumbbell Bench Press', 'Compound chest exercise with greater range of motion', 'hand_weight', 'chest', NULL, NOW()),
(30, UUID(), 'Dumbbell Shoulder Press', 'Compound shoulder exercise', 'hand_weight', 'shoulders', NULL, NOW()),
(31, UUID(), 'Dumbbell Bicep Curl', 'Isolation exercise for biceps', 'hand_weight', 'arms', NULL, NOW()),
(32, UUID(), 'Dumbbell Tricep Extension', 'Isolation exercise for triceps', 'hand_weight', 'arms', NULL, NOW()),
(33, UUID(), 'Dumbbell Lateral Raise', 'Isolation exercise for side delts', 'hand_weight', 'shoulders', NULL, NOW()),
(34, UUID(), 'Dumbbell Bent-Over Row', 'Compound exercise for back', 'hand_weight', 'back', NULL, NOW()),
(35, UUID(), 'Dumbbell Goblet Squat', 'Compound leg exercise', 'hand_weight', 'legs', NULL, NOW()),
(36, UUID(), 'Dumbbell Lunges', 'Compound leg exercise', 'hand_weight', 'legs', NULL, NOW()),
(37, UUID(), 'Dumbbell Chest Fly', 'Isolation exercise for chest', 'hand_weight', 'chest', NULL, NOW()),
(38, UUID(), 'Dumbbell Front Raise', 'Isolation exercise for front delts', 'hand_weight', 'shoulders', NULL, NOW()),
(39, UUID(), 'Dumbbell Shrug', 'Isolation exercise for traps', 'hand_weight', 'back', NULL, NOW()),
(40, UUID(), 'Dumbbell Hammer Curl', 'Isolation exercise for biceps and forearms', 'hand_weight', 'arms', NULL, NOW()),
(41, UUID(), 'Treadmill', 'Incline treadmill walk', 'other', 'cardio', NULL, NOW());

-- Fix types: bulk INSERT defaults to 'machine'; correct hand_weight and bodyweight rows
UPDATE fitness_exercise SET `type` = 'hand_weight' WHERE equipment_type = 'hand_weight';
UPDATE fitness_exercise SET `type` = 'bodyweight'  WHERE equipment_type = 'bodyweight';
UPDATE fitness_exercise SET `type` = 'cardio'      WHERE `name` = 'Treadmill';

-- Bodyweight + forearm exercises added in goals migration
INSERT INTO `fitness_exercise` (`exerciseID`, `name`, `description`, `equipment_type`, `muscle_group`, `created`) VALUES
(UUID(), 'Push-up', 'Standard push-up targeting chest, shoulders, and triceps', 'bodyweight', 'chest', NOW()),
(UUID(), 'Pike Push-up', 'Inverted V push-up that loads the shoulders like an overhead press', 'bodyweight', 'shoulders', NOW()),
(UUID(), 'Plank', 'Isometric core hold — builds deep stabilizer strength', 'bodyweight', 'core', NOW()),
(UUID(), 'Bicycle Crunch', 'Alternating elbow-to-knee crunch targeting abs and obliques', 'bodyweight', 'core', NOW()),
(UUID(), 'Russian Twist', 'Seated trunk rotation — primary oblique builder', 'bodyweight', 'core', NOW()),
(UUID(), 'Leg Raise', 'Lying leg raise targeting lower abs', 'bodyweight', 'core', NOW()),
(UUID(), 'Dumbbell Reverse Curl', 'Overhand-grip curl — builds brachioradialis and forearm extensors', 'hand_weight', 'forearms', NOW()),
(UUID(), 'Dumbbell Wrist Curl', 'Palm-up wrist flexion — targets forearm flexors', 'hand_weight', 'forearms', NOW());


--
-- Table structure for table `habit`
--

DROP TABLE IF EXISTS `habit`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `habit` (
  `id` int NOT NULL AUTO_INCREMENT,
  `habitID` varchar(36) NOT NULL,
  `userID` varchar(36) NOT NULL,
  `name` varchar(100) DEFAULT NULL COMMENT 'NULL = soft deleted',
  `description` text,
  `action` text COMMENT 'Optional URL or internal link for habit action',
  `color` varchar(7) DEFAULT NULL,
  `icon` varchar(50) DEFAULT NULL,
  `active` tinyint(1) DEFAULT NULL,
  `dayweek` int DEFAULT NULL,
  `position` tinyint unsigned DEFAULT NULL,
  `vacation_mode` tinyint(1) DEFAULT 1 COMMENT 'Whether this habit is affected by vacation mode',
  `created` datetime NOT NULL,
  `created_by` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `ix_habit_habitID` (`habitID`),
  KEY `ix_habit_userID` (`userID`)
) ENGINE=InnoDB AUTO_INCREMENT=18 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `habit_entry`
--

DROP TABLE IF EXISTS `habit_entry`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `habit_entry` (
  `id` int NOT NULL AUTO_INCREMENT,
  `habitID` varchar(36) NOT NULL,
  `entry` date NOT NULL,
  `completed` int DEFAULT NULL,
  `vacation` tinyint(1) DEFAULT NULL,
  `change_id` varchar(36) DEFAULT NULL COMMENT 'Client-generated UUID per toggle request; UNIQUE prevents duplicate processing on retry',
  `created` datetime NOT NULL,
  `created_by` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `idx_habit_entry` (`entry`),
  KEY `idx_user_entry` (`habitID`,`entry`),
  KEY `id` (`id`),
  UNIQUE KEY `uniq_change_id` (`change_id`)
) ENGINE=InnoDB AUTO_INCREMENT=6697 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `household`
--

DROP TABLE IF EXISTS `household`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `household` (
  `id` int NOT NULL AUTO_INCREMENT,
  `householdID` varchar(36) NOT NULL,
  `name` varchar(100) NOT NULL,
  `created` datetime NOT NULL,
  `created_by` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `idx_household_id` (`householdID`)
) ENGINE=InnoDB AUTO_INCREMENT=6697 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `household_member`
--

DROP TABLE IF EXISTS `household_member`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `household_member` (
  `id` int NOT NULL AUTO_INCREMENT,
  `householdID` varchar(36) NOT NULL,
  `userID` varchar(36) NOT NULL,
  `orderBy` int,
  `created` datetime NOT NULL,
  `created_by` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `idx_householdid` (`householdID`),
  KEY `idx_userID` (`userID`)
) ENGINE=InnoDB AUTO_INCREMENT=6697 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


--
-- Table structure for table `journal_answer`
--

DROP TABLE IF EXISTS `journal_answer`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `journal_answer` (
  `id` int NOT NULL AUTO_INCREMENT,
  `answerID` varchar(36) NOT NULL,
  `userID` varchar(36) NOT NULL,
  `questionID` varchar(36) NOT NULL,
  `answer` text NOT NULL,
  `answered` date NOT NULL,
  `created` datetime DEFAULT CURRENT_TIMESTAMP,
  `created_by` varchar(36) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `idx_answer_uuid` (`answerID`),
  KEY `idx_answer_user` (`userID`),
  KEY `idx_answer_question` (`questionID`),
  KEY `idx_answer_date` (`answered`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


--
-- Table structure for table `journal_mood`
--

DROP TABLE IF EXISTS `journal_mood`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `journal_mood` (
  `id` int NOT NULL AUTO_INCREMENT,
  `moodID` varchar(36) NOT NULL,
  `userID` varchar(36) NOT NULL,
  `categoryID` varchar(36) NOT NULL,
  `value` int NOT NULL,
  `answered` date NOT NULL,
  `created` datetime DEFAULT CURRENT_TIMESTAMP,
  `created_by` varchar(36) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `idx_moodID` (`moodID`),
  KEY `idx_user` (`userID`),
  KEY `idx_answer_question` (`categoryID`),
  KEY `idx_answer_date` (`answered`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


--
-- Table structure for table `journal_moodCategory`
--

DROP TABLE IF EXISTS `journal_moodCategory`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `journal_moodCategory` (
  `id` int NOT NULL AUTO_INCREMENT,
  `categoryID` varchar(36) NOT NULL,
  `userID` varchar(36) NOT NULL,
  `name` varchar(100) NOT NULL,
  `created` datetime DEFAULT CURRENT_TIMESTAMP,
  `created_by` varchar(36) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `idx_categoryID` (`categoryID`), 
  KEY `idx_user` (`userID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


--
-- Table structure for table `journal_moodValue`
--

DROP TABLE IF EXISTS `journal_moodValue`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `journal_moodValue` (
  `id` int NOT NULL AUTO_INCREMENT,
  `categoryID` varchar(36) DEFAULT NULL,
  `userID` varchar(36) NOT NULL,
  `value` int NOT NULL,
  `name` varchar(100) NOT NULL,
  `color` varchar(100) NOT NULL,
  `icon` text DEFAULT NULL,
  `created` datetime DEFAULT CURRENT_TIMESTAMP,
  `created_by` varchar(36) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `idx_categoryID` (`categoryID`),
  KEY `idx_user` (`userID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `journal_question`
--

DROP TABLE IF EXISTS `journal_question`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `journal_question` (
  `id` int NOT NULL AUTO_INCREMENT,
  `questionID` varchar(36) NOT NULL,
  `question` text NOT NULL,
  `day` int NOT NULL,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(36) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC)
) ENGINE=InnoDB AUTO_INCREMENT=21 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


--
-- Table structure for table `log`
--

DROP TABLE IF EXISTS `log`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `log` (
  `id` int NOT NULL AUTO_INCREMENT,
  `userid` varchar(36),
  `username` varchar(50),
  `area` varchar(50),
  `resource` varchar(150),
  `presentation` varchar(50),
  `parameters` varchar(250),
  `history` varchar(50),
  `get` text,
  `post` text,
  `ip` varchar(45) DEFAULT NULL,
  `user_agent` text,
  `created` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


--
-- Table structure for table `log_api`
--

DROP TABLE IF EXISTS `log_api`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `log_api` (
  `id` int NOT NULL AUTO_INCREMENT,
  `keyID` varchar(36) NOT NULL,
  `endpoint` varchar(200) NOT NULL,
  `method` varchar(10) NOT NULL,
  `ip` varchar(45) DEFAULT NULL,
  `user_agent` text,
  `response_status` int DEFAULT NULL,
  `response_time` int DEFAULT NULL,
  `request_size` int DEFAULT NULL,
  `response_size` int DEFAULT NULL,
  `created` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `idx_usage_log_key` (`keyID`),
  KEY `idx_usage_log_endpoint` (`endpoint`),
  KEY `idx_usage_log_status` (`response_status`),
  KEY `idx_usage_log` (`created`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `media`
--

DROP TABLE IF EXISTS `media`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `media` (
  `id` int NOT NULL AUTO_INCREMENT,
  `mediaID` varchar(36) NOT NULL,
  `userID` varchar(36) NOT NULL,
  `title` varchar(500) DEFAULT NULL,
  `kind` enum('book','movie','show','podcast','videogame','boardgame') NOT NULL DEFAULT 'book',
  `creator` varchar(255) DEFAULT NULL,
  `status` enum('want','in_progress','done','dismiss') NOT NULL DEFAULT 'want',
  `rating` tinyint DEFAULT NULL,
  `review` text,
  `external_id` varchar(500) DEFAULT NULL,
  `cover_url` varchar(500) DEFAULT NULL,
  `streaming` varchar(255) DEFAULT NULL,
  `next_date` date DEFAULT NULL,
  `started` date DEFAULT NULL,
  `finished` date DEFAULT NULL,
  `created` datetime NOT NULL,
  `created_by` varchar(36) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `mediaID` (`mediaID`),
  KEY `userID` (`userID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `media_episode`
--

DROP TABLE IF EXISTS `media_episode`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `media_episode` (
  `id` int NOT NULL AUTO_INCREMENT,
  `episodeID` varchar(36) NOT NULL,
  `mediaID` varchar(36) NOT NULL,
  `title` varchar(500) DEFAULT NULL,
  `season` smallint DEFAULT NULL,
  `episode_number` smallint DEFAULT NULL,
  `air_date` date DEFAULT NULL,
  `seen` tinyint NOT NULL DEFAULT '0',
  `description` text,
  `external_id` varchar(500) DEFAULT NULL,
  `created` datetime NOT NULL,
  `created_by` varchar(36) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `episodeID` (`episodeID`),
  KEY `mediaID` (`mediaID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `podcast`
--

DROP TABLE IF EXISTS `podcast`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `podcast` (
  `id` int NOT NULL AUTO_INCREMENT,
  `feedID` varchar(36) NOT NULL,
  `userID` varchar(36) NOT NULL,
  `name` varchar(200) NOT NULL,
  `description` text,
  `date_from` date DEFAULT NULL,
  `artwork` text,
  `created` datetime NOT NULL,
  `created_by` varchar(36) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `ix_podcast_feed_userID` (`userID`),
  KEY `ix_podcast_feed_feedID` (`feedID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `podcast_episode`
--

DROP TABLE IF EXISTS `podcast_episode`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `podcast_episode` (
  `id` int NOT NULL AUTO_INCREMENT,
  `episodeID` varchar(36) NOT NULL,
  `category` varchar(100) DEFAULT NULL,
  `title` varchar(500) NOT NULL,
  `author` varchar(200) DEFAULT NULL,
  `description` text,
  `file_url` text NOT NULL,
  `file_size` bigint DEFAULT NULL,
  `file_type` varchar(50) DEFAULT NULL,
  `duration` int DEFAULT NULL,
  `episode` int DEFAULT NULL,
  `season` varchar(100) DEFAULT NULL,
  `artwork` text,
  `created` datetime NOT NULL,
  `created_by` varchar(36) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `podcast_list`
--

DROP TABLE IF EXISTS `podcast_list`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `podcast_list` (
  `id` int NOT NULL AUTO_INCREMENT,
  `listID` varchar(36) NOT NULL,
  `category` varchar(100) DEFAULT NULL,
  `title` varchar(500) NOT NULL,
  `description` text,
  `frequency` enum('daily','twoperday','threeperday','fourperday','weekly') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'daily',
  `repeat` bit NOT NULL DEFAULT 1,
  `created` datetime NOT NULL,
  `created_by` varchar(36) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `podcast_listItem`
--

DROP TABLE IF EXISTS `podcast_listItem`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `podcast_listItem` (
  `id` int NOT NULL AUTO_INCREMENT,
  `itemID` varchar(36) NOT NULL,
  `listID` varchar(36) NOT NULL,
  `episodeID` varchar(36) NOT NULL,
  `created` datetime NOT NULL,
  `created_by` varchar(36) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `podcast_subscription`
--

DROP TABLE IF EXISTS `podcast_subscription`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `podcast_subscription` (
  `id` int NOT NULL AUTO_INCREMENT,
  `subscriptionID` varchar(36) NOT NULL,
  `feedID` varchar(36) NOT NULL,
  `listID` varchar(36) NOT NULL,
  `day_offset` int NOT NULL,
  `created` datetime NOT NULL,
  `created_by` varchar(36) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `project`
--

DROP TABLE IF EXISTS `project`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `project` (
  `id` int NOT NULL AUTO_INCREMENT,
  `projectID` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `userID` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'NULL = soft deleted',
  `description` text COLLATE utf8mb4_unicode_ci,
  `next_step` text COLLATE utf8mb4_unicode_ci,
  `position` int DEFAULT '0',
  `created` datetime DEFAULT CURRENT_TIMESTAMP,
  `created_by` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `idx_projectID` (`projectID`),
  KEY `idx_userID` (`userID`),
  KEY `idx_position` (`position`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `project_resource`
--

DROP TABLE IF EXISTS `project_resource`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `project_resource` (
  `id` int NOT NULL AUTO_INCREMENT,
  `resourceID` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `projectID` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'NULL = soft deleted',
  `resource` text COLLATE utf8mb4_unicode_ci,
  `note` text COLLATE utf8mb4_unicode_ci,
  `position` int DEFAULT '0',
  `created` datetime DEFAULT CURRENT_TIMESTAMP,
  `created_by` varchar(36) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `idx_resourceID` (`resourceID`),
  KEY `idx_projectID` (`projectID`),
  KEY `idx_position` (`position`)
) ENGINE=InnoDB AUTO_INCREMENT=4 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


--
-- Table structure for table `svg`
--

DROP TABLE IF EXISTS `svg`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `svg` (
  `id` int NOT NULL AUTO_INCREMENT,
  `imageID` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `description` text COLLATE utf8mb4_unicode_ci,
  `svg` text COLLATE utf8mb4_unicode_ci NOT NULL,
  `created` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  UNIQUE KEY `imageID` (`imageID`),
  KEY `idx_svg_images_name` (`name`)
) ENGINE=InnoDB AUTO_INCREMENT=26 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `todo`
--

DROP TABLE IF EXISTS `todo`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `todo` (
  `id` int NOT NULL AUTO_INCREMENT,
  `todoID` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `userID` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `title` varchar(255) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'NULL = soft deleted',
  `content` text COLLATE utf8mb4_unicode_ci,
  `due` date DEFAULT NULL,
  `list_type` enum('daily','custom','planning') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'daily',
  `list_name` varchar(100) COLLATE utf8mb4_unicode_ci DEFAULT NULL,
  `position` int NOT NULL DEFAULT '0',
  `completed` datetime DEFAULT NULL,
  `added` date DEFAULT NULL,
  `created` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `idx_todoID` (`todoID`),
  KEY `idx_userID` (`userID`),
  KEY `idx_user` (`userID`,`due`),
  KEY `idx_user_list` (`userID`,`list_type`,`list_name`),
  KEY `idx_completed` (`completed`),
  KEY `idx_position` (`position`),
  KEY `idx_created` (`created`),
  KEY `idx_daily_todos` (`userID`,`list_type`,`due`,`position`),
  KEY `idx_first_added` (`added`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `todo_lists`
--

DROP TABLE IF EXISTS `todo_list`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `todo_list` (
  `id` int NOT NULL AUTO_INCREMENT,
  `listID` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `userID` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `name` varchar(100) COLLATE utf8mb4_unicode_ci NOT NULL,
  `list_type` enum('custom','planning') COLLATE utf8mb4_unicode_ci NOT NULL DEFAULT 'custom',
  `position` int NOT NULL DEFAULT '0',
  `created` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `idx_listID` (`listID`),
  KEY `unique_user_list_name` (`userID`,`name`,`list_type`),
  KEY `idx_userID` (`userID`),
  KEY `idx_user_type` (`userID`,`list_type`),
  KEY `idx_position` (`position`),
  KEY `idx_user_type_active` (`userID`,`list_type`),
  KEY `idx_user_type_position` (`userID`,`list_type`,`position`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `todo_pushedForward`
--

DROP TABLE IF EXISTS `todo_pushedForward`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `todo_pushedForward` (
  `id` int NOT NULL AUTO_INCREMENT,
  `todoID` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `created` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `idx_todoID` (`todoID`),
  KEY `idx_movide` (`todoID`,`created`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `triage`
--

DROP TABLE IF EXISTS `triage`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `triage` (
  `id` int NOT NULL AUTO_INCREMENT,
  `triageID` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `userID` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  `gmailID` varchar(255),
  `completed` datetime DEFAULT NULL,
  `created` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by` varchar(36) COLLATE utf8mb4_unicode_ci NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `idx_triage` (`triageID`),
  KEY `idx_userID` (`userID`),
  KEY `idx_gmailID` (`gmailID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `user`
--

DROP TABLE IF EXISTS `user`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user` (
  `userID` varchar(36) NOT NULL,
  `username` varchar(50) NOT NULL,
  `google_id` varchar(100) NOT NULL,
  `email` varchar(100) NOT NULL,
  `name` varchar(100) NOT NULL,
  `access_token` text,
  `refresh_token` text,
  `token_expires` datetime DEFAULT NULL,
  `active` tinyint(1) DEFAULT NULL,
  `admin` tinyint(1) DEFAULT NULL,
  `created` datetime NOT NULL,
  `created_by` varchar(36) NOT NULL,
  `approval_status` enum('pending','approved','rejected') NOT NULL DEFAULT 'pending' COMMENT 'User approval workflow status',
  PRIMARY KEY (`userID`),
  KEY `ix_user_google_id` (`google_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


--
-- Table structure for table `user_permission`
--

DROP TABLE IF EXISTS `user_permission`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_permission` (
  `id` int NOT NULL AUTO_INCREMENT,
  `userID` varchar(36) NOT NULL,
  `read` bigint DEFAULT '0',  -- bitvector
  `write` bigint DEFAULT '0',  -- bitvector
  `created` datetime DEFAULT CURRENT_TIMESTAMP,
  `created_by` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `idx_user_permissionsID` (`userID`),
  CONSTRAINT `user_permissions_ibfk_1` FOREIGN KEY (`userID`) REFERENCES `user` (`userID`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `user_permission`
--

LOCK TABLES `user_permission` WRITE;
/*!40000 ALTER TABLE `user_permission` DISABLE KEYS */;
INSERT INTO user_permission (id, userID, `read`, `write`, created, created_by)
VALUES (1,'58ec8c11-e060-4367-93cf-91a6cc28db8c','4294967295','4294967295','2025-07-20 14:02:21','58ec8c11-e060-4367-93cf-91a6cc28db8c');
/*!40000 ALTER TABLE `user_permission` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_permission`
--

DROP TABLE IF EXISTS `user_permissionAccess`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_permissionAccess` (
  `id` int NOT NULL AUTO_INCREMENT,
  `access` bigint DEFAULT NULL,
  `name` varchar(50),
  `resource` varchar(250),
  `description` varchar(250),
  `created` datetime DEFAULT CURRENT_TIMESTAMP,
  `created_by` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `idx_user_permissionAccess` (`access`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


LOCK TABLES `user_permissionAccess` WRITE;
/*!40000 ALTER TABLE `user_permissionAccess` DISABLE KEYS */;
INSERT INTO `user_permissionAccess` (access, name, resource, description, created, created_by) VALUES
  (1,   'Admin',       'admin',        'Admin functions',        '2025-12-27 00:00:00', '58ec8c11-e060-4367-93cf-91a6cc28db8c'),
  (2,   'Podcast',     'podcast',      'Podcast feed',           '2025-12-27 00:00:00', '58ec8c11-e060-4367-93cf-91a6cc28db8c'),
  (4,   'Appointment', 'appointment',  'Scheduling',             '2025-12-27 00:00:00', '58ec8c11-e060-4367-93cf-91a6cc28db8c'),
  (8,   'Dashboard',   'dashboard',    'Dashboard view',         '2025-12-27 00:00:00', '58ec8c11-e060-4367-93cf-91a6cc28db8c'),
  (16,  'Todo',        'todo',         'Todo lists',             '2025-12-27 00:00:00', '58ec8c11-e060-4367-93cf-91a6cc28db8c'),
  (32,  'Habit',       'habit',        'Habit tracking',         '2025-12-27 00:00:00', '58ec8c11-e060-4367-93cf-91a6cc28db8c'),
  (64,  'Project',     'project',      'Long-term projects',     '2025-12-27 00:00:00', '58ec8c11-e060-4367-93cf-91a6cc28db8c'),
  (128, 'Triage',      'triage',       'Triage email/calendar',  '2025-12-27 00:00:00', '58ec8c11-e060-4367-93cf-91a6cc28db8c'),
  (256, 'Bookmark',    'bookmark',     'Manage bookmarks',       '2025-12-27 00:00:00', '58ec8c11-e060-4367-93cf-91a6cc28db8c'),
  (512, 'Fitness',     'fitness',      'Fitness program',        '2025-12-27 00:00:00', '58ec8c11-e060-4367-93cf-91a6cc28db8c'),
  (1024,'Chore',       'chore',        'Household chores',       '2025-12-27 00:00:00', '58ec8c11-e060-4367-93cf-91a6cc28db8c'),
  (2048,'Book',        'book',         'Book tracker',           '2025-12-27 00:00:00', '58ec8c11-e060-4367-93cf-91a6cc28db8c'),
  (4096, 'Journal', 'journal', 'Daily questions & mood', '2025-12-27 00:00:00', '58ec8c11-e060-4367-93cf-91a6cc28db8c'),
  (8192, 'Study',   'study',   'Daily study collections', '2025-12-27 00:00:00', '58ec8c11-e060-4367-93cf-91a6cc28db8c'),
  (16384,'Quote',   'quote',   'Quote tracker',           '2025-12-27 00:00:00', '58ec8c11-e060-4367-93cf-91a6cc28db8c'),
  (32768,'Recipe',  'recipe',  'Recipe tracker',          '2026-06-05 00:00:00', '58ec8c11-e060-4367-93cf-91a6cc28db8c');
/*!40000 ALTER TABLE `user_permissionAccess` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `user_preference`
--

DROP TABLE IF EXISTS `user_preference`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `user_preference` (
  `id` int NOT NULL AUTO_INCREMENT,
  `userID` varchar(36) NOT NULL,
  `preference` varchar(50),
  `value` varchar(500) DEFAULT NULL,
  `created_by` varchar(40),
  `created` datetime DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `idx_user_preferenceID` (`userID`),
  CONSTRAINT `user_preference_ibfk_1` FOREIGN KEY (`userID`) REFERENCES `user` (`userID`) ON DELETE CASCADE
) ENGINE=InnoDB AUTO_INCREMENT=8 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


--
-- Table structure for table `vacation`
--

DROP TABLE IF EXISTS `vacation`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vacation` (
  `id` int NOT NULL AUTO_INCREMENT,
  `vacationID` varchar(36) NOT NULL,
  `userID` varchar(36) NOT NULL,
  `start` date NOT NULL,
  `end` date NOT NULL,
  `name` varchar(100) NOT NULL,
  `description` text,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_id_desc` (`id` DESC),
  KEY `userID` (`userID`),
  CONSTRAINT `vacation_period_ibfk_1` FOREIGN KEY (`userID`) REFERENCES `user` (`userID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `quote`
--

DROP TABLE IF EXISTS `quote`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `quote` (
  `id` int NOT NULL AUTO_INCREMENT,
  `quoteID` varchar(36) NOT NULL,
  `userID` varchar(36) NOT NULL,
  `body` text DEFAULT NULL,
  `author` varchar(255) DEFAULT NULL,
  `title` varchar(500) DEFAULT NULL,
  `source` varchar(1000) DEFAULT NULL,
  `tags` varchar(500) DEFAULT NULL,
  `created` datetime NOT NULL,
  `created_by` varchar(36) NOT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_quote_id` (`quoteID`),
  KEY `idx_quote_user` (`userID`),
  CONSTRAINT `fk_quote_user` FOREIGN KEY (`userID`) REFERENCES `user` (`userID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;


--
-- Table structure for table `study_collection`
--

DROP TABLE IF EXISTS `study_collection`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `study_collection` (
  `id` int NOT NULL AUTO_INCREMENT,
  `collectionID` varchar(36) NOT NULL,
  `userID` varchar(36) NOT NULL,
  `name` varchar(200) DEFAULT NULL,
  `description` text,
  `mode` enum('rate','calendar') NOT NULL DEFAULT 'rate',
  `created` datetime DEFAULT NULL,
  `created_by` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_collection_id` (`collectionID`),
  KEY `idx_collection_user` (`userID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `study_completion`
--

DROP TABLE IF EXISTS `study_completion`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `study_completion` (
  `id` int NOT NULL AUTO_INCREMENT,
  `completionID` varchar(36) NOT NULL,
  `userID` varchar(36) NOT NULL,
  `sourceID` varchar(36) NOT NULL,
  `completed_date` date NOT NULL,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_completion_id` (`completionID`),
  UNIQUE KEY `uq_user_source_date` (`userID`,`sourceID`,`completed_date`),
  KEY `idx_user_date` (`userID`,`completed_date`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `study_schedule`
--

DROP TABLE IF EXISTS `study_schedule`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `study_schedule` (
  `id` int NOT NULL AUTO_INCREMENT,
  `scheduleID` varchar(36) NOT NULL,
  `userID` varchar(36) NOT NULL,
  `sourceID` varchar(36) NOT NULL,
  `scheduled_date` date NOT NULL,
  `created` datetime NOT NULL,
  `created_by` varchar(36) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_user_source` (`userID`,`sourceID`),
  UNIQUE KEY `uq_schedule_id` (`scheduleID`),
  KEY `idx_schedule_user_date` (`userID`,`scheduled_date`),
  CONSTRAINT `fk_schedule_user` FOREIGN KEY (`userID`) REFERENCES `user` (`userID`) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `study_source`
--

DROP TABLE IF EXISTS `study_source`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `study_source` (
  `id` int NOT NULL AUTO_INCREMENT,
  `sourceID` varchar(36) NOT NULL,
  `collectionID` varchar(36) NOT NULL,
  `userID` varchar(36) NOT NULL,
  `category` varchar(100) DEFAULT NULL,
  `title` varchar(500) DEFAULT NULL,
  `subtitle` varchar(500) DEFAULT NULL,
  `author` varchar(200) DEFAULT NULL,
  `url` varchar(1000) DEFAULT NULL,
  `audio_url` varchar(1000) DEFAULT NULL,
  `audio_length` varchar(20) DEFAULT NULL,
  `order_by` int NOT NULL DEFAULT '0',
  `scheduled_date` date DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(36) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `idx_source_id` (`sourceID`),
  KEY `idx_source_collection` (`collectionID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `study_subscription`
--

DROP TABLE IF EXISTS `study_subscription`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `study_subscription` (
  `id` int NOT NULL AUTO_INCREMENT,
  `subscriptionID` varchar(36) NOT NULL,
  `userID` varchar(36) NOT NULL,
  `collectionID` varchar(36) NOT NULL,
  `per_day` int NOT NULL DEFAULT '1',
  `start_date` date DEFAULT NULL,
  `created` datetime DEFAULT NULL,
  `created_by` varchar(36) DEFAULT NULL,
  `filter_author` varchar(500) DEFAULT NULL,
  `filter_category` varchar(500) DEFAULT NULL,
  `sort_order` enum('natural','newest','oldest') NOT NULL DEFAULT 'natural',
  `limit_count` int DEFAULT NULL,
  `start_offset` int NOT NULL DEFAULT '0',
  `repeat` tinyint NOT NULL DEFAULT '1',
  `use_personal_schedule` tinyint NOT NULL DEFAULT '0',
  `name` varchar(200) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_subscription_id` (`subscriptionID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Table structure for table `recipe`
-- insert-only; soft-delete via title IS NULL
--

DROP TABLE IF EXISTS `recipe`;
CREATE TABLE `recipe` (
  `id`          INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `recipeID`    VARCHAR(36)  NOT NULL,
  `userID`      VARCHAR(36)  NOT NULL,
  `title`       VARCHAR(500) DEFAULT NULL COMMENT 'NULL = soft deleted',
  `source`      TEXT,
  `type`        VARCHAR(100),
  `servings`    VARCHAR(100),
  `prep_time`   VARCHAR(100),
  `cook_time`   VARCHAR(100),
  `ingredients` TEXT COMMENT 'JSON: [{"amount":"","unit":"","item":"","note":""}]',
  `directions`  TEXT COMMENT 'JSON: ["Step 1.", "Step 2."]',
  `notes`       TEXT,
  `position`    INT NOT NULL DEFAULT 0,
  `created`     DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `created_by`  VARCHAR(36),
  PRIMARY KEY (`id`),
  KEY `idx_recipe_user` (`userID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

--
-- Table structure for table `recipe_image`
-- direct INSERT/DELETE (not insert-only)
--

DROP TABLE IF EXISTS `recipe_image`;
CREATE TABLE `recipe_image` (
  `id`       INT UNSIGNED NOT NULL AUTO_INCREMENT,
  `imageID`  VARCHAR(36)  NOT NULL,
  `recipeID` VARCHAR(36)  NOT NULL,
  `userID`   VARCHAR(36)  NOT NULL,
  `url`      TEXT         NOT NULL COMMENT 'External URL or /static/uploads/recipes/<uuid>.<ext>',
  `caption`  VARCHAR(500),
  `position` INT NOT NULL DEFAULT 0,
  `created`  DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uq_image` (`imageID`),
  KEY `idx_image_recipe` (`recipeID`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;
/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;
