-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1
-- Generation Time: Oct 29, 2024 at 07:54 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `lead_gen`
--

-- --------------------------------------------------------

--
-- Table structure for table `results`
--

CREATE TABLE `results` (
  `id` int(11) NOT NULL,
  `location` text NOT NULL,
  `industry` text NOT NULL,
  `place_id` text NOT NULL,
  `date_generated` text NOT NULL,
  `name` text NOT NULL,
  `address` text NOT NULL,
  `city` text NOT NULL,
  `state` text NOT NULL,
  `country` text NOT NULL,
  `tags` text NOT NULL,
  `phone` text NOT NULL,
  `email` text NOT NULL,
  `website` text NOT NULL,
  `lat` text NOT NULL,
  `lng` text NOT NULL,
  `phones_from_website` text NOT NULL,
  `emails_from_website` text NOT NULL,
  `facebook` text NOT NULL,
  `instagram` text NOT NULL,
  `linkedin` text NOT NULL,
  `owner_email` text NOT NULL,
  `owner_phone` text NOT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `results`
--

INSERT INTO `results` (`id`, `location`, `industry`, `place_id`, `date_generated`, `name`, `address`, `city`, `state`, `country`, `tags`, `phone`, `email`, `website`, `lat`, `lng`, `phones_from_website`, `emails_from_website`, `facebook`, `instagram`, `linkedin`, `owner_email`, `owner_phone`) VALUES
(1, 'Texas', 'Window Tint', '3504916396512347812', '2024-10-30 02:31:58', 'Summit Auto Tint', '2583, North 1st Street, Abilene, Taylor County, Texas, 79603, United States', 'Taylor County', 'Texas', 'United States', 'Window tinting service', '(325) 672-1344', '', 'http://www.summitautotint.com/', '32.450855', '-99.75355', '', '', '', '', '', '', ''),
(2, 'Texas', 'Window Tint', '3188007051352737422', '2024-10-30 02:31:58', 'Precision Solar Tint', 'United Rentals, 12017, North Loop Road, San Antonio, Bexar County, Texas, 78216, United States', 'Bexar County', 'Texas', 'United States', 'Window tinting service', '(210) 849-1305', '', 'https://www.precisionsolartint.com/', '29.551985', '-98.48932', '', '', '', '', '', '', ''),
(3, 'Texas', 'Window Tint', '7534169350860496894', '2024-10-30 02:31:58', 'The Trim Shop', '104, West Marshall Avenue, Longview, Gregg County, Texas, 75601, United States', 'Gregg County', 'Texas', 'United States', 'Window tinting service', '(903) 753-7456', '', 'https://www.trimshoplongview.com/', '32.500797', '-94.738846', '', '', '', '', '', '', ''),
(4, 'Texas', 'Window Tint', '17566352472805481466', '2024-10-30 02:31:58', 'Texas Heat Auto Tint', '3901, South US Highway 287, Waxahachie, Ellis County, Texas, United States', 'Waxahachie', 'Ellis County', 'United States', 'Window tinting service', '(214) 631-9495', '', 'https://www.facebook.com/Texas-Heat-Auto-Tint-Waxahachie-TX-105068228012080', '32.333027', '-96.76046', '', '', '', '', '', '', ''),
(5, 'Texas', 'Window Tint', '15898406841956051394', '2024-10-30 02:31:58', 'Darker Shade Mobile Window Tint', '8108, Arrowhead Pool, Bridgewood, Bexar County, Texas, 78254, United States', 'Bexar County', 'Texas', 'United States', 'Window tinting service', '(210) 504-1652', '', '<coroutine object GenerateLeadsService.get_missing_website_data at 0x000002203D08CB40>', '29.51592', '-98.70382', '', '', '', '', '', '', ''),
(6, 'Texas', 'Window Tint', '12591216733043735520', '2024-10-30 02:31:58', 'XPEL San Antonio', '12814, Cogburn, San Antonio, Bexar County, Texas, 78249, United States', 'Bexar County', 'Texas', 'United States', 'Window tinting service', '(210) 678-3789', '', 'https://sanantonio-clearbra.com/', '29.566065', '-98.59804', '', '', '', '', '', '', ''),
(7, 'Texas', 'Window Tint', '14304531128643857491', '2024-10-30 02:31:58', 'Affordable Window Tint LLC', 'Texana Drive, San Antonio, Bexar County, Texas, 78249, United States', 'Bexar County', 'Texas', 'United States', 'Window tinting service', '(956) 693-0556', '', '<coroutine object GenerateLeadsService.get_missing_website_data at 0x000002203D08D340>', '29.577173', '-98.589355', '', '', '', '', '', '', ''),
(8, 'Texas', 'Window Tint', '15264940894549680684', '2024-10-30 02:31:58', 'High Performance Tint', '1302, Missouri Street, South Houston, Harris County, Texas, 77587, United States', 'Harris County', 'Texas', 'United States', 'Window tinting service', '(832) 518-7266', '', '<coroutine object GenerateLeadsService.get_missing_website_data at 0x000002203D08DB40>', '29.653824', '-95.24235', '', '', '', '', '', '', ''),
(9, 'Texas', 'Window Tint', '7234825717575381691', '2024-10-30 02:31:58', 'Texas Tint Solutions LLC', '3728, CR 123, Round Rock, Williamson County, Texas, 78664, United States', 'Williamson County', 'Texas', 'United States', 'Window tinting service', '(512) 366-2700', '', 'https://texastintsolution.com/', '30.529634', '-97.61301', '', '', '', '', '', '', ''),
(10, 'Texas', 'Window Tint', '2771066753893248051', '2024-10-30 02:31:58', 'Vive Auto Houston-Galleria - Window Tint - PPF - Ceramic Coating - Auto Detailing', 'Pilgrim Academy, 6302, Skyline Drive, Houston, Harris County, Texas, 77057, United States', 'Harris County', 'Texas', 'United States', 'Window tinting service', '(832) 479-2525', '', 'https://www.vive-houston.com/?utm_campaign=gmb', '29.728018', '-95.49361', '', '', '', '', '', '', ''),
(11, 'Texas', 'Window Tint', '18153409466810020409', '2024-10-30 02:31:58', 'Magic Tint', '1456, South Treadaway Boulevard, Abilene, Taylor County, Texas, 79602, United States', 'Taylor County', 'Texas', 'United States', 'Window tinting service', '(325) 698-0082', '', 'https://magictintabilene.com/', '32.431995', '-99.72902', '', '', '', '', '', '', ''),
(12, 'Texas', 'Window Tint', '17015402450689133039', '2024-10-30 02:31:58', 'The Tint Factory', '1359, East 3rd Street, Boydstun, Big Spring, Howard County, Texas, 79720, United States', 'Howard County', 'Texas', 'United States', 'Window tinting service', '(432) 466-4980', '', '<coroutine object GenerateLeadsService.get_missing_website_data at 0x000002203D08DA40>', '32.258175', '-101.46246', '', '', '', '', '', '', ''),
(13, 'Texas', 'Window Tint', '1515294485290519660', '2024-10-30 02:31:58', 'Solstice Glass Tinting LLC', '16228, Robinwood Lane, San Antonio, Bexar County, Texas, 78248, United States', 'Bexar County', 'Texas', 'United States', 'Window tinting service', '(210) 306-7461', '', 'http://solsticeglasstinting.com/?utm_source=gmb&utm_medium=referral', '29.596926', '-98.51983', '', '', '', '', '', '', ''),
(14, 'Texas', 'Window Tint', '16699299946227958348', '2024-10-30 02:31:58', 'Super Luxury Window Tint', '13786, Blanco Road, San Antonio, Bexar County, Texas, 78216, United States', 'Bexar County', 'Texas', 'United States', 'Auto window tinting service', '(210) 926-3060', '', 'https://superluxurytint.com/', '29.570469', '-98.51656', '', '', '', '', '', '', ''),
(15, 'Texas', 'Window Tint', '628343084967798179', '2024-10-30 02:31:58', 'Platinum Auto Films', '8335, Hudson Hollow, Wildhorse at Tausch Farms, Helotes, Bexar County, Texas, 78254, United States', 'Bexar County', 'Texas', 'United States', 'Window tinting service', '(210) 850-2902', '', 'https://txplatinumautofilms.com/', '29.51867', '-98.70169', '', '', '', '', '', '', ''),
(16, 'Texas', 'Window Tint', '8165381985471290605', '2024-10-30 02:31:58', 'Sun-Masters Glass Tinting', 'Paseo Canada, Hollywood Park, Bexar County, Texas, 78232, United States', 'Bexar County', 'Texas', 'United States', 'Window tinting service', '(210) 520-1551', '', 'http://www.sun-masters.com/', '29.607496', '-98.49342', '', '', '', '', '', '', ''),
(17, 'Texas', 'Window Tint', '197596949986907209', '2024-10-30 02:31:58', 'Visions Glass Tinting, Inc.', '177, Industrial Drive, Ten West Industrial Park, Boerne, Kendall County, Texas, 78006, United States', 'Kendall County', 'Texas', 'United States', 'Window tinting service', '(210) 213-4078', '', 'https://www.visionsglasstintingtx.com/', '29.764536', '-98.71108', '', '', '', '', '', '', ''),
(18, 'Texas', 'Window Tint', '18340663593260788362', '2024-10-30 02:31:58', 'Texas Best Window Tinting', '2522, Franklin Drive, Mesquite, Dallas County, Texas, 75150, United States', 'Dallas County', 'Texas', 'United States', 'Window tinting service', '(972) 289-9000', '', '<coroutine object GenerateLeadsService.get_missing_website_data at 0x000002203D08D440>', '32.798023', '-96.619446', '', '', '', '', '', '', ''),
(19, 'Texas', 'Window Tint', '2725694112389487910', '2024-10-30 02:31:58', 'Abilene Window Tinting', '1443, Dunnam Drive, Abilene, Taylor County, Texas, 79602, United States', 'Taylor County', 'Texas', 'United States', 'Window tinting service', '(325) 660-1812', '', 'http://abilenetinting.com/', '32.391773', '-99.740456', '', '', '', '', '', '', ''),
(20, 'Texas', 'Window Tint', '1379984490963746397', '2024-10-30 02:31:58', 'Texas Mobile Glass Tinters', '1650, Farm-to-Market Road 66, Waxahachie, Ellis County, Texas, 75167, United States', 'Ellis County', 'Texas', 'United States', 'Window tinting service', '(972) 955-3463', '', 'http://texasmobileglasstinters.com/', '32.37257', '-96.870094', '', '', '', '', '', '', '');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `results`
--
ALTER TABLE `results`
  ADD PRIMARY KEY (`id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `results`
--
ALTER TABLE `results`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=21;
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
