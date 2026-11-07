                      

import hashlib,json,pathlib,datetime
ROOT=pathlib.Path('data/additional/nighttime-lights');OUT=pathlib.Path('datasets/additional/nighttime-lights')
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for c in iter(lambda:f.read(4*1024*1024),b''):h.update(c)
 return h.hexdigest()
entries=[]
for year in [2023,2024]:
 key=f'opengeohub_{year}';name=f'nightlights.average_viirs.v21_m_500m_s_{year}0101_{year}1231_go_epsg4326_v20250904.tif'
 url=(f'https://zenodo.org/api/records/17294744/files/{name}/content' if year==2023 else f'https://zenodo.org/records/17294744/files/{name}?download=1');page='https://doi.org/10.5281/zenodo.17294744'
 entry={'dataset_id':key,'year':year,'retrieval_date_utc':'2026-11-07','source_url':url,'metadata_url':page,'license':'CC-BY-4.0','license_url':'https://creativecommons.org/licenses/by/4.0/','status':'not_yet_validated'}
 p=OUT/f'validation_{key}.json'
 if p.exists():
  d=json.loads(p.read_text());entry.update(status='acquired_validated_raster',file=d['file'],bytes=d['bytes'],sha256=d['sha256'],validation_file=str(p),coverage=d['bounds'],crs=d['crs'],resolution_arcseconds=d['resolution_arcseconds'],nodata=d['nodata'],settlement_samples=d['settlement_sampling'])
 entry.update(product=f'OpenGeoHub observed-period {year} EOG annual average-masked VNL derivative; global COG includes Russia',scale_warning='Raw integers preserved. Source describes 10x radiance encoding, but band scale metadata may be 10; calibrated radiance is not asserted.',citation='Hengl (2025), DOI 10.5281/zenodo.17294744; Elvidge et al. (2021), DOI 10.3390/rs13050922')
 entries.append(entry)
metadata=[]
for p in sorted((OUT/'source').glob('*')):
 if p.is_file() and p.suffix not in ['.tmp']:
  metadata.append({'file':str(p),'bytes':p.stat().st_size,'sha256':sha(p),'type':'metadata_or_provenance_not_raster'})
result={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'datasets':entries,'metadata_files':metadata,'access_attempts_file':str(OUT/'source/access_log.json'),'settlement_input_manifest':str(OUT/'settlement_inputs.json'),'high_north_caveat':'EOG public annual product documentation gives75N limit. Rectangular derivative extent above75N does not establish valid original observations; zero cannot establish electricity access or cloud-free observation coverage.','worldpop_2023_status':'not_acquired; partial transfer stopped and removed in favor of comparable native-grid observed 2023/2024; see source/worldpop_partial_attempt.json','total_acquired_raster_bytes':sum(e.get('bytes',0) for e in entries)}
(OUT/'manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print([(e['dataset_id'],e['status']) for e in entries])
