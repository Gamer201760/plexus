import pathlib,subprocess
ROOT=pathlib.Path('data/additional/nighttime-lights')
FILES={
 'nightlights.average_viirs.v21_m_500m_s_20230101_20231231_go_epsg4326_v20250904.tif':62086259,
 'nightlights.average_viirs.v21_m_500m_s_20240101_20241231_go_epsg4326_v20250904.tif':63713625,
}
def main():
 ROOT.mkdir(parents=True,exist_ok=True)
 for name,size in FILES.items():
  dst=ROOT/name
  if dst.exists() and dst.stat().st_size==size:continue
  temp=dst.with_suffix(dst.suffix+'.part')
  url=f'https://zenodo.org/api/records/17294744/files/{name}/content'
  subprocess.run(['curl','--fail','--location','--retry','2','--connect-timeout','30','--max-time','1800','--output',str(temp),url],check=True)
  if temp.stat().st_size!=size:raise IOError(f'Unexpected file length: {name}')
  temp.replace(dst)
if __name__=='__main__':main()
