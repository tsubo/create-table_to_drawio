CREATE TABLE `example_table` (
  `id` int unsigned NOT NULL AUTO_INCREMENT COMMENT 'サンプルテーブルID',
  `int_column` int unsigned NOT NULL COMMENT 'int 項目',
  `boolean_column` tinyint unsigned NOT NULL COMMENT 'boolean 項目',
  `varchar_column` varchar(128) COLLATE utf8mb4_unicode_ci DEFAULT NULL COMMENT 'varchar 項目',
  `text_column` text COLLATE utf8mb4_unicode_ci NOT NULL COMMENT 'text 項目',
  `created_at` timestamp NULL DEFAULT NULL,
  `updated_at` timestamp NULL DEFAULT NULL,
  PRIMARY KEY (`id`),
  KEY `example_table_int_column_index` (`int_column`)
) ENGINE = InnoDB DEFAULT CHARSET = utf8mb4 COLLATE = utf8mb4_unicode_ci COMMENT = 'サンプルテーブル'