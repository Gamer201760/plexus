from client import ClickHouse

EXPRESSION = "trimBoth(replaceRegexpAll(replaceAll(lowerUTF8(name),'ё','е'),'[\\\\s\\\\p{Z}]+',' '))"


def main():
    c=ClickHouse()
    c.request('ALTER TABLE plexus_atlas.atlas_settlements MODIFY COLUMN name_key String MATERIALIZED '+EXPRESSION)
    c.request('ALTER TABLE plexus_atlas.atlas_settlements MATERIALIZE COLUMN name_key SETTINGS mutations_sync=1')
    c.request('ALTER TABLE plexus_atlas.atlas_settlements MATERIALIZE INDEX place_name SETTINGS mutations_sync=1')
    print('search normalization materialized')

if __name__=='__main__':main()
