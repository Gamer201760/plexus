from pathlib import Path
import json,zipfile
import pandas as pd

ROOT=Path(__file__).resolve().parents[3]
OUT=Path(__file__).resolve().parent
a=pd.read_csv(OUT/'municipal-balanced-changes-2023-2024.csv')
d=pd.read_csv(OUT/'municipal-upper-paired-2024.csv')
res={'2024_paired_distribution':{c:{'min':d[c].min(),'median':d[c].median(),'max':d[c].max(),'zero':int(d[c].eq(0).sum()),'hundred':int(d[c].eq(100).sum())} for c in ['number_road','number_service']},'balanced_changes':{c:{'improved':int(a[c].lt(0).sum()),'same':int(a[c].eq(0).sum()),'worsened':int(a[c].gt(0).sum()),'min_pp':a[c].min(),'median_pp':a[c].median(),'max_pp':a[c].max()} for c in ['road_change_pp','service_change_pp']}}
(OUT/'additional-results.json').write_text(json.dumps(res,ensure_ascii=False,indent=2))

turnover=pd.read_csv(OUT/'regional-2023-Y477110292-with-grp.csv',dtype={'object_oktmo':str})
passengers=pd.read_csv(OUT/'regional-2023-Y477110294-with-grp.csv',dtype={'object_oktmo':str})
with zipfile.ZipFile(next((ROOT/'datasets/demography/raw').glob('*.zip'))) as z:
 member=next(x for x in z.namelist() if x.endswith('.csv') and not x.startswith('__MACOSX'))
 population=pd.read_csv(z.open(member),sep=';',dtype=str,keep_default_na=False)
population=population[(population.indicator_code=='Y477010003')&(population.year=='2023')&(population.object_level=='Регион')&(~population.object_name.str.contains(r'\(с автономн',regex=True))][['object_name','object_oktmo','indicator_value']]
population['population_thousand']=pd.to_numeric(population.indicator_value)
regional=turnover[['object_name','object_oktmo','number_transport','number_grp']].rename(columns={'number_transport':'bus_passenger_km_million','number_grp':'grp_per_capita_rub'}).merge(passengers[['object_name','object_oktmo','number_transport']].rename(columns={'number_transport':'bus_passengers_million'}),on=['object_name','object_oktmo'],validate='one_to_one').merge(population[['object_name','object_oktmo','population_thousand']],on=['object_name','object_oktmo'],validate='one_to_one')
regional['bus_passenger_km_per_resident']=1000*regional.bus_passenger_km_million/regional.population_thousand
regional['bus_boardings_per_resident']=1000*regional.bus_passengers_million/regional.population_thousand
regional['mean_bus_trip_km']=regional.bus_passenger_km_million/regional.bus_passengers_million
regional.to_csv(OUT/'regional-bus-intensities-2023.csv',index=False)
rstats={c:{'n':len(regional),'min':regional[c].min(),'median':regional[c].median(),'max':regional[c].max()} for c in ['bus_passenger_km_per_resident','bus_boardings_per_resident','mean_bus_trip_km']}
(OUT/'regional-bus-intensity-summary.json').write_text(json.dumps(rstats,ensure_ascii=False,indent=2))

print('Produced descriptive regional intensity measures; curated findings.md is preserved.')
