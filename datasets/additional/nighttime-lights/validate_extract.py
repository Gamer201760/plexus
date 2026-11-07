                      




import collections,csv,hashlib,json,pathlib,sys
import numpy as np
import rasterio
from rasterio.windows import Window
ROOT=pathlib.Path('data/additional/nighttime-lights')
OUT=pathlib.Path('datasets/additional/nighttime-lights')
SOURCES=[('opengeohub_2023','nightlights.average_viirs.v21_m_500m_s_20230101_20231231_go_epsg4326_v20250904.tif',2023,62086259),('opengeohub_2024','nightlights.average_viirs.v21_m_500m_s_20240101_20241231_go_epsg4326_v20250904.tif',2024,63713625)]
def digest(path,algo='sha256'):
 h=hashlib.new(algo)
 with path.open('rb') as f:
  for chunk in iter(lambda:f.read(4*1024*1024),b''): h.update(chunk)
 return h.hexdigest()
def main():
 points=[]
 for f in sorted(pathlib.Path('data_manual/regions_input').glob('*.csv')):
  with f.open(encoding='utf-8-sig',newline='') as inp:
   for row in csv.DictReader(inp):
    points.append({'region_input_file':f.name,**{k:row[k] for k in ['point_id','name','lat','lon']}})
 reports=[]
 for label,name,year,expected_size in SOURCES:
  if len(sys.argv)>1 and label not in sys.argv[1:]:
   previous=OUT/f'validation_{label}.json'
   if previous.exists(): reports.append(json.loads(previous.read_text()))
   continue
  path=ROOT/name
  if not path.exists() or path.stat().st_size!=expected_size:
   print('Not complete, skipping',name,flush=True);continue
  print('Validating',name,flush=True)
  report={'dataset_id':label,'file':str(path),'bytes':path.stat().st_size,'sha256':digest(path),'year':year}
  report['md5']=digest(path,'md5')
  assert report['md5']=={'opengeohub_2023':'7108c72e049e2e718213816e3dad3ed2','opengeohub_2024':'0b976892d40c2d0d99177c727289eaf2'}[label]
  with rasterio.open(path) as d:
   assert d.driver=='GTiff' and d.count==1 and d.crs.to_epsg()==4326
   report.update(driver=d.driver,crs=d.crs.to_string(),width=d.width,height=d.height,bands=d.count,dtype=d.dtypes[0],nodata=d.nodata,resolution_degrees=list(d.res),resolution_arcseconds=[x*3600 for x in d.res],bounds=dict(zip(['left','bottom','right','top'],d.bounds)),transform=list(d.transform),scales=list(d.scales),offsets=list(d.offsets),block_shapes=d.block_shapes,tags=d.tags(),image_structure_tags=d.tags(ns='IMAGE_STRUCTURE'))
                                                                                        
   valid=[];nread=0
   for r in np.linspace(0,max(0,d.height-32),8,dtype=int):
    for c in np.linspace(0,max(0,d.width-32),8,dtype=int):
     ar=d.read(1,window=Window(int(c),int(r),32,32),masked=True)
     vv=ar.compressed();nread+=1
     if vv.size:valid.extend([float(vv.min()),float(vv.max())])
   report['stratified_window_read_count']=nread
   report['stratified_sample_min']=min(valid) if valid else None
   report['stratified_sample_max']=max(valid) if valid else None
   by,bx=d.block_shapes[0];groups=collections.defaultdict(list);results={}
   for i,p in enumerate(points):
    lat,lon=float(p['lat']),float(p['lon'])
    row,col=d.index(lon,lat)
    if not (0<=row<d.height and 0<=col<d.width):results[i]=(None,'outside_raster_bounds')
    else:groups[(row//by,col//bx)].append((i,row,col))
   for j,((br,bc),items) in enumerate(sorted(groups.items())):
    row0,col0=br*by,bc*bx
    a=d.read(1,window=Window(col0,row0,min(bx,d.width-col0),min(by,d.height-row0)),masked=True)
    for i,row,col in items:
     v=a[row-row0,col-col0]
     if np.ma.is_masked(v):results[i]=(None,'nodata')
     elif float(points[i]['lat'])>75:results[i]=(v.item(),'above_75N_source_coverage_caution')
     else:results[i]=(v.item(),'valid')
   counts=collections.Counter(status for value,status in results.values())
   report['settlement_sampling']={'rows':len(points),'status_counts':dict(counts),'method':'Containing pixel; raw stored band value, no interpolation or scale application','input_files':82,'blocks_read':len(groups)}
   out=ROOT/f'settlements_{label}.csv'
   fields=['region_input_file','point_id','name','lat','lon','year','raw_value','status']
   with out.open('w',encoding='utf-8',newline='') as f:
    w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
    for i,p in enumerate(points):
     value,status=results[i]
     w.writerow({**p,'year':year,'raw_value':'' if value is None else value,'status':status})
   report['settlement_sampling'].update(file=str(out),bytes=out.stat().st_size,sha256=digest(out))
  reports.append(report)
  (OUT/f'validation_{label}.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n')
  print('Validated',label,report['settlement_sampling']['status_counts'],flush=True)
 (OUT/'validation.json').write_text(json.dumps(reports,ensure_ascii=False,indent=2)+'\n')
if __name__=='__main__':main()
