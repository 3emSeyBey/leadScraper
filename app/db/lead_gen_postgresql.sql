-- PostgreSQL SQL Dump
-- Host: 127.0.0.1
-- Generation Time: Oct 29, 2024 at 07:54 PM
-- Server version: PostgreSQL 13
-- PHP Version: 8.2.12

-- Remove MySQL-specific SQL_MODE setting
-- SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";

BEGIN;

-- Set the time zone
SET TIME ZONE '+00:00';

-- Remove MySQL-specific character set settings
-- /*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
-- /*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
-- /*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
-- /*!40101 SET NAMES utf8mb4 */;

-- Database: lead_gen

-- Table structure for table results

CREATE TABLE results (
  id SERIAL PRIMARY KEY,
  location TEXT NOT NULL,
  industry TEXT NOT NULL,
  place_id TEXT NOT NULL,
  date_generated TIMESTAMP NOT NULL,
  name TEXT NOT NULL,
  address TEXT NOT NULL,
  city TEXT NOT NULL,
  state TEXT NOT NULL,
  country TEXT NOT NULL,
  tags TEXT NOT NULL,
  phone TEXT NOT NULL,
  email TEXT NOT NULL,
  website TEXT NOT NULL,
  lat TEXT NOT NULL,         -- Changed to TEXT
  lng TEXT NOT NULL,         -- Changed to TEXT
  phones_from_website TEXT NOT NULL,
  emails_from_website TEXT NOT NULL,
  facebook TEXT NOT NULL,
  instagram TEXT NOT NULL,
  linkedin TEXT NOT NULL,
  owner_email TEXT NOT NULL,
  owner_phone TEXT NOT NULL
);

-- Remove MySQL-specific AUTO_INCREMENT setting
-- ALTER TABLE results MODIFY id cast(11 as int) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=21;

COMMIT;

-- Remove MySQL-specific character set settings
-- /*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
-- /*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
-- /*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;