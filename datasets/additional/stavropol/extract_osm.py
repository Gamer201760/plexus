import csv
import hashlib
import json
from collections import Counter
from pathlib import Path
import osmium
import pyarrow as pa
import pyarrow.parquet as pq
from shapely import wkb
from shapely.geometry import Point, LineString, mapping
from shapely.prepared import prep

ROOT = Path(__file__).resolve().parents[3]
META = Path(__file__).resolve().parent
BASE = ROOT / 'data/additional/stavropol'
SOURCE = BASE / 'raw/north-caucasus-261107.osm.pbf'
OUT = BASE / 'derived'
FACTORY = osmium.geom.WKBFactory()

class Boundary(osmium.SimpleHandler):
    def __init__(self):
        super().__init__()
        self.geometry = None
        self.tags = None
        self.relation_id = None

    def area(self, area):
        tags = dict(area.tags)
        if tags.get('admin_level') == '4' and (tags.get('name') == 'Ставропольский край' or tags.get('ISO3166-2') == 'RU-STA'):
            self.geometry = wkb.loads(FACTORY.create_multipolygon(area), hex=True)
            self.tags = tags
            self.relation_id = area.orig_id()

class Features(osmium.SimpleHandler):
    def __init__(self, boundary):
        super().__init__()
        self.boundary = prep(boundary)
        self.counts = Counter()
        self.ways = []
        self.pois = []
        self.relations = []
        self.way_ids = set()
        self.node_ids = set()

    def category(self, tags):
        if tags.get('amenity') in {'hospital','clinic','doctors','pharmacy','school','college','university'}:
            return tags['amenity']
        if tags.get('healthcare'):
            return 'healthcare:' + tags['healthcare']
        if tags.get('highway') == 'bus_stop' or tags.get('public_transport') in {'station','platform','stop_position'}:
            return 'public_transport'
        if tags.get('railway') in {'station','halt'}:
            return 'railway_station'
        if tags.get('aeroway') in {'aerodrome','terminal'}:
            return 'airport'
        return None

    def add_poi(self, kind, identifier, tags, point, method):
        category = self.category(tags)
        if category and self.boundary.covers(point):
            self.pois.append(dict(osm_type=kind,osm_id=identifier,category=category,name=tags.get('name'),lat=point.y,lon=point.x,location_method=method,tags_json=json.dumps(tags,ensure_ascii=False)))
            if kind == 'node':
                self.node_ids.add(identifier)

    def node(self, node):
        tags = dict(node.tags)
        if self.category(tags):
            self.add_poi('node',node.id,tags,Point(node.location.lon,node.location.lat),'source_node')

    def way(self, way):
        tags = dict(way.tags)
        network = bool(tags.get('highway') or tags.get('railway') or tags.get('route') == 'ferry')
        if not network and not self.category(tags):
            return
        if len(way.nodes)<2 or not all(node.location.valid() for node in way.nodes):
            self.counts['missing_geometry'] += 1
            return
        coordinates = [(node.lon,node.lat) for node in way.nodes]
        geometry = LineString(coordinates)
        if not self.boundary.intersects(geometry):
            return
        if network:
            row = {key:tags.get(key) for key in ['name','highway','railway','route','ref','bridge','tunnel','surface','oneway','access','motor_vehicle','maxspeed','maxweight','seasonal']}
            row.update(osm_way_id=way.id,version=way.version,node_ids=[node.ref for node in way.nodes],lon=[pair[0] for pair in coordinates],lat=[pair[1] for pair in coordinates],tags_json=json.dumps(tags,ensure_ascii=False))
            self.ways.append(row)
            self.way_ids.add(way.id)
            for key in ['highway','railway','bridge','oneway','maxweight','seasonal']:
                if tags.get(key) not in (None,'no'):
                    self.counts[key+'_ways'] += 1
        if self.category(tags):
            self.add_poi('way',way.id,tags,geometry.representative_point(),'representative_point_of_way_line')

    def relation(self, relation):
        tags = dict(relation.tags)
        if tags.get('type') not in {'route','restriction'}:
            return
        touched = any((member.type=='w' and member.ref in self.way_ids) or (member.type=='n' and member.ref in self.node_ids) for member in relation.members)
        if touched:
            self.relations.append(dict(osm_relation_id=relation.id,type=tags.get('type'),route=tags.get('route'),name=tags.get('name'),ref=tags.get('ref'),tags_json=json.dumps(tags,ensure_ascii=False),members_json=json.dumps([dict(type=m.type,ref=m.ref,role=m.role) for m in relation.members],ensure_ascii=False)))

def main():
    with SOURCE.open('rb') as source:
        md5 = hashlib.file_digest(source,'md5').hexdigest()
    expected = (BASE/'raw/north-caucasus-261107.osm.pbf.md5').read_text().split()[0]
    if md5 != expected:
        raise ValueError('Publisher PBF checksum mismatch')
    boundary = Boundary()
    boundary.apply_file(str(SOURCE),locations=True,idx='flex_mem')
    if boundary.geometry is None or not boundary.geometry.is_valid:
        raise ValueError('Valid regional OSM boundary missing')
    (OUT/'boundary.geojson').write_text(json.dumps(dict(type='Feature',geometry=mapping(boundary.geometry),properties=dict(osm_relation_id=boundary.relation_id,**boundary.tags)),ensure_ascii=False)+'\n')
    features = Features(boundary.geometry)
    features.apply_file(str(SOURCE),locations=True,idx='flex_mem')
    for name, rows in [('network_ways',features.ways),('osm_places',features.pois),('osm_relations',features.relations)]:
        pq.write_table(pa.Table.from_pylist(rows),OUT/(name+'.parquet'),compression='zstd')
    with (OUT/'osm_places.csv').open('w',newline='') as output:
        writer = csv.DictWriter(output,fieldnames=list(features.pois[0]));writer.writeheader();writer.writerows(features.pois)
    with osmium.io.Reader(str(SOURCE)) as reader:
        timestamp = reader.header().get('osmosis_replication_timestamp')
    profile = dict(publisher_md5_matches=True,replication_timestamp=timestamp,boundary_relation_id=boundary.relation_id,boundary_bounds=list(boundary.geometry.bounds),network_ways=len(features.ways),poi_features=len(features.pois),route_relations=sum(r['type']=='route' for r in features.relations),restriction_relations=sum(r['type']=='restriction' for r in features.relations),counts=dict(features.counts),poi_categories=dict(Counter(r['category'] for r in features.pois)),source_scope='North Caucasus Federal District',derived_scope='ways intersecting RU-STA boundary; whole crossing ways retained; POI representative points inside boundary',routable_graph=False)
    (META/'osm-profile.json').write_text(json.dumps(profile,ensure_ascii=False,indent=2)+'\n')
    print(json.dumps(profile,ensure_ascii=False))

if __name__ == '__main__':
    main()
