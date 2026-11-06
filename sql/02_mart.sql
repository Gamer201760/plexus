-- MART: муниципалитеты верхнего уровня и регионы.

-- последнее доступное значение каждой метрики по МО верхнего уровня
create or replace table mart_mo as
with latest as (
  select oktmo, metric, arg_max(value, year) as value, max(year) as year
  from stg_bdmo
  where mun_level ilike '%верхнего%' and value is not null
  group by all
),
pop as (
  select oktmo, object_name as mo_name, region, population
  from stg_settlements where object_level = 'Муниципалитет верхнего уровня'
),
np as (  -- населённые пункты внутри МО
  select left(oktmo, 5) || '000' as oktmo, count(*) as n_settlements,
         count(*) filter (population < 500) as n_small, sum(population) filter (population < 500) as pop_small
  from stg_settlements where object_level = 'Населенный пункт' group by 1
)
select p.oktmo, p.region, p.mo_name, p.population,
       np.n_settlements, np.n_small, np.pop_small,
       max(value) filter (metric = 'no_regular_transport_pct') as no_regular_transport_pct,
       max(year)  filter (metric = 'no_regular_transport_pct') as no_regular_transport_year,
       max(value) filter (metric = 'roads_substandard_pct')    as roads_substandard_pct,
       max(value) filter (metric = 'roads_local_km')           as roads_local_km
from pop p
left join latest l using (oktmo)
left join np using (oktmo)
group by all;

-- регионы: агрегаты + изолированность столицы в магистральной сети
create or replace table mart_region as
with mo as (
  select region,
         sum(population) as population,
         sum(population * no_regular_transport_pct / 100) as pop_no_transport,
         sum(population * roads_substandard_pct) / nullif(sum(population) filter (roads_substandard_pct is not null), 0) as roads_substandard_pct_w,
         sum(n_settlements) as n_settlements, sum(n_small) as n_small, sum(pop_small) as pop_small,
         count(*) filter (no_regular_transport_pct is not null) as mo_with_data, count(*) as mo_total
  from mart_mo group by 1
),
budget as (  -- 2020: последний год с разбивкой по статьям, сумма всех МО региона
  select region_name as region,
         sum(value) filter (metric = 'budget_spend_roads_krub')     as roads_krub_2020,
         sum(value) filter (metric = 'budget_spend_transport_krub') as transport_krub_2020,
         sum(value) filter (metric = 'budget_spend_total_krub')     as total_krub_2020
  from stg_bdmo where year = 2020 and mun_level ilike 'Муниципальное образование%' group by 1
),
cap as (
  select region_from as region, city_from as capital,
         count(*) filter (transport_type = 'road' and distance_hr is not null) as cap_road_links,
         count(*) filter (transport_type = 'rail' and distance_hr is not null) as cap_rail_links,
         count(*) filter (transport_type = 'air'  and distance_hr is not null) as cap_air_direct
  from stg_intercity where is_capital_from group by all
)
select mo.*,
       pop_no_transport / population as share_no_transport,
       pop_small / population as share_small_np,
       budget.roads_krub_2020, budget.transport_krub_2020, budget.total_krub_2020,
       budget.roads_krub_2020 * 1000 / mo.population as roads_rub_per_capita_2020,
       cap.capital, cap.cap_road_links, cap.cap_rail_links, cap.cap_air_direct
from mo
left join budget using (region)
left join cap using (region);
