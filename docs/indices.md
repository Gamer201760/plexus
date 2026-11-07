# Индексы доступности и удалённости

Считает `etl/indices.py` для каждого из 155,7 тыс. н.п. России в трёх сценариях (`road` — только дороги,
`summer` / `winter` — плюс местная авиация, зимники, реки и переправы из `data_manual/`).
Таблицы DuckDB: `idx_np`, `idx_np_gap`, `idx_mo`, `idx_region`, `idx_theil`.

Отбор: индекс используется в официальной статистике или в рецензируемых работах, где показана связь
с экономическими или социальными исходами, и считается из наших данных (время по графу OSM + магистраль Точно
+ ручные связи, население н.п.).

## Индексы

| Колонка | Что это | Откуда | Чем подтверждено влияние |
|---|---|---|---|
| `hansen_{1,2,4}h`, `hansen_idx` | Σ M_j·exp(−β t_ij), M — население 180 городов; полупериод 2 ч (1 и 4 ч — чувствительность). `hansen_idx`: РФ (road) = 100 | Hansen (1959), основа концепции кейса | «Market access» Donaldson & Hornbeck (2016, QJE): рост доступа рынков капитализируется в стоимость земли; без ЖД земля США 1890 г. стоила бы на 60 % меньше |
| `harris`, `remoteness_ca` | Рыночный потенциал Σ M_j / (t_ij + 0,5 ч); `remoteness_ca` = 1 − min-max(ln harris), 0..1 | Harris (1954); Redding & Venables (2004); Index of Remoteness, Statistics Canada | Redding & Venables: доступ к рынкам значимо объясняет различия в доходе на душу после контроля институтов и географии. Индекс StatCan — гравитационный, применяется в канадской статистике здравоохранения (CIHI) |
| `cum_pop_{1,2,4}h` | Население городов в пределах 1/2/4 ч; 4 ч — «дневная доступность» (съездить и вернуться за день) | Gutiérrez (2001); Martín, Gutiérrez, Román (2004) | Стандарт оценки эффекта ВСМ Мадрид — Барселона |
| `t_city50k_road_h`, `oecd_remote` | На машине до ближайшего города ≥50 тыс.; удалённый — > 1 ч. Регион удалённый (`oecd_remote_region`), если таких > 50 % жителей | Типология регионов OECD (Dijkstra & Ruiz 2010) | Официальная типология OECD; удалённые сельские регионы систематически отстают в росте |
| `t_city50k_best_h` | То же со всеми видами транспорта | Weiss et al. (2018, Nature), карта времени до городов | Время до городов связано с детской смертностью: −1 σ времени ≈ −9,3 смертей на 1000 рождений (Boot & Skali, AidData WP) |
| `aria`, `aria_class` | ARIA+: 5 классов центров (≥250k, ≥48k, ≥18k, ≥5k, ≥1k); время / среднее по н.п. РФ (road), cap 3, сумма 0–15. Классы по порогам ABS 0,2 / 2,4 / 5,92 / 10,53 | ARIA+, University of Adelaide / ABS | Официальная классификация удалённости Австралии: по ней распределяют надбавки медикам и финансирование |
| `lancet_2h` | ≤ 2 ч до райцентра | Lancet Commission on Global Surgery (2015): 2 ч до больницы с кесаревым, лапаротомией, открытым переломом; цель 80 % к 2030 | Индикатор Всемирного банка; удалённость от стационара повышает смертность детей до 5 лет (HR 1,52–1,74 при 40+ мин, Буркина-Фасо) |
| `km_allseason_road`, `rai_2km` | Сельский н.п. в 2 км от всесезонной дороги | SDG 9.1.1 Rural Access Index, Всемирный банк | Индикатор ЦУР ООН |
| `net_efficiency` | Σ (t_ij / t_ideal_ij)·M_j / Σ M_j, t_ideal — по прямой на 90 км/ч. 1 — как по прямой | Gutiérrez & Monzón (1998) | Показывает, где сеть «кривая»: кандидаты на новую связь |
| `exposure_manual` (`idx_np_gap`) | Доля Hansen, теряемая без ручных связей (авиа, зимники, переправы) | Site exposure, Jenelius, Petersen, Mattsson (2006) | Классика анализа уязвимости дорожной сети (север Швеции) |
| `seasonal_gap` | 1 − min/max(Hansen лето, зима) | — | Межсезонье: ледостав, ледоход |
| `gini`, `palma`, `theil` | Неравенство Hansen по жителям; Theil раскладывается на «между регионами» и «внутри» | Delbosc & Currie (2011) | Стандарт оценки транспортной справедливости |
| `access_poor_share` | Доля жителей с Hansen < 50 % медианы РФ (road) | Порог достаточности, Martens «Transport Justice» (2017) | Ставит вопрос «сколько людей ниже минимума», а не «каково среднее» |

## Адаптации и допущения

- **Время вместо км** (ARIA+ меряет км по дорогам): зимники, паромы и авиа иначе не учесть.
- **Рынки** — 180 городов из матрицы Точно (от 13 тыс. жителей). ARIA классы C–E — ближайший н.п. нужного размера по графу.
- **Lancet**: в данных нет больниц; райцентр ≈ ЦРБ. Оценка сверху: не каждая ЦРБ делает кесарево.
- **RAI**: «всесезонная» = motorway…tertiary без грунтового покрытия или любая с твёрдым покрытием,
  не сезонная, не паром; расстояние до вершин OSM, отрезки дробятся по 250 м.
- **Сельские** н.п. — все, кроме «г.», «пгт», «рп», «кп», «гп», «дп».
- **Время** > 72 ч не хранится, такие пары в Hansen дают ~0.

## Результаты (РФ)

| | road | summer | winter |
|---|---|---|---|
| жителей > 1 ч на машине до города ≥50 тыс. (OECD) | 31,8 % | 31,8 % | 31,8 % |
| ≤ 2 ч до райцентра (Lancet) | 99,57 % | 99,58 % | 99,58 % |
| сельских в 2 км от всесезонной дороги (RAI) | 94,4 % | | |
| ARIA+ remote + very remote | 4,8 % (6,2 млн чел.) | | |
| дневная доступность ≥ 1 млн | 79,1 % | | |
| Gini / Palma Hansen | 0,346 / 1,40 | | |
| Theil: между регионами / внутри | 0,153 / 0,049 | | |

По стране сезоны почти не различаются: ручные связи касаются ~200 тыс. жителей. Различие — на уровне регионов
(Чукотка: `exposure_manual` 0,38, НАО 0,13). Три четверти неравенства доступа — между регионами.

## Проверка на официальных данных

Spearman по 2 335 МО (`idx_mo` winter × `mart_mo`): доля жителей без регулярного автобусного/ЖД сообщения
с адм. центром (БД ПМО) — независимый официальный показатель изолированности.

| индекс | ρ c долей без сообщения | ρ c долей ненормативных дорог |
|---|---|---|
| `aria` | **0,46** | 0,28 |
| `share_aria_remote` | 0,41 | 0,25 |
| `rai` | −0,33 | −0,20 |
| `share_oecd_remote` | 0,27 | 0,21 |
| `share_lancet_2h` | −0,27 | −0,11 |
| `daily_access_pop` | −0,23 | −0,20 |
| `hansen_idx` | −0,18 | −0,17 |
| `net_efficiency` | 0,01 | 0,14 |

ARIA+ — лучший предиктор изолированности: многоуровневый (от сёл ≥1 тыс. до городов ≥250 тыс.).
Hansen меряет другое — доступ к крупным рынкам, слабо связан с бытовой изолированностью, — поэтому
нужны оба: Hansen для экономики, ARIA+/RAI для социальной доступности.

## Источники

- Donaldson, Hornbeck. Railroads and American Economic Growth: A “Market Access” Approach. QJE 131(2), 2016 — [NBER w19213](https://nber.org/papers/w19213), [RePEc](https://econpapers.repec.org/RePEc:oup:qjecon:v:131:y:2016:i:2:p:799-858.)
- Redding, Venables. Economic geography and international inequality. J. Int. Econ. 62(1), 2004 — [Princeton](https://collaborate.princeton.edu/en/publications/economic-geography-and-international-inequality/)
- Statistics Canada. Index of Remoteness — [описание](https://www150.statcan.gc.ca/n1/pub/17-26-0001/172600012020001-eng.htm), [метаданные 2021](https://www150.statcan.gc.ca/n1/pub/17-26-0001/2020001/meta-doc-eng.htm)
- ARIA+ — [University of Adelaide](https://able.adelaide.edu.au/hugo-centre/services/aria), [QGSO](https://www.qgso.qld.gov.au/about-statistics/statistical-standards-classifications/accessibility-remoteness-index-australia), [классы и средние расстояния (NESP)](https://www.nespsustainable.edu.au/sites/default/files/documents/IP2.02.02%20Definitions%20for%20Regional%20and%20Remote%20in%20Australia%20v2.4.pdf)
- Weiss et al. A global map of travel time to cities to assess inequalities in accessibility in 2015. Nature 553, 2018 — [ORA Oxford](https://ora.ox.ac.uk/objects/uuid:e4584ac4-b89c-488a-9f88-57b2fffc1aa8)
- Boot, Skali. Transportation infrastructure and child mortality — [AidData WPS128](https://aiddata.org/publications/transportation-infrastructure-and-child-mortality-subnational-evidence-for-22-developing-countries)
- Dijkstra, Ruiz. Refinement of the OECD regional typology, 2010 — [OECD](https://www.oecd.org/regional/regional-policy/45511797.pdf); [OECD Regions and Cities at a Glance 2026](https://www.oecd.org/en/publications/oecd-regions-and-cities-at-a-glance-2026_1fc64125-en/full-report/reader-s-guide_8338ef0b.html)
- SDG 9.1.1 Rural Access Index — [метаданные Всемирного банка](https://worldbank.github.io/sdg-metadata/metadata/en/9-1-1), [методология RAI](https://sdgtransformationcenter.org/static/docs/methodologies/RAI-methodology.pdf)
- Lancet Commission on Global Surgery, 2015 — [PubMed 26313062](https://www.pubmed.gov/26313062/), [World Bank blog](https://blogs.worldbank.org/en/opendata/measuring-surgical-systems-new-paradigm-health-systems-strengthening)
- Gutiérrez. Location, economic potential and daily accessibility… J. Transport Geography 9(4), 2001; Gutiérrez, Monzón. Accessibility, network efficiency and transport infrastructure planning. Environment and Planning A, 1998; Martín, Gutiérrez, Román. Regional Studies 38(6), 2004 — [ULPGC](https://accedacris.ulpgc.es/handle/10553/46384)
- Jenelius, Petersen, Mattsson. Importance and exposure in road network vulnerability analysis. Transp. Res. A 40(7), 2006 — [IDEAS](https://ideas.repec.org/a/eee/transa/v40y2006i7p537-560.html)
- Delbosc, Currie. Using Lorenz curves to assess public transport equity. J. Transport Geography 19(6), 2011 — [RePEc](https://econpapers.repec.org/RePEc:eee:jotrge:v:19:y:2011:i:6:p:1252-1259)
- Martens. Transport Justice: Designing Fair Transportation Systems. Routledge, 2017.
