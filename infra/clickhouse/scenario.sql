CREATE DATABASE IF NOT EXISTS plexus_scenario;
CREATE TABLE IF NOT EXISTS plexus_scenario.catalog (model_version String, artifact_version String, seasons Array(String), normalization_base Float64, assumptions Array(String)) ENGINE=MergeTree ORDER BY artifact_version;
CREATE TABLE IF NOT EXISTS plexus_scenario.cities (ordinal UInt32, id String, region String, population Float64, latitude Float64, longitude Float64, is_capital Bool) ENGINE=MergeTree ORDER BY ordinal;
CREATE TABLE IF NOT EXISTS plexus_scenario.regions (ordinal UInt32, region_id String, name String) ENGINE=MergeTree ORDER BY ordinal;
CREATE TABLE IF NOT EXISTS plexus_scenario.points (season String, point_idx UInt32, population Float64, region_idx Int32) ENGINE=MergeTree ORDER BY (season,point_idx);
CREATE TABLE IF NOT EXISTS plexus_scenario.times (season String, point_idx UInt32, city_idx UInt32, road_h Float32, best_h Float32) ENGINE=MergeTree ORDER BY (season,point_idx,city_idx);
CREATE TABLE IF NOT EXISTS plexus_scenario.city_times (season String, from_idx UInt32, to_idx UInt32, best_h Float64) ENGINE=MergeTree ORDER BY (season,from_idx,to_idx);
