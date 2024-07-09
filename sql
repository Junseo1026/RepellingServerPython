CREATE TABLE `farm` (
  `gateway_id` bigint DEFAULT NULL,
  `id` bigint NOT NULL,
  `member_id` bigint DEFAULT NULL,
  `address` varchar(255) DEFAULT NULL,
  `farm_type` enum('GINGSENG_FIELD','ONCHARD','RICE_FARM') DEFAULT NULL,
  `name` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `UK_8ppqpbvds3dnnoas7y9mogro` (`gateway_id`),
  KEY `FKnyh3qk34tni2idhtvlccuool6` (`member_id`),
  CONSTRAINT `FKnn86yotlwhc8b4r9n736pj1y9` FOREIGN KEY (`gateway_id`) REFERENCES `gateway` (`id`),
  CONSTRAINT `FKnyh3qk34tni2idhtvlccuool6` FOREIGN KEY (`member_id`) REFERENCES `member` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


CREATE TABLE `gateway` (
  `is_activated` bit(1) DEFAULT b'0',
  `id` bigint NOT NULL,
  `ipv4` varchar(255) DEFAULT NULL,
  `serial_id` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


CREATE TABLE `member` (
  `id` bigint NOT NULL,
  `email` varchar(255) DEFAULT NULL,
  `login_id` varchar(255) DEFAULT NULL,
  `name` varchar(255) DEFAULT NULL,
  `password` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


CREATE TABLE `refresh_token` (
  `id` bigint NOT NULL,
  `member_id` bigint NOT NULL,
  `refresh_token` varchar(255) NOT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `UK_dnbbikqdsc2r2cee1afysqfk9` (`member_id`),
  CONSTRAINT `FK5gdbafb2i76hk1ai18ah6an4w` FOREIGN KEY (`member_id`) REFERENCES `member` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


CREATE TABLE `repellent_data` (
  `detection_date` date DEFAULT NULL,
  `detection_num` int DEFAULT '0',
  `detection_time` datetime(6) DEFAULT NULL,
  `farm_id` bigint DEFAULT NULL,
  `id` bigint NOT NULL,
  `member_id` bigint DEFAULT NULL,
  `re_detection_minutes` bigint DEFAULT '0',
  `repellent_device_id` bigint DEFAULT NULL,
  `repellent_sound_id` bigint DEFAULT NULL,
  `detection_type` enum('BIRD','PIG','PIR') DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `FKjocv4be6uippxphfxgujkqrqo` (`farm_id`),
  KEY `FK5jl4ilq799yt1j5qnsmg067oy` (`member_id`),
  KEY `FK39h4636f25dfblcrrepjab7lp` (`repellent_device_id`),
  KEY `FK41ehc4s8hl1cbkhthokcvpjbo` (`repellent_sound_id`),
  CONSTRAINT `FK39h4636f25dfblcrrepjab7lp` FOREIGN KEY (`repellent_device_id`) REFERENCES `repellent_device` (`id`),
  CONSTRAINT `FK41ehc4s8hl1cbkhthokcvpjbo` FOREIGN KEY (`repellent_sound_id`) REFERENCES `repellent_sound` (`id`),
  CONSTRAINT `FK5jl4ilq799yt1j5qnsmg067oy` FOREIGN KEY (`member_id`) REFERENCES `member` (`id`),
  CONSTRAINT `FKjocv4be6uippxphfxgujkqrqo` FOREIGN KEY (`farm_id`) REFERENCES `farm` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


CREATE TABLE `repellent_device` (
  `is_activated` bit(1) DEFAULT b'0',
  `is_working` bit(1) DEFAULT b'0',
  `farm_id` bigint DEFAULT NULL,
  `id` bigint NOT NULL,
  `latitude` varchar(255) DEFAULT NULL,
  `longitude` varchar(255) DEFAULT NULL,
  `name` varchar(255) DEFAULT NULL,
  `serial_id` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `FKfo2knjjwfstortre5yh8wnlva` (`farm_id`),
  CONSTRAINT `FKfo2knjjwfstortre5yh8wnlva` FOREIGN KEY (`farm_id`) REFERENCES `farm` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


CREATE TABLE `repellent_sound` (
  `sound_level` int DEFAULT NULL,
  `id` bigint NOT NULL,
  `sound_name` varchar(255) DEFAULT NULL,
  PRIMARY KEY (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
