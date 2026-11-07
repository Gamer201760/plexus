import sys
import unittest
import tempfile
from pathlib import Path
import duckdb

sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'etl'))
from additional_data import REGION_MAP, normalize_name, route_matches, optional_access


class MatchingTests(unittest.TestCase):
    def test_region_concordance_is_one_to_one(self):
        self.assertEqual(len(REGION_MAP), 82)
        self.assertEqual(len(set(REGION_MAP.values())), 82)
        self.assertEqual(REGION_MAP['khanty-mansijsk'], '71800000')
        self.assertNotIn('moscow city', REGION_MAP)

    def test_district_disambiguates_names_without_guessing(self):
        rows = [{'point_id':'1','name':'село Угут','mun_upper':'Сургутский район'},
                {'point_id':'2','name':'деревня Каюкова','mun_upper':'Сургутский район'},
                {'point_id':'3','name':'деревня Каюкова','mun_upper':'Другой район'}]
        self.assertEqual(route_matches('с.Угут - д.Каюкова','Сургутский район',rows),(['1','2'],[]))
        rows.append({'point_id':'4','name':'деревня Каюкова','mun_upper':'Сургутский район'})
        self.assertEqual(route_matches('с.Угут - д.Каюкова','Сургутский район',rows),(['1'],['д.Каюкова']))

    def test_normalization_preserves_internal_hyphens(self):
        self.assertEqual(normalize_name('посёлок Северо-Енисейский'),'северо-енисейский')

    def test_access_requires_real_times_and_preserves_missing_weights(self):
        with tempfile.TemporaryDirectory() as tmp, duckdb.connect() as con:
            path = Path(tmp)/'transport.duckdb'
            self.assertEqual(optional_access(con,path)['status'],'missing_transport_graph')
            with duckdb.connect(str(path)) as transport:
                transport.execute("create table market_cities(city varchar, oktmo varchar)")
                transport.execute("insert into market_cities values ('A','01'),('B','02')")
                transport.execute("create table np_access(point_id varchar)")
                transport.execute("create table np_city_times(season varchar, point_id varchar, city varchar, best_h double)")
                transport.execute("insert into np_city_times values ('winter','x','A',2),('winter','x','B',1),('winter','y','B',1)")
            con.execute('create table mart_np_economy(point_id varchar, market_weight_rub double, company_rows int, revenue_rows int)')
            con.execute("insert into mart_np_economy values ('01',100,1,1),('02',null,1,0)")
            result=optional_access(con,path)
            self.assertEqual(result['target_coverage'],{'targets':2,'weighted_targets':1})
            rows=con.execute('select point_id,economic_access_rub,markets_with_weight from idx_economic_np order by point_id').fetchall()
            self.assertAlmostEqual(rows[0][1],50)
            self.assertEqual(rows[1],('y',None,0))


if __name__ == '__main__':
    unittest.main()
