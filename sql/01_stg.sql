-- STG: типизированные таблицы поверх data/raw. Ключ территорий — ОКТМО.

create or replace table stg_intercity as
select city_from, region_from, oktmo_from, is_capital_from = 1 as is_capital_from, population_from, lat_from, lon_from,
       city_to,   region_to,   oktmo_to,   is_capital_to = 1   as is_capital_to,   population_to,   lat_to,   lon_to,
       transport_type, distance_km, distance_hr, missing_reason, source
from 'data/raw/intercity/*.parquet';

create or replace table stg_settlements as
select object_level, object_name, oktmo, region, mun_upper, mun_lower, settlement,
       population, latitude, longitude
from 'data/raw/settlements/*.parquet'
where object_level in ('Населенный пункт', 'Муниципалитет верхнего уровня', 'Регион', 'Город федерального значения');

-- БД ПМО: показатели в длинном формате (oktmo, год, значение)
create or replace table stg_bdmo as
with no_tr(metric, region_name, municipality, mun_level, oktmo, year, value) as (
  select 'no_regular_transport_pct' as metric, region_name, municipality, mun_level, oktmo,
         cast(year as int) as year, try_cast(replace(indicator_value, ',', '.') as double) as value
  from read_csv('data/raw/bdmo_no_regular_transport/*.csv', delim=';', header=true, all_varchar=true)
),
roads_bad(metric, region_name, municipality, mun_level, oktmo, year, value) as (
  select 'roads_substandard_pct', region_name, municipality, mun_level, oktmo,
         cast(year as int), try_cast(replace(indicator_value, ',', '.') as double)
  from read_csv('data/raw/bdmo_roads_substandard/*.csv', delim=';', header=true, all_varchar=true)
),
roads_len(metric, region_name, municipality, mun_level, oktmo, year, value) as (
  select 'roads_local_km', region_name, municipality, mun_level, oktmo, year, indicator_value
  from 'data/raw/bdmo_roads_length/*.parquet'
),
spend(metric, region_name, municipality, mun_level, oktmo, year, value) as (
  select case strashod when 'Всего' then 'budget_spend_total_krub'
                       when 'Дорожное хозяйство (дорожные фонды)' then 'budget_spend_roads_krub'
                       when 'Транспорт' then 'budget_spend_transport_krub' end,
         region_name, municipality, mun_level, oktmo, year, indicator_value
  from 'data/raw/bdmo_budget_spend/*.parquet'
  where strashod in ('Всего', 'Дорожное хозяйство (дорожные фонды)', 'Транспорт')
)
select * replace (case region_name
    when 'Архангельская область без автономного округа' then 'Архангельская область'
    when 'Тюменская область без автономных округов' then 'Тюменская область'
    else region_name end as region_name)
from (
select * from no_tr union all
select * from roads_bad union all
select * from roads_len union all
select * from spend
);
